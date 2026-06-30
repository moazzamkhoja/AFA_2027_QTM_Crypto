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


def fetch_capped(addr, chainid, lo, hi, out, cap):
    """Like eng.fetch_transfers but aborts (raises) once eng._CALLS['getLogs'] exceeds cap so a
    high-volume token is deferred rather than partially fetched."""
    if eng._CALLS["getLogs"] >= cap:
        raise _CapHit()
    j = eng.api({"module": "logs", "action": "getLogs", "address": addr,
                 "topic0": eng.TRANSFER_TOPIC, "fromBlock": lo, "toBlock": hi},
                chainid, "getLogs")
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


def fetch_token(cmc_id, sym, chainid, addr, months):
    """Full-history Transfer fetch with per-token cap. Returns (events, mblocks, decimals,
    calls) or raises _CapHit. Writes nothing (caller checkpoints)."""
    eng._CALLS["getLogs"] = 0
    eng._CALLS["other"] = 0
    decimals = get_decimals(addr, chainid)
    last_block = eng.block_at(months[-1], chainid) or 999_999_999
    ev = []
    fetch_capped(addr, chainid, 0, last_block, ev, PER_TOKEN_CAP)
    ev.sort(key=lambda e: (e[0], e[1]))
    mblocks = {m: eng.block_at(m, chainid) for m in months}
    return ev, mblocks, decimals, dict(eng._CALLS)


SCREEN_TOPK = int(os.environ.get("SCREEN_TOPK", "20"))     # top >6m holders/month to consider
SCREEN_MAXADDR = int(os.environ.get("SCREEN_MAXADDR", "150"))  # cap unique eth_getCode calls/token


def compute_rows(cmc_id, sym, chainid, addr, ev, mblocks, decimals, obs):
    """FIFO replay -> per-month HODL shares. Contract screen applied to EVERY month using the
    union of large >6m holders across ALL months: eth_getCode is time-invariant (an address is
    a contract in every month it exists), so one classification pass cleans the whole series.
    This fixes the session-024 prototype's last-month-only screen. CEX custodial EOAs are NOT
    screened (no free label feed) -> a named residual limitation (cex_screened=False)."""
    months = list(obs.month_end)
    me_ts = {m: int(time.mktime(time.strptime(m + " 23:59:59", "%Y-%m-%d %H:%M:%S"))) for m in months}
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    scale = 10 ** decimals
    lots = defaultdict(deque)
    idx = 0
    first_block = ev[0][0] if ev else None
    # PASS 1: replay; per active month store held totals + per-address >6m holdings
    month_state = {}   # m -> {"held":{w:raw}, "per_addr_old":{a:raw}, "c":circ, "active":bool}
    for m in months:
        mb = mblocks.get(m)
        if mb is None:
            month_state[m] = {"active": None, "note": "no month-end block", "c": circ.get(m)}
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
            month_state[m] = {"active": False, "note": "pre-history", "c": circ.get(m)}
            continue
        t_now = me_ts[m]
        held = {w: 0 for w in WINDOWS}
        per_addr_old = defaultdict(int)
        for a, dq in lots.items():
            for ts, amt in dq:
                age = t_now - ts
                for w, thr in WINDOWS.items():
                    if age > thr:
                        held[w] += amt
                if age > WINDOWS["hodl_6m"]:
                    per_addr_old[a] += amt
        month_state[m] = {"active": True, "held": held, "per_addr_old": dict(per_addr_old),
                          "c": circ.get(m), "note": ""}
    # build the union of candidate contract addresses: each active month's top-K >6m holders,
    # ranked by max holding across months, capped at SCREEN_MAXADDR unique eth_getCode calls.
    maxhold = defaultdict(int)
    for m, st in month_state.items():
        if st.get("active"):
            for a, amt in sorted(st["per_addr_old"].items(), key=lambda kv: kv[1],
                                 reverse=True)[:SCREEN_TOPK]:
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
    # PASS 2: emit rows; screened = (>6m supply held by NON-contract addrs) / circulating
    rows = []
    n_screened_months = 0
    for m in months:
        st = month_state[m]
        if not st.get("active"):
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                         "hodl_6m": None, "hodl_12m": None, "hodl_6m_contractscreened": None,
                         "circulating_supply": st.get("c"),
                         "cex_screened": False, "note": st.get("note", "")})
            continue
        c = st["c"]
        held = st["held"]
        pa = st["per_addr_old"]
        old_contract = sum(amt for a, amt in pa.items() if a in contracts)
        old_total = sum(pa.values())
        screened = ((old_total - old_contract) / scale / c) if c else None
        if screened is not None:
            n_screened_months += 1
        rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                     "hodl_6m": (held["hodl_6m"] / scale / c) if c else None,
                     "hodl_12m": (held["hodl_12m"] / scale / c) if c else None,
                     "hodl_6m_contractscreened": screened,
                     "circulating_supply": c, "cex_screened": False, "note": ""})
    screen_info = {"n_candidate_addr": len(cand), "n_contracts": len(contracts),
                   "n_screened_months": n_screened_months,
                   "getcode_calls": len(cand)}
    return rows, screen_info


