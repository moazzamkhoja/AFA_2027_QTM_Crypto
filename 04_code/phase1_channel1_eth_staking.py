"""
phase1_channel1_eth_staking.py  --  Phase 1, Channel 1 for ETH (canonical on-chain)

Reconstructs month-end ETH staked supply directly from the Beacon Chain deposit
contract's on-chain `DepositEvent` logs (Etherscan V2 `logs/getLogs`), NOT from a
staking dashboard (beaconcha.in now requires a paid key -- Entry 21) and NOT from
historical state reads (free-tier `eth_call` is silently latest-only -- Entry 21).

METHOD (Entry 23):
  deposit contract: 0x00000000219ab540356cBB839Cbe05303d7705Fa
  Each validator deposit emits DepositEvent(pubkey, withdrawal_credentials, amount,
  signature, index); `amount` is 8-byte little-endian gwei. We page all DepositEvents
  from the first-deposit block (Nov 2020) to the sample end, summing `amount`, and
  snapshot the running cumulative at each month-end block (block <= month-end via
  block/getblocknobytime).

CAVEAT (logged): the deposit contract only ever RECEIVES ether; post-Shapella
  (2023-04) validator withdrawals are processed on the consensus layer and do NOT
  debit this contract. So cumulative-deposited is the canonical *execution-layer*
  staking measure but OVERSTATES net active stake after 2023-04. Flagged in the
  coverage report; it remains a monotone, on-chain conviction proxy.

  Per classification_table staking_start=2020-12-01, ETH has NO staking λ channel
  before 2020-12 (PoW) -- months before that are emitted as NaN, not 0.

Output: 03_data/phase1/channel1_eth_staking.csv
        03_data/raw/phase1_onchain/eth_staking_monthly.json  (resumable checkpoint)
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_eth_staking.csv"
CKPT_DIR = REPO / "03_data" / "raw" / "phase1_onchain"
CKPT = CKPT_DIR / "eth_staking_monthly.json"

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
DEP = "0x00000000219ab540356cBB839Cbe05303d7705Fa"
TOPIC = "0x649bbc62d0e31342afea4e5cd82d4049e7e1ee912fc0889aa790803be39038c5"
ETH_CMC_ID = 1027
STAKING_START = "2020-12-01"
SLEEP = 0.22  # ~4.5 req/s, under the 5/s free-tier cap


def api(params, tries=5):
    for t in range(1, tries + 1):
        try:
            r = requests.get(BASE, params={"chainid": 1, "apikey": KEY, **params},
                             headers=H, timeout=50)
            j = r.json()
            time.sleep(SLEEP)
            return j
        except Exception as e:
            print(f"    retry {t}: {e}")
            time.sleep(SLEEP * t * 2)
    return {"status": "0", "result": []}


def block_at(date_str):
    """Last block at or before 23:59:59 of date_str (month-end)."""
    ts = int(time.mktime(time.strptime(date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
    j = api({"module": "block", "action": "getblocknobytime",
             "timestamp": ts, "closest": "before"})
    return int(j["result"]) if j.get("status") == "1" else None


def parse_amount_gwei(log):
    d = log["data"][2:]
    w = [d[i:i + 64] for i in range(0, len(d), 64)]
    off = int(w[2], 16) // 32          # offset (bytes) -> word index of `amount`
    length = int(w[off], 16)
    raw = w[off + 1][:length * 2]
    return int.from_bytes(bytes.fromhex(raw), "little")  # gwei


def sum_deposits(lo, hi, depth=0):
    """Sum deposited gwei in [lo, hi], recursively splitting if the 1000-log window
    truncates. Returns (gwei_sum, n_logs)."""
    j = api({"module": "logs", "action": "getLogs", "address": DEP, "topic0": TOPIC,
             "fromBlock": lo, "toBlock": hi})
    res = j.get("result")
    msg = (j.get("message") or "")
    if not isinstance(res, list):
        # error (often "result window is too large") -> split
        if lo >= hi:
            return 0, 0
        mid = (lo + hi) // 2
        a, na = sum_deposits(lo, mid, depth + 1)
        b, nb = sum_deposits(mid + 1, hi, depth + 1)
        return a + b, na + nb
    if len(res) >= 1000 and lo < hi:   # truncated -> split for completeness
        mid = (lo + hi) // 2
        a, na = sum_deposits(lo, mid, depth + 1)
        b, nb = sum_deposits(mid + 1, hi, depth + 1)
        return a + b, na + nb
    total = sum(parse_amount_gwei(l) for l in res)
    return total, len(res)


def main():
    CKPT_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PANEL)
    eth = panel[(panel.cmc_id == ETH_CMC_ID) & (panel.status == "observed")][
        ["month_end", "circulating_supply"]].sort_values("month_end")
    months = list(eth.month_end)

    ckpt = json.loads(CKPT.read_text()) if CKPT.exists() else {}
    cum_gwei = ckpt.get("_cum_gwei", 0)
    monthly = ckpt.get("monthly", {})          # month_end -> cumulative ETH staked
    last_block = ckpt.get("_last_block", None)

    # only reconstruct from staking_start onward
    active_months = [m for m in months if m >= STAKING_START]
    print(f"ETH staking reconstruction: {len(active_months)} months from {STAKING_START}")

    prev_block = last_block
    for m in active_months:
        if m in monthly:
            prev_block = monthly[m].get("_block", prev_block)
            continue
        mb = block_at(m)
        if mb is None:
            print(f"  {m}  block lookup FAILED")
            continue
        lo = (prev_block + 1) if prev_block else 11000000  # contract era start
        gwei, n = sum_deposits(lo, mb)
        cum_gwei += gwei
        cum_eth = cum_gwei / 1e9
        monthly[m] = {"cum_eth_staked": cum_eth, "month_deposits_eth": gwei / 1e9,
                      "n_deposits": n, "_block": mb}
        prev_block = mb
        # persist checkpoint each month
        CKPT.write_text(json.dumps({"monthly": monthly, "_cum_gwei": cum_gwei,
                                    "_last_block": mb}))
        print(f"  {m}  block={mb}  +{gwei/1e9:,.0f} ETH ({n} deps)  cum={cum_eth:,.0f} ETH")

    # build output joined to circulating supply
    rows = []
    circ = dict(zip(eth.month_end, eth.circulating_supply))
    for m in months:
        if m < STAKING_START:
            rows.append({"cmc_id": ETH_CMC_ID, "symbol": "ETH", "month_end": m,
                         "staked_eth": None, "circulating_supply": circ.get(m),
                         "staking_ratio": None,
                         "note": "PoW; no staking channel before staking_start"})
        elif m in monthly:
            s = monthly[m]["cum_eth_staked"]
            c = circ.get(m)
            rows.append({"cmc_id": ETH_CMC_ID, "symbol": "ETH", "month_end": m,
                         "staked_eth": s, "circulating_supply": c,
                         "staking_ratio": (s / c) if c else None,
                         "note": "cumulative deposit-contract ETH (overstates post-Shapella)"})
    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({out.staking_ratio.notna().sum()} months with a ratio)")
    nz = out[out.staking_ratio.notna()]
    if len(nz):
        print(nz[["month_end", "staked_eth", "staking_ratio"]].iloc[::6].to_string(index=False))


if __name__ == "__main__":
    main()
