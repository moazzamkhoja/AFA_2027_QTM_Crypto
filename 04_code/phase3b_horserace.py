"""
phase3b_horserace.py -- Phase 3b Task C (spec sections 5.2 / 8.3): horse race.

(a) Panel race per track: dep = r_fwd1_w, month FE, SEs two-way clustered (asset,
    month). Each standardized comparator signal singly, then all jointly with conv_std.
    Comparators: raw valuation (raw NVT coins / raw NV/TVL tokens), S2F (literal s2f_ln
    where 12m flow > 0; supply_g12 full-coverage inverse proxy used in the joint),
    52-wk high, MA cross, momentum family (r_1m, mom_3m, mom_12_2).
    Coins add a joint spec with val_std + conv x val (the surviving coin result is the
    interaction, so the race must test IT, not the dead unconditional slope).
    MVRV skipped (Entry 96); Metcalfe descriptive only (phase3b_metcalfe.py).

(b) Spanning both directions, token track (quintile EW min-3 construction as in 8.2):
    q5_ew on LTW + competitor long-shorts (done in phase3b_sorts.py; repeated here with
    the raw-valuation and MA-cross long-shorts added), and each competitor long-short
    on LTW + q5_ew. Coin track: no portfolio spanning (breadth; 043 quadrant SMA dead).

(c) Sub-period stability: (a) singles + joint repeated on formation months
    2024-01..2026-05.

Outputs: 03_data/phase3/tables/horserace_panel.csv, horserace_spanning.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path
from linearmodels.panel import PanelOLS
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

SINGLES = ["conv_std", "raw_val_std", "s2f_ln_std", "supply_g12_std", "high52_std",
           "ma_cross_std", "r_1m_std", "mom_3m_std", "mom_12_2_std"]
JOINT = ["conv_std", "raw_val_std", "supply_g12_std", "high52_std", "ma_cross_std",
         "r_1m_std", "mom_3m_std", "mom_12_2_std"]


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
                         t=res.tstats[v], p=res.pvalues[v], n=int(res.nobs)))


def sort_ls(d, sig, q, min_leg=3):
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


def binary_ls(d, sig, min_leg=3):
    rets = {}
    for t, g in d.groupby("month_end"):
        g = g.dropna(subset=[sig, "r_fwd1"])
        on, off = g[g[sig] == 1], g[g[sig] == 0]
        if len(on) < min_leg or len(off) < min_leg:
            continue
        rets[t] = on.r_fwd1.mean() - off.r_fwd1.mean()
    s = pd.Series(rets).sort_index()
    s.index = pd.DatetimeIndex(s.index)
    return s


def nw(y, X, lags=3):
    return sm.OLS(y, sm.add_constant(X), missing="drop").fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})


def main():
    p = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    sig = pd.read_csv(OUT / "horserace_signals.csv", parse_dates=["month_end"])
    p = p.merge(sig.drop(columns=["track"]), on=["cmc_id", "month_end"], how="left")
    p["conv_x_val"] = p["conv_std"] * p["val_std"]
    fac = (pd.read_csv(OUT / "ltw_factors_monthly.csv", parse_dates=["month_end"])
           .set_index("month_end"))
    F = fac[["cmkt", "csmb", "cmom"]]

    # ---------- (a) + (c) panel race ----------
    rows = []
    for track in ("coin", "token"):
        d0 = p[p.track == track]
        for per, d in (("full", d0), ("sub2024", d0[d0.month_end >= "2024-01-01"])):
            pre = f"{track}_{per}_"
            for v in SINGLES:
                run_panel(d, "r_fwd1_w", [v], pre + "single_" + v.replace("_std", ""), rows)
            run_panel(d, "r_fwd1_w", JOINT, pre + "joint", rows)
            if track == "coin":
                run_panel(d, "r_fwd1_w", JOINT + ["val_std", "conv_x_val"],
                          pre + "joint_int", rows)
    pd.DataFrame(rows).to_csv(TAB / "horserace_panel.csv", index=False)

    # ---------- (b) spanning, token track ----------
    tok = p[(p.track == "token") & p.conv.notna()].copy()
    ls = {"q5_ew": sort_ls(tok, "conv", 5)}
    for name, col in (("rev_ls", "r_1m"), ("mom3_ls", "mom_3m"), ("mom12_ls", "mom_12_2"),
                      ("high52_ls", "high52"), ("size_ls", "market_cap"),
                      ("rawval_ls", "raw_val"), ("s2f_ls", "supply_g12")):
        ls[name] = sort_ls(tok, col, 5)
    ls["macross_ls"] = binary_ls(tok, "ma_cross")

    span_rows = []
    comp_names = [k for k in ls if k != "q5_ew"]

    def span(label, yname, xnames):
        xdf = pd.concat([ls[x].rename(x) for x in xnames] , axis=1, sort=True)
        j = pd.concat([ls[yname].rename("y"), F, xdf], axis=1, sort=True).dropna()
        X = j[["cmkt", "csmb", "cmom"] + xnames]
        m = nw(j["y"], X)
        row = dict(spec=label, y=yname, alpha=m.params["const"],
                   alpha_t=m.tvalues["const"], n=int(m.nobs), r2=m.rsquared)
        for c in xnames:
            row[f"b_{c}"] = m.params[c]
            row[f"t_{c}"] = m.tvalues[c]
        span_rows.append(row)

    # direction 1: our portfolio on LTW + competitors
    for c in comp_names:
        span(f"q5_on_ltw+{c}", "q5_ew", [c])
    span("q5_on_ltw+all", "q5_ew", comp_names)
    # direction 2: each competitor on LTW + q5_ew
    for c in comp_names:
        span(f"{c}_on_ltw+q5", c, ["q5_ew"])
    pd.DataFrame(span_rows).to_csv(TAB / "horserace_spanning.csv", index=False)

    # ---------- console ----------
    res = pd.DataFrame(rows)
    print("=== panel race: singles (own coefficient) ===")
    for r in res.itertuples():
        if "single" in r.spec and r.var != "const":
            print(f"  {r.spec:44s} {r.coef:+.4f} (t={r.t:+.2f}) n={r.n}")
    print("\n=== panel race: joint (all signals incl conv) ===")
    for r in res.itertuples():
        if "joint" in r.spec:
            print(f"  {r.spec:32s} {r.var:16s} {r.coef:+.4f} (t={r.t:+.2f})")
    print("\n=== spanning ===")
    for r in span_rows:
        print(f"  {r['spec']:26s} alpha={r['alpha']:+.4f} (t={r['alpha_t']:+.2f}) "
              f"n={r['n']} r2={r['r2']:.2f}")


if __name__ == "__main__":
    main()