def load_universe():
    m = pd.read_csv(MAP)
    free = m[(m.chain.isin(CHAIN_ID)) & (m.etherscan_reachable == "yes") & (m.address.notna())]
    free = free.drop_duplicates("cmc_id")
    return [(int(r.cmc_id), str(r.symbol), CHAIN_ID[r.chain], str(r.address))
            for r in free.itertuples()]


def aggregate():
    """Rebuild channel2_holding.csv from all completed per-token checkpoints."""
    rows = []
    comp = defe = 0
    for f in sorted(RAW.glob("*.json")):
        try:
            blob = json.loads(f.read_text())
        except Exception:
            continue
        if blob.get("deferred"):
            defe += 1
            continue
        if "rows" in blob:
            rows.extend(blob["rows"])
            comp += 1
    if rows:
        df = pd.DataFrame(rows)
        # drop any private helper cols
        df = df[[c for c in df.columns if not c.startswith("_")]]
        df.to_csv(OUT, index=False)
    print(f"aggregate: {comp} completed tokens, {defe} deferred -> {OUT} ({len(rows)} rows)")
    return comp, defe, len(rows)


def main():
    if "--aggregate" in sys.argv:
        aggregate()
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
    print(f"Channel-2 panel build: {len(universe)} free-chain tokens | "
          f"PER_TOKEN_CAP={PER_TOKEN_CAP} DAILY_CAP={DAILY_CAP}")
    for cmc_id, sym, chainid, addr in universe:
        ckf = ck_path(cmc_id, sym)
        if ckf.exists():
            skipped += 1
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
        except _CapHit:
            calls_today += eng._CALLS["getLogs"] + eng._CALLS["other"]
            ckf.write_text(json.dumps({"cmc_id": cmc_id, "symbol": sym, "deferred": True,
                                       "reason": f"high-volume: >{PER_TOKEN_CAP} getLogs calls",
                                       "getLogs_calls_at_cap": eng._CALLS["getLogs"]}))
            deferred += 1
            processed += 1
            print(f"  {sym:10} cmc={cmc_id:<6} DEFERRED (>{PER_TOKEN_CAP} calls)")
            continue
        except Exception as e:
            print(f"  {sym:10} cmc={cmc_id:<6} ERROR {e} -> pending (no checkpoint)")
            calls_today += eng._CALLS["getLogs"] + eng._CALLS["other"]
            continue
        try:
            rows, screen = compute_rows(cmc_id, sym, chainid, addr, ev, mblocks, decimals, obs)
        except Exception as e:
            print(f"  {sym:10} cmc={cmc_id:<6} COMPUTE-ERROR {e} -> pending")
            calls_today += calls.get("getLogs", 0) + calls.get("other", 0)
            continue
        calls_total = eng._CALLS["getLogs"] + eng._CALLS["other"]
        calls_today += calls_total
        blob = {"cmc_id": cmc_id, "symbol": sym, "chainid": chainid, "address": addr,
                "decimals": decimals, "n_transfers": len(ev),
                "getLogs_calls": eng._CALLS["getLogs"], "other_calls": eng._CALLS["other"],
                "screen": screen, "rows": [{k: v for k, v in r.items()
                                            if not k.startswith("_")} for r in rows]}
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
            "this_run_deferred": deferred, "already_done_skipped": skipped,
            "calls_this_run": calls_today, "DAILY_CAP": DAILY_CAP,
            "PER_TOKEN_CAP": PER_TOKEN_CAP, "wall_secs": round(time.time() - t_start, 1)}
    PROG.write_text(json.dumps(prog, indent=2))
    print(f"\n=== PANEL PROGRESS ===")
    print(json.dumps(prog, indent=2))
    print(f"completed/universe = {comp}/{len(universe)}; deferred(tail) = {defe}; "
          f"pending = {len(universe) - comp - defe}")


if __name__ == "__main__":
    main()
