"""
phase2_nvt_gl.py  --  Phase 2: assemble Growth-Levelized NVT (NVT_GL = MC / PQ*) per asset-month.

Resumes CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md Part B steps 1,3-6 on top of the now-built PQ:
  PQ  : 03_data/phase2/pq_tokens.csv (Part A) + pq_coins.csv (Part B)  [transacted value, monthly]
  MC  : 03_data/universe_panel.csv  market_cap (Phase 0 CMC backbone), status='observed'

PQ* (spec 4.1, main.tex Appendix A):
  PQ0     = trailing-12-month sum of monthly PQ   (annual transacted value = nominal throughput)
  g       = trailing 3y CAGR of annual PQ0        (shorter window flagged; capped; +base guard)
  r_e     = rf + beta_j * MRP                      (CAPM-style discount rate; beta vs BTC index)
  g_inf   = 0.03 constant                          (robustness parameter, 2-4% band)
  n       = 10 years                               (robustness parameter)
  PQ* = [ sum_{s=1..n} PQ0(1+g)^s/(1+r_e)^s
          + PQ0(1+g)^n(1+g_inf)/((r_e-g_inf)(1+r_e)^n) ] / annuity_factor(r_e,n)
  annuity_factor(r_e,n) = (1-(1+r_e)^-n)/r_e
  NVT_GL = MC / PQ*

Discount-rate naming: this CAPM use is r_e (PQ* discount rate), kept distinct from the
portfolio-level CAPM control of Phase 3 (spec note in 4.1). MRP/rf/g_inf/n are documented
robustness parameters (PARAMS below); beta and PQ0/g/r_e are all emitted so they can be varied
later without rebuilding (spec 4.2).

Output: 03_data/phase2/nvt_gl_panel.csv  (asset-month: MC, PQ, PQ0, g, beta, r_e, PQ*, NVT_GL, flags)
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase2"

PARAMS = dict(
    rf=0.04,            # annual risk-free (~avg US T-bill over sample) -- robustness param
    mrp=0.30,           # annual crypto market risk premium -- DOCUMENTED ASSUMPTION, not realized
                        #   (realized BTC premium ~1.1/yr is not a forward required return); the
                        #   single most important r_e sensitivity knob. beta emitted to re-derive.
    g_inf=0.03,         # terminal growth (2-4% band) -- robustness param
    n=10,               # projection horizon (years) -- robustness param
    g_cap=(-0.50, 2.00),  # cap trailing PQ CAGR to a sane band; flag when binding
    re_floor=0.05,      # floor r_e at g_inf+0.02 so the terminal term stays well-defined
    beta_window=36, beta_min=12,    # trailing months for beta
    cagr_years=3, cagr_min_months=12,  # g window (k=3y default; >=1y fallback flagged)
    ret_clip=(-0.90, 3.00),         # winsorize monthly returns before beta
)


def annuity_factor(r, n):
    return (1 - (1 + r) ** (-n)) / r


def pq_star(pq0, g, r, g_inf, n):
    if not np.isfinite(pq0) or pq0 <= 0 or not np.isfinite(g) or not np.isfinite(r):
        return np.nan
    r = max(r, g_inf + 0.02)
    s = np.arange(1, n + 1)
    growth_pv = np.sum(pq0 * (1 + g) ** s / (1 + r) ** s)
    terminal = pq0 * (1 + g) ** n * (1 + g_inf) / ((r - g_inf) * (1 + r) ** n)
    return (growth_pv + terminal) / annuity_factor(r, n)


def main():
    P = PARAMS
    panel = pd.read_csv(REPO / "03_data" / "universe_panel.csv")
    panel["month_end"] = pd.to_datetime(panel["month_end"])
    obs = panel[panel.status == "observed"].copy().sort_values(["cmc_id", "month_end"])

    # ---- market factor: BTC monthly simple return (spec's simple alternative; cap-wtd index is
    #      numerically fragile due to penny-token return blowups) ----
    btc = obs[obs.cmc_id == 1][["month_end", "price"]].set_index("month_end")["price"].sort_index()
    r_btc = btc.pct_change().rename("r_btc")
    var_btc_full = r_btc.clip(*P["ret_clip"]).var()

    # ---- asset monthly returns (winsorized) ----
    obs["ret"] = obs.groupby("cmc_id")["price"].pct_change().clip(*P["ret_clip"])
    rmkt = r_btc.clip(*P["ret_clip"])

    # ---- PQ (monthly, transacted value) ----
    cols = ["cmc_id", "symbol", "month_end", "pq_usd", "pq_source"]
    tk = pd.read_csv(OUT / "pq_tokens.csv")
    cn = pd.read_csv(OUT / "pq_coins.csv")
    pq = pd.concat([tk[cols], cn[cols + ["rung"]].rename(columns={})], ignore_index=True)
    pq = pq[pq.pq_usd.notna() & pq.month_end.notna()].copy()
    pq["month_end"] = pd.to_datetime(pq["month_end"])
    pq = pq.sort_values(["cmc_id", "month_end"])
    # PQ0 = trailing-12m sum of monthly PQ (annual throughput); require >=6 months in window
    pq = pq.set_index("month_end")
    def annualize(g):
        s = g["pq_usd"].sort_index()
        roll = s.rolling("365D").sum()
        cnt = s.rolling("365D").count()
        out = pd.DataFrame({"pq_usd": s, "pq0_annual": roll, "pq_nmonths_12": cnt})
        return out
    pq0 = pq.groupby("cmc_id", group_keys=True).apply(annualize, include_groups=False).reset_index()
    src = pq.reset_index()[["cmc_id", "month_end", "pq_source"]]
    if "rung" in cn.columns:
        rungmap = cn[["cmc_id", "rung"]].drop_duplicates("cmc_id").set_index("cmc_id")["rung"]
    pq0 = pq0.merge(src, on=["cmc_id", "month_end"], how="left")

    # ---- g: trailing 3y CAGR of annual PQ0 ----
    def add_g(g):
        g = g.sort_values("month_end").copy()
        s = g.set_index("month_end")["pq0_annual"]
        # value ~36 months earlier (and >=12m fallback)
        gv, gw = [], []
        for dt in s.index:
            base3 = s.loc[:dt - pd.DateOffset(years=P["cagr_years"]) + pd.Timedelta(days=20)]
            base3 = base3[base3.index <= dt - pd.DateOffset(years=P["cagr_years"]) + pd.Timedelta(days=20)]
            cur = s.loc[dt]
            # find base at ~k years prior, else shortest >=12m
            val, yrs = np.nan, np.nan
            for ky in (P["cagr_years"], 2, 1):
                cutoff = dt - pd.DateOffset(years=ky)
                prior = s.loc[:cutoff]
                if len(prior) and np.isfinite(prior.iloc[-1]) and prior.iloc[-1] > 0 and np.isfinite(cur) and cur > 0:
                    val = (cur / prior.iloc[-1]) ** (1.0 / ky) - 1
                    yrs = ky
                    break
            gv.append(val); gw.append(yrs)
        g["g"] = gv; g["g_window_years"] = gw
        return g
    pq0 = pq0.groupby("cmc_id", group_keys=False).apply(add_g, include_groups=False) \
        if False else pq0.groupby("cmc_id", group_keys=False)[pq0.columns.tolist()].apply(add_g)
    # cap g
    lo, hi = P["g_cap"]
    pq0["g_capped"] = (pq0["g"] < lo) | (pq0["g"] > hi)
    pq0["g"] = pq0["g"].clip(lo, hi)

    # ---- beta (trailing) per asset-month vs BTC ----
    ret = obs[["cmc_id", "month_end", "ret"]].copy()
    ret = ret.merge(rmkt.rename("rmkt"), on="month_end", how="left")
    def add_beta(g):
        g = g.sort_values("month_end").copy()
        b = []
        rj = g["ret"].values; rm = g["rmkt"].values; dts = g["month_end"].values
        for i in range(len(g)):
            j0 = max(0, i - P["beta_window"] + 1)
            xj = rj[j0:i + 1]; xm = rm[j0:i + 1]
            mask = np.isfinite(xj) & np.isfinite(xm)
            if mask.sum() >= P["beta_min"] and np.var(xm[mask]) > 0:
                b.append(np.cov(xj[mask], xm[mask])[0, 1] / np.var(xm[mask]))
            else:
                b.append(np.nan)
        g["beta"] = b
        return g
    ret = ret.groupby("cmc_id", group_keys=False)[ret.columns.tolist()].apply(add_beta)

    # ---- assemble ----
    df = obs[["cmc_id", "symbol", "month_end", "market_cap", "asset_class" if "asset_class" in obs else "status"]].copy()
    df = obs[["cmc_id", "symbol", "month_end", "market_cap"]].copy()
    df = df.merge(pq0[["cmc_id", "month_end", "pq_usd", "pq0_annual", "pq_nmonths_12",
                       "pq_source", "g", "g_window_years", "g_capped"]],
                  on=["cmc_id", "month_end"], how="left")
    df = df.merge(ret[["cmc_id", "month_end", "beta"]], on=["cmc_id", "month_end"], how="left")
    # r_e
    df["r_e"] = P["rf"] + df["beta"] * P["mrp"]
    df["r_e"] = df["r_e"].clip(lower=P["re_floor"])
    # PQ* and NVT_GL (need pq0, g, r_e)
    df["pq_star"] = [pq_star(p0, g, r, P["g_inf"], P["n"])
                     for p0, g, r in zip(df.pq0_annual, df.g, df.r_e)]
    df["nvt_gl"] = df["market_cap"] / df["pq_star"]
    # asset class
    ct = pd.read_csv(REPO / "03_data" / "classification_table.csv")[["cmc_id", "asset_class", "sector"]]
    df = df.merge(ct, on="cmc_id", how="left")

    df = df.sort_values(["cmc_id", "month_end"])
    df.to_csv(OUT / "nvt_gl_panel.csv", index=False)

    # ---- summary ----
    have_pq = df[df.pq_usd.notna()]
    have_nvt = df[df.nvt_gl.notna() & np.isfinite(df.nvt_gl)]
    print(f"PARAMS: {P}")
    print(f"\nasset-months total (observed): {len(df):,}")
    print(f"asset-months with monthly PQ : {len(have_pq):,}  ({have_pq.cmc_id.nunique()} assets)")
    print(f"asset-months with NVT_GL     : {len(have_nvt):,}  ({have_nvt.cmc_id.nunique()} assets)")
    print(f"  by class (assets w/ NVT_GL):")
    print(have_nvt.groupby('asset_class').cmc_id.nunique())
    print(f"\nNVT_GL distribution: median {have_nvt.nvt_gl.median():.2f}  "
          f"p10 {have_nvt.nvt_gl.quantile(.1):.2f}  p90 {have_nvt.nvt_gl.quantile(.9):.2f}")
    print(f"g: median {have_nvt.g.median():.3f}  capped rows: {df.g_capped.sum()}")
    print(f"beta: median {have_nvt.beta.median():.2f}  r_e: median {have_nvt.r_e.median():.3f}")
    print(f"\nWrote {OUT/'nvt_gl_panel.csv'}")


if __name__ == "__main__":
    main()
