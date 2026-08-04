"""
phase3b_signals.py -- Phase 3b Task C prerequisite (spec sections 5.1/8.3): horse-race
comparator signals for every asset-month in the Phase 3 regression panel.

Signals (all free derivations; Entry 100 operationalizations):
  raw_val   : coins ln(raw NVT) = ln(MC / PQ0_annual)  [nvt_gl_panel];
              tokens ln(raw NV/TVL) = ln(nv_tvl_raw)   [nv_tvl_gl_panel].
              Winsorized 1/99 pooled within track (mirrors the GL val treatment).
  s2f_ln    : ln(circulating_supply / trailing-12m Delta supply), defined only where the
              12m flow is positive (deflationary/no-emission months = NaN; coverage
              reported). Literal spec 5.1 definition.
  supply_g12: (S_t - S_{t-12}) / S_{t-12} -- monotone inverse transform of S2F defined
              for ALL months (incl. deflationary); used in the joint race for coverage.
  high52    : price_t / max(price over months t-11..t), observed monthly prices,
              >= 6 obs required in the window (George-Hwang nearness to 52-wk high).
  ma_cross  : 1[MA3 > MA10] on monthly closes, full windows required.
  Momentum family (r_1m, mom_3m, mom_12_2) already lives in regression_panel.csv.

_std columns: standardized within class-month (track x month), same as the panel.

Output: 03_data/phase3/horserace_signals.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"


def winsorize(s, lo=0.01, hi=0.99):
    if s.notna().sum() < 3:
        return s
    return s.clip(s.quantile(lo), s.quantile(hi))


def main():
    p = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    keys = p[["cmc_id", "track", "month_end"]].copy()
    ids = set(p.cmc_id)

    # ---------- raw valuation ratios ----------
    nvt = pd.read_csv(REPO / "03_data" / "phase2" / "nvt_gl_panel.csv",
                      parse_dates=["month_end"])
    nvt = nvt[nvt.cmc_id.isin(ids)]
    nvt["raw_nvt"] = np.where(nvt.pq0_annual > 0, nvt.market_cap / nvt.pq0_annual, np.nan)
    tvl = pd.read_csv(REPO / "03_data" / "phase2" / "nv_tvl_gl_panel.csv",
                      parse_dates=["month_end"])
    tvl = tvl[tvl.cmc_id.isin(ids)]

    keys = keys.merge(nvt[["cmc_id", "month_end", "raw_nvt"]], on=["cmc_id", "month_end"], how="left")
    keys = keys.merge(tvl[["cmc_id", "month_end", "nv_tvl_raw"]], on=["cmc_id", "month_end"], how="left")
    keys["raw_val"] = np.where(keys.track == "coin",
                               np.log(keys.raw_nvt.where(keys.raw_nvt > 0)),
                               np.log(keys.nv_tvl_raw.where(keys.nv_tvl_raw > 0)))
    keys["raw_val"] = keys.groupby("track")["raw_val"].transform(winsorize)

    # ---------- price/supply machinery from universe_panel (observed rows only) ----------
    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv", parse_dates=["month_end"])
    obs = uni[(uni.status == "observed") & uni.price.notna() & (uni.price > 0)
              & uni.cmc_id.isin(ids)].copy()
    px = (obs.pivot_table(index="month_end", columns="cmc_id", values="price")
          .resample("ME").last())
    sup = (obs.pivot_table(index="month_end", columns="cmc_id", values="circulating_supply")
           .resample("ME").last())

    high52 = px / px.rolling(12, min_periods=6).max()
    ma3 = px.rolling(3, min_periods=3).mean()
    ma10 = px.rolling(10, min_periods=10).mean()
    ma_cross = (ma3 > ma10).astype(float).where(ma3.notna() & ma10.notna())

    flow12 = sup - sup.shift(12)
    s2f = (sup / flow12).where(flow12 > 0)
    s2f_ln = np.log(s2f)
    supply_g12 = flow12 / sup.shift(12)

    def melt(w, name):
        m = w.stack().rename(name).reset_index()
        m.columns = ["month_end", "cmc_id", name]
        return m

    for w, name in ((high52, "high52"), (ma_cross, "ma_cross"),
                    (s2f_ln, "s2f_ln"), (supply_g12, "supply_g12")):
        keys = keys.merge(melt(w, name), on=["month_end", "cmc_id"], how="left")

    # ---------- class-month standardization ----------
    def zs(s):
        sd = s.std()
        return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * np.nan
    for c in ("raw_val", "high52", "ma_cross", "s2f_ln", "supply_g12"):
        keys[c + "_std"] = keys.groupby(["track", "month_end"])[c].transform(zs)

    out_cols = ["cmc_id", "track", "month_end", "raw_val", "high52", "ma_cross",
                "s2f_ln", "supply_g12"] + \
               [c + "_std" for c in ("raw_val", "high52", "ma_cross", "s2f_ln", "supply_g12")]
    keys[out_cols].to_csv(OUT / "horserace_signals.csv", index=False)

    print(f"wrote {OUT/'horserace_signals.csv'}: {len(keys):,} rows")
    for tr, g in keys.groupby("track"):
        print(f"\n[{tr}] coverage of {len(g)} asset-months:")
        for c in ("raw_val", "high52", "ma_cross", "s2f_ln", "supply_g12"):
            print(f"  {c:11s} {g[c].notna().sum():5d} ({g[c].notna().mean():.1%})")


if __name__ == "__main__":
    main()
