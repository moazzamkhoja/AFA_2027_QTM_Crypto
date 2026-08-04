"""
phase3c_technicals.py -- Phase 3c Task D signals (spec 8.8): five additions to the
horse-race comparator set, all derived from universe_panel (no new data).

  ma_dist : price / MA10 - 1 (monthly closes, full 10m window) -- continuous
            MA-distance; SUPERSEDES the binary MA-cross in spanning (the binary
            long-shorts had only 28-31 overlapping months in session 044).
  vol12   : trailing 12m monthly-return SD, >= 8 obs.
  ivol    : residual SD from trailing 36m OLS of asset return on CMKT
            (ltw_factors_monthly), >= 12 joint obs.
  amihud  : ln of trailing 12m mean of |r_month| / volume_24h(month-end), >= 6 obs.
            CAVEAT (logged): volume_24h is a MONTH-END SNAPSHOT, not a monthly
            aggregate -- a noisy illiquidity proxy.
  skew36  : trailing 36m monthly-return skewness, >= 18 obs.

Returns: observed-row month-end grid, consecutive-month pct_change, clipped at
(-0.90, +3.00) before moments -- the phase2 beta-build convention (penny guard).

_std columns standardized within class-month (track x month), same as the panel.
Output: 03_data/phase3/technical_signals.csv (regression-panel keys, both tracks).
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"

RET_CLIP = (-0.90, 3.00)
IVOL_WIN, IVOL_MIN = 36, 12


def main():
    p = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    keys = p[["cmc_id", "track", "month_end"]].copy()
    ids = set(p.cmc_id)

    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv", parse_dates=["month_end"])
    obs = uni[(uni.status == "observed") & uni.price.notna() & (uni.price > 0)
              & uni.cmc_id.isin(ids)].copy()
    px = (obs.pivot_table(index="month_end", columns="cmc_id", values="price")
          .resample("ME").last())
    vol24 = (obs.pivot_table(index="month_end", columns="cmc_id", values="volume_24h")
             .resample("ME").last())
    r = px.pct_change(fill_method=None).clip(*RET_CLIP)

    # ---- ma_dist, vol12, skew36 ----
    ma10 = px.rolling(10, min_periods=10).mean()
    ma_dist = px / ma10 - 1
    vol12 = r.rolling(12, min_periods=8).std()
    skew36 = r.rolling(36, min_periods=18).skew()

    # ---- amihud (snapshot-volume caveat) ----
    illiq = (r.abs() / vol24.where(vol24 > 0))
    amihud = np.log(illiq.rolling(12, min_periods=6).mean())

    # ---- ivol vs CMKT ----
    fac = pd.read_csv(OUT / "ltw_factors_monthly.csv", parse_dates=["month_end"])
    cmkt = fac.set_index("month_end")["cmkt"].reindex(r.index)
    ivol = pd.DataFrame(np.nan, index=r.index, columns=r.columns)
    rm = cmkt.values
    for cid in r.columns:
        rj = r[cid].values
        for i in range(len(r.index)):
            j0 = max(0, i - IVOL_WIN + 1)
            xj, xm = rj[j0:i + 1], rm[j0:i + 1]
            mask = np.isfinite(xj) & np.isfinite(xm)
            if mask.sum() >= IVOL_MIN and np.var(xm[mask]) > 0:
                b = np.cov(xj[mask], xm[mask])[0, 1] / np.var(xm[mask])
                resid = xj[mask] - (xj[mask].mean() + b * (xm[mask] - xm[mask].mean()))
                ivol.iloc[i, ivol.columns.get_loc(cid)] = resid.std(ddof=1)
    ivol = ivol.astype(float)

    def melt(w, name):
        m = w.stack().rename(name).reset_index()
        m.columns = ["month_end", "cmc_id", name]
        return m

    for w, name in ((ma_dist, "ma_dist"), (vol12, "vol12"), (ivol, "ivol"),
                    (amihud, "amihud"), (skew36, "skew36")):
        keys = keys.merge(melt(w, name), on=["month_end", "cmc_id"], how="left")

    def zs(s):
        sd = s.std()
        return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * np.nan
    SIGS = ["ma_dist", "vol12", "ivol", "amihud", "skew36"]
    for c in SIGS:
        keys[c + "_std"] = keys.groupby(["track", "month_end"])[c].transform(zs)

    keys.to_csv(OUT / "technical_signals.csv", index=False)
    print(f"wrote {OUT/'technical_signals.csv'}: {len(keys):,} rows")
    for tr, g in keys.groupby("track"):
        print(f"\n[{tr}] coverage of {len(g)} asset-months:")
        for c in SIGS:
            print(f"  {c:8s} {g[c].notna().sum():5d} ({g[c].notna().mean():.1%})")


if __name__ == "__main__":
    main()
