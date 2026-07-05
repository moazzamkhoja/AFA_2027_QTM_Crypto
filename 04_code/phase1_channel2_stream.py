"""
phase1_channel2_stream.py  --  SESSION 026: STREAMING + CONCURRENT Channel-2 (coin-age/HODL)
engine for the HIGH-VOLUME TAIL (CRV/1INCH/SUSHI/AAVE/GMX ...).

WHY: the session-025 panel engine (phase1_channel2_panel.py) loads a token's ENTIRE Transfer
history into RAM before replaying. That is fine to ~2M transfers (FRAX 1.3M ~460MB) but OOMs on
the 100k+-holder giants (AAVE ~40M transfers ~10GB, GMX ~60M ~15GB) -- the "did not complete"
wall from Entries 59/63. It is also SERIAL (~1-1.5 calls/s, network-latency-bound) far under the
Etherscan Pro 10 calls/s ceiling.

TWO UPGRADES, output byte-identical to the validated engine:
  (1) STREAMING FIFO replay -- events are fetched in block-order batches and folded into the
      per-address FIFO lot state AS THEY ARRIVE; the running month-end HODL snapshots are taken
      when a month-end block is crossed; raw events are then DISCARDED. Memory is bounded by the
      live-address lot state (the FIFO `lots` dict), not the event count. The per-month state
      dict produced is IDENTICAL to phase1_channel2_panel._replay, so the SAME screen_contracts
      + rows_from_state produce identical rows. Validated offline against RPL's stored events
      (`--validate 2943`): the streamed rows must equal the panel engine's rows exactly.
  (2) CONCURRENT windowed fetch -- windows are fetched in parallel (ThreadPoolExecutor) under a
      global ~9 calls/s token-bucket rate limiter, in block-ordered BATCHES so the stream stays
      monotonic (a batch is fully fetched + sorted before being fed to the replay). ~6-8x the
      serial throughput while respecting the 10/s Pro limit.

Checkpoint blob is aggregate()-compatible (cmc_id/symbol/chainid/address/decimals/n_transfers/
getLogs_calls/screen/contracts/rows) but stores NO raw events (that's the point) -> `streamed:
True`; --recompute is not available for streamed tokens (documented tradeoff; the rows are
final). NetworkError on any window aborts the token WITHOUT a checkpoint (no partial history).

Run:  PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py --validate 2943      # offline gate
      WORKLIST=6538,8104,6758,7278,11857 WORKERS=8 BLOCK_WINDOW=100000 \
        PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py                     # build tail
"""
import json
import os
import sys
import threading
import time
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

import phase1_channel2_holding as eng
import phase1_channel2_panel as panel

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "03_data" / "phase1" / "universe_lambda_channel_map.csv"
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel2_holding.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "holding"
PROG = REPO / "03_data" / "phase1" / "_channel2_stream_progress.json"
SIZES = REPO / "03_data" / "phase1" / "_channel2_sizes.csv"
RAW.mkdir(parents=True, exist_ok=True)

# Session 029 (Entry 76): +BSC/+Base. The engine was already per-token multi-chain -- every
# API call passes the token's chainid (robust_getlogs / get_decimals / month_block /
# screen_contracts) -- the only mainnet-era constraint was this chain-name lookup used by
# load_worklist. Etherscan Pro V2 getLogs coverage probed live this session: 56/137/42161/8453
# all answer (BSC already proven by the session-028 BNB build).
CHAIN_ID = {"Ethereum": 1, "Polygon": 137, "Arbitrum": 42161, "Blast": 81457,
            "BSC": 56, "Base": 8453}
WINDOWS = eng.WINDOWS
ZERO = eng.ZERO
SCREEN_TOPK = panel.SCREEN_TOPK

