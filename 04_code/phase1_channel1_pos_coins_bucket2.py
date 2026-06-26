"""
phase1_channel1_pos_coins_bucket2.py  --  SESSION 020, Part A (Bucket 2): coin Channel-1
staking/locking series for non-EVM PoS coins, RESPONSE-BODY-verified live this session
(the successor to Entry 42's docs-level findings).

This file upgrades three of Entry 42's "free, inferred" coins to "free, response-body
verified, BUILT", with the exact gate each turned out to have:

  TRX  (cmc 1958, coin) -- TronScan public `freezeresource` endpoint
       (apilist.tronscanapi.com/api/freezeresource?start_day=YYYY-MM-DD&end_day=YYYY-MM-DD).
       VERIFIED KEYLESS THIS SESSION: the endpoint returns full daily history with NO API key
       (Entry 42 said a free signup was needed; live, the read endpoint answers unauthenticated).
       Field used: `total_freeze_weight` = total frozen TRX (already in TRX, not sun). History
       starts ~2020-05 (2019 returns total:0). Last calendar-day observation per month.

  SOL  (cmc 5426, coin) -- validators.app `/api/v1/epochs/mainnet.json`.
       VERIFIED KEYLESS THIS SESSION with `?per=200&page=N`: `total_active_stake` (lamports,
       /1e9 = SOL) is populated WITHOUT an API token for all epochs validators.app actually
       recorded stake for -- which begins ~epoch 414 (~2023-01). Earlier epochs return
       total_active_stake=null on the free/keyless tier (validators.app simply did not collect
       the figure before then -- a data-vintage limit, not a paywall: the null pattern is
       time-based, not all-or-nothing as a key gate would be). So SOL is built from ~2023-01
       forward; pre-2023 observed months get NaN (no value guessed). Corrects Entry 42's "free,
       verified" to "free & keyless, but only ~2023-01+ depth".

  CELO (cmc 5567, coin) -- Tier 4 EVM-reclassification CHECKED, but NOT BUILT (cross-check
       FAILED -> documented open gap, per the flag-don't-ship rule). The reclassification half
       is confirmed: Celo migrated to an Ethereum L2 (OP Stack) on 2025-03-26 and IS on
       Etherscan V2 (chainid 42220, existing multichain key -- confirmed in /v2/chainlist); the
       legacy LockedGold contract 0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E is still the live
       locking custody (live balanceOf 85.65M CELO; on-chain getTotalLockedGold() 82.43M CELO).
       BUT the free getLogs reconstruction does NOT reproduce that on-chain total, so it fails
       the Entry-26 cross-check and was NOT shipped:
         - GoldToken (0x471E..438) Transfer in/out of LockedGold -> only 2.0M CELO. Reason:
           Celo's NATIVE CELO locking (lock() sends native value) does not emit a standard
           ERC20 Transfer on GoldToken, so Transfer logs miss almost all of it.
         - LockedGold's own native events cumsum(GoldLocked)+cumsum(GoldRelocked)-cumsum(
           GoldUnlocked) -> only 25.8M CELO vs the 82.43M getTotalLockedGold target. The ~57M
           shortfall is locked CELO carried over as STATE in the 2025-03 L2 migration without a
           re-emitted lock event on the indexed chain (lock=676M / unlock=662M churn nets tiny).
       The only clean number is historical getTotalLockedGold()/balanceOf, i.e. archive
       eth_call / Etherscan balancehistory -- a PRO endpoint, not free. So CELO stays an open
       Bucket-2 gap this session: the EVM path exists but the free-tier log reconstruction
       cannot reproduce the on-chain locked total. (Entry 43.) Not emitted below.

DOT/KSM (Subscan): NOT built. Live this session Subscan returns HTTP 403 "API strictly
       requires an API key. Unauthenticated access is disabled" -- so Entry 42's docs-level
       inference that era_stat is free-tier could not be response-body confirmed; the endpoint
       is unreachable without a (free-signup, email-verified) key, which was not obtainable in
       this non-interactive session. Logged as a correction to Entry 42 (Entry 43); a free key
       would let this same script be extended. No Pro purchase.

Ratio denominator = circulating supply from the Phase 0 universe panel (cmc_id+month_end),
the same convention as channel1_pos_coins.csv (ADA/XTZ). No interpolation, no carry-forward.

Output: 03_data/phase1/channel1_pos_coins_bucket2.csv  (picked up by the channel1_*.csv glob).
        Raw series cached under 03_data/raw/phase1_onchain/pos_coins_b2/.
"""

