"""
phase1_op_delegation.py  --  SESSION 026, Task A: OP (Optimism) on-chain governance
DELEGATION via a BLOCK-WINDOWED, STREAMING DelegateVotesChanged replay.

WHY A SEPARATE SCRIPT (the prompt permits "or a separate OP-specific incremental script"):
OP (cmc 11840, Optimism chain 10, ERC20Votes at the 0x4200..0042 predeploy) was VERIFIED
FIRING in session 025 (Entry 62) but the full-history replay in
phase1_channel3_onchain_delegation.py did NOT complete (>80 min, killed). Root cause: that
builder binary-splits getLogs from block 0 to ~153 M; the first calls span 100 M+ blocks,
which Optimism's getLogs cannot serve in one shot -> the request TIMES OUT (60 s) and returns a
non-list, forcing a split; a cascade of top-level timeouts is the >80 min.

Two problems, two fixes:
  (1) TIMEOUT  -> BLOCK-WINDOWING: never issue getLogs over a range larger than BLOCK_WINDOW,
      so no single call spans a timeout-inducing block count. Within a window that returns the
      1000-log page cap, binary-split (windows are small -> splits are shallow).
  (2) VOLUME   -> STREAMING replay: OP's DelegateVotesChanged history is enormous (>579 k events
      by block 25 M alone -- the OP airdrop made hundreds of thousands of recipients self-
      delegate, and the event re-fires on every balance change of a delegated holder). Storing
      the full event list is the ~400 MB / 1 GB memory wall session 025 also hit. Instead we
      FOLD each event into the running per-delegate balance AS IT ARRIVES and snapshot the total
      at each month-end block, then DISCARD the raw log. Memory is bounded by the delegate count
      (the balance dict), not the event count. Windows are fetched in increasing block order and
      getLogs returns logs in (block, logIndex) order, so the stream is monotonic -> the
      incremental replay is identical to the batch replay in build_token (a month-end is
      snapshotted only after every event at block <= its month-end block has been folded in).

REPLAY (identical measure to every other delegation build): each delegate's latest newBalance;
at month-end block, total delegated weight = sum of latest newBalance over all delegates;
ratio = delegated / circulating supply.

GOVERNANCE WATERFALL (prompt task e, Entry 57): OP ALREADY has a Snapshot ch3_voting turnout
series, so on-chain delegation is a CROSS-CHECK only (role=crosscheck) -> written to
channel3_onchain_delegation.csv for the record, but the assembler folds ONLY role=='primary'
delegation rows into lambda. OP is NOT added as a second governance input to lambda.

Run:  PYTHONUTF8=1 python 04_code/phase1_op_delegation.py
      BLOCK_WINDOW=500000 python ...        # tune the window (default 500,000)
"""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

import phase1_channel3_onchain_delegation as dele
import phase1_channel2_stream as strm   # reuse the validated pooled-Session + rate limiter

WORKERS = int(os.environ.get("WORKERS", "8"))

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel3_onchain_delegation.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "delegation"
CK = RAW / "OP.json"

CMC_ID = 11840
SYM = "OP"
CHAINID = 10
ADDR = "0x4200000000000000000000000000000000000042"
TOPIC0 = dele.TOPIC_U256
ROLE = "crosscheck"   # OP has a Snapshot ch3_voting series -> delegation is cross-check only

BLOCK_WINDOW = int(os.environ.get("BLOCK_WINDOW", "500000"))
CK_EVERY = int(os.environ.get("CK_EVERY", "30"))   # checkpoint every N windows


def _getlogs(lo, hi):
    dele._DCALLS["n"] = dele._DCALLS.get("n", 0) + 1
    for _ in range(8):
        j = dele.api({"module": "logs", "action": "getLogs", "address": ADDR, "topic0": TOPIC0,
                      "fromBlock": lo, "toBlock": hi}, CHAINID)
        msg = (str(j.get("message", "")) + " " + str(j.get("result", ""))).lower()
        # transient per-second rate limit -> back off and retry (do NOT split/abort)
        if ("per sec" in msg or "10/sec" in msg or "max rate limit" in msg) and "daily" not in msg:
            time.sleep(0.6)
            continue
        return j
    return j


