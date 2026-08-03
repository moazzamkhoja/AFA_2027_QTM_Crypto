"""
phase2_tvl_gl.py  --  Phase 2: assemble Growth-Levelized NV/TVL (NV/TVL_GL = MC / TVL*) per asset-month.

Token-track analog of phase2_nvt_gl.py. TVL is a STOCK (month-end level), not a flow like PQ,
so the base is a trailing-12-month AVERAGE level rather than a trailing sum:

  TVL0    = trailing-12-month mean of month-end TVL   (smoothed current scale; >=6 obs in window)
  g       = trailing 3y CAGR of TVL0                  (2y/1y fallback flagged; capped)
  r_e     = rf + beta_j * MRP                          (same CAPM machinery as NVT_GL; beta vs BTC)
  g_inf   = 0.03, n = 10                               (same robustness parameters)
  TVL* = [ sum_{s=1..n} TVL0(1+g)^s/(1+r_e)^s
           + TVL0(1+g)^n(1+g_inf)/((r_e-g_inf)(1+r_e)^n) ] / annuity_factor(r_e,n)
  NV/TVL_GL = MC / TVL*

All PARAMS identical to phase2_nvt_gl.py so coin and token tracks share one assumption set.
Joins on cmc_id only.

Output: 03_data/phase2/nv_tvl_gl_panel.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase2"

PARAMS = dict(
    rf=0.04,
    mrp=0.30,
    g_inf=0.03,
    n=10,
    g_cap=(-0.50, 2.00),
    re_floor=0.05,
    beta_window=36, beta_min=12,
    cagr_years=3, cagr_min_months=12,
    ret_clip=(-0.90, 3.00),
    tvl0_min_months=6,          # >=6 monthly obs in trailing-12m window for TVL0
)


def annuity_factor(r, n):
    return (1 - (1 + r) ** (-n)) / r


def tvl_star(tvl0, g, r, g_inf, n):
    if not np.isfinite(tvl0) or tvl0 <= 0 or not np.isfinite(g) or not np.isfinite(r):
        return np.nan
    r = max(r, g_inf + 0.02)
    s = np.arange(1, n + 1)
    growth_pv = np.sum(tvl0 * (1 + g) ** s / (1 + r) ** s)
    terminal = tvl0 * (1 + g) ** n * (1 + g_inf) / ((r - g_inf) * (1 + r) ** n)
    return (growth_pv + terminal) / annuity_factor(r, n)


def main():
    P = PARAMS
    panel = pd.read_csv(REPO / "03_data" / "universe_panel.csv")
    panel["month_end"] = pd.to_datetime(panel["month_end"])
    obs = panel[panel.status == "observed"].copy().sort_values(["cmc_id", "month_end"])

    # ---- market factor: BTC monthly simple return (same as phase2_nvt_gl) ----
    btc = obs[obs.cmc_id == 1][["month_end", "price"]].set_index("month_end")["price"].sort_index()
    rmkt = btc.pct_change().clip(*P["ret_clip"]).rename("rmkt")

    obs["ret"] = obs.groupby("cmc_id")["price"].pct_change().clip(*P["ret_clip"])

    # ---- TVL (month-end level) ----
    tvl = pd.read_csv(OUT / "tvl_panel.csv")
    tvl = tvl[tvl.tvl_usd.notna() & (tvl.tvl_usd > 0)].copy()
    tvl["month_end"] = pd.to_datetime(tvl["month_end"])
    tvl = tvl.sort_values(["cmc_id", "month_end"]).set_index("month_end")

    # TVL0 = trailing-12m mean level (>=6 obs)
    def smooth(g):
        s = g["tvl_usd"].sort_index()
        roll = s.rolling("365D").mean()
        cnt = s.rolling("365D").count()
        return pd.DataFrame({"tvl_usd": s, "tvl0_smooth": roll, "tvl_nmonths_12": cnt})
    t0 = tvl.groupby("cmc_id", group_keys=True).apply(smooth, include_groups=False).reset_index()
    t0.loc[t0.tvl_nmonths_12 < P["tvl0_min_months"], "tvl0_smooth"] = np.nan

    # ---- g: trailing 3y CAGR of TVL0 (2y/1y fallback) ----
    def add_g(g):
        g = g.sort_values("month_end").copy()
        s = g.set_index("month_end")["tvl0_smooth"]
        gv, gw = [], []
        for dt in s.index:
            cur = s.loc[dt]
            val, yrs = np.nan, np.nan
            for ky in (P["cagr_years"], 2, 1):
                cutoff = dt - pd.DateOffset(years=ky)
                prior = s.loc[:cutoff]
                if len(prior) and np.isfinite(prior.iloc[-1]) and prior.iloc[-1] > 0 \
                        and np.isfinite(cur) and cur > 0:
                    val = (cur / prior.iloc[-1]) ** (1.0 / ky) - 1
                    yrs = ky
                    break
            gv.append(val); gw.append(yrs)
        g["g"] = gv; g["g_window_years"] = gw
        return g
    t0 = t0.groupby("cmc_id", group_keys=False)[t0.columns.tolist()].apply(add_g)
    lo, hi = P["g_cap"]
    t0["g_capped"] = (t0["g"] < lo) | (t0["g"] > hi)
    t0["g"] = t0["g"].clip(lo, hi)

    # ---- beta (trailing 36m vs BTC), same as phase2_nvt_gl ----
    ret = obs[["cmc_id", "month_end", "ret"]].copy()
    ret = ret.merge(rmkt, on="month_end", how="left")
    def add_beta(g):
        g = g.sort_values("month_end").copy()
        b = []
        rj = g["ret"].values; rm = g["rmkt"].values
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
    df = obs[["cmc_id", "symbol", "month_end", "market_cap"]].copy()
    df = df.merge(t0[["cmc_id", "month_end", "tvl_usd", "tvl0_smooth", "tvl_nmonths_12",
                      "g", "g_window_years", "g_capped"]],
                  on=["cmc_id", "month_end"], how="inner")
    df = df.merge(ret[["cmc_id", "month_end", "beta"]], on=["cmc_id", "month_end"], how="left")
    df["r_e"] = (P["rf"] + df["beta"] * P["mrp"]).clip(lower=P["re_floor"])
    df["tvl_star"] = [tvl_star(t, g, r, P["g_inf"], P["n"])
                      for t, g, r in zip(df.tvl0_smooth, df.g, df.r_e)]
    df["nv_tvl_gl"] = df["market_cap"] / df["tvl_star"]
    # plain ratio retained for comparison
    df["nv_tvl_raw"] = df["market_cap"] / df["tvl_usd"]

    ct = pd.read_csv(REPO / "03_data" / "classification_table.csv")[["cmc_id", "asset_class", "sector"]]
    df = df.merge(ct, on="cmc_id", how="left")

    df = df.sort_values(["cmc_id", "month_end"])
    df.to_csv(OUT / "nv_tvl_gl_panel.csv", index=False)

    # ---- summary ----
    have = df[df.nv_tvl_gl.notna() & np.isfinite(df.nv_tvl_gl)]
    print(f"PARAMS: {P}")
    print(f"\nasset-months with positive TVL joined to MC: {len(df):,}  ({df.cmc_id.nunique()} assets)")
    print(f"asset-months with NV/TVL_GL               : {len(have):,}  ({have.cmc_id.nunique()} assets)")
    print(f"  by class:")
    print(have.groupby('asset_class').cmc_id.nunique())
    print(f"\nNV/TVL_GL: median {have.nv_tvl_gl.median():.3f}  "
          f"p10 {have.nv_tvl_gl.quantile(.1):.3f}  p90 {have.nv_tvl_gl.quantile(.9):.3f}")
    print(f"NV/TVL raw: median {have.nv_tvl_raw.median():.3f}")
    print(f"g: median {have.g.median():.3f}  capped rows: {int(df.g_capped.sum())}")
    print(f"beta: median {have.beta.median():.2f}  r_e: median {have.r_e.median():.3f}")
    print(f"date range: {have.month_end.min().date()} to {have.month_end.max().date()}")
    print(f"\nWrote {OUT/'nv_tvl_gl_panel.csv'}")


if __name__ == "__main__":
    main()
