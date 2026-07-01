"""
phase1_channel2_panel.py  --  SESSION 025, Task B: Channel-2 (coin-age / HODL) at PANEL SCALE.

Session 024 PROVED the FIFO coin-age engine on MET and MEASURED that the free getLogs cap
binds (RAD mid-size 700+ calls, did not complete on 100k/day). Etherscan Pro (200k/day, Entry
61) unlocks the panel build. This driver REUSES the proven engine functions from
phase1_channel2_holding.py (fetch_transfers, fifo_pop, contract_screen, block_at, WINDOWS,
ZERO) -- it does NOT reimplement them -- and adds:

  * a RESUMABLE per-token checkpoint (03_data/raw/phase1_onchain/holding/<cmc>_<SYM>.json):
    a token is fetched once; reruns load its events from disk and recompute instantly.
  * a per-token CALL CAP: a token whose full Transfer history exceeds PER_TOKEN_CAP getLogs
    calls is checkpointed as `deferred` (high-volume tail) and SKIPPED, not partially built
    (a partial Transfer history would give a WRONG coin-age series). Deferred tokens are the
    documented next-session worklist, not silent failures.
  * a DAILY budget guard: stop cleanly when cumulative getLogs calls approach DAILY_CAP so a
    single run never blows the 200k/day Pro quota. The build resumes next run from the
    un-checkpointed tokens.
  * contract-address screening (eth_getCode on the top >6m holders) carried over from the
    engine -- writes BOTH raw and contract-screened HODL-6m. CEX custodial EOAs are NOT
    screened (no paid label feed) -> a NAMED limitation in the output `cex_screened` flag.

HODL metric (unchanged from the engine): share of circulating supply held by addresses in
acquisition lots older than the window (6m primary, 12m robustness) at each observed
month-end block.

Scope: the 793 free-chain EVM tokens (chain in Ethereum/Polygon/Arbitrum/Blast AND
etherscan_reachable, == getlogs_free_tier 'yes' in universe_lambda_channel_map.csv). Channel 2
is built for ALL of them regardless of existing channels -- it WIDENS the per-asset channel
count (an asset already on ch1/ch3 gains ch2).

Output: 03_data/phase1/channel2_holding.csv  (all tokens completed so far; append-merge across
        runs from the per-token checkpoints). Plus 03_data/phase1/_channel2_panel_progress.json
        (completed / deferred / pending accounting + budget consumed).

Run:  PYTHONUTF8=1 python 04_code/phase1_channel2_panel.py            # process until DAILY_CAP
      PYTHONUTF8=1 python 04_code/phase1_channel2_panel.py --aggregate # rebuild CSV from cks only
      DAILY_CAP=180000 PER_TOKEN_CAP=2500 ... python ...               # tune via env
"""
import json
import os
import sys
import time
from collections import deque, defaultdict
from pathlib import Path

import pandas as pd
import requests

import phase1_channel2_holding as eng  # the PROVEN engine (session 024)

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "03_data" / "phase1" / "universe_lambda_channel_map.csv"
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel2_holding.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "holding"
PROG = REPO / "03_data" / "phase1" / "_channel2_panel_progress.json"
RAW.mkdir(parents=True, exist_ok=True)

CHAIN_ID = {"Ethereum": 1, "Polygon": 137, "Arbitrum": 42161, "Blast": 81457}
PER_TOKEN_CAP = int(os.environ.get("PER_TOKEN_CAP", "2500"))   # calls; tail above this -> deferred
DAILY_CAP = int(os.environ.get("DAILY_CAP", "170000"))         # leave headroom under 200k Pro
WINDOWS = eng.WINDOWS
ZERO = eng.ZERO


def ck_path(cmc_id, sym):
    return RAW / f"{cmc_id}_{sym}.json"


class NetworkError(Exception):
    """A getLogs request failed all retries (DNS/connection). MUST abort the token -- treating a
    network failure as an empty block range would silently DROP transfers and corrupt the coin-age
    series (the overnight-outage bug). Raised instead of returning empty so no token is ever
    checkpointed with a partial history due to a transient network drop."""