def fetch_window(lo, hi, sink):
    """Fetch [lo,hi] (hi-lo < BLOCK_WINDOW) and feed each parsed event to sink(bn,li,delegate,
    newbal) in increasing (block, logIndex) order. Binary-split on the 1000-log page cap or a
    non-list result -- but the range is already small, so this recursion is shallow and never
    spans a timeout-inducing block count. Splits are disjoint block ranges -> no double count."""
    j = _getlogs(lo, hi)
    res = j.get("result")
    if not isinstance(res, list):
        # QUOTA / RATE guard (see phase1_channel2_stream): a quota/rate-limit response must NOT
        # be split (that storms the API) -> raise to abort; the incremental checkpoint means the
        # resume picks up from the last completed window.
        msg = (str(j.get("message", "")) + " " + str(res)).lower()
        if "max daily" in msg or "daily rate limit" in msg:
            raise RuntimeError(f"DAILY quota exhausted: {msg[:100]}")
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_window(lo, mid, sink)
        fetch_window(mid + 1, hi, sink)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_window(lo, mid, sink)
        fetch_window(mid + 1, hi, sink)
        return
    for lg in res:
        try:
            data = lg["data"][2:]
            new_bal = int(data[64:128], 16) if len(data) >= 128 else 0
            delegate = lg["topics"][1]
            bn = int(lg["blockNumber"], 16)
            li = int(lg["logIndex"], 16)
        except (ValueError, KeyError, IndexError):
            continue
        sink(bn, li, delegate, new_bal)


def _robust_getlogs_op(lo, hi, tries=8):
    """Pooled-Session, rate-limited getLogs for the DelegateVotesChanged topic that RAISES on a
    genuine failure (never swallows it into an empty result -> no silent block-window gap). The
    keep-alive Session (reused from the ch2 stream engine) eliminates the connect/close churn that
    was triggering Optimism ConnectionReset storms in the serial path. Transient per-second rate
    limits are retried; only exhaustion raises."""
    dele._DCALLS["n"] = dele._DCALLS.get("n", 0) + 1
    last = None
    for t in range(1, tries + 1):
        strm._RL.acquire()
        try:
            r = strm._session().get(dele.BASE, params={
                "chainid": CHAINID, "apikey": dele.KEY, "module": "logs", "action": "getLogs",
                "address": ADDR, "topic0": TOPIC0, "fromBlock": lo, "toBlock": hi}, timeout=60)
            j = r.json()
        except Exception as e:
            last = e
            strm._TLS.session = None   # drop the broken pooled connection before retrying
            time.sleep(min(0.5 * t * t, 20))
            continue
        msg = (str(j.get("message", "")) + " " + str(j.get("result", ""))).lower()
        if ("per sec" in msg or "10/sec" in msg or "max rate limit" in msg) and "daily" not in msg:
            last = msg[:80]
            time.sleep(0.4 * t + 0.3)
            continue
        return j
    raise strm.NetworkError(f"OP getLogs [{lo},{hi}] failed {tries}x: {last}")


def fetch_window_list(lo, hi, out):
    """Recursively fetch DelegateVotesChanged in [lo,hi], appending (bn,li,delegate,newbal) to
    `out`. Binary-split on the 1000-log page cap / non-list; disjoint ranges -> each log once."""
    j = _robust_getlogs_op(lo, hi)
    res = j.get("result")
    if not isinstance(res, list):
        msg = (str(j.get("message", "")) + " " + str(res)).lower()
        if "max daily" in msg or "daily rate limit" in msg:
            raise strm.NetworkError(f"DAILY quota exhausted: {msg[:80]}")
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_window_list(lo, mid, out)
        fetch_window_list(mid + 1, hi, out)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_window_list(lo, mid, out)
        fetch_window_list(mid + 1, hi, out)
        return
    for lg in res:
        try:
            data = lg["data"][2:]
            new_bal = int(data[64:128], 16) if len(data) >= 128 else 0
            delegate = lg["topics"][1]
            bn = int(lg["blockNumber"], 16)
            li = int(lg["logIndex"], 16)
        except (ValueError, KeyError, IndexError):
            continue
        out.append((bn, li, delegate, new_bal))


