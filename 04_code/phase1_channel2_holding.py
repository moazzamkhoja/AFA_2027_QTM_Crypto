"""
phase1_channel2_holding.py  --  SESSION 024, Task C: Channel 2 (holding duration / coin-age),
the Entry-24 gap ("the single highest-value addition"). PROTOTYPE + call-budget measurement on
ONE Ethereum token's FULL Transfer-log history, before any panel-scale scaling.

WHY THIS IS A PROTOTYPE (Entry 24): a credible coin-age series needs the ENTIRE Transfer
history of a token (every address's acquisition lots), not the targeted escrow-only logs of
Channel 1. The open question is the free-tier CALL BUDGET: full Transfer history windowed by
block vs the free 100k getLogs-calls/day cap. This script builds the engine correctly on one
token, MEASURES the getLogs call count, and extrapolates to the free-chain EVM population
(793 tokens, Entry 53) so the paid/free decision is data-driven, not assumed.

METHOD (FIFO per-address coin-age, "logs not eth_call" -- Entry 21):
  * Page ALL Transfer(from,to,value) logs (topic0 0xddf252ad...) over full history. Each log
    carries its own `timeStamp` -> NO extra calls to date a lot.
  * Replay in (block, logIndex) order maintaining, per address, a FIFO deque of acquisition
    lots (timestamp, amount):
       - mint  (from == 0x0): push a lot onto `to`.
       - burn  (to   == 0x0): FIFO-pop from `from`.
       - xfer:  FIFO-pop `value` from `from` (oldest lots first), push ONE lot onto `to`
                stamped at the transfer time (the received coins' age resets, standard
                coin-age / HODL-wave convention).
  * At each month-end (block <= month-end via getblocknobytime), HODL metric =
       share of circulating supply sitting in lots older than WINDOW (default 180d / ~6mo)
       = sum(lot.amount : month_end_time - lot.ts > WINDOW) / circulating_supply.
    A second window (365d) is reported alongside for robustness.

ADDRESS-CLASS HYGIENE (Entry-24 / spec section 0 judgment call, documented):
  The 0x0 mint/burn sink is handled structurally (not a holder). Exchange/contract/LP wallets
  inflate "supply" but are NOT holder conviction; Etherscan address labels are incomplete and
  not free at scale, so the prototype additionally screens out addresses that are CONTRACTS
  (eth_getCode non-empty) among the top balance holders only (bounded #calls), capturing LP
  pools / staking contracts / bridges / CEX hot-contract wallets without a paid label feed.
  EOAs that are CEX wallets cannot be filtered for free -> flagged as a known residual bias
  (a Phase-2 paid-label task). Both the raw and the contract-screened HODL share are written.

Output: 03_data/phase1/channel2_holding.csv  (one token; the prototype)
        03_data/raw/phase1_onchain/holding/<SYM>.json  (resumable transfer cache)
        prints the getLogs call budget + panel-scale extrapolation.
"""

import json
import sys
import time
from collections import deque, defaultdict
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel2_holding.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "holding"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = 0.22
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x0000000000000000000000000000000000000000000000000000000000000000"
WINDOWS = {"hodl_6m": 180 * 86400, "hodl_12m": 365 * 86400}

# prototype token: MET (Metronome, cmc 2873) -- a SMALL token (24,636 transfers, ~79 getLogs
# calls, fetches to completion per the budget probe) so the FIFO HODL engine can be validated
# END-TO-END on a complete history. The call-budget side of Task C is measured separately on a
# mid-size token (RAD, 204k+ transfers, 700+ calls, does NOT complete on the free tier) in
# phase1_channel2_budget_probe.py -- together they show the engine works but panel-scale
# Channel-2 blows the free getLogs cap (the Phase-2 trigger, Entry 24 / Task C2).
PROTO = {"cmc_id": 2873, "symbol": "MET", "chainid": 1,
         "address": "0x2Ebd53d035150f328bd754D6DC66B99B0eDB89aa", "decimals": 18}

_CALLS = {"getLogs": 0, "other": 0}


def api(params, chainid, kind="other", tries=5):
    _CALLS[kind] = _CALLS.get(kind, 0) + 1
    for t in range(1, tries + 1):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, **params},
                             headers=H, timeout=60)
            j = r.json()
            time.sleep(SLEEP)
            return j
        except Exception as e:
            print(f"    retry {t}: {e}")
            time.sleep(SLEEP * t * 2)
    return {"status": "0", "result": []}


