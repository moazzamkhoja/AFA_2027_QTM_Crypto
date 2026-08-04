"""
phase3c_comparators.py -- Phase 3c Task B (spec 8.7 as amended: TOKENS ONLY):
the two fee-anchored valuation comparators.

  pf      = MC / f12        practitioner price-to-fees multiple
  pf_gl   = MC / F*         growth-levelized fees variant (flagged, secondary)
  prev_gl = MC / REV*       revenue DCF ratio -- PRIMARY (discount what holders
                            could claim, not what users pay)

f12 / rev12 = trailing-365D sum of monthly DeFiLlama fees / revenue, >= 6 monthly
obs required (PQ0 house convention, phase2_nvt_gl.py). F* / REV* apply the EXACT
PQ* machinery and PARAMS of phase2_nvt_gl.py (rf 4%, MRP 30%, g_inf 3%, n 10,
g cap [-50%, +200%] flagged, beta36 from the regression panel, r_e floor 5%) to
the f12 / rev12 base, with g = trailing 3y CAGR of the base (2y/1y fallback,
window recorded) -- same add_g logic as phase2.

Transforms mirror the val treatment (phase3_panel.py): ln, winsorized 1/99 pooled
within track (all-token), then standardized within token-month (>= 2 names).

Output: 03_data/phase3/fee_comparators.csv -- one row per token regression-panel
asset-month (2,771), columns NaN where uncovered. Coverage printed and saved to
tables/fee_comparators_coverage.csv.
"""
import numpy as np
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase2_nvt_gl import PARAMS, pq_star  # exact machinery reuse

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

MIN_OBS_12 = 6


def winsorize(s, lo=0.01, hi=0.99):
    if s.notna().sum() < 3:
        return s
    return s.clip(s.quantile(lo), s.quantile(hi))


def trailing12(df, col):
    """cmc_id x month_end monthly series -> trailing-365D sum + obs count."""
    out = []
    for cid, g in df.dropna(subset=[col]).groupby("cmc_id"):
        s = g.set_index("month_end")[col].sort_index()
        roll = s.rolling("365D").sum()
        cnt = s.rolling("365D").count()
        out.append(pd.DataFrame({"cmc_id": cid, "month_end": s.index,
                                 f"{col}12": roll.values, f"n12_{col}": cnt.values}))
    return pd.concat(out, ignore_index=True)


def add_g(base, col):
    """Trailing 3y CAGR (2y/1y fallback) of an annualized base series -- phase2 add_g logic."""
    P = PARAMS
    lo, hi = P["g_cap"]
    out = []
    for cid, g in base.groupby("cmc_id"):
        g = g.sort_values("month_end").copy()
        s = g.set_index("month_end")[col]
        gv, gw = [], []
        for dt in s.index:
            cur = s.loc[dt]
            val, yrs = np.nan, np.nan
            for ky in (P["cagr_years"], 2, 1):
                prior = s.loc[:dt - pd.DateOffset(years=ky)]
                if len(prior) and np.isfinite(prior.iloc[-1]) and prior.iloc[-1] > 0 \
                        and np.isfinite(cur) and cur > 0:
                    val = (cur / prior.iloc[-1]) ** (1.0 / ky) - 1
                    yrs = ky
                    break
            gv.append(val); gw.append(yrs)
        g["g"] = gv
        g["g_window_years"] = gw
        out.append(g)
    res = pd.concat(out, ignore_index=True)
    res["g_capped"] = (res["g"] < lo) | (res["g"] > hi)
    res["g"] = res["g"].clip(lo, hi)
    return res