class Replay:
    """Streaming DelegateVotesChanged replay. Fold events in block order; snapshot the running
    total delegated weight at each month-end block. Bounded memory: one balance per delegate."""
    def __init__(self, month_blocks):
        # month_blocks: list of (month_str, block) with block not None, sorted ascending by block
        self.month_blocks = month_blocks
        self.mi = 0
        self.bal = {}
        self.running = 0
        self.snap = {}
        self.n_events = 0
        self.first_block = None

    def load(self, bal, running, mi, snap, n_events, first_block):
        self.bal = {k: int(v) for k, v in bal.items()}
        self.running = int(running)
        self.mi = mi
        self.snap = snap
        self.n_events = n_events
        self.first_block = first_block

    def feed(self, bn, li, delegate, newbal):
        if self.first_block is None:
            self.first_block = bn
        # snapshot any month-end strictly before this block (all its events are folded in)
        while self.mi < len(self.month_blocks) and self.month_blocks[self.mi][1] < bn:
            self.snap[self.month_blocks[self.mi][0]] = self.running
            self.mi += 1
        self.running += newbal - self.bal.get(delegate, 0)
        self.bal[delegate] = newbal
        self.n_events += 1

    def finalize(self):
        # remaining months (block >= last event block) take the final running total
        while self.mi < len(self.month_blocks):
            self.snap[self.month_blocks[self.mi][0]] = self.running
            self.mi += 1