def block_at(date_str, chainid, tries=4):
    ts = int(time.mktime(time.strptime(date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
    for _ in range(tries):
        j = api({"module": "block", "action": "getblocknobytime",
                 "timestamp": ts, "closest": "before"}, chainid)
        try:
            return int(j["result"])
        except Exception:
            time.sleep(0.5)
    return None


def fetch_transfers(addr, chainid, lo, hi, out):
    j = api({"module": "logs", "action": "getLogs", "address": addr,
             "topic0": TRANSFER_TOPIC, "fromBlock": lo, "toBlock": hi}, chainid, "getLogs")
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_transfers(addr, chainid, lo, mid, out)
        fetch_transfers(addr, chainid, mid + 1, hi, out)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_transfers(addr, chainid, lo, mid, out)
        fetch_transfers(addr, chainid, mid + 1, hi, out)
        return
    for lg in res:
        try:
            frm = lg["topics"][1]
            to = lg["topics"][2]
            val = int(lg["data"], 16) if lg["data"] not in ("0x", "") else 0
            bn = int(lg["blockNumber"], 16)
            li = int(lg["logIndex"], 16)
            ts = int(lg["timeStamp"], 16)
        except (ValueError, KeyError, IndexError):
            continue
        out.append((bn, li, ts, frm, to, val))


def fifo_pop(dq, amount):
    """Remove `amount` from the oldest lots in deque dq (FIFO)."""
    rem = amount
    while rem > 0 and dq:
        ts, amt = dq[0]
        if amt <= rem:
            rem -= amt
            dq.popleft()
        else:
            dq[0] = (ts, amt - rem)
            rem = 0


def build(token):
    cmc_id, sym, chainid, addr, dec = (token["cmc_id"], token["symbol"], token["chainid"],
                                       token["address"], token["decimals"])
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    obs = panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")][
        ["month_end", "ym", "circulating_supply"]].sort_values("ym")
    months = list(obs.month_end)
    ckf = RAW / f"{sym}.json"

    if ckf.exists():
        blob = json.loads(ckf.read_text())
        ev = [(e[0], e[1], e[2], e[3], e[4], int(e[5])) for e in blob["events"]]
        mblocks = blob["mblocks"]
        calls = blob.get("calls", {})
    else:
        last_block = block_at(months[-1], chainid) or 999_999_999
        ev = []
        t0 = time.time()
        fetch_transfers(addr, chainid, 0, last_block, ev)
        ev.sort(key=lambda e: (e[0], e[1]))
        mblocks = {m: block_at(m, chainid) for m in months}
        calls = dict(_CALLS)
        calls["seconds"] = round(time.time() - t0, 1)
        ckf.write_text(json.dumps({"events": [[e[0], e[1], e[2], e[3], e[4], str(e[5])] for e in ev],
                                   "mblocks": mblocks, "calls": calls}))
    print(f"  {sym}: transfers={len(ev)}  getLogs_calls={calls.get('getLogs','?')}  "
          f"fetch_secs={calls.get('seconds','?')}")

    # month-end block -> month-end timestamp (use the panel month-end date as the clock)
    me_ts = {m: int(time.mktime(time.strptime(m + " 23:59:59", "%Y-%m-%d %H:%M:%S"))) for m in months}
    me_block = mblocks

    # replay FIFO lots, snapshotting HODL shares at each month-end block
    lots = defaultdict(deque)   # address -> deque[(ts, amount)]
    idx = 0
    scale = 10 ** dec
    rows = []
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    first_block = ev[0][0] if ev else None
    for m in months:
        mb = me_block.get(m)
        if mb is None:
            continue
        while idx < len(ev) and ev[idx][0] <= mb:
            _, _, ts, frm, to, val = ev[idx]
            idx += 1
            if val <= 0:
                continue
            if frm != ZERO:
                fifo_pop(lots[frm], val)
            if to != ZERO:
                lots[to].append((ts, val))
        # only emit once events exist at/before this month (else pre-history -> NaN)
        active = first_block is not None and mb >= first_block
        if not active:
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                         **{w: None for w in WINDOWS}, "hodl_6m_contractscreened": None,
                         "circulating_supply": circ.get(m), "note": "pre-history"})
            continue
        t_now = me_ts[m]
        held = {w: 0 for w in WINDOWS}
        per_addr_old = defaultdict(int)   # addr -> amount older than 6m (for contract screen)
        for a, dq in lots.items():
            for ts, amt in dq:
                age = t_now - ts
                for w, thr in WINDOWS.items():
                    if age > thr:
                        held[w] += amt
                if age > WINDOWS["hodl_6m"]:
                    per_addr_old[a] += amt
        c = circ.get(m)
        row = {"cmc_id": cmc_id, "symbol": sym, "month_end": m,
               "circulating_supply": c, "note": ""}
        for w in WINDOWS:
            row[w] = (held[w] / scale / c) if c else None
        # stash the per-address >6m holdings of this month for the (later) contract screen
        row["_per_addr_old"] = {a: amt for a, amt in per_addr_old.items()}
        rows.append(row)
    return rows, calls, dec, scale