def _robust_getlogs(addr, chainid, lo, hi, tries=6):
    """getLogs that RAISES NetworkError on network failure (vs eng.api which swallows it into an
    empty result). Distinguishes a genuine empty range (valid JSON, empty result -> returned)
    from a dropped connection (exception after all retries -> raised)."""
    eng._CALLS["getLogs"] = eng._CALLS.get("getLogs", 0) + 1
    last = None
    for t in range(1, tries + 1):
        try:
            r = requests.get(eng.BASE, params={"chainid": chainid, "apikey": eng.KEY,
                             "module": "logs", "action": "getLogs", "address": addr,
                             "topic0": eng.TRANSFER_TOPIC, "fromBlock": lo, "toBlock": hi},
                             headers=eng.H, timeout=60)
            j = r.json()
            time.sleep(eng.SLEEP)
            return j
        except Exception as e:
            last = e
            time.sleep(min(eng.SLEEP * t * 3, 20))  # backoff, capped
    raise NetworkError(f"getLogs {addr} [{lo},{hi}] failed {tries}x: {last}")


def fetch_capped(addr, chainid, lo, hi, out, cap):
    """Page getLogs in [lo,hi]; abort (raise _CapHit) once past `cap` calls so a high-volume token
    defers rather than fetching partially. NetworkError (from _robust_getlogs) propagates up so a
    dropped connection aborts+retries the token instead of silently corrupting it."""
    if eng._CALLS["getLogs"] >= cap:
        raise _CapHit()
    j = _robust_getlogs(addr, chainid, lo, hi)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_capped(addr, chainid, lo, mid, out, cap)
        fetch_capped(addr, chainid, mid + 1, hi, out, cap)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_capped(addr, chainid, lo, mid, out, cap)
        fetch_capped(addr, chainid, mid + 1, hi, out, cap)
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


class _CapHit(Exception):
    pass


def get_decimals(addr, chainid):
    j = eng.api({"module": "proxy", "action": "eth_call", "to": addr,
                 "data": "0x313ce567", "tag": "latest"}, chainid, "other")
    try:
        d = int(j["result"], 16)
        return d if 0 < d <= 36 else 18
    except Exception:
        return 18


# month-end block numbers are identical for every token on a chain -> compute once per
# (chainid, month) and reuse across the whole panel (saves ~1 getblocknobytime per token-month).
_MBLOCK_CACHE = {}


def month_block(month, chainid):
    key = (chainid, month)
    if _MBLOCK_CACHE.get(key) is None:   # (re)fetch if absent OR previously failed -- never cache
        b = eng.block_at(month, chainid)  # a None (a network-failed lookup would poison every
        if b is not None:                 # later token for this month otherwise)
            _MBLOCK_CACHE[key] = b
        return b
    return _MBLOCK_CACHE[key]


def fetch_token(cmc_id, sym, chainid, addr, months):
    """Full-history Transfer fetch with per-token cap. Returns (events, mblocks, decimals,
    calls) or raises _CapHit. Writes nothing (caller checkpoints). Month-end blocks come from
    the shared per-chain cache so they're fetched once, not once per token."""
    eng._CALLS["getLogs"] = 0
    eng._CALLS["other"] = 0
    decimals = get_decimals(addr, chainid)
    last_block = month_block(months[-1], chainid) or 999_999_999
    ev = []
    fetch_capped(addr, chainid, 0, last_block, ev, PER_TOKEN_CAP)
    ev.sort(key=lambda e: (e[0], e[1]))
    mblocks = {m: month_block(m, chainid) for m in months}
    return ev, mblocks, decimals, dict(eng._CALLS)


SCREEN_TOPK = int(os.environ.get("SCREEN_TOPK", "25"))     # top >6m holders/month to consider
SCREEN_MAXADDR = int(os.environ.get("SCREEN_MAXADDR", "150"))  # cap unique eth_getCode calls/token


