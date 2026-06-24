"""
phase2_pq_pilot.py  --  Phase 2 PQ-definition DIAGNOSTIC PILOT (not the Phase 2 build).

Answers one empirical question before Decision 1/2 in PHASE2_PQ_DECISION_STATUS.md can be
finalized: can raw-Transfer-log transacted-value PQ be built at panel scale on the free
rate-limited Etherscan key, or must we fall back to DeFiLlama's reported volume?

Mechanism = the exact getLogs recursive block-bisection from phase1_channel1_evm_locks.py,
with ONE change: NO counterparty-address filter (topic1/topic2 dropped) -> ALL Transfer
events of the token, not just transfers to/from one escrow. This is what makes it expensive,
and quantifying that cost is the whole point (Entry 24 flagged it "orders of magnitude beyond"
the free key for a different purpose; never re-tested for THIS purpose with real numbers).

Two tokens, recent complete-month window (May 2026):
  UNI  cmc_id 7083  0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984  (Uniswap gov token; AMM/DEX)
  AAVE cmc_id 7278  0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9  (Aave gov token; lending)
  ( NB: panel also has a dead namesake "UNI" cmc_id 4113 -- NOT Uniswap; we use 7083. )

Processes the window DAY BY DAY so that (a) each completed day is a clean measurement, (b) an
early stop on the per-token call budget leaves N whole days to extrapolate from, and (c) we get
a daily series directly. Checkpoints per day; resumable.

Outputs (no large raw dumps committed):
  03_data/raw/phase2_pilot/eth_day_blocks.json     day-edge block cache
  03_data/raw/phase2_pilot/pilot_<SYM>.json        per-token measured day series + stats
"""

import json
import time
import calendar
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
OUTDIR = REPO / "03_data" / "raw" / "phase2_pilot"
BLOCKCACHE = OUTDIR / "eth_day_blocks.json"

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SLEEP = 0.22                      # ~4.5 calls/s, under the free 5/s cap

# May 2026 = most recent complete month in universe_panel.csv (max month_end 2026-05-31).
DAYS = [datetime(2026, 5, d, tzinfo=timezone.utc) for d in range(1, 32)]  # 31 days
WINDOW_EDGES = DAYS + [datetime(2026, 6, 1, tzinfo=timezone.utc)]         # 32 midnights

# month-end USD price straight from universe_panel.csv (Phase 0 CMC backbone), applied flat
# across the window -- the panel is monthly, so there is one price point; daily-price refinement
# is out of pilot scope (this pilot measures call-cost + magnitude, not precise dollarization).
TOKENS = [
    # sym, cmc_id, contract, decimals, may2026_price
    ("UNI",  7083, "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", 18, 3.01964106),
    ("AAVE", 7278, "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", 18, 82.05048239),
]

PER_TOKEN_CALL_BUDGET = 1500     # stop a token between days once cumulative calls hit this
PER_TOKEN_TIME_BUDGET = 900      # ...or once wall-clock for the token exceeds this (s)

CALLS = {"n": 0}                 # global call counter (across everything)


class Budget(Exception):
    pass


def api(params, tries=5):
    for t in range(1, tries + 1):
        try:
            r = requests.get(BASE, params={"chainid": 1, "apikey": KEY, **params},
                             headers=H, timeout=50)
            j = r.json()
            CALLS["n"] += 1
            time.sleep(SLEEP)
            return j
        except Exception as e:
            print(f"      retry {t}: {e}")
            time.sleep(SLEEP * t * 2)
    CALLS["n"] += 1
    return {"status": "0", "result": []}


def block_at(dt, closest):
    ts = calendar.timegm(dt.timetuple())
    j = api({"module": "block", "action": "getblocknobytime",
             "timestamp": ts, "closest": closest})
    if j.get("status") == "1":
        return int(j["result"])
    raise RuntimeError(f"getblocknobytime failed for {dt}: {j}")


def day_edges():
    """Block number at each window midnight (closest=after). Cached."""
    cache = json.loads(BLOCKCACHE.read_text()) if BLOCKCACHE.exists() else {}
    for dt in WINDOW_EDGES:
        k = dt.strftime("%Y-%m-%d")
        if k not in cache:
            cache[k] = block_at(dt, "after")
            BLOCKCACHE.write_text(json.dumps(cache, indent=1))
            print(f"  edge {k} -> block {cache[k]}")
    return cache


