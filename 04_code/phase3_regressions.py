"""
phase3_regressions.py -- Phase 3 Task C: H1/H2 predictive regressions (spec section 3).

Specification ladder per track (coin / token), dep = r_fwd1_w (monthly 1/99 winsorized
forward return), month FE, SEs two-way clustered by asset and month:

  s1: conv_std
  s2: s1 + size_std, mom_3m_std, mom_12_2_std, r_1m_std, beta36_std
  s3: s2 + val_std
  s4: s3 + conv_std x val_std                     <- H2: interaction < 0
  s5_low / s5_high: s2 on below-/above-median val (within class-month)
  s5_diff: s2 + high_val + conv_std x high_val    <- H2: interaction < 0
  Tokens add: s6_* (sector FE repeat of s1-s5), s7a (conv_vw_std replaces conv on the
  ch3 subsample), s7b (both), s7c (s2 on ch3 subsample for comparability).
  Pooled: s2/s4 with track dummy + conv x token interaction.
  Secondary horizons r_fwd3_w / r_fwd6_w: s4 only, clustered by month (descriptive,
  overlapping windows).
  FM (tokens only, secondary): monthly cross-sections of s2 and s4, Newey-West 3 lags.

Sector FE: first DeFiLlama-style tag consolidated into 7 groups (DEX, LendingCDP,
Derivatives, Bridge, YieldStaking, Stables, Other) -- Entry 95.

Outputs: 03_data/phase3/tables/h1h2_coefficients.csv (tidy),
         03_data/phase3/tables/h1h2_fm_tokens.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path
from linearmodels.panel import PanelOLS
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
TAB = REPO / "03_data" / "phase3" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

CONTROLS = ["size_std", "mom_3m_std", "mom_12_2_std", "r_1m_std", "beta36_std"]

SECTOR_MAP = {
    "Dexs": "DEX", "DEX": "DEX", "DEX Aggregator": "DEX", "Liquidity Manager": "DEX",
    "Lending": "LendingCDP", "CDP": "LendingCDP", "Uncollateralized Lending": "LendingCDP",
    "Derivatives": "Derivatives", "Options": "Derivatives", "Synthetics": "Derivatives",
    "Basis Trading": "Derivatives", "Prediction Market": "Derivatives",
    "Bridge": "Bridge", "Canonical Bridge": "Bridge", "Cross Chain Bridge": "Bridge",
    "Yield": "YieldStaking", "Yield Aggregator": "YieldStaking", "Farm": "YieldStaking",
    "Liquid Staking": "YieldStaking", "Restaking": "YieldStaking", "Token Locker": "YieldStaking",
    "Algo-Stables": "Stables",
}


def run_panel(df, dep, xcols, sector_fe=False, cluster_time_only=False, label=""):
    d = df.dropna(subset=[dep] + xcols).copy()
    X = d[xcols].copy()
    if sector_fe:
        X = pd.concat([X, pd.get_dummies(d["sector_grp"], prefix="sec",
                                         drop_first=True, dtype=float)], axis=1)
    d = d.set_index(["cmc_id", "month_end"])
    X.index = d.index
    mod = PanelOLS(d[dep], X, time_effects=True, check_rank=False)
    if cluster_time_only:
        res = mod.fit(cov_type="clustered", cluster_time=True)
    else:
        res = mod.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
    rows = []
    for v in xcols:
        rows.append(dict(spec=label, var=v, coef=res.params[v], se=res.std_errors[v],
                         t=res.tstats[v], p=res.pvalues[v],
                         n=int(res.nobs), r2_within=res.rsquared_within))
    return rows


def fm_monthly(df, dep, xcols, nw_lags=3):
    """Fama-MacBeth: monthly cross-sectional OLS, NW t-stats on the coefficient series."""
    coefs = []
    for me, g in df.dropna(subset=[dep] + xcols).groupby("month_end"):
        if len(g) < len(xcols) + 3:
            continue
        X = sm.add_constant(g[xcols])
        b = sm.OLS(g[dep], X).fit().params
        b["month_end"] = me
        coefs.append(b)
    cs = pd.DataFrame(coefs).set_index("month_end").sort_index()
    rows = []
    for v in ["const"] + xcols:
        s = cs[v].dropna()
        nw = sm.OLS(s, np.ones(len(s))).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags})
        rows.append(dict(var=v, mean_coef=s.mean(), nw_se=nw.bse.iloc[0],
                         nw_t=nw.tvalues.iloc[0], n_months=len(s)))
    return rows


def main():
    p = pd.read_csv(REPO / "03_data" / "phase3" / "regression_panel.csv")
    p["month_end"] = pd.to_datetime(p["month_end"])
    p["sector_grp"] = p["sector"].fillna("UNK").str.split(";").str[0].map(SECTOR_MAP).fillna("Other")
    p["conv_x_val"] = p["conv_std"] * p["val_std"]

    # median-split on val within track-month
    med = p.groupby(["track", "month_end"])["val"].transform("median")
    p["high_val"] = (p["val"] > med).astype(float)
    p["conv_x_high"] = p["conv_std"] * p["high_val"]

    dep = "r_fwd1_w"
    out = []

    for track in ("coin", "token"):
        d = p[p.track == track]
        pre = f"{track}_"
        out += run_panel(d, dep, ["conv_std"], label=pre + "s1")
        out += run_panel(d, dep, ["conv_std"] + CONTROLS, label=pre + "s2")
        out += run_panel(d, dep, ["conv_std"] + CONTROLS + ["val_std"], label=pre + "s3")
        out += run_panel(d, dep, ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"],
                         label=pre + "s4")
        out += run_panel(d[d.high_val == 0], dep, ["conv_std"] + CONTROLS, label=pre + "s5_low")
        out += run_panel(d[d.high_val == 1], dep, ["conv_std"] + CONTROLS, label=pre + "s5_high")
        out += run_panel(d, dep, ["conv_std", "high_val", "conv_x_high"] + CONTROLS,
                         label=pre + "s5_diff")
        # secondary horizons (descriptive, overlapping -> cluster by month only)
        for h in ("r_fwd3_w", "r_fwd6_w"):
            out += run_panel(d, h, ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"],
                             cluster_time_only=True, label=pre + "s4_" + h.split("_")[1])

    # token sector-FE ladder
    d = p[p.track == "token"]
    for lab, xs in [("s6_1", ["conv_std"]),
                    ("s6_2", ["conv_std"] + CONTROLS),
                    ("s6_3", ["conv_std"] + CONTROLS + ["val_std"]),
                    ("s6_4", ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"]),
                    ("s6_5diff", ["conv_std", "high_val", "conv_x_high"] + CONTROLS)]:
        out += run_panel(d, dep, xs, sector_fe=True, label="token_" + lab)

    # token voting-weighted lambda (ch3 subsample)
    dv = d[d.conv_vw_std.notna()]
    out += run_panel(dv, dep, ["conv_vw_std"] + CONTROLS, label="token_s7a_vw")
    out += run_panel(dv, dep, ["conv_std", "conv_vw_std"] + CONTROLS, label="token_s7b_both")
    out += run_panel(dv, dep, ["conv_std"] + CONTROLS, label="token_s7c_lz_sub")

    # pooled with track interaction
    p["token_dum"] = (p.track == "token").astype(float)
    p["conv_x_token"] = p["conv_std"] * p["token_dum"]
    out += run_panel(p, dep, ["conv_std", "conv_x_token", "token_dum"] + CONTROLS,
                     label="pooled_s2x")
    out += run_panel(p, dep, ["conv_std", "conv_x_token", "token_dum"] + CONTROLS
                     + ["val_std", "conv_x_val"], label="pooled_s4x")

    res = pd.DataFrame(out)
    res.to_csv(TAB / "h1h2_coefficients.csv", index=False)

    # FM tokens (secondary)
    fm = []
    for lab, xs in [("fm_s2", ["conv_std"] + CONTROLS),
                    ("fm_s4", ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"])]:
        for r in fm_monthly(d, dep, xs):
            r["spec"] = lab
            fm.append(r)
    pd.DataFrame(fm).to_csv(TAB / "h1h2_fm_tokens.csv", index=False)

    # ---------- console: key cells ----------
    key = res[res["var"].isin(["conv_std", "conv_x_val", "conv_x_high", "conv_vw_std", "val_std"])]
    pd.set_option("display.width", 200)
    for sp in key.spec.unique():
        g = key[key.spec == sp]
        cells = "  ".join(f"{r.var}={r.coef:+.4f} (t={r.t:+.2f})" for r in g.itertuples())
        n = g.n.iloc[0]
        print(f"{sp:22s} n={n:5d}  {cells}")
    print("\nFM tokens:")
    for r in fm:
        if r["var"] in ("conv_std", "conv_x_val"):
            print(f"  {r['spec']:6s} {r['var']:11s} mean={r['mean_coef']:+.4f} "
                  f"nw_t={r['nw_t']:+.2f}  ({r['n_months']} months)")


if __name__ == "__main__":
    main()