def _replay(ev, mblocks, months):
    """FIFO replay over the panel months. Returns per-month aggregates needed for the HODL
    metric AND the per-month top-SCREEN_TOPK >6m holders (screen candidates). Pure, no network.
    DENOMINATOR FIX (session 025): the HODL share is measured against ON-CHAIN supply (the sum
    of all live lots at month-end), NOT CMC circulating_supply -- CMC circulating excludes
    locked/treasury/vested tokens (the Entry-49 pattern), so dividing the full on-chain coin-age
    numerator by it produced shares >100% (RAD raw 148-398%). On-chain supply is the supply
    whose age the channel actually measures, so the share is a proper fraction in [0,1]."""
    me_ts = {m: int(time.mktime(time.strptime(m + " 23:59:59", "%Y-%m-%d %H:%M:%S"))) for m in months}
    lots = defaultdict(deque)
    idx = 0
    first_block = ev[0][0] if ev else None
    state = {}   # m -> dict
    for m in months:
        mb = mblocks.get(m)
        if mb is None:
            state[m] = {"active": None, "note": "no month-end block"}
            continue
        while idx < len(ev) and ev[idx][0] <= mb:
            _, _, ts, frm, to, val = ev[idx]; idx += 1
            if val <= 0:
                continue
            if frm != ZERO:
                eng.fifo_pop(lots[frm], val)
            if to != ZERO:
                lots[to].append((ts, val))
        active = first_block is not None and mb >= first_block
        if not active:
            state[m] = {"active": False, "note": "pre-history"}
            continue
        t_now = me_ts[m]
        held = {w: 0 for w in WINDOWS}
        onchain = 0
        per_addr_old = defaultdict(int)
        for a, dq in lots.items():
            for ts, amt in dq:
                onchain += amt
                age = t_now - ts
                for w, thr in WINDOWS.items():
                    if age > thr:
                        held[w] += amt
                if age > WINDOWS["hodl_6m"]:
                    per_addr_old[a] += amt
        topk = sorted(per_addr_old.items(), key=lambda kv: kv[1], reverse=True)[:SCREEN_TOPK]
        state[m] = {"active": True, "held": held, "onchain": onchain,
                    "topk_old": topk, "note": ""}
    return state


def screen_contracts(state, chainid):
    """eth_getCode over the union of each month's top-K >6m holders (ranked by max holding,
    capped). Returns (contract_set, n_candidates). Network: <= SCREEN_MAXADDR 'other' calls."""
    maxhold = defaultdict(int)
    for st in state.values():
        if st.get("active"):
            for a, amt in st["topk_old"]:
                if amt > maxhold[a]:
                    maxhold[a] = amt
    cand = [a for a, _ in sorted(maxhold.items(), key=lambda kv: kv[1], reverse=True)[:SCREEN_MAXADDR]]
    contracts = set()
    for a in cand:
        a40 = "0x" + a[-40:]
        j = eng.api({"module": "proxy", "action": "eth_getCode", "address": a40,
                     "tag": "latest"}, chainid, "other")
        code = j.get("result", "0x")
        if code and code not in ("0x", "0x0"):
            contracts.add(a)
    return contracts, len(cand)


def rows_from_state(cmc_id, sym, state, months, decimals, contracts, circ):
    """Pure: build output rows from a replayed state + an already-computed contract set.
    hodl_6m = onchain supply in >6m lots / onchain supply (raw, incl. contracts).
    hodl_6m_contractscreened = (>6m supply held by NON-contract addrs, approximated by removing
      the contract holders among each month's top-K) / onchain supply -- the conviction signal.
    CEX custodial EOAs are NOT screened (no free label feed): named limitation cex_screened=False."""
    scale = 10 ** decimals
    rows = []
    n_scr = 0
    for m in months:
        st = state[m]
        if not st.get("active"):
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                         "hodl_6m": None, "hodl_12m": None, "hodl_6m_contractscreened": None,
                         "onchain_supply": None, "circulating_supply": circ.get(m),
                         "cex_screened": False, "note": st.get("note", "")})
            continue
        onchain = st["onchain"]
        held = st["held"]
        old_contract = sum(amt for a, amt in st["topk_old"] if a in contracts)
        old_total_topk = sum(amt for _, amt in st["topk_old"])
        # screened >6m supply = total >6m supply minus the contract part captured in top-K
        screened_old = held["hodl_6m"] - old_contract
        denom = onchain
        row = {"cmc_id": cmc_id, "symbol": sym, "month_end": m,
               "hodl_6m": (held["hodl_6m"] / denom) if denom else None,
               "hodl_12m": (held["hodl_12m"] / denom) if denom else None,
               "hodl_6m_contractscreened": (screened_old / denom) if denom else None,
               "onchain_supply": onchain / scale,
               "circulating_supply": circ.get(m), "cex_screened": False, "note": ""}
        if row["hodl_6m_contractscreened"] is not None:
            n_scr += 1
        rows.append(row)
    return rows, n_scr