def pull_range(token, lo, hi, acc, stat, budget_call, depth=0):
    """Sum ERC-20 Transfer `value` over [lo,hi], ALL transfers (no addr filter).
    Recursively bisect on the 1000-log cap, exactly like Channel 1. Mutates acc/stat."""
    stat["max_depth"] = max(stat["max_depth"], depth)
    if CALLS["n"] >= budget_call:
        raise Budget()
    j = api({"module": "logs", "action": "getLogs", "address": token,
             "topic0": TRANSFER, "fromBlock": lo, "toBlock": hi})
    stat["calls"] += 1
    res = j.get("result")
    if not isinstance(res, list):            # error / rate-limit / non-list -> bisect
        if lo >= hi:
            stat["uncuttable"] += 1
            return
        mid = (lo + hi) // 2
        pull_range(token, lo, mid, acc, stat, budget_call, depth + 1)
        pull_range(token, mid + 1, hi, acc, stat, budget_call, depth + 1)
        return
    if len(res) >= 1000 and lo < hi:         # hit the 1000-log cap -> bisect
        mid = (lo + hi) // 2
        pull_range(token, lo, mid, acc, stat, budget_call, depth + 1)
        pull_range(token, mid + 1, hi, acc, stat, budget_call, depth + 1)
        return
    if len(res) >= 1000 and lo >= hi:
        stat["uncuttable"] += 1              # single block > 1000 logs (undercount risk)
    for lg in res:
        d = lg.get("data", "0x")
        if d and d != "0x":
            acc["sum_raw"] += int(d, 16)
        acc["count"] += 1


def run_token(sym, cmc_id, contract, dec, price, edges):
    ckf = OUTDIR / f"pilot_{sym}.json"
    ck = json.loads(ckf.read_text()) if ckf.exists() else {
        "sym": sym, "cmc_id": cmc_id, "contract": contract, "decimals": dec,
        "price_usd": price, "days": {}, "truncated": False, "done": False}
    print(f"\n=== {sym} (cmc_id {cmc_id})  contract {contract} ===")
    t_token0 = time.time()
    calls_token0 = CALLS["n"]
    try:
        for dt in DAYS:
            k = dt.strftime("%Y-%m-%d")
            if k in ck["days"]:
                continue
            # budget check BETWEEN days so each stored day is whole
            if (CALLS["n"] - calls_token0) >= PER_TOKEN_CALL_BUDGET or \
               (time.time() - t_token0) >= PER_TOKEN_TIME_BUDGET:
                ck["truncated"] = True
                print(f"  [budget] stopping {sym} before {k} "
                      f"(calls={CALLS['n']-calls_token0}, t={time.time()-t_token0:.0f}s)")
                break
            nxt = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
            lo, hi = edges[k], edges[nxt] - 1
            acc = {"sum_raw": 0, "count": 0}
            stat = {"calls": 0, "max_depth": 0, "uncuttable": 0}
            d_t0, d_c0 = time.time(), CALLS["n"]
            try:
                pull_range(contract, lo, hi, acc, stat,
                           budget_call=calls_token0 + PER_TOKEN_CALL_BUDGET)
            except Budget:
                ck["truncated"] = True
                print(f"  [budget] hit mid-day {k}; discarding partial day")
                break
            tokens_moved = acc["sum_raw"] / (10 ** dec)
            ck["days"][k] = {
                "block_lo": lo, "block_hi": hi,
                "transfer_count": acc["count"],
                "tokens_transferred": tokens_moved,
                "usd_transfer_volume": tokens_moved * price,
                "api_calls": stat["calls"],
                "max_depth": stat["max_depth"],
                "uncuttable_blocks": stat["uncuttable"],
                "wall_s": round(time.time() - d_t0, 1),
            }
            ckf.write_text(json.dumps(ck, indent=1))
            print(f"  {k}  transfers={acc['count']:>7,}  "
                  f"usd_vol=${tokens_moved*price:>16,.0f}  "
                  f"calls={stat['calls']:>4}  depth={stat['max_depth']:>2}  "
                  f"{time.time()-d_t0:>5.1f}s")
        else:
            ck["done"] = True
    finally:
        ck["token_calls_total"] = CALLS["n"] - calls_token0
        ck["token_wall_s"] = round(time.time() - t_token0, 1)
        ckf.write_text(json.dumps(ck, indent=1))
    nd = len(ck["days"])
    tc = sum(d["transfer_count"] for d in ck["days"].values())
    tcalls = sum(d["api_calls"] for d in ck["days"].values())
    print(f"  -> {sym}: {nd} days, {tc:,} transfers, {tcalls:,} getLogs calls, "
          f"{ck['token_wall_s']:.0f}s, truncated={ck['truncated']}, done={ck['done']}")
    return ck


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("Resolving day-edge blocks (May 2026)...")
    edges = day_edges()
    for sym, cmc_id, contract, dec, price in TOKENS:
        run_token(sym, cmc_id, contract, dec, price, edges)
    print(f"\nTOTAL API calls this run: {CALLS['n']}")


if __name__ == "__main__":
    main()
