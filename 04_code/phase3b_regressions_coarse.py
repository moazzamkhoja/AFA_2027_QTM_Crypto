"""
phase3b_regressions_coarse.py -- Phase 3b Task A second half (spec section 8.1):
re-run the token regression ladder s6_1-s6_4 with COARSE-sector FE (sector_coarse_map)
and report side-by-side with the session-043 raw-sector (7-group Entry-95 consolidation)
FE versions. Same estimator as phase3_regressions.py: dep = r_fwd1_w, month FE
(time_effects), SEs two-way clustered (asset, month).

Output: 03_data/phase3/tables/h1h2_sector_fe_comparison.csv
"""
import pandas as pd
from pathlib import Path
from linearmodels.panel import PanelOLS

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

CONTROLS = ["size_std", "mom_3m_std", "mom_12_2_std", "r_1m_std", "beta36_std"]

# session-043 raw-sector consolidation (Entry 95) -- reproduced for the side-by-side
SECTOR_MAP_043 = {
    "Dexs": "DEX", "DEX": "DEX", "DEX Aggregator": "DEX", "Liquidity Manager": "DEX",
    "Lending": "LendingCDP", "CDP": "LendingCDP", "Uncollateralized Lending": "LendingCDP",
    "Derivatives": "Derivatives", "Options": "Derivatives", "Synthetics": "Derivatives",
    "Basis Trading": "Derivatives", "Prediction Market": "Derivatives",
    "Bridge": "Bridge", "Canonical Bridge": "Bridge", "Cross Chain Bridge": "Bridge",
    "Yield": "YieldStaking", "Yield Aggregator": "YieldStaking", "Farm": "YieldStaking",
    "Liquid Staking": "YieldStaking", "Restaking": "YieldStaking", "Token Locker": "YieldStaking",
    "Algo-Stables": "Stables",
}


def run_panel(d, dep, xcols, fe_col, label):
    d = d.dropna(subset=[dep] + xcols).copy()
    X = pd.concat([d[xcols],
                   pd.get_dummies(d[fe_col], prefix="sec", drop_first=True, dtype=float)],
                  axis=1)
    d = d.set_index(["cmc_id", "month_end"])
    X.index = d.index
    res = PanelOLS(d[dep], X, time_effects=True, check_rank=False).fit(
        cov_type="clustered", cluster_entity=True, cluster_time=True)
    return [dict(spec=label, var=v, coef=res.params[v], se=res.std_errors[v],
                 t=res.tstats[v], p=res.pvalues[v], n=int(res.nobs),
                 r2_within=res.rsquared_within) for v in xcols]


def main():
    p = pd.read_csv(OUT / "regression_panel.csv")
    p["month_end"] = pd.to_datetime(p["month_end"])
    cmap = pd.read_csv(OUT / "sector_coarse_map.csv")[["cmc_id", "sector_coarse"]]
    d = p[p.track == "token"].merge(cmap, on="cmc_id", how="left")
    d["sector_grp043"] = (d["sector"].fillna("UNK").str.split(";").str[0]
                          .map(SECTOR_MAP_043).fillna("Other"))
    d["conv_x_val"] = d["conv_std"] * d["val_std"]

    ladder = [("s6_1", ["conv_std"]),
              ("s6_2", ["conv_std"] + CONTROLS),
              ("s6_3", ["conv_std"] + CONTROLS + ["val_std"]),
              ("s6_4", ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"])]
    out = []
    for lab, xs in ladder:
        out += run_panel(d, "r_fwd1_w", xs, "sector_grp043", f"raw7_{lab}")
        out += run_panel(d, "r_fwd1_w", xs, "sector_coarse", f"coarse_{lab}")
    res = pd.DataFrame(out)
    res.to_csv(TAB / "h1h2_sector_fe_comparison.csv", index=False)

    key = res[res["var"].isin(["conv_std", "conv_x_val"])]
    print(f"{'spec':16s} {'var':11s} {'coef':>9s} {'t':>7s} {'n':>6s}")
    for r in key.itertuples():
        print(f"{r.spec:16s} {r.var:11s} {r.coef:+9.4f} {r.t:+7.2f} {r.n:6d}")


if __name__ == "__main__":
    main()