def contract_screen(rows, addr_token, chainid, dec, scale):
    """For the LAST month, identify which big >6m-holder addresses are CONTRACTS (eth_getCode
    non-empty) and report the HODL-6m share with those removed. Bounded #calls (top holders)."""
    last = next((r for r in reversed(rows) if r.get("_per_addr_old")), None)
    if not last:
        return None, []
    pa = last["_per_addr_old"]
    top = sorted(pa.items(), key=lambda kv: kv[1], reverse=True)[:40]  # bound the call budget
    contracts = []
    for a, _ in top:
        a40 = "0x" + a[-40:]
        j = api({"module": "proxy", "action": "eth_getCode", "address": a40, "tag": "latest"},
                chainid, "other")
        code = j.get("result", "0x")
        if code and code not in ("0x", "0x0"):
            contracts.append(a)
    c = last["circulating_supply"]
    old_total = sum(pa.values())
    old_contract = sum(amt for a, amt in pa.items() if a in contracts)
    raw_share = old_total / scale / c if c else None
    screened_share = (old_total - old_contract) / scale / c if c else None
    return (raw_share, screened_share, len(contracts), len(top)), contracts


def main():
    token = PROTO
    if len(sys.argv) > 1:
        token = dict(PROTO)  # allow override later; prototype defaults to RAD
    rows, calls, dec, scale = build(token)
    screen, contracts = contract_screen(rows, token["address"], token["chainid"], dec, scale)

    # write output (drop the helper column)
    out_rows = []
    for r in rows:
        rr = {k: v for k, v in r.items() if not k.startswith("_")}
        out_rows.append(rr)
    out = pd.DataFrame(out_rows)
    out.to_csv(OUT, index=False)

    nz = out[out["hodl_6m"].notna()]
    print(f"\nwrote {OUT}  ({len(nz)} month-obs, token {token['symbol']})")
    if len(nz):
        d = nz.sort_values("month_end")
        print(f"  HODL-6m share: {d['hodl_6m'].min():.1%} -> {d['hodl_6m'].max():.1%} "
              f"(latest {d['hodl_6m'].iloc[-1]:.1%})")
        print(f"  HODL-12m share: {d['hodl_12m'].min():.1%} -> {d['hodl_12m'].max():.1%}")
    if screen:
        raw_s, scr_s, n_contracts, n_top = screen
        print(f"  contract-screen (last month, top {n_top} >6m holders): {n_contracts} are "
              f"contracts -> HODL-6m {raw_s:.1%} raw vs {scr_s:.1%} contract-screened")

    # ---- CALL BUDGET + panel-scale extrapolation (the Entry-24 decision input) ----
    gl = calls.get("getLogs", 0)
    secs = calls.get("seconds", 0)
    print(f"\n=== CALL BUDGET (Channel-2 free-tier feasibility) ===")
    print(f"  {token['symbol']}: {gl} getLogs calls for full Transfer history "
          f"({len(out)} months), ~{secs}s wall.")
    print(f"  Free tier cap ~100,000 getLogs calls/day.")
    if gl:
        print(f"  At {gl} calls/token, a single day's budget covers ~{100000//gl:,} tokens like this.")
        print(f"  Free-chain EVM population (Entry 53) = 793 tokens. If the AVERAGE token cost "
              f"matched {token['symbol']} ({gl} calls), the whole population = ~{gl*793:,} calls "
              f"= ~{gl*793/100000:.1f} free-day-equivalents.")
        print(f"  NOTE: {token['symbol']} is mid-size; high-volume tokens (UNI/major DeFi) have "
              f"100x-1000x more Transfers -> their per-token getLogs cost scales with transfer "
              f"count. The blocker is the HIGH-VOLUME TAIL, not the median token. Whether the "
              f"free cap binds is therefore a function of how many high-volume tokens are in "
              f"scope -- this prototype measures the per-token cost so that tail can be priced "
              f"(Phase-2 trigger if it binds).")


if __name__ == "__main__":
    main()