def compute_rows(cmc_id, sym, chainid, addr, ev, mblocks, decimals, obs, contracts=None):
    """Full path: replay -> (screen if contracts not supplied) -> rows. Returns
    (rows, screen_info, contracts) so the caller can cache the contract set in the checkpoint."""
    months = list(obs.month_end)
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    state = _replay(ev, mblocks, months)
    n_cand = 0
    if contracts is None:
        contracts, n_cand = screen_contracts(state, chainid)
    rows, n_scr = rows_from_state(cmc_id, sym, state, months, decimals, contracts, circ)
    screen_info = {"n_candidate_addr": n_cand, "n_contracts": len(contracts),
                   "n_screened_months": n_scr, "getcode_calls": n_cand}
    return rows, screen_info, list(contracts)


def _lambda_cmc_ids():
    lp = OUT.parent / "lambda_panel.csv"
    if lp.exists():
        try:
            return set(pd.read_csv(lp)["cmc_id"].unique())
        except Exception:
            return set()
    return set()


SIZES = OUT.parent / "_channel2_sizes.csv"
HOLDER_MAX = int(os.environ.get("HOLDER_MAX", "4000"))  # tokens above this defer BY METADATA


def load_universe():
    m = pd.read_csv(MAP)
    free = m[(m.chain.isin(CHAIN_ID)) & (m.etherscan_reachable == "yes") & (m.address.notna())]
    free = free.drop_duplicates("cmc_id").copy()
    # SIZE-DRIVEN ORDERING (session 025, holder-count pre-pass phase1_channel2_sizeprobe.py):
    # attach each token's holder count (a cheap 1-call proxy for Transfer-log volume) and process
    # SMALLEST FIRST, so the session completes the maximum number of tokens per call/wall budget
    # and the high-volume tail is DEFERRED BY METADATA (main() skips fetching tokens above
    # HOLDER_MAX) instead of by hit-and-trial fetch-until-cap. No size file -> fall back to the
    # in-lambda-first ordering (still useful, just not size-aware).
    hc = {}
    if SIZES.exists():
        s = pd.read_csv(SIZES)
        hc = {int(r.cmc_id): (r.holder_count if pd.notna(r.holder_count) else None)
              for r in s.itertuples()}
    inlam = _lambda_cmc_ids()
    def keyrow(r):
        cid = int(r.cmc_id)
        h = hc.get(cid)
        # sort key: (holders known? , holders asc , in-lambda-first tiebreak). Unknown-holder
        # tokens go last (can't size them -> treat as large/unknown).
        h_sort = h if h is not None else 10 ** 12
        lam_tie = 0 if cid in inlam else 1   # among equal size, prefer in-lambda (depth headline)
        return (h_sort, lam_tie, -cid)
    free["_k0"] = [keyrow(r)[0] for r in free.itertuples()]
    free["_k1"] = [keyrow(r)[1] for r in free.itertuples()]
    free["_k2"] = [keyrow(r)[2] for r in free.itertuples()]
    free = free.sort_values(["_k0", "_k1", "_k2"])
    return [(int(r.cmc_id), str(r.symbol), CHAIN_ID[r.chain], str(r.address), hc.get(int(r.cmc_id)))
            for r in free.itertuples()]