def build():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    obs = panel[(panel.cmc_id == CMC_ID) & (panel.status == "observed")][
        ["month_end", "ym", "circulating_supply"]].sort_values("ym")
    months = list(obs.month_end)

    # ---- resume state ----
    decimals = mblocks = None
    last_done = 0
    complete = False
    resume = None
    if CK.exists():
        b = json.loads(CK.read_text())
        decimals = b.get("decimals")
        mblocks = b.get("mblocks")
        last_done = b.get("last_block_done", 0)
        complete = b.get("complete", False)
        resume = b

    if decimals is None:
        decimals = dele.get_decimals(ADDR, CHAINID)
    if mblocks is None:
        mblocks = {m: dele.block_at(m, CHAINID) for m in months}
    last_block = mblocks.get(months[-1]) or 999_999_999

    month_blocks = sorted([(m, mblocks[m]) for m in months if mblocks.get(m) is not None],
                          key=lambda x: x[1])
    rep = Replay(month_blocks)
    if resume and "bal" in resume:
        rep.load(resume["bal"], resume["running"], resume["mi"], resume["snap"],
                 resume.get("n_events", 0), resume.get("first_block"))

    def save(lb, done):
        CK.write_text(json.dumps({
            "decimals": decimals, "mblocks": mblocks, "last_block_done": lb,
            "complete": done, "n_events": rep.n_events, "first_block": rep.first_block,
            "running": str(rep.running), "mi": rep.mi,
            "snap": rep.snap, "block_window": BLOCK_WINDOW,
            "bal": {k: str(v) for k, v in rep.bal.items()}}))

    if not complete:
        print(f"OP streaming replay: decimals={decimals} last_block={last_block:,} "
              f"BLOCK_WINDOW={BLOCK_WINDOW:,} resume@{last_done:,} "
              f"have {rep.n_events} events / {len(rep.bal)} delegates")
        t0 = time.time()
        lo = last_done + 1 if last_done else 0
        # CONCURRENT batched fetch (session 026): windows fetched WORKERS-at-a-time under the
        # pooled-Session + global rate limiter, in block-ordered batches (each batch fully fetched
        # + sorted before feeding the replay -> the stream stays monotonic). The pooled keep-alive
        # Session removes the connect/close churn that caused the serial path's Optimism
        # ConnectionReset storm; a genuinely failed call RAISES (no silent gap) and the run stops
        # with the checkpoint preserved (resumable).
        wins = []
        lo2 = lo
        while lo2 <= last_block:
            hi2 = min(lo2 + BLOCK_WINDOW - 1, last_block)
            wins.append((lo2, hi2)); lo2 = hi2 + 1
        n_batches = max(1, (len(wins) + WORKERS - 1) // WORKERS)
        try:
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                for bi in range(0, len(wins), WORKERS):
                    batch = wins[bi:bi + WORKERS]
                    results = [[] for _ in batch]
                    futs = [ex.submit(fetch_window_list, w[0], w[1], results[i])
                            for i, w in enumerate(batch)]
                    for fu in futs:
                        fu.result()   # raises NetworkError on genuine failure
                    evs = []
                    for r in results:
                        evs.extend(r)
                    evs.sort(key=lambda e: (e[0], e[1]))
                    for e in evs:
                        rep.feed(e[0], e[1], e[2], e[3])
                    last_done = batch[-1][1]
                    if (bi // WORKERS) % 3 == 0:
                        save(last_done, False)
                        el = time.time() - t0
                        print(f"  batch {bi//WORKERS+1}/{n_batches} block<={last_done:,} "
                              f"events={rep.n_events} delegates={len(rep.bal)} "
                              f"calls={dele._DCALLS['n']} run={rep.running/10**decimals:,.0f} {el:.0f}s",
                              flush=True)
        except strm.NetworkError as e:
            save(last_done, False)
            print(f"  OP fetch interrupted at block {last_done:,}: {e} -> checkpoint saved (resumable)",
                  flush=True)
            raise SystemExit(1)
        rep.finalize()
        save(last_block, True)
        print(f"  COMPLETE: {rep.n_events} events, {len(rep.bal)} delegates, "
              f"{dele._DCALLS['n']} calls, {time.time()-t0:.0f}s", flush=True)
    else:
        rep.finalize()
        print(f"OP already complete in checkpoint: {rep.n_events} events")

    # ---- rows ----
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    scale = 10 ** decimals
    first_event_ym = None
    if rep.first_block is not None:
        for m in months:
            if mblocks.get(m) and mblocks[m] >= rep.first_block:
                first_event_ym = m[:7]
                break
    rows = []
    for m in months:
        ym = m[:7]
        raw = rep.snap.get(m)
        delegated = (raw / scale) if raw is not None else None
        c = circ.get(m)
        active = first_event_ym is not None and ym >= first_event_ym
        ratio = (delegated / c) if (active and delegated and c and c > 0) else None
        flag = ("delegated>circulating (CMC circ excludes delegated locked/treasury supply, "
                "the Entry-49 pattern); kept un-capped & flagged, lambda z-scores rank not level"
                if (ratio is not None and ratio > 1) else "")
        rows.append({"cmc_id": CMC_ID, "symbol": SYM, "month_end": m, "ym": ym,
                     "role": ROLE, "chain_id": CHAINID,
                     "delegated_supply": delegated if active else None,
                     "circulating_supply": c, "delegation_ratio": ratio, "flag": flag,
                     "source": "etherscan getLogs DelegateVotesChanged replay (block-windowed streaming)"})

    df = pd.read_csv(OUT)
    df = df[df.cmc_id != CMC_ID]
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    df.to_csv(OUT, index=False)

    nz = [r for r in rows if r["delegation_ratio"] is not None]
    fr = rows[-1]["delegation_ratio"]
    print(f"\nwrote OP to {OUT}: {len(rows)} rows, {len(nz)} with ratio, role={ROLE}")
    finald = (rep.snap.get(months[-1]) or 0) / scale
    print(f"  n_events={rep.n_events} delegates={len(rep.bal)} first_event_ym={first_event_ym} "
          f"final_delegated={finald:,.0f} final_ratio={('%.2f%%' % (fr*100)) if fr else 'NA'}")
    if nz:
        import statistics
        rr = [r["delegation_ratio"] for r in nz]
        print(f"  ratio range {min(rr):.2%}..{max(rr):.2%} median {statistics.median(rr):.2%}")


if __name__ == "__main__":
    dele.SLEEP = float(os.environ.get("SLEEP", "0.12"))
    dele._DCALLS["n"] = 0
    build()