# VALUE-SANITY cap: a real ERC20 Transfer cannot move more than the token's supply, so any
# Transfer whose value exceeds VAL_CAP_MULT x the token's max circulating supply is address-
# poisoning SPAM (fake near-max-uint256 Transfers that, replayed through FIFO, become PHANTOM lots
# the sender never held -> they dominate the coin-age on-chain-supply denominator; AAVE was
# contaminated across 2024-26 with 8e12-1e18-token phantoms). The cap is PER-TOKEN (computed from
# circulating supply per token); MAX_RAW_VAL is a universal backstop when circ is unavailable.
# Skipping such events is correctness-preserving. Mirrored in phase1_channel2_panel (VAL_CAP_MULT).
MAX_RAW_VAL = 2 ** 128
VAL_CAP_MULT = int(os.environ.get("VAL_CAP_MULT", "100"))

# Session 028 (Entry 74): per-token ABSOLUTE value cap, in TOKEN units. For tokens whose
# address-poisoning phantoms stay UNDER VAL_CAP_MULT x circ per event (AAVE: the 100x-circ
# cap left enough sub-cap phantoms to push reconstructed supply to 1.02e9 vs the real 16M,
# nulling 2024-08..2026-05 via the CONTAM_MULT guard). A real Transfer can never exceed the
# token's fixed totalSupply, so the cap for a listed token is its on-chain totalSupply
# (verified live via eth_call before listing). PER-TOKEN ONLY -- the global VAL_CAP_MULT /
# CONTAM_MULT thresholds are untouched.
PER_TOKEN_VAL_CAP = {
    7278: 16_000_000,   # AAVE: eth_call totalSupply() == 16,000,000.0 exactly (constant)
}


def compute_val_cap(circ_series, decimals):
    """Per-token raw-value cap = VAL_CAP_MULT x max(circulating_supply) x 10**decimals; falls
    back to MAX_RAW_VAL if circulating is unavailable."""
    try:
        vals = [c for c in circ_series if c is not None and c == c and c > 0]
        mx = max(vals) if vals else None
    except Exception:
        mx = None
    return int(VAL_CAP_MULT * mx * (10 ** decimals)) if mx else MAX_RAW_VAL

WORKERS = int(os.environ.get("WORKERS", "8"))
BLOCK_WINDOW = int(os.environ.get("BLOCK_WINDOW", "100000"))
RATE_PER_SEC = float(os.environ.get("RATE_PER_SEC", "8.0"))   # margin under the 10/s Pro ceiling
DAILY_CAP = int(os.environ.get("DAILY_CAP", "185000"))
PRUNE_EVERY = int(os.environ.get("PRUNE_EVERY", "1000000"))    # prune empty deques every N events


# ------------------------- global rate limiter (token bucket) -------------------------
class RateLimiter:
    """Enforce a global max call-start rate across all worker threads (min interval between
    successive call starts). Keeps concurrent getLogs under the 10/s Pro limit."""
    def __init__(self, per_sec):
        self.min_interval = 1.0 / per_sec
        self.lock = threading.Lock()
        self.next_ok = 0.0

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            wait = self.next_ok - now
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
            self.next_ok = max(now, self.next_ok) + self.min_interval


_RL = RateLimiter(RATE_PER_SEC)
_CALLS = {"getLogs": 0, "other": 0}
_CALLS_LOCK = threading.Lock()


class NetworkError(Exception):
    pass


# thread-local requests.Session so each worker REUSES its TCP/TLS connection (HTTP keep-alive)
# instead of a fresh TLS handshake per call. Without pooling, 8 concurrent workers at ~9 calls/s
# do ~9 TLS handshakes/s = several CPU cores burned on crypto for a network-bound job; with it,
# the handshake is once per connection -> CPU near-idle (the job is I/O-bound as it should be).
_TLS = threading.local()


