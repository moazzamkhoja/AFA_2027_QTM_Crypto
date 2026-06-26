"""
phase1_channel1_pos_coins.py  --  SESSION 019, Part A.3: Coin Channel 1 (staking ratio)
for PoS coins, from each chain's OWN free, keyless, historical on-chain API.

Before building, an Entry-21-style LIVE free-access audit was run across the highest-cap
PoS/staking coins in the 633-coin roster (candidates derived from classification_table
consensus tags + the reference list SOL/ADA/DOT/ATOM/AVAX/NEAR/ALGO/TRX/XTZ/EOS/ICP/KSM/
CELO/KAVA/HBAR/INJ/SEI/SUI/APT). Only two chains publish a genuinely FREE, KEYLESS,
HISTORICAL bonded/staked-supply time series:

  ADA (cmc 2010) -- Koios  api.koios.rest /epoch_info  -> active_stake per epoch (lovelace,
                    /1e6 = ADA). Shelley staking begins epoch 210 (2020-08); pre-Shelley
                    (Byron) epochs have no active_stake -> emitted NaN, never 0.
  XTZ (cmc 2011) -- TzKT   api.tzkt.io /cycles         -> totalBakingPower per cycle (mutez,
                    /1e6 = XTZ). Available from cycle 0 (2018-07). FLAG: the 2024 "Paris"
                    protocol (Adaptive Issuance + staking) redefined baking power, so the
                    post-2024 level is not strictly comparable to the delegation-era level
                    (analogous to ETH's post-Shapella caveat). Kept as a monotone on-chain
                    participation proxy with this flag.

DOCUMENTED GAPS (live-verified this session; no free historical staked-supply series):
  Cosmos SDK chains  ATOM/INJ/SEI/KAVA/CELO -- /cosmos/staking/v1beta1/pool returns only
                     CURRENT bonded_tokens, no history (confirms Entry 24 / Phase 2b).
  SOL                public RPC getEpochInfo/getVoteAccounts are current-state only;
                     historical staked supply needs a keyed indexer (Solana Beach /
                     validators.app) -- not free/keyless.
  HBAR               Hedera Mirror /network/stake returns current reward params only.
  ICP                ic-api governance metric endpoints now 404 (API moved); no verified
                     free historical neuron-staking series located this session.
  DOT/KSM            Subscan requires an API key; public RPC is current-state only.
  AVAX/NEAR/ALGO/TRX/EOS/SUI/APT -- no verified free, keyless, historical staked-supply
                     series found; not built (gap, per the no-guess/no-interpolate rule).

Ratio denominator = circulating supply from the Phase 0 universe panel (cmc_id+month_end),
the same convention as the other channel1_*.csv files. "Last observation per calendar
month" = the epoch/cycle with the latest end time within that YYYY-MM. No interpolation,
no carry-forward of a current ratio backward in time.

Output: 03_data/phase1/channel1_pos_coins.csv  (picked up by the channel1_*.csv glob).
        Raw series cached under 03_data/raw/phase1_onchain/pos_coins/.
"""

import json
import datetime as dt
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_pos_coins.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins"
RAW.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "afa-2027-qtm-research (academic, free-tier)"}
NOW = dt.datetime.utcnow().timestamp()


def _get_json(url, cache_name):
    cf = RAW / cache_name
    if cf.exists():
        return json.loads(cf.read_text(encoding="utf-8"))
    r = requests.get(url, headers=H, timeout=90)
    r.raise_for_status()
    d = r.json()
    cf.write_text(json.dumps(d), encoding="utf-8")
    return d


def ada_series():
    """ADA staked (active_stake) per calendar month from Koios epoch_info."""
    ep = _get_json("https://api.koios.rest/api/v1/epoch_info?select=epoch_no,active_stake,end_time&order=epoch_no.asc",
                   "koios_epoch_info.json")
    by_ym = {}
    for e in ep:
        end = e.get("end_time")
        av = e.get("active_stake")
        if not end or end > NOW or not av:   # skip future/projected epochs and pre-Shelley nulls
            continue
        ym = dt.datetime.utcfromtimestamp(int(end)).strftime("%Y-%m")
        staked = int(av) / 1e6
        cur = by_ym.get(ym)
        if cur is None or int(end) >= cur[0]:
            by_ym[ym] = (int(end), staked)
    return {ym: v for ym, (_, v) in by_ym.items()}, "koios:epoch_info.active_stake"


def xtz_series():
    """XTZ baking power (totalBakingPower) per calendar month from TzKT cycles."""
    cy = _get_json("https://api.tzkt.io/v1/cycles?select=index,endTime,totalBakingPower&sort.asc=index&limit=10000",
                   "tzkt_cycles.json")
    by_ym = {}
    for c in cy:
        end = c.get("endTime")
        bp = c.get("totalBakingPower")
        if not end or not bp:
            continue
        ts = dt.datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()
        if ts > NOW:   # skip future cycles
            continue
        ym = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m")
        staked = int(bp) / 1e6
        cur = by_ym.get(ym)
        if cur is None or ts >= cur[0]:
            by_ym[ym] = (ts, staked)
    return {ym: v for ym, (_, v) in by_ym.items()}, "tzkt:cycles.totalBakingPower"


def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]

    chains = [
        (2010, "ADA", ada_series, ""),
        (2011, "XTZ", xtz_series, "PARIS-2024 baking-power redefinition (post-2024 not "
                                  "strictly comparable to delegation-era level)"),
    ]
    rows = []
    for cid, sym, fn, flag in chains:
        series, src = fn()
        obs = panel[(panel.cmc_id == cid) & (panel.status == "observed")][["month_end", "ym", "circulating_supply"]]
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
        print(f"  {sym}: {n} months with a staking_ratio  (series months={len(series)}, "
              f"{min(series) if series else '-'}->{max(series) if series else '-'}) src={src}")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    nz = out[out.staking_ratio.notna()]
    print(f"\nwrote {OUT}  ({len(nz)} asset-months with a ratio, {nz.cmc_id.nunique()} assets)")
    # sanity: show a few ratios per chain
    for sym in ["ADA", "XTZ"]:
        d = nz[nz.symbol == sym]
        if len(d):
            print(f"  {sym} ratio range: {d.staking_ratio.min():.2%} -> {d.staking_ratio.max():.2%} "
                  f"(latest {d.sort_values('month_end').staking_ratio.iloc[-1]:.2%})")


if __name__ == "__main__":
    main()