def aggregate(recompute=False):
    """Rebuild channel2_holding.csv from all completed per-token checkpoints. With recompute=
    True, regenerate each token's rows from its stored events + cached contract set (no network)
    -- used after a methodology change (e.g. the denominator fix) so the panel updates without
    re-fetching. Checkpoints written before events were cached keep their stored rows."""
    pf = pd.read_csv(PANEL); pf["ym"] = pf["month_end"].str[:7]
    rows = []
    comp = defe = recomp = 0
    for f in sorted(RAW.glob("*.json")):
        try:
            blob = json.loads(f.read_text())
        except Exception:
            continue
        if blob.get("deferred"):
            defe += 1
            continue
        if recompute and "events" in blob and "cmc_id" in blob and "decimals" in blob:
            cmc_id = blob["cmc_id"]; sym = blob["symbol"]
            obs = pf[(pf.cmc_id == cmc_id) & (pf.status == "observed")][
                ["month_end", "ym", "circulating_supply"]].sort_values("ym")
            if obs.empty:
                continue
            ev = [(e[0], e[1], e[2], e[3], e[4], int(e[5])) for e in blob["events"]]
            mblocks = blob["mblocks"]
            months = list(obs.month_end)
            circ = dict(zip(obs.month_end, obs.circulating_supply))
            state = _replay(ev, mblocks, months)
            r, _ = rows_from_state(cmc_id, sym, state, months, blob["decimals"],
                                   set(blob.get("contracts", [])), circ)
            blob["rows"] = r
            f.write_text(json.dumps(blob))
            rows.extend(r); comp += 1; recomp += 1
        elif "rows" in blob:
            rows.extend(blob["rows"]); comp += 1
    if rows:
        df = pd.DataFrame(rows)
        df = df[[c for c in df.columns if not c.startswith("_")]]
        df.to_csv(OUT, index=False)
    print(f"aggregate: {comp} completed tokens ({recomp} recomputed), {defe} deferred -> "
          f"{OUT} ({len(rows)} rows)")
    return comp, defe, len(rows)


