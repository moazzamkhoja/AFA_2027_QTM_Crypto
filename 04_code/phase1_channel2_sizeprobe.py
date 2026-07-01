"""
phase1_channel2_sizeprobe.py  --  SESSION 025, Task B (pre-pass): size EVERY free-chain token
CHEAPLY before building Channel 2, so the panel build processes smallest-first and defers the
high-volume tail BY METADATA instead of by hit-and-trial (fetch-until-cap, which wastes ~cap
calls per giant just to discover it's too big).

Signal: Etherscan Pro `module=token&action=tokenholdercount` = 1 call/token. Holder count is a
monotone proxy for Transfer-log volume (calibration: MET 748 holders / 24.6k transfers / 79
getLogs calls; RAD 7,785 / 397k / 1,357; XAN 12,963 / giant). Empirically ~30-50 transfers per
holder, so est_getlogs_calls ~= holders * 0.08. A token under ~3,000 holders reliably completes
Channel 2 under a few hundred getLogs calls.

Output: 03_data/phase1/_channel2_sizes.csv  (cmc_id, symbol, chainid, address, holder_count,
        est_transfers, est_getlogs_calls) -- consumed by phase1_channel2_panel.py to order and
        threshold the build. Resumable: skips tokens already sized.
"""
import json, os, time
from pathlib import Path
import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
MAP = REPO / "03_data" / "phase1" / "universe_lambda_channel_map.csv"
OUT = REPO / "03_data" / "phase1" / "_channel2_sizes.csv"
BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = float(os.environ.get("SLEEP", "0.11"))
CHAIN_ID = {"Ethereum": 1, "Polygon": 137, "Arbitrum": 42161, "Blast": 81457}
TF_PER_HOLDER = 40      # calibration midpoint
CALLS_PER_TF = 2.0 / 1000  # recursion overhead / 1000-per-page


def holder_count(addr, chainid, tries=4):
    for t in range(tries):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, "module": "token",
                                           "action": "tokenholdercount", "contractaddress": addr},
                             headers=H, timeout=40)
            j = r.json()
            time.sleep(SLEEP)
            res = j.get("result")
            if isinstance(res, str) and res.isdigit():
                return int(res)
            return None
        except Exception:
            time.sleep(SLEEP * (t + 1) * 2)
    return None


def main():
    m = pd.read_csv(MAP)
    free = m[(m.chain.isin(CHAIN_ID)) & (m.etherscan_reachable == "yes") & (m.address.notna())]
    free = free.drop_duplicates("cmc_id")
    done = {}
    if OUT.exists():
        prev = pd.read_csv(OUT)
        done = {int(r.cmc_id): r for r in prev.itertuples()}
    rows = []
    n = 0
    for r in free.itertuples():
        cmc_id = int(r.cmc_id)
        if cmc_id in done and pd.notna(getattr(done[cmc_id], "holder_count", None)):
            d = done[cmc_id]
            rows.append({"cmc_id": cmc_id, "symbol": d.symbol, "chainid": d.chainid,
                         "address": d.address, "holder_count": d.holder_count,
                         "est_transfers": d.est_transfers, "est_getlogs_calls": d.est_getlogs_calls})
            continue
        chainid = CHAIN_ID[r.chain]
        hc = holder_count(str(r.address), chainid)
        est_tf = (hc * TF_PER_HOLDER) if hc is not None else None
        est_calls = round(est_tf * CALLS_PER_TF) if est_tf is not None else None
        rows.append({"cmc_id": cmc_id, "symbol": r.symbol, "chainid": chainid,
                     "address": r.address, "holder_count": hc,
                     "est_transfers": est_tf, "est_getlogs_calls": est_calls})
        n += 1
        if n % 25 == 0:
            pd.DataFrame(rows).to_csv(OUT, index=False)   # checkpoint
            print(f"  sized {n} new tokens (total {len(rows)}) ...")
    df = pd.DataFrame(rows).sort_values("holder_count", na_position="last")
    df.to_csv(OUT, index=False)
    ok = df[df.holder_count.notna()]
    print(f"\nwrote {OUT}: {len(df)} tokens, {len(ok)} with holder counts, {n} newly probed")
    for thr in (1000, 2000, 3000, 5000, 10000):
        print(f"  holders <= {thr:>6}: {int((ok.holder_count <= thr).sum()):>4} tokens "
              f"(est <= {round(thr*TF_PER_HOLDER*CALLS_PER_TF)} getLogs calls each)")


if __name__ == "__main__":
    main()