def main():
    P = PARAMS
    fees = pd.read_csv(OUT / "fees_revenue_panel.csv", parse_dates=["month_end"])
    rp = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    tok = rp[rp.track == "token"][["cmc_id", "symbol", "month_end", "market_cap",
                                   "beta36"]].copy()

    # ---- trailing-12m bases (full fee history, then merged into panel rows) ----
    f12 = trailing12(fees, "fees_usd")
    r12 = trailing12(fees, "revenue_usd")
    f12 = f12.rename(columns={"fees_usd12": "f12", "n12_fees_usd": "n12_f"})
    r12 = r12.rename(columns={"revenue_usd12": "rev12", "n12_revenue_usd": "n12_r"})
    f12.loc[f12.n12_f < MIN_OBS_12, "f12"] = np.nan
    r12.loc[r12.n12_r < MIN_OBS_12, "rev12"] = np.nan

    # ---- g per base ----
    gf = add_g(f12[["cmc_id", "month_end", "f12"]], "f12")
    gr = add_g(r12[["cmc_id", "month_end", "rev12"]], "rev12")

    # ---- assemble on the token regression panel ----
    d = tok.merge(gf.rename(columns={"g": "g_f", "g_window_years": "gw_f",
                                     "g_capped": "g_capped_f"}),
                  on=["cmc_id", "month_end"], how="left")
    d = d.merge(gr.rename(columns={"g": "g_r", "g_window_years": "gw_r",
                                   "g_capped": "g_capped_r"}),
                on=["cmc_id", "month_end"], how="left")
    d = d.merge(f12[["cmc_id", "month_end", "n12_f"]], on=["cmc_id", "month_end"], how="left")
    d = d.merge(r12[["cmc_id", "month_end", "n12_r"]], on=["cmc_id", "month_end"], how="left")

    d["r_e"] = (P["rf"] + d["beta36"] * P["mrp"]).clip(lower=P["re_floor"])
    d["f_star"] = [pq_star(b, g, r, P["g_inf"], P["n"])
                   for b, g, r in zip(d.f12, d.g_f, d.r_e)]
    d["rev_star"] = [pq_star(b, g, r, P["g_inf"], P["n"])
                     for b, g, r in zip(d.rev12, d.g_r, d.r_e)]

    d["pf"] = np.where(d.f12 > 0, d.market_cap / d.f12, np.nan)
    d["pf_gl"] = np.where(d.f_star > 0, d.market_cap / d.f_star, np.nan)
    d["prev_gl"] = np.where(d.rev_star > 0, d.market_cap / d.rev_star, np.nan)

    # ---- ln, winsorize 1/99 pooled (single track), standardize within month ----
    def zs(s):
        sd = s.std()
        return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * np.nan
    for c in ("pf", "pf_gl", "prev_gl"):
        d[c + "_ln"] = winsorize(np.log(d[c].where(d[c] > 0)))
        d[c + "_ln_std"] = d.groupby("month_end")[c + "_ln"].transform(zs)

    cols = ["cmc_id", "symbol", "month_end", "f12", "n12_f", "rev12", "n12_r",
            "g_f", "gw_f", "g_capped_f", "g_r", "gw_r", "g_capped_r", "r_e",
            "f_star", "rev_star", "pf", "pf_gl", "prev_gl",
            "pf_ln", "pf_gl_ln", "prev_gl_ln",
            "pf_ln_std", "pf_gl_ln_std", "prev_gl_ln_std"]
    d[cols].to_csv(OUT / "fee_comparators.csv", index=False)

    # ---- coverage ----
    print(f"token regression asset-months: {len(d):,}")
    for c in ("pf", "pf_gl", "prev_gl"):
        n = d[c].notna().sum()
        print(f"  {c:8s} covered: {n:5d} ({n/len(d):.1%})  tokens: {d[d[c].notna()].cmc_id.nunique()}")
    only_f = d[d.pf_gl.notna() & d.prev_gl.isna()]
    print(f"  pf_gl-only (fees reported, revenue not): {len(only_f)} rows, "
          f"{only_f.cmc_id.nunique()} tokens  <- flagged variant")
    both = d[d.pf.notna()]
    print(f"  pf-covered months span: {both.month_end.min().date()}..{both.month_end.max().date()}")
    print(f"  g capped (fees base): {d.g_capped_f.sum()}  (rev base): {d.g_capped_r.sum()}")
    print(f"  median pf: {d.pf.median():.1f}   median prev_gl: {d.prev_gl.median():.1f}")
    cov = d.groupby("month_end").agg(n_pf=("pf", "count"), n_prev=("prev_gl", "count"),
                                     n_tot=("cmc_id", "size")).reset_index()
    cov.to_csv(TAB / "fee_comparators_coverage.csv", index=False)
    print(f"\nwrote {OUT/'fee_comparators.csv'} and {TAB/'fee_comparators_coverage.csv'}")


if __name__ == "__main__":
    main()