def main():
    if "--aggregate" in sys.argv:
        aggregate(recompute="--recompute" in sys.argv)
        return
    # Pro allows 10 calls/sec; the engine default (0.22s ~ 4.5/s) is conservative. Use ~0.12s
    # (~8/s) to roughly double throughput while staying under the rate limit. Run ONE network
    # script at a time so concurrent jobs don't jointly exceed 10/s.
    eng.SLEEP = float(os.environ.get("SLEEP", "0.12"))
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    universe = load_universe()
    # MET legacy checkpoint used a different filename (SYM.json); skip-aware via cmc check below
    completed = deferred = skipped = processed = 0
    calls_today = 0
    t_start = time.time()
    n_bymeta = 0
    net_fail_streak = 0
    print(f"Channel-2 panel build: {len(universe)} free-chain tokens | "
          f"PER_TOKEN_CAP={PER_TOKEN_CAP} DAILY_CAP={DAILY_CAP} HOLDER_MAX={HOLDER_MAX}")
    for cmc_id, sym, chainid, addr, holders in universe:
        ckf = ck_path(cmc_id, sym)
        if ckf.exists():
            skipped += 1
            continue
        # DEFER BY METADATA: skip the high-volume tail without fetching (holder count is a cheap
        # proxy for Transfer volume; the sizeprobe pre-pass measured it). No wasted cap-burning.
        if holders is not None and holders > HOLDER_MAX:
            ckf.write_text(json.dumps({"cmc_id": cmc_id, "symbol": sym, "deferred": True,
                                       "reason": f"high-volume by metadata: {int(holders)} holders "
                                                 f"> HOLDER_MAX {HOLDER_MAX}", "holder_count": int(holders)}))
            deferred += 1
            n_bymeta += 1
            continue
        if calls_today >= DAILY_CAP:
            print(f"  DAILY_CAP reached ({calls_today} calls) -> stopping; remaining tokens pending.")
            break
        obs = panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")][
            ["month_end", "ym", "circulating_supply"]].sort_values("ym")
        if obs.empty:
            ckf.write_text(json.dumps({"cmc_id": cmc_id, "symbol": sym, "deferred": True,
                                       "reason": "no observed panel months"}))
            deferred += 1
            continue
        months = list(obs.month_end)
        try:
            ev, mblocks, decimals, calls = fetch_token(cmc_id, sym, chainid, addr, months)
            net_fail_streak = 0
        except _CapHit:
            calls_today += eng._CALLS["getLogs"] + eng._CALLS["other"]
            ckf.write_text(json.dumps({"cmc_id": cmc_id, "symbol": sym, "deferred": True,
                                       "reason": f"high-volume: >{PER_TOKEN_CAP} getLogs calls",
                                       "getLogs_calls_at_cap": eng._CALLS["getLogs"]}))
            deferred += 1
            processed += 1
            print(f"  {sym:10} cmc={cmc_id:<6} DEFERRED (>{PER_TOKEN_CAP} calls)")
            continue
        except NetworkError as e:
            # a dropped connection -> NO checkpoint (token stays pending, retried next run). Wait
            # for the network to recover rather than churning the whole universe into 'pending';
            # after too many consecutive failures the network is down -> stop cleanly.
            calls_today += eng._CALLS["getLogs"] + eng._CALLS["other"]
            net_fail_streak += 1
            print(f"  {sym:10} cmc={cmc_id:<6} NETWORK-FAIL ({e}) -> pending; streak={net_fail_streak}")
            if net_fail_streak >= 8:
                print("  >=8 consecutive network failures -> network appears down; stopping cleanly.")
                break
            time.sleep(min(30 * net_fail_streak, 300))  # wait for the network to come back
            continue
        except Exception as e:
            print(f"  {sym:10} cmc={cmc_id:<6} ERROR {e} -> pending (no checkpoint)")
            calls_today += eng._CALLS["getLogs"] + eng._CALLS["other"]
            continue
        try:
            rows, screen, contracts = compute_rows(cmc_id, sym, chainid, addr, ev, mblocks,
                                                    decimals, obs)
        except Exception as e:
            print(f"  {sym:10} cmc={cmc_id:<6} COMPUTE-ERROR {e} -> pending")
            calls_today += calls.get("getLogs", 0) + calls.get("other", 0)
            continue
        calls_total = eng._CALLS["getLogs"] + eng._CALLS["other"]
        calls_today += calls_total
        # store events + contract set so the metric is RE-COMPUTABLE from checkpoint without
        # re-fetching (methodology can change -- e.g. the denominator fix this session -- via
        # `--recompute`). events as compact [bn,li,ts,frm,to,val_str] lists.
        blob = {"cmc_id": cmc_id, "symbol": sym, "chainid": chainid, "address": addr,
                "decimals": decimals, "n_transfers": len(ev),
                "getLogs_calls": eng._CALLS["getLogs"], "other_calls": eng._CALLS["other"],
                "screen": screen, "contracts": contracts,
                "events": [[e[0], e[1], e[2], e[3], e[4], str(e[5])] for e in ev],
                "mblocks": mblocks,
                "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]}
        ckf.write_text(json.dumps(blob))
        completed += 1
        processed += 1
        nz = [r for r in rows if r.get("hodl_6m") is not None]
        last = nz[-1] if nz else None
        scr = (f" scr_last={last['hodl_6m_contractscreened']:.1%}"
               if last and last.get("hodl_6m_contractscreened") is not None else "")
        print(f"  {sym:10} cmc={cmc_id:<6} tf={len(ev):>7} gl={eng._CALLS['getLogs']:>4} "
              f"code={screen['n_contracts']}/{screen['n_candidate_addr']} months={len(nz):>3}"
              f"{(' raw_last=%.1f%%'%(last['hodl_6m']*100)) if last else ''}{scr} "
              f"[today={calls_today}]")
    # rebuild the aggregate CSV from all checkpoints
    comp, defe, nrows = aggregate()
    prog = {"universe": len(universe), "completed_total": comp, "deferred_total": defe,
            "this_run_processed": processed, "this_run_completed": completed,
            "this_run_deferred": deferred, "deferred_by_metadata": n_bymeta,
            "already_done_skipped": skipped, "calls_this_run": calls_today, "DAILY_CAP": DAILY_CAP,
            "PER_TOKEN_CAP": PER_TOKEN_CAP, "HOLDER_MAX": HOLDER_MAX,
            "wall_secs": round(time.time() - t_start, 1)}
    PROG.write_text(json.dumps(prog, indent=2))
    print(f"\n=== PANEL PROGRESS ===")
    print(json.dumps(prog, indent=2))
    print(f"completed/universe = {comp}/{len(universe)}; deferred(tail) = {defe}; "
          f"pending = {len(universe) - comp - defe}")


if __name__ == "__main__":
    main()
