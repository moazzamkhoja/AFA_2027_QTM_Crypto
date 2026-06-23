"""
phase1_channel1_evm_locks.py  --  Phase 1, Channel 1 for EVM vote-escrow / staking
                                   tokens (canonical on-chain reconstruction)

For ERC-20 governance tokens whose conviction is revealed by locking the BASE token
in a single, identifiable escrow/staking contract, locked supply at a month-end =
cumulative (Transfer into escrow) - (Transfer out of escrow), reconstructed from the
token's on-chain Transfer event logs (Etherscan V2 getLogs). This is the only
historical-correct method on the free tier (Entry 21: historical balanceOf/eth_call is
silently latest-only; logs are immutable history).

CURATED ESCROW TABLE (Entry 26): only high-confidence cases where the escrow holds the
BASE token directly, so balanceOf(escrow) == locked supply. Excluded by design: veBAL
(locks an 80/20 BPT, not BAL), SNX (collateral C-ratio system, not a simple lock) --
documented, not silently proxied.

  cmc_id symbol  base token                                   escrow / staking contract                    mechanism
  6538   CRV     0xD533...cd52                                veCRV 0x5f3b...e2A2                           vote-escrow
  9903   CVX     0x4e3F...9D2B                                vlCVX 0x72a1...b86E                           vote-lock
  6953   FXS     0x3432...64D0                                veFXS 0xc841...C5b0                           vote-escrow
  6758   SUSHI   0x6B35...0fE2                                xSUSHI 0x8798...4272                          fee-share stake
  7278   AAVE    0x7Fc6...DaE9                                stkAAVE 0x4da2...70f5                          safety-module stake
  5864   YFI     0x0bc5...d93e                                veYFI 0x90c1...8aD5                           vote-escrow

CAVEAT: xSUSHI/stkAAVE are reward-staking (b_t>0-ish) rather than pure vote-escrow, but
both are a locked/committed-supply signal and are kept in Channel 1 (staking/locking
ratio), flagged via `mechanism`. Ratio denominator = circulating supply (Phase 0 panel).

Output: 03_data/phase1/channel1_evm_locks.csv
        03_data/raw/phase1_onchain/eth_monthend_blocks.json  (shared block cache)
        03_data/raw/phase1_onchain/locks_<symbol>.json        (per-token checkpoint)
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_evm_locks.csv"
CK = REPO / "03_data" / "raw" / "phase1_onchain"
BLOCKCACHE = CK / "eth_monthend_blocks.json"

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SLEEP = 0.22

ESCROWS = [
    # cmc_id, symbol, token, escrow, decimals, mechanism
    (6538, "CRV", "0xD533a949740bb3306d119CC777fa900bA034cd52",
     "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2", 18, "vote-escrow (veCRV)"),
    (9903, "CVX", "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B",
     "0x72a19342e8F1838460eBFCCEf09F6585e32db86E", 18, "vote-lock (vlCVX)"),
    (6953, "FXS", "0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0",
     "0xc8418aF6358FFddA74e09Ca9CC3Fe03Ca6aDC5b0", 18, "vote-escrow (veFXS)"),
    (6758, "SUSHI", "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
     "0x8798249c2E607446Efb7Ad49eC89dD1865Ff4272", 18, "fee-share stake (xSUSHI)"),
    (7278, "AAVE", "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
     "0x4da27a545c0c5B758a6BA100e3a049001de870f5", 18, "safety-module stake (stkAAVE)"),
    (5864, "YFI", "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
     "0x90c1f9220d90d3966fbEE24045EDd73E1d588aD5", 18, "vote-escrow (veYFI)"),
]


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


def monthend_blocks(months):
    """Cache Ethereum block at each month-end (shared across tokens)."""
    cache = json.loads(BLOCKCACHE.read_text()) if BLOCKCACHE.exists() else {}
    for m in months:
        if m in cache:
            continue
        ts = int(time.mktime(time.strptime(m + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
        j = api({"module": "block", "action": "getblocknobytime",
                 "timestamp": ts, "closest": "before"})
        if j.get("status") == "1":
            cache[m] = int(j["result"])
            BLOCKCACHE.write_text(json.dumps(cache))
    return cache


def transfers_to_from(token, lo, hi, topic_pos, addr, depth=0):
    """Sum ERC-20 Transfer `value` in [lo,hi] where addr is at topic position
    topic_pos (1=from, 2=to). Recursively split on the 1000-log cap. Returns raw sum."""
    padded = "0x" + "0" * 24 + addr[2:].lower()
    params = {"module": "logs", "action": "getLogs", "address": token,
              "topic0": TRANSFER, "fromBlock": lo, "toBlock": hi,
              f"topic{topic_pos}": padded,
              f"topic0_{topic_pos}_opr": "and"}
    j = api(params)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return 0
        mid = (lo + hi) // 2
        return (transfers_to_from(token, lo, mid, topic_pos, addr, depth + 1) +
                transfers_to_from(token, mid + 1, hi, topic_pos, addr, depth + 1))
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        return (transfers_to_from(token, lo, mid, topic_pos, addr, depth + 1) +
                transfers_to_from(token, mid + 1, hi, topic_pos, addr, depth + 1))
    total = 0
    for lg in res:
        d = lg.get("data", "0x")
        if d and d != "0x":
            total += int(d, 16)
    return total


def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    months = sorted(panel[panel.status == "observed"].month_end.unique())
    blocks = monthend_blocks(months)

    rows = []
    for cmc_id, sym, token, escrow, dec, mech in ESCROWS:
        ckf = CK / f"locks_{sym}.json"
        ck = json.loads(ckf.read_text()) if ckf.exists() else {"monthly": {}}
        monthly = ck["monthly"]
        circ = dict(zip(panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")].month_end,
                        panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")].circulating_supply))
        asset_months = [m for m in months if m in circ and m in blocks]
        prev_block, cum_in, cum_out = None, ck.get("_cum_in", 0), ck.get("_cum_out", 0)
        for m in asset_months:
            if m in monthly:
                prev_block = blocks[m]
                continue
            mb = blocks[m]
            lo = (prev_block + 1) if prev_block else 1
            inc = transfers_to_from(token, lo, mb, 2, escrow)   # into escrow
            out = transfers_to_from(token, lo, mb, 1, escrow)   # out of escrow
            cum_in += inc
            cum_out += out
            locked = max(cum_in - cum_out, 0) / (10 ** dec)
            monthly[m] = {"locked": locked, "_block": mb}
            prev_block = mb
            ck.update({"monthly": monthly, "_cum_in": cum_in, "_cum_out": cum_out})
            ckf.write_text(json.dumps(ck))
        # build rows
        for m in asset_months:
            locked = monthly.get(m, {}).get("locked")
            c = circ.get(m)
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                         "locked_supply": locked, "circulating_supply": c,
                         "staking_ratio": (locked / c) if (locked is not None and c) else None,
                         "escrow": escrow, "mechanism": mech})
        last = [v["locked"] for k, v in sorted(monthly.items())]
        print(f"  {sym:6} {mech:28} months={len(monthly)}  latest_locked={last[-1] if last else 0:,.0f}")

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({out.staking_ratio.notna().sum()} asset-months with a ratio, "
          f"{out[out.staking_ratio.notna()].cmc_id.nunique()} assets)")


if __name__ == "__main__":
    main()