import json
import time
import datetime as dt
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_pos_coins_bucket2.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_b2"
RAW.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "afa-2027-qtm-research (academic, free-tier)"}
NOW = dt.datetime.utcnow().timestamp()

# Reuse the verified EVM getLogs reconstruction machinery (Celo runs on it via chainid 42220).
from phase1_channel1_evm_locks_ext import monthend_blocks, transfers_to_from

CELO_GOLDTOKEN = "0x471EcE3750Da237f93B8E339c536989b8978a438"
CELO_LOCKEDGOLD = "0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E"
CELO_CHAINID = 42220


def _get(url, cache_name, tries=4):
    cf = RAW / cache_name
    if cf.exists():
        return json.loads(cf.read_text(encoding="utf-8"))
    last = None
    for t in range(1, tries + 1):
        try:
            r = requests.get(url, headers=H, timeout=90)
            r.raise_for_status()
            d = r.json()
            cf.write_text(json.dumps(d), encoding="utf-8")
            return d
        except Exception as e:
            last = e
            time.sleep(1.5 * t)
    raise RuntimeError(f"fetch failed {url}: {last}")


def trx_series():
    """TRX total frozen weight per calendar month from TronScan freezeresource (keyless)."""
    by_ym = {}
    for yr in range(2019, 2027):
        d = _get(f"https://apilist.tronscanapi.com/api/freezeresource"
                 f"?start_day={yr}-01-01&end_day={yr}-12-31", f"trx_{yr}.json")
        for rec in d.get("data", []):
            day = rec.get("day")
            w = rec.get("total_freeze_weight")
            if not day or w is None:
                continue
            ym = day[:7]
            ts = dt.datetime.strptime(day, "%Y-%m-%d").timestamp()
            cur = by_ym.get(ym)
            if cur is None or ts >= cur[0]:
                by_ym[ym] = (ts, float(w))
    return {ym: v for ym, (_, v) in by_ym.items()}, "tronscan:freezeresource.total_freeze_weight"


def sol_series():
    """SOL total_active_stake per calendar month from validators.app epochs (keyless)."""
    by_ym = {}
    for pg in range(1, 8):
        d = _get(f"https://www.validators.app/api/v1/epochs/mainnet.json?per=200&page={pg}",
                 f"sol_epochs_p{pg}.json")
        eps = d.get("epochs", [])
        if not eps:
            break
        for e in eps:
            av = e.get("total_active_stake")
            created = e.get("created_at")
            if av is None or not created:
                continue
            ts = dt.datetime.strptime(created[:19], "%Y-%m-%dT%H:%M:%S").timestamp()
            if ts > NOW:
                continue
            ym = created[:7]
            staked = int(av) / 1e9   # lamports -> SOL
            cur = by_ym.get(ym)
            if cur is None or ts >= cur[0]:
                by_ym[ym] = (ts, staked)
    return {ym: v for ym, (_, v) in by_ym.items()}, "validators.app:epochs.total_active_stake"


