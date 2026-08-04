"""
phase3b_sorts.py -- Phase 3b Task B (spec section 8.2): CONFIRMATORY conviction-only
token sorts. Upgraded from Entry 97 (exploratory); the paper must disclose that origin.

Construction (all sorts formed monthly on information through t, held t+1, raw r_fwd1):
  PRIMARY   : token conviction (lambda_z) quintile long-short, EW, min 3 per leg.
  SECONDARY : quintile VW; decile EW (min 3/leg, thin months flagged); tercile EW/VW
              (min 4/leg -- continuity with 043/Entry 97).
  SECTOR-NEUTRAL: conv demeaned within coarse sector-month (groups >= 3 names; smaller
              groups demeaned within class-month), then quintile EW on the full token
              cross-section.
  PER-SECTOR: tercile EW long-short (min 3/leg) inside each of the 3 largest coarse
              groups (DEX, Other, Lending) -- single sort, no valuation dimension.
  COIN ANALOG: conviction tercile EW (min 3/leg), descriptive only.

Evaluation (spec 4.3): NW-3 alpha vs monthly LTW factors (CMKT/CSMB/CMOM), annualized
Sharpe (excess of rf = 4%/12), pre/post-2023 sub-periods, one-way leg turnover, net
alphas at 25/50 bps per side.

Spanning (make-or-break, spec 8.2): quintile SMA regressed on LTW factors PLUS
identically-built (quintile EW min-3 top-minus-bottom) token long-shorts on r_1m
(reversal), mom_3m, 52-wk-high and size; jointly and each added singly.

Outputs: 03_data/phase3/conv_sort_returns.csv,
         03_data/phase3/tables/convsort_{alphas,stats,spanning}.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

RF_M = 0.04 / 12
COSTS = (0.0025, 0.0050)
SECTORS_TESTED = ["DEX", "Other", "Lending"]  # 3 largest coarse groups (Task A output)


def sort_ls(d, sig, q, vw=False, min_leg=3):
    """Quantile long-short within each month. Returns (series, top_w, bot_w, legsizes)."""
    rets, topw, botw, sizes = {}, [], [], {}
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
        wt = (top.market_cap / top.market_cap.sum()) if vw else pd.Series(1 / len(top), index=top.index)
        wb = (bot.market_cap / bot.market_cap.sum()) if vw else pd.Series(1 / len(bot), index=bot.index)
        rets[t] = float((wt * top.r_fwd1).sum() - (wb * bot.r_fwd1).sum())
        for wl, leg, store in ((wt, top, topw), (wb, bot, botw)):
            s = pd.Series(wl.values, index=leg.cmc_id.values)
            s.name = t
            store.append(s)
        sizes[t] = (len(top), len(bot))
    s = pd.Series(rets).sort_index()
    s.index = pd.DatetimeIndex(s.index)
    return s, topw, botw, sizes


def turnover(wlist):
    tos = {}
    for i in range(1, len(wlist)):
        prev, cur = wlist[i - 1], wlist[i]
        union = prev.index.union(cur.index)
        tos[cur.name] = 0.5 * float((cur.reindex(union, fill_value=0)
                                     - prev.reindex(union, fill_value=0)).abs().sum())
    s = pd.Series(tos)
    s.index = pd.DatetimeIndex(s.index)
    return s


def nw(y, X, lags=3):
    return sm.OLS(y, sm.add_constant(X), missing="drop").fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})


def sharpe(r):
    ex = r - RF_M
    return float(ex.mean() / ex.std() * np.sqrt(12)) if ex.std() > 0 else np.nan


def main():
    p = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    cmap = pd.read_csv(OUT / "sector_coarse_map.csv")[["cmc_id", "sector_coarse"]]
    sig = pd.read_csv(OUT / "horserace_signals.csv", parse_dates=["month_end"])
    fac = (pd.read_csv(OUT / "ltw_factors_monthly.csv", parse_dates=["month_end"])
           .set_index("month_end"))
    p = p.merge(cmap, on="cmc_id", how="left")
    p = p.merge(sig[["cmc_id", "month_end", "high52"]], on=["cmc_id", "month_end"], how="left")

    tok = p[(p.track == "token") & p.conv.notna()].copy()
    coin = p[(p.track == "coin") & p.conv.notna()].copy()

    # sector-neutral conviction: demean within coarse sector-month if n>=3, else class-month
    tok["sec_n"] = tok.groupby(["month_end", "sector_coarse"])["conv"].transform("count")
    sec_mean = tok.groupby(["month_end", "sector_coarse"])["conv"].transform("mean")
    cls_mean = tok.groupby("month_end")["conv"].transform("mean")
    tok["conv_sn"] = np.where(tok.sec_n >= 3, tok.conv - sec_mean, tok.conv - cls_mean)

    # ---------- build all sort variants ----------
    variants = {}   # name -> (series, topw, botw, sizes)
    variants["q5_ew"] = sort_ls(tok, "conv", 5, vw=False, min_leg=3)      # PRIMARY
    variants["q5_vw"] = sort_ls(tok, "conv", 5, vw=True, min_leg=3)
    variants["d10_ew"] = sort_ls(tok, "conv", 10, vw=False, min_leg=3)
    variants["t3_ew"] = sort_ls(tok, "conv", 3, vw=False, min_leg=4)
    variants["t3_vw"] = sort_ls(tok, "conv", 3, vw=True, min_leg=4)
    variants["q5_ew_secneutral"] = sort_ls(tok, "conv_sn", 5, vw=False, min_leg=3)
    for sec in SECTORS_TESTED:
        variants[f"t3_ew_{sec}"] = sort_ls(tok[tok.sector_coarse == sec], "conv", 3,
                                           vw=False, min_leg=3)
    variants["coin_t3_ew"] = sort_ls(coin, "conv", 3, vw=False, min_leg=3)

    # competitor long-shorts for spanning (identical construction: quintile EW min3)
    comp = {}
    for name, col in (("rev_ls", "r_1m"), ("mom3_ls", "mom_3m"),
                      ("high52_ls", "high52"), ("size_ls", "market_cap")):
        comp[name], *_ = sort_ls(tok, col, 5, vw=False, min_leg=3)

    # ---------- evaluation ----------
    alpha_rows, stat_rows = [], []
    F = fac[["cmkt", "csmb", "cmom"]]

    def evaluate(name, s, to_total=None):
        s = s.dropna()
        if len(s) < 12:
            stat_rows.append(dict(portfolio=name, note=f"too few months ({len(s)})"))
            return
        stat_rows.append(dict(portfolio=name, mean=s.mean(), sd=s.std(), sharpe=sharpe(s),
                              n=len(s), start=s.index.min().date(), end=s.index.max().date()))
        j = pd.concat([s.rename("y"), F], axis=1).dropna()
        m = nw(j["y"], j[["cmkt", "csmb", "cmom"]])
        alpha_rows.append(dict(portfolio=name, period="full", alpha=m.params["const"],
                               alpha_t=m.tvalues["const"], b_cmkt=m.params["cmkt"],
                               b_csmb=m.params["csmb"], b_cmom=m.params["cmom"],
                               n=int(m.nobs), r2=m.rsquared))
        for lab, mask in (("pre2023", j.index < "2023-01-01"),
                          ("post2023", j.index >= "2023-01-01")):
            jj = j[mask]
            if len(jj) >= 12:
                mm = nw(jj["y"], jj[["cmkt", "csmb", "cmom"]])
                alpha_rows.append(dict(portfolio=name, period=lab, alpha=mm.params["const"],
                                       alpha_t=mm.tvalues["const"], b_cmkt=mm.params["cmkt"],
                                       b_csmb=mm.params["csmb"], b_cmom=mm.params["cmom"],
                                       n=int(mm.nobs), r2=mm.rsquared))
        if to_total is not None:
            for c in COSTS:
                net = (s - to_total.reindex(s.index).fillna(0.0) * c).rename("y")
                jn = pd.concat([net, F], axis=1).dropna()
                mn = nw(jn["y"], jn[["cmkt", "csmb", "cmom"]])
                alpha_rows.append(dict(portfolio=f"{name}_net{int(c*1e4)}bps", period="full",
                                       alpha=mn.params["const"], alpha_t=mn.tvalues["const"],
                                       b_cmkt=mn.params["cmkt"], b_csmb=mn.params["csmb"],
                                       b_cmom=mn.params["cmom"], n=int(mn.nobs), r2=mn.rsquared))

    series_out = {}
    for name, (s, topw, botw, sizes) in variants.items():
        to_l, to_s = turnover(topw), turnover(botw)
        to_total = to_l.add(to_s, fill_value=np.nan)
        evaluate(name, s, to_total=to_total)
        if len(to_l):
            stat_rows.append(dict(portfolio=f"{name}_turnover", mean=to_l.mean(),
                                  sd=to_s.mean(), n=len(to_l)))
        if sizes:
            ls = pd.DataFrame(sizes).T
            stat_rows.append(dict(portfolio=f"{name}_legsize", mean=ls[0].mean(),
                                  sd=ls[1].mean(), n=int((ls.min(axis=1) <= 3).sum())))
        series_out[name] = s
    for name, s in comp.items():
        evaluate(name, s)
        series_out[name] = s

    # ---------- spanning: THE make-or-break test ----------
    span_rows = []
    y = variants["q5_ew"][0].rename("y")
    compdf = pd.DataFrame(comp)

    def span(label, xdf):
        j = pd.concat([y, xdf], axis=1).dropna()
        m = nw(j["y"], j[xdf.columns])
        row = dict(spec=label, alpha=m.params["const"], alpha_t=m.tvalues["const"],
                   n=int(m.nobs), r2=m.rsquared)
        for c in xdf.columns:
            row[f"b_{c}"] = m.params[c]
            row[f"t_{c}"] = m.tvalues[c]
        span_rows.append(row)

    span("ltw_only", F)
    for c in compdf.columns:
        span(f"ltw+{c}", pd.concat([F, compdf[[c]]], axis=1))
    span("ltw+all4", pd.concat([F, compdf], axis=1))
    span("all4_only", compdf)

    pd.DataFrame(alpha_rows).to_csv(TAB / "convsort_alphas.csv", index=False)
    pd.DataFrame(stat_rows).to_csv(TAB / "convsort_stats.csv", index=False)
    pd.DataFrame(span_rows).to_csv(TAB / "convsort_spanning.csv", index=False)
    allret = pd.DataFrame(series_out)
    allret.index.name = "month_end"
    allret.to_csv(OUT / "conv_sort_returns.csv")

    # ---------- console ----------
    print("=== conviction sorts: NW-3 alpha vs LTW ===")
    for r in alpha_rows:
        print(f"  {r['portfolio']:26s} {r['period']:9s} alpha={r['alpha']:+.4f} "
              f"(t={r['alpha_t']:+.2f})  n={r['n']}")
    print("\n=== stats ===")
    for r in stat_rows:
        if "mean" in r and not str(r["portfolio"]).endswith(("_turnover", "_legsize")):
            print(f"  {r['portfolio']:26s} mean={r['mean']:+.4f} sharpe={r['sharpe']:+.2f} n={r['n']}")
        elif str(r["portfolio"]).endswith("_turnover"):
            print(f"  {r['portfolio']:26s} TO top={r['mean']:.3f} bot={r['sd']:.3f}")
        elif str(r["portfolio"]).endswith("_legsize"):
            print(f"  {r['portfolio']:26s} legsize top={r['mean']:.1f} bot={r['sd']:.1f} "
                  f"months_at_min={r['n']}")
        elif "note" in r:
            print(f"  {r['portfolio']:26s} {r['note']}")
    print("\n=== spanning of q5_ew (alpha must survive the reversal battery) ===")
    for r in span_rows:
        extras = "  ".join(f"{k[2:]}={r[k]:+.2f}(t={r['t_'+k[2:]]:+.1f})"
                           for k in r if k.startswith("b_"))
        print(f"  {r['spec']:14s} alpha={r['alpha']:+.4f} (t={r['alpha_t']:+.2f}) "
              f"n={r['n']} r2={r['r2']:.2f}\n{'':17s}{extras}")


if __name__ == "__main__":
    main()
