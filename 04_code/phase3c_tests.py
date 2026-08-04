"""
phase3c_tests.py -- Phase 3c Tasks C and D tests (spec 8.7 amended + 8.8).

C1 (the session's core question): token H2 with a fee-anchored valuation proxy.
    Token spec s4 (conv + controls + val + conv x val, month FE, two-way clustered)
    with val = ln P/F and separately val = ln prev_gl (+ pf_gl flagged variant).
    Split-sample s5 versions; coverage-matched baselines: the NV/TVL_GL s4
    re-estimated on the SAME covered subsample, so denominator and sample effects
    are separable.
C2  Horse race singles + joint with the fee columns; conviction slope re-estimated
    on the fee-covered subsample with and without the fee signal.
C3  Portfolios: quintile CHEAP-minus-EXPENSIVE long-shorts on P/F and prev_gl
    (EW, min 3/leg) vs LTW; spanning both directions vs the conviction quintile.
C4  Post-2023 sub-periods for the portfolio cells.

D   Technical battery: singles + joint per track for ma_dist/vol12/ivol/amihud/
    skew36 (joint replaces the superseded binary MA-cross with ma_dist -- logged);
    quintile long-shorts per signal (token track); the COMPLETED conviction-quintile
    spanning battery incl. re-run of the two session-044 MA-cross cells with
    ma_dist quintile long-shorts; coin joint re-run with conv x val (does the coin
    interaction survive the completed battery).

Outputs (03_data/phase3/tables/):
  phase3c_c1_feeval.csv, phase3c_race_panel.csv, phase3c_portfolios.csv,
  phase3c_spanning.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path
from linearmodels.panel import PanelOLS
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

CONTROLS = ["size_std", "mom_3m_std", "mom_12_2_std", "r_1m_std", "beta36_std"]
RF_M = 0.04 / 12

# session-044 joint set with the binary MA-cross SUPERSEDED by ma_dist (Entry 110)
JOINT_COMPLETED = ["conv_std", "raw_val_std", "supply_g12_std", "high52_std",
                   "r_1m_std", "mom_3m_std", "mom_12_2_std",
                   "ma_dist_std", "vol12_std", "ivol_std", "amihud_std", "skew36_std"]
TECHS = ["ma_dist", "vol12", "ivol", "amihud", "skew36"]


def run_panel(d, dep, xcols, label, rows):
    d = d.dropna(subset=[dep] + xcols).copy()
    if d.cmc_id.nunique() < 3 or d.month_end.nunique() < 3:
        return
    X = d[xcols].copy()
    d = d.set_index(["cmc_id", "month_end"])
    X.index = d.index
    res = PanelOLS(d[dep], X, time_effects=True, check_rank=False).fit(
        cov_type="clustered", cluster_entity=True, cluster_time=True)
    for v in xcols:
        rows.append(dict(spec=label, var=v, coef=res.params[v], se=res.std_errors[v],
                         t=res.tstats[v], p=res.pvalues[v], n=int(res.nobs),
                         n_assets=d.index.get_level_values(0).nunique()))


def sort_ls(d, sig, q=5, min_leg=3):
    rets = {}
    for t, g in d.groupby("month_end"):
        g = g.dropna(subset=[sig, "r_fwd1"])
        if len(g) < 2 * min_leg:
            continue
        try:
            b = pd.qcut(g[sig], q, labels=False, duplicates="drop")
        except ValueError:
            continue
        if b.max() != q - 1:
            continue
        top, bot = g[b == q - 1], g[b == 0]
        if len(top) < min_leg or len(bot) < min_leg:
            continue
        rets[t] = top.r_fwd1.mean() - bot.r_fwd1.mean()
    s = pd.Series(rets).sort_index()
    s.index = pd.DatetimeIndex(s.index)
    return s


def nw(y, X, lags=3):
    return sm.OLS(y, sm.add_constant(X), missing="drop").fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})


def main():
    p = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    fee = pd.read_csv(OUT / "fee_comparators.csv", parse_dates=["month_end"])
    tech = pd.read_csv(OUT / "technical_signals.csv", parse_dates=["month_end"])
    sig = pd.read_csv(OUT / "horserace_signals.csv", parse_dates=["month_end"])
    p = p.merge(fee.drop(columns=["symbol", "market_cap", "beta36", "r_e"],
                         errors="ignore"), on=["cmc_id", "month_end"], how="left")
    p = p.merge(tech.drop(columns=["track"]), on=["cmc_id", "month_end"], how="left")
    p = p.merge(sig.drop(columns=["track"]), on=["cmc_id", "month_end"], how="left")
    p["conv_x_val"] = p["conv_std"] * p["val_std"]
    fac = (pd.read_csv(OUT / "ltw_factors_monthly.csv", parse_dates=["month_end"])
           .set_index("month_end"))
    F = fac[["cmkt", "csmb", "cmom"]]
    tok = p[p.track == "token"].copy()

    # ================= C1: H2 with fee-anchored valuation =================
    c1 = []
    for vname in ("pf_ln", "prev_gl_ln", "pf_gl_ln"):
        vstd = vname + "_std"
        d = tok[tok[vstd].notna()].copy()
        d["conv_x_fee"] = d["conv_std"] * d[vstd]
        pre = f"token_{vname}_"
        # s4 with the fee-anchored valuation
        run_panel(d, "r_fwd1_w", ["conv_std"] + CONTROLS + [vstd, "conv_x_fee"],
                  pre + "s4", c1)
        # split-sample s5 on the fee valuation (median within month)
        med = d.groupby("month_end")[vname].transform("median")
        d["high_fee"] = (d[vname] > med).astype(float)
        d["conv_x_highfee"] = d["conv_std"] * d["high_fee"]
        run_panel(d[d.high_fee == 0], "r_fwd1_w", ["conv_std"] + CONTROLS,
                  pre + "s5_cheap", c1)
        run_panel(d[d.high_fee == 1], "r_fwd1_w", ["conv_std"] + CONTROLS,
                  pre + "s5_expensive", c1)
        run_panel(d, "r_fwd1_w", ["conv_std", "high_fee", "conv_x_highfee"] + CONTROLS,
                  pre + "s5_diff", c1)
        # coverage-matched baseline: NV/TVL_GL s4 on the SAME subsample
        run_panel(d, "r_fwd1_w", ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"],
                  pre + "s4_TVLGL_matched", c1)
    # full-sample baseline for reference
    run_panel(tok, "r_fwd1_w", ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"],
              "token_s4_TVLGL_full", c1)
    pd.DataFrame(c1).to_csv(TAB / "phase3c_c1_feeval.csv", index=False)

    # ================= C2 + D: horse race panel =================
    race = []
    for track in ("coin", "token"):
        d0 = p[p.track == track]
        for per, d in (("full", d0), ("sub2024", d0[d0.month_end >= "2024-01-01"])):
            pre = f"{track}_{per}_"
            sing = [t + "_std" for t in TECHS]
            if track == "token":
                sing += ["pf_ln_std", "prev_gl_ln_std", "pf_gl_ln_std"]
            for v in sing:
                run_panel(d, "r_fwd1_w", [v], pre + "single_" + v.replace("_std", ""), race)
            # joint: completed battery
            run_panel(d, "r_fwd1_w", JOINT_COMPLETED, pre + "joint_completed", race)
            if track == "coin":
                run_panel(d, "r_fwd1_w", JOINT_COMPLETED + ["val_std", "conv_x_val"],
                          pre + "joint_completed_int", race)
            if track == "token":
                # fee columns into the race (each on its covered subsample)
                for vstd, tag in (("pf_ln_std", "pf"), ("prev_gl_ln_std", "prevgl")):
                    dc = d[d[vstd].notna()]
                    run_panel(dc, "r_fwd1_w", JOINT_COMPLETED + [vstd],
                              pre + f"joint_completed+{tag}", race)
                    # conviction slope on the SAME subsample without the fee column
                    run_panel(dc, "r_fwd1_w", JOINT_COMPLETED,
                              pre + f"joint_completed_{tag}cov_nofee", race)
    pd.DataFrame(race).to_csv(TAB / "phase3c_race_panel.csv", index=False)

    # ================= C3 + D: portfolios =================
    # negated ratio so top quintile = CHEAP (low P/F, low prev_gl)
    tok["neg_pf"] = -tok["pf_ln"]
    tok["neg_prevgl"] = -tok["prev_gl_ln"]
    ls = {"q5_ew": sort_ls(tok[tok.conv.notna()], "conv")}
    for name, col in (("pf_cheap_ls", "neg_pf"), ("prevgl_cheap_ls", "neg_prevgl"),
                      ("ma_dist_ls", "ma_dist"), ("vol12_ls", "vol12"),
                      ("ivol_ls", "ivol"), ("amihud_ls", "amihud"),
                      ("skew36_ls", "skew36"),
                      ("rev_ls", "r_1m"), ("mom3_ls", "mom_3m"), ("mom12_ls", "mom_12_2"),
                      ("high52_ls", "high52"), ("size_ls", "market_cap"),
                      ("rawval_ls", "raw_val"), ("s2f_ls", "supply_g12")):
        ls[name] = sort_ls(tok, col)

    port_rows = []
    for name, s in ls.items():
        for per, mask in (("full", s.index >= "2000-01-01"),
                          ("post2023", s.index >= "2023-01-01")):
            si = s[mask]
            if len(si) < 12:
                continue
            j = pd.concat([si.rename("y"), F], axis=1).dropna()
            m = nw(j["y"], j[["cmkt", "csmb", "cmom"]])
            sh = (si.mean() - RF_M) / si.std() * np.sqrt(12) if si.std() > 0 else np.nan
            port_rows.append(dict(portfolio=name, period=per, mean_mo=si.mean(),
                                  alpha=m.params["const"], alpha_t=m.tvalues["const"],
                                  sharpe=sh, n=len(j)))
    pd.DataFrame(port_rows).to_csv(TAB / "phase3c_portfolios.csv", index=False)

    # ================= spanning battery =================
    span_rows = []

    def span(label, yname, xnames):
        xdf = pd.concat([ls[x].rename(x) for x in xnames], axis=1, sort=True)
        j = pd.concat([ls[yname].rename("y"), F, xdf], axis=1, sort=True).dropna()
        if len(j) < 12:
            span_rows.append(dict(spec=label, y=yname, alpha=np.nan, alpha_t=np.nan,
                                  n=len(j), note="under 12 months"))
            return
        X = j[["cmkt", "csmb", "cmom"] + xnames]
        m = nw(j["y"], X)
        row = dict(spec=label, y=yname, alpha=m.params["const"],
                   alpha_t=m.tvalues["const"], n=int(m.nobs), r2=m.rsquared)
        for c in xnames:
            row[f"b_{c}"] = m.params[c]
            row[f"t_{c}"] = m.tvalues[c]
        span_rows.append(row)

    new_comps = ["pf_cheap_ls", "prevgl_cheap_ls", "ma_dist_ls", "vol12_ls",
                 "ivol_ls", "amihud_ls", "skew36_ls"]
    old_comps = ["rev_ls", "mom3_ls", "mom12_ls", "high52_ls", "size_ls",
                 "rawval_ls", "s2f_ls"]
    # direction 1: conviction quintile on LTW + each new competitor singly
    for c in new_comps:
        span(f"q5_on_ltw+{c}", "q5_ew", [c])
    # the two superseded session-044 cells, re-run with ma_dist (Entry 110)
    span("q5_on_ltw+all7_madist", "q5_ew", old_comps + ["ma_dist_ls"])
    # the COMPLETED battery (old 7 with ma_dist + 4 new technicals)
    span("q5_on_ltw+completed", "q5_ew",
         old_comps + ["ma_dist_ls", "vol12_ls", "ivol_ls", "amihud_ls", "skew36_ls"])
    # completed + fee comparators (coverage shrinks to fee months)
    span("q5_on_ltw+completed+fees", "q5_ew",
         old_comps + ["ma_dist_ls", "vol12_ls", "ivol_ls", "amihud_ls", "skew36_ls",
                      "pf_cheap_ls", "prevgl_cheap_ls"])
    # direction 2: each new competitor on LTW + q5_ew
    for c in new_comps:
        span(f"{c}_on_ltw+q5", c, ["q5_ew"])
    pd.DataFrame(span_rows).to_csv(TAB / "phase3c_spanning.csv", index=False)

    # ================= console =================
    pd.set_option("display.width", 250)
    print("=== C1: H2 with fee-anchored valuation (key cells) ===")
    c1df = pd.DataFrame(c1)
    key = c1df[c1df["var"].isin(["conv_std", "conv_x_fee", "conv_x_val",
                                 "conv_x_highfee"])]
    for sp in key.spec.unique():
        g = key[key.spec == sp]
        cells = "  ".join(f"{r.var}={r.coef:+.4f} (t={r.t:+.2f})" for r in g.itertuples())
        print(f"  {sp:38s} n={g.n.iloc[0]:5d} a={g.n_assets.iloc[0]:3d}  {cells}")
    print("\n=== C2/D: race (key cells) ===")
    rdf = pd.DataFrame(race)
    show = rdf[((rdf.spec.str.contains("single")) & (rdf.t.abs() > 1.6)) |
               ((rdf.spec.str.contains("joint")) &
                rdf["var"].isin(["conv_std", "conv_x_val", "pf_ln_std", "prev_gl_ln_std"]))]
    for r in show.itertuples():
        print(f"  {r.spec:44s} {r.var:16s} {r.coef:+.4f} (t={r.t:+.2f}) n={r.n}")
    print("\n=== C3/D: portfolios (alpha vs LTW) ===")
    for r in port_rows:
        print(f"  {r['portfolio']:18s} {r['period']:9s} mean={r['mean_mo']:+.4f} "
              f"alpha={r['alpha']:+.4f} (t={r['alpha_t']:+.2f}) sharpe={r['sharpe']:+.2f} n={r['n']}")
    print("\n=== spanning ===")
    for r in span_rows:
        extra = "" if "note" not in r else f"  [{r['note']}]"
        print(f"  {r['spec']:34s} alpha={r['alpha']:+.4f} (t={r['alpha_t']:+.2f}) "
              f"n={r['n']}{extra}")


if __name__ == "__main__":
    main()
