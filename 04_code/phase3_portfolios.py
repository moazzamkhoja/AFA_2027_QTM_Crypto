"""
phase3_portfolios.py -- Phase 3 Task D: H3 quadrant portfolio (spec sections 4.2-4.3).

Construction (section 4.2):
  Each formation month t, within each class (coin/token) over asset-months with
  non-missing conv AND val: median split on conv and on val.
    Stars = high conv & low val;  Avoid = low conv & high val.
  Breadth guard: a class-month enters only if BOTH legs have >= 4 assets (excluded
  months logged to console and the report). Hold t+1, rebalance monthly.
  EW primary, VW (MC_t) secondary. Portfolio returns are RAW r_fwd1 (no winsorization;
  spec section 1). Pooled = union of class-level memberships, not re-sorted.
  Single-dimension comparators: conviction-only (high conv - low conv) and
  valuation-only (low val - high val) long-shorts, same guard.

Evaluation (section 4.3):
  SMA_t on CMKT/CSMB/CMOM (Task B factors), Newey-West 3 lags -> H3: alpha > 0.
  Sharpe (annualized, excess of rf_m) vs EW-universe benchmark (observed, MC>=$1M).
  Sub-periods: return months before / from 2023-01. Turnover per leg (one-way,
  0.5*sum|dw|), net-of-cost alpha at 25 and 50 bps per side:
  net_t = gross_t - (TO_long_t + TO_short_t) * cost_per_side.

Outputs: 03_data/phase3/portfolio_returns.csv,
         03_data/phase3/tables/h3_alphas.csv, h3_stats.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"
TAB.mkdir(parents=True, exist_ok=True)

MIN_LEG = 4
RF_M = 0.04 / 12
COSTS = (0.0025, 0.0050)


def leg_weights(g, vw):
    w = g["market_cap"] if vw else pd.Series(1.0, index=g.index)
    return w / w.sum()


def build_series(panel, legs_def, vw=False):
    """legs_def: dict name -> boolean mask column. Returns monthly return + weights per leg."""
    rets, weights = {}, {}
    for name, mask_col in legs_def.items():
        rows = []
        wlist = []
        for t, g in panel[panel[mask_col]].groupby("month_end"):
            g = g[g.r_fwd1.notna()]
            if len(g) == 0:
                continue
            w = leg_weights(g, vw)
            rows.append((t, float((w * g.r_fwd1).sum()), len(g)))
            ww = pd.Series(w.values, index=g.cmc_id.values)
            ww.name = t
            wlist.append(ww)
        s = pd.DataFrame(rows, columns=["month_end", "ret", "n"]).set_index("month_end")
        rets[name] = s
        weights[name] = wlist
    return rets, weights


def turnover(wlist):
    """Average one-way turnover per rebalance: 0.5 * sum |w_new - w_old| (first month = full buy, excluded)."""
    tos = {}
    for i in range(1, len(wlist)):
        prev, cur = wlist[i - 1], wlist[i]
        union = prev.index.union(cur.index)
        tos[cur.name] = 0.5 * float((cur.reindex(union, fill_value=0.0)
                                     - prev.reindex(union, fill_value=0.0)).abs().sum())
    return pd.Series(tos)


def nw_alpha(y, X, lags=3):
    Xc = sm.add_constant(X)
    m = sm.OLS(y, Xc, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return m


def sharpe(r):
    ex = r - RF_M
    return float(ex.mean() / ex.std() * np.sqrt(12)) if ex.std() > 0 else np.nan


def main():
    p = pd.read_csv(OUT / "regression_panel.csv")
    p["month_end"] = pd.to_datetime(p["month_end"])
    p = p[p.conv.notna() & p.val.notna()].copy()

    # quadrant assignment within class-month
    med_c = p.groupby(["track", "month_end"])["conv"].transform("median")
    med_v = p.groupby(["track", "month_end"])["val"].transform("median")
    p["hi_conv"] = p.conv > med_c
    p["lo_val"] = p.val <= med_v
    p["star"] = p.hi_conv & p.lo_val
    p["avoid"] = ~p.hi_conv & ~p.lo_val

    # breadth guard per class-month (quadrant portfolio)
    counts = p.groupby(["track", "month_end"]).agg(n_star=("star", "sum"), n_avoid=("avoid", "sum"))
    ok = counts[(counts.n_star >= MIN_LEG) & (counts.n_avoid >= MIN_LEG)].reset_index()
    excluded = counts[(counts.n_star < MIN_LEG) | (counts.n_avoid < MIN_LEG)].reset_index()
    print("breadth-guard EXCLUDED class-months (quadrant):")
    for tr, g in excluded.groupby("track"):
        print(f"  {tr}: {len(g)} months "
              f"({g.month_end.min().date()}..{g.month_end.max().date()})")
    p_ok = p.merge(ok[["track", "month_end"]], on=["track", "month_end"])

    # single-dimension guard: >=4 per side of each single split
    cnt1 = p.groupby(["track", "month_end"]).agg(
        n_hc=("hi_conv", "sum"), n_lc=("hi_conv", lambda s: (~s).sum()),
        n_lv=("lo_val", "sum"), n_hv=("lo_val", lambda s: (~s).sum()))
    ok1 = cnt1[(cnt1 >= MIN_LEG).all(axis=1)].reset_index()[["track", "month_end"]]
    p_ok1 = p.merge(ok1, on=["track", "month_end"])

    series = {}
    tostats = {}
    for scope in ("coin", "token", "pooled"):
        sel = p_ok if scope == "pooled" else p_ok[p_ok.track == scope]
        sel1 = p_ok1 if scope == "pooled" else p_ok1[p_ok1.track == scope]
        for vw in (False, True):
            tag = f"{scope}_{'vw' if vw else 'ew'}"
            rets, wts = build_series(sel, {"star": "star", "avoid": "avoid"}, vw=vw)
            idx = rets["star"].index.intersection(rets["avoid"].index)
            sma = (rets["star"].loc[idx, "ret"] - rets["avoid"].loc[idx, "ret"]).rename("ret")
            series[f"sma_{tag}"] = sma
            series[f"star_{tag}"] = rets["star"]["ret"]
            series[f"avoid_{tag}"] = rets["avoid"]["ret"]
            to_l, to_s = turnover(wts["star"]), turnover(wts["avoid"])
            tostats[tag] = (to_l, to_s)
            # single-dimension comparators (EW only, primary weighting)
            if not vw:
                sel1_ = sel1.copy()
                sel1_["lo_conv"] = ~sel1_.hi_conv
                sel1_["hi_val"] = ~sel1_.lo_val
                r1, _ = build_series(sel1_, {"hc": "hi_conv", "lc": "lo_conv",
                                             "lv": "lo_val", "hv": "hi_val"}, vw=False)
                i1 = r1["hc"].index.intersection(r1["lc"].index)
                series[f"convonly_{scope}_ew"] = (r1["hc"].loc[i1, "ret"]
                                                  - r1["lc"].loc[i1, "ret"]).rename("ret")
                i2 = r1["lv"].index.intersection(r1["hv"].index)
                series[f"valonly_{scope}_ew"] = (r1["lv"].loc[i2, "ret"]
                                                 - r1["hv"].loc[i2, "ret"]).rename("ret")

    # EW-universe benchmark
    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv")
    uni["month_end"] = pd.to_datetime(uni["month_end"])
    obs = uni[(uni.status == "observed") & (uni.price > 0)]
    px = obs.pivot_table(index="month_end", columns="cmc_id", values="price").resample("ME").last()
    mcw = obs.pivot_table(index="month_end", columns="cmc_id", values="market_cap").resample("ME").last()
    r_fwd = px.pct_change(fill_method=None).shift(-1).clip(-0.90, 3.00)
    elig = mcw >= 1e6
    ew_bench = r_fwd.where(elig).mean(axis=1).shift(1).rename("ew_universe")  # index by return month
    series["ew_universe"] = ew_bench.dropna()

    allret = pd.DataFrame(series)
    allret.index.name = "month_end"
    allret.to_csv(OUT / "portfolio_returns.csv")

    # ---------- evaluation ----------
    fac = pd.read_csv(OUT / "ltw_factors_monthly.csv", parse_dates=["month_end"]).set_index("month_end")
    stats_rows, alpha_rows = [], []
    for name, s in series.items():
        s = pd.Series(s).dropna()
        if name == "ew_universe" or len(s) < 12:
            continue
        j = pd.concat([s.rename("y"), fac[["cmkt", "csmb", "cmom"]]], axis=1).dropna()
        m = nw_alpha(j["y"], j[["cmkt", "csmb", "cmom"]])
        alpha_rows.append(dict(portfolio=name, period="full", alpha=m.params["const"],
                               alpha_t=m.tvalues["const"], b_cmkt=m.params["cmkt"],
                               b_csmb=m.params["csmb"], b_cmom=m.params["cmom"],
                               n=int(m.nobs), r2=m.rsquared))
        for lab, mask in (("pre2023", j.index < "2023-01-01"), ("post2023", j.index >= "2023-01-01")):
            jj = j[mask]
            if len(jj) >= 12:
                mm = nw_alpha(jj["y"], jj[["cmkt", "csmb", "cmom"]])
                alpha_rows.append(dict(portfolio=name, period=lab, alpha=mm.params["const"],
                                       alpha_t=mm.tvalues["const"], b_cmkt=mm.params["cmkt"],
                                       b_csmb=mm.params["csmb"], b_cmom=mm.params["cmom"],
                                       n=int(mm.nobs), r2=mm.rsquared))
        stats_rows.append(dict(portfolio=name, mean=s.mean(), sd=s.std(), sharpe=sharpe(s),
                               n=len(s), start=s.index.min().date(), end=s.index.max().date()))

    # turnover + cost-adjusted alphas for SMA EW/VW
    for tag, (to_l, to_s) in tostats.items():
        sma = series[f"sma_{tag}"].dropna()
        to_total = (to_l.add(to_s, fill_value=np.nan)).reindex(sma.index)
        stats_rows.append(dict(portfolio=f"sma_{tag}_turnover", mean=to_l.mean(),
                               sd=to_s.mean(), sharpe=np.nan, n=len(to_l),
                               start=None, end=None))
        for c in COSTS:
            net = (sma - to_total.fillna(0.0) * c).rename("y")
            j = pd.concat([net, fac[["cmkt", "csmb", "cmom"]]], axis=1).dropna()
            m = nw_alpha(j["y"], j[["cmkt", "csmb", "cmom"]])
            alpha_rows.append(dict(portfolio=f"sma_{tag}_net{int(c*1e4)}bps", period="full",
                                   alpha=m.params["const"], alpha_t=m.tvalues["const"],
                                   b_cmkt=m.params["cmkt"], b_csmb=m.params["csmb"],
                                   b_cmom=m.params["cmom"], n=int(m.nobs), r2=m.rsquared))

    bench = series["ew_universe"].dropna()
    stats_rows.append(dict(portfolio="ew_universe", mean=bench.mean(), sd=bench.std(),
                           sharpe=sharpe(bench), n=len(bench),
                           start=bench.index.min().date(), end=bench.index.max().date()))

    pd.DataFrame(alpha_rows).to_csv(TAB / "h3_alphas.csv", index=False)
    pd.DataFrame(stats_rows).to_csv(TAB / "h3_stats.csv", index=False)

    print("\n=== SMA alphas (NW-3) ===")
    for r in alpha_rows:
        if r["portfolio"].startswith(("sma_", "convonly", "valonly")):
            print(f"  {r['portfolio']:26s} {r['period']:9s} alpha={r['alpha']:+.4f} "
                  f"(t={r['alpha_t']:+.2f})  n={r['n']}")
    print("\n=== Sharpe (ann.) ===")
    for r in stats_rows:
        if not str(r["portfolio"]).endswith("_turnover"):
            print(f"  {r['portfolio']:26s} mean={r['mean']:+.4f} sd={r['sd']:.4f} "
                  f"sharpe={r['sharpe'] if r['sharpe']==r['sharpe'] else float('nan'):+.2f} n={r['n']}")
    print("\n=== turnover (mean one-way per month: star leg / avoid leg) ===")
    for tag, (to_l, to_s) in tostats.items():
        print(f"  {tag:12s} star {to_l.mean():.3f}  avoid {to_s.mean():.3f}")


if __name__ == "__main__":
    main()
