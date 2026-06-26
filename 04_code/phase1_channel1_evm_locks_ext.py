"""
phase1_channel1_evm_locks_ext.py  --  SESSION 019, Part A.1: widen Token Channel 1.

Same canonical method as phase1_channel1_evm_locks.py (Etherscan V2 getLogs
reconstruction of cumulative Transfer-in minus Transfer-out of the escrow/staking
contract; the only historical-correct method on the free tier -- Entry 21), applied to
NEW vote-escrow / staking-lock tokens that passed the Entry-26 individual-verification
standard this session: a single, identifiable contract holds the BASE token directly, so
balanceOf(contract) == locked supply of THAT token.

Each candidate was sanity-checked live with a current balanceOf(escrow) read before being
added (eth_call latest-state is fine for a presence check; Entry 21 only forbids
*historical* state reads):

  cmc_id sym    chain      base token / escrow                         current locked share   verdict
  9481   PENDLE Ethereum   PENDLE / vePENDLE                           64.5M / 281.5M = 22.9%  VERIFIED (vote-escrow of PENDLE)
  7429   LQTY   Ethereum   LQTY / LQTYStaking                          57.8M / 100M   = 57.8%  VERIFIED (fee-share stake of LQTY)
  8104   1INCH  Ethereum   1INCH / St1inch                            237.1M / 1.5B   = 15.8%  VERIFIED (governance stake of 1INCH)
  2943   RPL    Ethereum   RPL / RocketVault                          10.66M / 22.5M  = 47.3%  VERIFIED w/ FLAG (shared vault; ~node-staked RPL)
  11857  GMX    Arbitrum   GMX / StakedGmxTracker                       6.16M / 9.6M   = 65%    VERIFIED (single-tracker stake of GMX)

REJECTED this session (documented, not silently proxied -- the veBAL/SNX standard):
  MKR   -- DSChief holds only 432 of 90,225 MKR (0.5%): post-Sky migration the governance
           lock is fragmented across chief versions and largely abandoned; no single
           contract is a clean meaningful locked-supply signal.
  BAL   -- no clean BAL-only lock (veBAL locks an 80/20 BPT, not BAL -- Entry 26).
  COMP  -- governance by in-wallet delegation, no token lock at all (cf. SNX).
  RUNE  -- native THORChain L1 asset; its identity-map "address" is a placeholder
           (thorchain:0x000...000), bonding happens on the L1, not via an EVM escrow.
  ANGLE -- not in the universe (no panel rows); cannot contribute to lambda.

RPL FLAG: RocketVault is a shared protocol vault, not a dedicated escrow; its RPL balance
is dominantly node-operator staked collateral plus a small undistributed-inflation/auction
buffer, so the reconstructed series slightly overstates pure node-stake. Kept as a
staking/locking signal with this caveat, the same way xSUSHI/stkAAVE (reward-staking) were
kept flagged in the original 6.

Output: 03_data/phase1/channel1_evm_locks_ext.csv  (picked up by phase1_assemble_lambda's
        channel1_*.csv glob). Block caches per chain under raw/phase1_onchain/.
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_evm_locks_ext.csv"
CK = REPO / "03_data" / "raw" / "phase1_onchain"
CK.mkdir(parents=True, exist_ok=True)

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SLEEP = 0.22

# cmc_id, symbol, token, escrow, decimals, chainid, mechanism
ESCROWS = [
    (9481, "PENDLE", "0x808507121B80c02388fAd14726482e061B8da827",
     "0x4f30A9D41B80ecC5B94306AB4364951AE3170210", 18, 1, "vote-escrow (vePENDLE)"),
    (7429, "LQTY", "0x6DEA81C8171D0bA574754EF6F8b412F2Ed88c54D",
     "0x4f9Fbb3f1E99B56e0Fe2892e623Ed36A76Fc605d", 18, 1, "fee-share stake (LQTYStaking)"),
    (8104, "1INCH", "0x111111111117dC0aa78b770fA6A738034120C302",
     "0x9A0C8Ff858d273f57072D714bca7411D717501D7", 18, 1, "governance stake (St1inch)"),
    (2943, "RPL", "0xD33526068D116cE69F19A9ee46F0bd304F21A51f",
     "0x3bDC69C4E5e13E52A65f5583c23EFB9636b469d6", 18, 1, "node-collateral stake (RocketVault; shared-vault FLAG)"),
    # GMX -- VERDICT: VERIFIED CLEAN MECHANISM, SERIES BUILD DEFERRED (performance, not data).
    # The StakedGmxTracker (Arbitrum, chainid 42161) holds 6.16M GMX of ~9.6M supply (~65%)
    # directly -- a clean single-contract base-token lock that passes the Entry-26 standard
    # (live balanceOf-verified). BUT the getLogs reconstruction over Arbitrum's full history
    # is impractically slow on the free tier: Arbitrum mines millions of blocks/month, so each
    # month-end window blows past Etherscan's result-window cap and recurses into a deep split
    # tree (>60 s/month observed; 44 months would take far longer than this session allows).
    # Deferred to a follow-up that uses a transfer-pagination method (account tokentx) instead
    # of block-range getLogs. The VERDICT stands (verified); only the series is pending.
    # (11857, "GMX", "0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a",
    #  "0x908C4D94D34924765f1eDc22A1DD098397c59dD4", 18, 42161, "single-tracker stake (StakedGmxTracker, Arbitrum)"),
]


def api(params, chainid, tries=5):
    for t in range(1, tries + 1):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, **params},
                             headers=H, timeout=50)
            j = r.json()
            time.sleep(SLEEP)
            return j
        except Exception as e:
            print(f"    retry {t}: {e}")
            time.sleep(SLEEP * t * 2)
    return {"status": "0", "result": []}


def monthend_blocks(months, chainid):
    """Cache the block at each month-end for the given chain (per-chain cache file)."""
    cf = CK / (f"eth_monthend_blocks.json" if chainid == 1
               else f"monthend_blocks_{chainid}.json")
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    for m in months:
        if m in cache:
            continue
        ts = int(time.mktime(time.strptime(m + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
        j = api({"module": "block", "action": "getblocknobytime",
                 "timestamp": ts, "closest": "before"}, chainid)
        if j.get("status") == "1":
            cache[m] = int(j["result"])
            cf.write_text(json.dumps(cache))
    return cache


def transfers_to_from(token, lo, hi, topic_pos, addr, chainid, depth=0):
    """Sum ERC-20 Transfer `value` in [lo,hi] where addr is at topic position
    topic_pos (1=from, 2=to). Recursively split on the 1000-log cap. Returns raw sum."""
    padded = "0x" + "0" * 24 + addr[2:].lower()
    params = {"module": "logs", "action": "getLogs", "address": token,
              "topic0": TRANSFER, "fromBlock": lo, "toBlock": hi,
              f"topic{topic_pos}": padded,
              f"topic0_{topic_pos}_opr": "and"}
    j = api(params, chainid)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return 0
        mid = (lo + hi) // 2
        return (transfers_to_from(token, lo, mid, topic_pos, addr, chainid, depth + 1) +
                transfers_to_from(token, mid + 1, hi, topic_pos, addr, chainid, depth + 1))
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        return (transfers_to_from(token, lo, mid, topic_pos, addr, chainid, depth + 1) +
                transfers_to_from(token, mid + 1, hi, topic_pos, addr, chainid, depth + 1))
    total = 0
    for lg in res:
        d = lg.get("data", "0x")
        if d and d != "0x":
            total += int(d, 16)
    return total


def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    obs_months = sorted(panel[panel.status == "observed"].month_end.unique())

    rows = []
    for cmc_id, sym, token, escrow, dec, chainid, mech in ESCROWS:
        circ = dict(zip(panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")].month_end,
                        panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")].circulating_supply))
        # only reconstruct months this asset is observed
        months = [m for m in obs_months if m in circ]
        if not months:
            print(f"  {sym}: no observed months, skip")
            continue
        blocks = monthend_blocks(months, chainid)
        ckf = CK / f"locks_{sym}.json"
        ck = json.loads(ckf.read_text()) if ckf.exists() else {"monthly": {}}
        monthly = ck["monthly"]
        asset_months = [m for m in months if m in blocks]
        prev_block = None
        cum_in, cum_out = ck.get("_cum_in", 0), ck.get("_cum_out", 0)
        for m in asset_months:
            if m in monthly:
                prev_block = blocks[m]
                continue
            mb = blocks[m]
            lo = (prev_block + 1) if prev_block else 1
            inc = transfers_to_from(token, lo, mb, 2, escrow, chainid)   # into escrow
            out = transfers_to_from(token, lo, mb, 1, escrow, chainid)   # out of escrow
            cum_in += inc
            cum_out += out
            locked = max(cum_in - cum_out, 0) / (10 ** dec)
            monthly[m] = {"locked": locked, "_block": mb}
            prev_block = mb
            ck.update({"monthly": monthly, "_cum_in": cum_in, "_cum_out": cum_out})
            ckf.write_text(json.dumps(ck))
        for m in asset_months:
            locked = monthly.get(m, {}).get("locked")
            c = circ.get(m)
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                         "locked_supply": locked, "circulating_supply": c,
                         "staking_ratio": (locked / c) if (locked is not None and c) else None,
                         "escrow": escrow, "mechanism": mech})
        last = [v["locked"] for k, v in sorted(monthly.items())]
        print(f"  {sym:6} {mech:50} months={len(monthly)}  latest_locked={last[-1] if last else 0:,.0f}")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT}  ({out.staking_ratio.notna().sum()} asset-months with a ratio, "
          f"{out[out.staking_ratio.notna()].cmc_id.nunique()} assets)")


if __name__ == "__main__":
    main()