def celo_series(months):
    """CELO locked supply per month: cumulative GoldToken Transfer-in minus Transfer-out of
    the LockedGold contract, reconstructed on chainid 42220 (Etherscan V2). Same method as the
    EVM token locks; cross-checked below against the live balanceOf(LockedGold)."""
    ckf = RAW / "celo_locked.json"
    ck = json.loads(ckf.read_text()) if ckf.exists() else {"monthly": {}, "_cum_in": 0, "_cum_out": 0}
    blocks = monthend_blocks(months, CELO_CHAINID)
    asset_months = [m for m in months if m in blocks]
    monthly = ck["monthly"]
    prev_block = None
    cum_in, cum_out = ck.get("_cum_in", 0), ck.get("_cum_out", 0)
    for m in asset_months:
        if m in monthly:
            prev_block = blocks[m]
            continue
        mb = blocks[m]
        lo = (prev_block + 1) if prev_block else 1
        inc = transfers_to_from(CELO_GOLDTOKEN, lo, mb, 2, CELO_LOCKEDGOLD, CELO_CHAINID)
        out = transfers_to_from(CELO_GOLDTOKEN, lo, mb, 1, CELO_LOCKEDGOLD, CELO_CHAINID)
        cum_in += inc
        cum_out += out
        locked = max(cum_in - cum_out, 0) / 1e18
        monthly[m] = {"locked": locked, "_block": mb}
        prev_block = mb
        ck.update({"monthly": monthly, "_cum_in": cum_in, "_cum_out": cum_out})
        ckf.write_text(json.dumps(ck))
    return {m: monthly[m]["locked"] for m in asset_months if m in monthly}, \
        "celoscan(etherscanV2/42220):GoldToken Transfer in/out of LockedGold"


def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]

    rows = []

    def add(cid, sym, series, src, flag=""):
        obs = panel[(panel.cmc_id == cid) & (panel.status == "observed")][
            ["month_end", "ym", "circulating_supply"]]
        n = 0
        for _, r in obs.sort_values("ym").iterrows():
            staked = series.get(r.ym)
            c = r.circulating_supply
            ratio = (staked / c) if (staked is not None and c and c > 0) else None
            if ratio is not None:
                n += 1
            rows.append({"cmc_id": cid, "symbol": sym, "month_end": r.month_end,
                         "staked_native": staked, "circulating_supply": c,
                         "staking_ratio": ratio, "source": src, "flag": flag})
        smin = min(series) if series else "-"
        smax = max(series) if series else "-"
        print(f"  {sym:5} {n:3} months w/ ratio  (series {len(series)} mo, {smin}->{smax})  src={src}")

    # --- TRX (keyless) ---
    s, src = trx_series()
    add(1958, "TRX", s, src)

    # --- SOL (keyless, ~2023-01+ depth) ---
    s, src = sol_series()
    add(5426, "SOL", s, src,
        flag="validators.app keyless stake depth starts ~2023-01 (epochs before that null on free tier); "
             "a few early months show staking_ratio>1 because total_active_stake includes stake from "
             "tokens CMC counts as non-circulating -- kept un-capped and flagged, not silently clipped")

    # --- CELO: Tier-4 EVM-reclassification checked but NOT BUILT (failed Entry-26 cross-check;
    # free getLogs reconstruction = 2.0M Transfer-based / 25.8M event-based vs on-chain
    # getTotalLockedGold 82.43M -- pre-L2-migration locked state not in post-migration logs).
    # Documented open gap (Entry 43). The check code is preserved in celo_series() above and in
    # _celo_event_check.py for reproducibility; deliberately not emitted into the panel.

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    nz = out[out.staking_ratio.notna()]
    print(f"\nwrote {OUT}  ({len(nz)} asset-months w/ ratio, {nz.cmc_id.nunique()} assets)")
    for sym in ["TRX", "SOL"]:
        d = nz[nz.symbol == sym]
        if len(d):
            print(f"  {sym}: ratio {d.staking_ratio.min():.2%}->{d.staking_ratio.max():.2%} "
                  f"(latest {d.sort_values('month_end').staking_ratio.iloc[-1]:.2%}, "
                  f"latest_staked {d.sort_values('month_end').staked_native.iloc[-1]:,.0f})")


if __name__ == "__main__":
    main()
