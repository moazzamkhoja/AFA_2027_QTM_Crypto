"""
phase1_assemble_lambda.py  --  Phase 1, λ index assembly (spec Section 3)

Combines whichever of the three conviction channels are observable for each
`status='observed'` asset-month into the locking/conviction index λ_t:

  1. standardize (z-score) each channel WITHIN its monthly cross-section, using only
     the observed assets that actually have that channel that month;
  2. λ_t = equal-weighted mean of the available z-scored channels for that asset-month
     (NO imputation of missing channels);
  3. record n_channels and which channels contributed.

Channel inputs (canonical sources, Phase 1):
  ch1_staking  -- staking/locking ratio (staked-or-locked / circulating)
                  ETH from beacon deposit-contract logs; EVM vote-escrow tokens from
                  escrow Transfer-log reconstruction (channel1_*.csv).
  ch2_holding  -- holding duration / coin-age: NOT BUILT this phase (documented gap,
                  Entry 24); column kept for the schema, always NaN.
  ch3_voting   -- token-weighted voting turnout (channel3_voting.csv vw_turnout).

Z-SCORING RULE: a channel is standardizable in a month only if >=2 observed assets
have a finite value AND the cross-sectional std > 0. A non-standardizable channel
(e.g. a month where only one asset has staking data) cannot enter the z-score average
for that month -- it is dropped for that month and the fact is counted in the coverage
diagnostics (a single-asset channel is degenerate, not a λ).

Output: 03_data/phase1/lambda_panel.csv   (one row per observed asset-month with >=1
        standardizable channel) + console coverage summary.
"""

import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "03_data" / "phase1"
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = P / "lambda_panel.csv"


def load_channels():
    """Return long df: cmc_id, ym, channel, value (raw channel value)."""
    frames = []
    # Channel 1 -- staking/locking (concat all channel1_*.csv produced this phase)
    for f in sorted(P.glob("channel1_*.csv")):
        d = pd.read_csv(f)
        col = "staking_ratio" if "staking_ratio" in d.columns else "locking_ratio"
        if col not in d.columns:
            continue
        d = d[d[col].notna()][["cmc_id", "month_end", col]].rename(columns={col: "value"})
        d["channel"] = "ch1_staking"
        d["ym"] = d["month_end"].str[:7]
        frames.append(d[["cmc_id", "ym", "channel", "value"]])
    # Channel 3 -- voting turnout
    cv = P / "channel3_voting.csv"
    if cv.exists():
        d = pd.read_csv(cv)
        d = d[d["vw_turnout"].notna()][["cmc_id", "ym", "vw_turnout"]].rename(
            columns={"vw_turnout": "value"})
        d["channel"] = "ch3_voting"
        frames.append(d[["cmc_id", "ym", "channel", "value"]])
    if not frames:
        raise SystemExit("no channel inputs found")
    return pd.concat(frames, ignore_index=True)


def main():
    panel = pd.read_csv(PANEL)
    obs = panel[panel.status == "observed"][["cmc_id", "month_end"]].copy()
    obs["ym"] = obs["month_end"].str[:7]
    obs_keys = set(zip(obs.cmc_id, obs.ym))

    ch = load_channels()
    # keep only observed asset-months (λ is computed on observed rows only)
    ch = ch[[(c, y) in obs_keys for c, y in zip(ch.cmc_id, ch.ym)]].copy()

    # z-score each channel within each (ym, channel) cross-section
    ch["z"] = np.nan
    diag = []  # per (ym, channel): n_assets, standardizable?
    for (ym, channel), g in ch.groupby(["ym", "channel"]):
        vals = g["value"].astype(float)
        n = vals.notna().sum()
        std = vals.std(ddof=0)
        ok = (n >= 2) and (std and std > 0)
        if ok:
            ch.loc[g.index, "z"] = (vals - vals.mean()) / std
        diag.append({"ym": ym, "channel": channel, "n_assets": int(n),
                     "standardizable": bool(ok)})
    diag = pd.DataFrame(diag)

    # λ = equal-weighted mean of available standardized channels per asset-month
    z = ch[ch["z"].notna()]
    lam = (z.groupby(["cmc_id", "ym"])
             .agg(lambda_z=("z", "mean"),
                  n_channels=("channel", "nunique"),
                  channels=("channel", lambda s: "+".join(sorted(set(s)))))
             .reset_index())
    # attach month_end + class + raw channel values (wide) for audit
    me = obs.drop_duplicates("ym").set_index("ym")["month_end"].to_dict()
    lam["month_end"] = lam["ym"].map(me)
    raw_wide = ch.pivot_table(index=["cmc_id", "ym"], columns="channel",
                              values="value", aggfunc="first")
    raw_wide.columns = [f"raw_{c}" for c in raw_wide.columns]
    lam = lam.merge(raw_wide.reset_index(), on=["cmc_id", "ym"], how="left")

    cls = pd.read_csv(REPO / "03_data" / "classification_table.csv")[
        ["cmc_id", "symbol", "asset_class"]]
    lam = lam.merge(cls, on="cmc_id", how="left")
    lam = lam.sort_values(["ym", "cmc_id"])
    cols = ["cmc_id", "symbol", "asset_class", "month_end", "ym", "lambda_z",
            "n_channels", "channels"] + [c for c in lam.columns if c.startswith("raw_")]
    lam[cols].to_csv(OUT, index=False)

    # coverage summary
    print(f"wrote {OUT}")
    print(f"  lambda asset-months: {len(lam)} | distinct assets: {lam.cmc_id.nunique()}")
    print(f"  month range: {lam.ym.min()}→{lam.ym.max()}")
    print("\n  n_channels distribution (asset-months):")
    print(lam.n_channels.value_counts().sort_index().to_string())
    print("\n  channel-combo distribution:")
    print(lam.channels.value_counts().to_string())
    print("\n  standardizable cross-sections by channel (months where the channel had >=2 assets):")
    print(diag[diag.standardizable].channel.value_counts().to_string())
    print("\n  by asset_class (distinct assets with any λ):")
    print(lam.groupby("asset_class").cmc_id.nunique().to_string())
    diag.to_csv(P / "_lambda_channel_diagnostics.csv", index=False)


if __name__ == "__main__":
    main()
