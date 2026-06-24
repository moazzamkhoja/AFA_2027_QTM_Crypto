"""
phase2_pq_pilot_diag.py -- noise/outlier diagnostic for the PQ pilot.

The first pass (phase2_pq_pilot.py) found AAVE's raw Transfer-value sum physically impossible
($8.2e19, i.e. ~1e18 AAVE vs a 15.4M-token supply). Raw Transfer logs include mint/burn/bridge
and spurious max-value events that are not economic throughput -- the classic NVT contamination
(specticket: wash/internal churn). This re-pulls May 2026 for both tokens, keeps the full value
array, and reports: max, the count and sum of "impossible" transfers (> circulating supply),
percentiles, and a cleaned monthly volume (outliers above circulating supply removed).
"""
import json, time, calendar
from pathlib import Path
from datetime import datetime, timezone, timedelta
import requests, numpy as np

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
OUT = REPO / "03_data" / "raw" / "phase2_pilot"
BLOCKS = json.loads((OUT / "eth_day_blocks.json").read_text())
BASE = "https://api.etherscan.io/v2/api"; H = {"User-Agent": "Mozilla/5.0"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SLEEP = 0.22

TOKENS = [  # sym, contract, dec, price, circ_supply_may2026
    ("UNI",  "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", 18, 3.01964106, 635485562.74),
    ("AAVE", "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", 18, 82.05048239, 15405821.58),
]
DAYS = [datetime(2026, 5, d, tzinfo=timezone.utc) for d in range(1, 32)]


def api(p):
    for t in range(5):
        try:
            r = requests.get(BASE, params={"chainid": 1, "apikey": KEY, **p}, headers=H, timeout=50)
            j = r.json(); time.sleep(SLEEP); return j
        except Exception as e:
            print("  retry", e); time.sleep(SLEEP * (t + 1) * 2)
    return {"result": []}


def pull(contract, lo, hi, vals, depth=0):
    j = api({"module": "logs", "action": "getLogs", "address": contract,
             "topic0": TRANSFER, "fromBlock": lo, "toBlock": hi})
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi: return
        m = (lo + hi) // 2; pull(contract, lo, m, vals, depth + 1); pull(contract, m + 1, hi, vals, depth + 1); return
    if len(res) >= 1000 and lo < hi:
        m = (lo + hi) // 2; pull(contract, lo, m, vals, depth + 1); pull(contract, m + 1, hi, vals, depth + 1); return
    for lg in res:
        d = lg.get("data", "0x")
        vals.append(int(d, 16) if d and d != "0x" else 0)


def main():
    summary = {}
    for sym, contract, dec, price, circ in TOKENS:
        print(f"\n=== {sym} ===")
        vals = []
        for dt in DAYS:
            k = dt.strftime("%Y-%m-%d"); nxt = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
            pull(contract, BLOCKS[k], BLOCKS[nxt] - 1, vals)
        a = np.array(vals, dtype=object)  # exact big ints
        toks = np.array([float(v) / 10 ** dec for v in vals])
        n = len(toks)
        impossible = toks > circ                      # single transfer > entire circ supply
        n_imp = int(impossible.sum())
        raw_sum = float(toks.sum())
        clean_sum = float(toks[~impossible].sum())
        mx = float(toks.max()) if n else 0
        pct = {p: float(np.percentile(toks, p)) for p in (50, 90, 99, 99.9)}
        summary[sym] = {
            "transfers": n, "circ_supply": circ,
            "raw_tokens": raw_sum, "raw_usd": raw_sum * price,
            "clean_tokens": clean_sum, "clean_usd": clean_sum * price,
            "n_impossible": n_imp, "max_transfer_tokens": mx,
            "max_transfer_x_supply": mx / circ if circ else None,
            "pctiles_tokens": pct,
        }
        print(f"  transfers={n:,}  impossible(> {circ:,.0f} supply)={n_imp}")
        print(f"  max single transfer = {mx:,.3e} tokens ({mx/circ:,.1f}x supply)")
        print(f"  RAW   month tokens={raw_sum:,.3e}  USD=${raw_sum*price:,.3e}")
        print(f"  CLEAN month tokens={clean_sum:,.0f}  USD=${clean_sum*price:,.0f}")
        print(f"  median transfer={pct[50]:,.2f}  p99={pct[99]:,.2f}  p99.9={pct[99.9]:,.2f} tokens")
    (OUT / "pilot_noise_diag.json").write_text(json.dumps(summary, indent=1, default=str))
    print("\nsaved pilot_noise_diag.json")


if __name__ == "__main__":
    main()