def _session():
    s = getattr(_TLS, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update(eng.H)
        _TLS.session = s
    return s


def _bump(kind):
    with _CALLS_LOCK:
        _CALLS[kind] = _CALLS.get(kind, 0) + 1


def robust_getlogs(addr, chainid, lo, hi, tries=6):
    """Rate-limited getLogs that RAISES NetworkError on a dropped connection (never swallows it
    into an empty range -> no silent gap). Distinguishes a genuine empty range (valid JSON) from
    a connection failure (exception after all retries)."""
    _bump("getLogs")
    last = None
    for t in range(1, tries + 1):
        _RL.acquire()
        try:
            r = _session().get(eng.BASE, params={"chainid": chainid, "apikey": eng.KEY,
                               "module": "logs", "action": "getLogs", "address": addr,
                               "topic0": eng.TRANSFER_TOPIC, "fromBlock": lo, "toBlock": hi},
                               timeout=60)
            j = r.json()
        except Exception as e:
            last = e
            _TLS.session = None  # drop a possibly-broken pooled connection before retrying
            time.sleep(min(0.5 * t * t, 20))
            continue
        # TRANSIENT per-second rate limit -> back off and RETRY (do NOT abort, do NOT split).
        # Only the DAILY quota is fatal (handled by the caller's guard on the returned message).
        msg = (str(j.get("message", "")) + " " + str(j.get("result", ""))).lower()
        if ("per sec" in msg or "10/sec" in msg or "max rate limit" in msg) and "daily" not in msg:
            last = msg[:80]
            time.sleep(0.4 * t + 0.3)
            continue
        return j
    raise NetworkError(f"getLogs {addr} [{lo},{hi}] failed {tries}x: {last}")


def fetch_window(addr, chainid, lo, hi, out):
    """Fetch Transfer logs in [lo,hi], appending (bn,li,ts,frm,to,val). Binary-split on the
    1000-log page cap or a non-list result. Disjoint ranges -> each log fetched exactly once."""
    j = robust_getlogs(addr, chainid, lo, hi)
    res = j.get("result")
    if not isinstance(res, list):
        # DAILY-QUOTA guard: a daily-quota-exhausted response is NOT a "range too large" signal
        # -> splitting it would storm the API. ABORT the token (raise). (Transient per-second
        # limits are retried inside robust_getlogs and never reach here as a non-list.)
        msg = (str(j.get("message", "")) + " " + str(res)).lower()
        if "max daily" in msg or "daily rate limit" in msg:
            raise NetworkError(f"DAILY quota exhausted: {msg[:100]}")
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_window(addr, chainid, lo, mid, out)
        fetch_window(addr, chainid, mid + 1, hi, out)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_window(addr, chainid, lo, mid, out)
        fetch_window(addr, chainid, mid + 1, hi, out)
        return
    for lg in res:
        try:
            frm = lg["topics"][1]; to = lg["topics"][2]
            val = int(lg["data"], 16) if lg["data"] not in ("0x", "") else 0
            bn = int(lg["blockNumber"], 16); li = int(lg["logIndex"], 16)
            ts = int(lg["timeStamp"], 16)
        except (ValueError, KeyError, IndexError):
            continue
        out.append((bn, li, ts, frm, to, val))


# ------------------------- streaming FIFO replay -------------------------
class StreamReplay:
    """Streaming form of phase1_channel2_panel._replay. Fold Transfer events (in (block,logIndex)
    order) into per-address FIFO lots; snapshot the per-month HODL state at each month-end block.
    Produces the SAME `state` dict as _replay -> identical downstream rows. Memory bounded by the
    live lot state, not the event count."""
    def __init__(self, months, mblocks, val_cap=2 ** 128):
        self.months = months
        self.mblocks = mblocks
        self.val_cap = val_cap   # per-token spam cap (raw units); see MAX_RAW_VAL note
        self.me_ts = {m: int(time.mktime(time.strptime(m + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
                      for m in months}
        # month-end pointer over months WITH a block, in month (chronological) order
        self.state = {}
        for m in months:
            if mblocks.get(m) is None:
                self.state[m] = {"active": None, "note": "no month-end block"}
        self._sched = [(m, mblocks[m]) for m in months if mblocks.get(m) is not None]
        # _replay iterates months in chronological order; blocks are monotonic in months here
        self.mi = 0
        self.lots = defaultdict(deque)
        self.first_block = None
        self._since_prune = 0

    def _prune(self):
        """Drop addresses whose FIFO deque is empty (fully sold out). An empty deque contributes
        0 to every future snapshot and the defaultdict recreates the key if the address receives
        again -> pruning is correctness-preserving. Churn/dust-heavy giants (YFI/AAVE/GMX) leave
        millions of empty-deque keys; pruning bounds memory to live holders + recent churn."""
        self.lots = defaultdict(deque, {a: dq for a, dq in self.lots.items() if dq})
        self._since_prune = 0

    def _snapshot(self, m):
        mb = self.mblocks[m]
        active = self.first_block is not None and mb >= self.first_block
        if not active:
            self.state[m] = {"active": False, "note": "pre-history"}
            return
        t_now = self.me_ts[m]
        held = {w: 0 for w in WINDOWS}
        onchain = 0
        per_addr_old = defaultdict(int)
        for a, dq in self.lots.items():
            for ts, amt in dq:
                onchain += amt
                age = t_now - ts
                for w, thr in WINDOWS.items():
                    if age > thr:
                        held[w] += amt
                if age > WINDOWS["hodl_6m"]:
                    per_addr_old[a] += amt
        topk = sorted(per_addr_old.items(), key=lambda kv: kv[1], reverse=True)[:SCREEN_TOPK]
        self.state[m] = {"active": True, "held": held, "onchain": onchain,
                         "topk_old": topk, "note": ""}

    def feed(self, bn, li, ts, frm, to, val):
        if self.first_block is None:
            self.first_block = bn
        # snapshot every month-end strictly before this block (all its events are folded in)
        while self.mi < len(self._sched) and self._sched[self.mi][1] < bn:
            self._snapshot(self._sched[self.mi][0])
            self.mi += 1
        if val <= 0 or val >= self.val_cap:   # skip zero and address-poisoning spam (phantom lots)
            return
        # SELF-TRANSFER SKIP (session 028, Entry 74): a Transfer with from==to is a balance
        # no-op regardless of value -- but replayed as pop+append it (a) creates PHANTOM supply
        # whenever the fake value exceeds the address's live lots (the AAVE poisoning vector:
        # fake-value SELF-transfers from a 0-balance address, incl. the Entry-66 max-uint256
        # 1.16e60 and sub-cap 1e7 values that pass ANY value cap), and (b) would wrongly refresh
        # the lot age of a real holder. Skipping is an accounting identity, not a threshold.
        if frm == to:
            return
        if frm != ZERO:
            eng.fifo_pop(self.lots[frm], val)
        if to != ZERO:
            self.lots[to].append((ts, val))
        self._since_prune += 1
        if self._since_prune >= PRUNE_EVERY:
            self._prune()

    def finalize(self):
        while self.mi < len(self._sched):
            self._snapshot(self._sched[self.mi][0])
            self.mi += 1


def _replay_stream_from_events(events, months, mblocks, val_cap=2 ** 128):
    """Feed an in-memory event list (sorted) through StreamReplay -> state. Used by --validate
    to prove the streaming replay equals panel._replay on the same events (offline, no network)."""
    rep = StreamReplay(months, mblocks, val_cap)
    for e in events:
        rep.feed(e[0], e[1], e[2], e[3], e[4], int(e[5]))
    rep.finalize()
    return rep.state


# ------------------------- concurrent batched fetch + stream -------------------------
def build_token_stream(cmc_id, sym, chainid, addr, obs):
    months = list(obs.month_end)
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    decimals = panel.get_decimals(addr, chainid)
    mblocks = {m: panel.month_block(m, chainid) for m in months}
    last_block = mblocks.get(months[-1]) or 999_999_999

    if cmc_id in PER_TOKEN_VAL_CAP:
        val_cap = int(PER_TOKEN_VAL_CAP[cmc_id] * (10 ** decimals))
        print(f"    {sym}: per-token val_cap = {PER_TOKEN_VAL_CAP[cmc_id]:,} tokens "
              f"(Entry-74 totalSupply cap)", flush=True)
    else:
        val_cap = compute_val_cap(obs.circulating_supply, decimals)
    rep = StreamReplay(months, mblocks, val_cap)
    # window boundaries
    wins = []
    lo = 0
    while lo <= last_block:
        hi = min(lo + BLOCK_WINDOW - 1, last_block)
        wins.append((lo, hi))
        lo = hi + 1
    n_transfers = 0
    t0 = time.time()
    # process in block-ordered batches of WORKERS windows; fetch each batch concurrently, then
    # sort the batch's events and feed the replay in order (keeps the stream monotonic).
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for b0 in range(0, len(wins), WORKERS):
            batch = wins[b0:b0 + WORKERS]
            results = [[] for _ in batch]
            futs = {ex.submit(fetch_window, addr, chainid, w[0], w[1], results[i]): i
                    for i, w in enumerate(batch)}
            for f in futs:
                f.result()   # propagates NetworkError -> aborts token (no checkpoint)
            evs = []
            for r in results:
                evs.extend(r)
            evs.sort(key=lambda e: (e[0], e[1]))
            for e in evs:
                rep.feed(e[0], e[1], e[2], e[3], e[4], e[5])
            n_transfers += len(evs)
            if (b0 // WORKERS) % 5 == 0:
                el = time.time() - t0
                print(f"    {sym} batch {b0//WORKERS+1}/{(len(wins)+WORKERS-1)//WORKERS} "
                      f"block<={batch[-1][1]:,} tf={n_transfers} gl={_CALLS['getLogs']} "
                      f"lots={len(rep.lots)} {el:.0f}s", flush=True)
    rep.finalize()

    # identical downstream path as the panel engine
    contracts, n_cand = panel.screen_contracts(rep.state, chainid)
    rows, n_scr = panel.rows_from_state(cmc_id, sym, rep.state, months, decimals, contracts, circ)
    screen_info = {"n_candidate_addr": n_cand, "n_contracts": len(contracts),
                   "n_screened_months": n_scr, "getcode_calls": n_cand}
    return rows, screen_info, list(contracts), decimals, n_transfers, mblocks


def build_and_checkpoint(cmc_id, sym, chainid, addr, obs):
    rows, screen, contracts, decimals, n_transfers, mblocks = build_token_stream(
        cmc_id, sym, chainid, addr, obs)
    blob = {"cmc_id": cmc_id, "symbol": sym, "chainid": chainid, "address": addr,
            "decimals": decimals, "n_transfers": n_transfers,
            "getLogs_calls": _CALLS["getLogs"], "other_calls": _CALLS["other"],
            "screen": screen, "contracts": contracts, "streamed": True,
            "mblocks": mblocks,
            "rows": [{k: v for k, v in r.items() if not str(k).startswith("_")} for r in rows]}
    panel.ck_path(cmc_id, sym).write_text(json.dumps(blob))
    nz = [r for r in rows if r.get("hodl_6m_contractscreened") is not None]
    last = nz[-1] if nz else None
    import statistics
    scr = [r["hodl_6m_contractscreened"] for r in nz]
    print(f"  {sym:8} cmc={cmc_id} DONE tf={n_transfers} gl={_CALLS['getLogs']} "
          f"code={screen['n_contracts']}/{screen['n_candidate_addr']} scrMo={len(nz)} "
          f"HODLmed={statistics.median(scr)*100:.1f}% last={last['hodl_6m_contractscreened']*100:.1f}%"
          if nz else f"  {sym} DONE (no screened months)", flush=True)


# ------------------------- validate (offline) -------------------------
def validate(cmc_id):
    """Prove the streaming replay == panel._replay on a completed token's STORED events (no
    network). Loads the token's checkpoint (must have raw events -> a session-025/026 non-streamed
    token like RPL 2943), runs both replays, and asserts the resulting rows are identical."""
    fs = list(RAW.glob(f"{cmc_id}_*.json"))
    if not fs:
        print(f"validate: no checkpoint for cmc {cmc_id}")
        return False
    blob = json.loads(fs[0].read_text())
    if "events" not in blob:
        print(f"validate: checkpoint {fs[0].name} has no stored events (streamed?) -> pick a "
              f"non-streamed token like RPL 2943")
        return False
    sym = blob["symbol"]
    events = [(e[0], e[1], e[2], e[3], e[4], str(e[5])) for e in blob["events"]]
    mblocks = blob["mblocks"]
    pf = pd.read_csv(PANEL); pf["ym"] = pf["month_end"].str[:7]
    obs = pf[(pf.cmc_id == cmc_id) & (pf.status == "observed")][
        ["month_end", "ym", "circulating_supply"]].sort_values("ym")
    months = list(obs.month_end)
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    decimals = blob["decimals"]
    contracts = set(blob.get("contracts", []))

    # panel engine path (batch _replay) and streaming path, SAME events + contracts + val cap
    val_cap = compute_val_cap(obs.circulating_supply, decimals)
    ev_int = [(e[0], e[1], e[2], e[3], e[4], int(e[5])) for e in events]
    panel.set_val_cap(obs.circulating_supply, decimals)
    state_batch = panel._replay(ev_int, mblocks, months)
    rows_batch, _ = panel.rows_from_state(cmc_id, sym, state_batch, months, decimals, contracts, circ)

    state_stream = _replay_stream_from_events(events, months, mblocks, val_cap)
    rows_stream, _ = panel.rows_from_state(cmc_id, sym, state_stream, months, decimals, contracts, circ)

    # compare rows field-by-field
    assert len(rows_batch) == len(rows_stream), f"row count {len(rows_batch)} vs {len(rows_stream)}"
    diffs = 0
    for rb, rs in zip(rows_batch, rows_stream):
        for k in rb:
            a, b = rb[k], rs.get(k)
            if isinstance(a, float) and isinstance(b, float):
                if abs(a - b) > 1e-12:
                    diffs += 1; print(f"  DIFF {rb['month_end']} {k}: {a} vs {b}")
            elif a != b:
                diffs += 1; print(f"  DIFF {rb['month_end']} {k}: {a} vs {b}")
    ok = diffs == 0
    print(f"validate {sym} (cmc {cmc_id}): {len(rows_batch)} rows, {diffs} diffs -> "
          f"{'IDENTICAL ✓' if ok else 'MISMATCH ✗'}")
    # also compare the compute-critical screened series numerically
    sb = [r["hodl_6m_contractscreened"] for r in rows_batch if r["hodl_6m_contractscreened"] is not None]
    ss = [r["hodl_6m_contractscreened"] for r in rows_stream if r["hodl_6m_contractscreened"] is not None]
    print(f"  screened months batch={len(sb)} stream={len(ss)} "
          f"max|diff|={max((abs(x-y) for x,y in zip(sb,ss)), default=0):.2e}")
    return ok


def checkfetch(cmc_id):
    """End-to-end validation of the CONCURRENT FETCH + streaming pipeline: re-fetch a small
    ALREADY-DONE token via the stream path and compare its screened HODL series to the stored
    (serially-built) checkpoint. Does NOT overwrite the checkpoint. Proves the concurrent
    batched fetch returns the same events (no dropped/duplicated windows) as the serial engine."""
    fs = list(RAW.glob(f"{cmc_id}_*.json"))
    if not fs:
        print(f"checkfetch: no existing checkpoint for cmc {cmc_id}"); return False
    stored = json.loads(fs[0].read_text())
    sym = stored["symbol"]
    stored_scr = [r["hodl_6m_contractscreened"] for r in stored["rows"]
                  if r.get("hodl_6m_contractscreened") is not None]
    pf = pd.read_csv(PANEL); pf["ym"] = pf["month_end"].str[:7]
    obs = pf[(pf.cmc_id == cmc_id) & (pf.status == "observed")][
        ["month_end", "ym", "circulating_supply"]].sort_values("ym")
    print(f"checkfetch {sym} cmc={cmc_id}: fetching via concurrent stream path...")
    rows, screen, contracts, decimals, n_tf, _ = build_token_stream(
        cmc_id, sym, stored["chainid"], stored["address"], obs)
    new_scr = [r["hodl_6m_contractscreened"] for r in rows
               if r.get("hodl_6m_contractscreened") is not None]
    print(f"  stored: tf={stored.get('n_transfers')} scrMo={len(stored_scr)} | "
          f"stream: tf={n_tf} scrMo={len(new_scr)} gl={_CALLS['getLogs']}")
    if len(stored_scr) != len(new_scr):
        print(f"  MISMATCH: screened-month count differs ✗"); return False
    md = max((abs(a - b) for a, b in zip(stored_scr, new_scr)), default=0)
    tf_match = (n_tf == stored.get("n_transfers"))
    ok = md < 1e-9 and tf_match
    print(f"  transfers match={tf_match}  max|scr diff|={md:.2e} -> "
          f"{'IDENTICAL ✓' if ok else 'MISMATCH ✗'}")
    return ok


def load_worklist(cmc_ids):
    m = pd.read_csv(MAP)
    free = m[(m.chain.isin(CHAIN_ID)) & (m.etherscan_reachable == "yes") & (m.address.notna())]
    free = free.drop_duplicates("cmc_id")
    by = {int(r.cmc_id): r for r in free.itertuples()}
    out = []
    for cid in cmc_ids:
        r = by.get(cid)
        if r is None:
            print(f"  worklist: cmc {cid} not in free-chain map -> skip"); continue
        out.append((cid, str(r.symbol), CHAIN_ID[r.chain], str(r.address)))
    return out


def main():
    if "--validate" in sys.argv:
        cid = int(sys.argv[sys.argv.index("--validate") + 1])
        ok = validate(cid)
        sys.exit(0 if ok else 1)
    if "--checkfetch" in sys.argv:
        cid = int(sys.argv[sys.argv.index("--checkfetch") + 1])
        ok = checkfetch(cid)
        sys.exit(0 if ok else 1)

    wl = os.environ.get("WORKLIST", "").strip()
    if not wl:
        print("set WORKLIST=cmc1,cmc2,... (largest-value-first tail)")
        return
    universe = load_worklist([int(x) for x in wl.replace(" ", "").split(",") if x])
    panel_df = pd.read_csv(PANEL); panel_df["ym"] = panel_df["month_end"].str[:7]
    print(f"STREAM build: {len(universe)} tokens | WORKERS={WORKERS} BLOCK_WINDOW={BLOCK_WINDOW} "
          f"RATE={RATE_PER_SEC}/s DAILY_CAP={DAILY_CAP}")
    done = skipped = 0
    for cmc_id, sym, chainid, addr in universe:
        ckf = panel.ck_path(cmc_id, sym)
        if ckf.exists():
            b = json.loads(ckf.read_text())
            if not b.get("deferred"):
                print(f"  {sym} cmc={cmc_id} already complete -> skip"); skipped += 1; continue
        if _CALLS["getLogs"] >= DAILY_CAP:
            print(f"  DAILY_CAP reached ({_CALLS['getLogs']}) -> stop; rest pending."); break
        obs = panel_df[(panel_df.cmc_id == cmc_id) & (panel_df.status == "observed")][
            ["month_end", "ym", "circulating_supply"]].sort_values("ym")
        if obs.empty:
            print(f"  {sym} cmc={cmc_id} no observed months -> skip"); continue
        print(f"  --- {sym} cmc={cmc_id} chain={chainid} START (gl_so_far={_CALLS['getLogs']}) ---", flush=True)
        try:
            build_and_checkpoint(cmc_id, sym, chainid, addr, obs)
            done += 1
        except NetworkError as e:
            print(f"  {sym} cmc={cmc_id} NETWORK-ABORT {e} -> no checkpoint (pending)", flush=True)
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  {sym} cmc={cmc_id} ERROR {e} -> pending", flush=True)
    # rebuild the aggregate CSV from ALL checkpoints (session 025 + 026 stream)
    comp, defe, nrows = panel.aggregate()
    PROG.write_text(json.dumps({"done_this_run": done, "skipped": skipped,
                                "getLogs": _CALLS["getLogs"], "completed_total": comp,
                                "rows": nrows}, indent=2))
    print(f"\nSTREAM done: {done} built, {skipped} skipped, {_CALLS['getLogs']} getLogs; "
          f"aggregate -> {comp} tokens / {nrows} rows")


if __name__ == "__main__":
    eng.SLEEP = 0  # rate limiting is handled by the global token bucket, not per-call sleep
    main()
