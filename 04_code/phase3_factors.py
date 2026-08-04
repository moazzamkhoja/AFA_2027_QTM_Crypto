"""
phase3_factors.py -- Phase 3 Task B: monthly LTW factor analogs (spec section 4.1).

Monthly analogs of Liu-Tsyvinski-Wu (2022 JF) crypto factors, built from our own
1,939-asset universe (LTW original is weekly -- documented deviation, Entry 94):

  Eligible universe at formation month t: universe_panel observed rows, price > 0,
  MC >= $1M, with an observed return over t+1 (consecutive calendar month-ends).
  Constituent monthly returns winsorized at (-90%, +300%) before aggregating
  (same penny-token guard as the beta build).

  CMKT_{t+1} = VW return of eligible universe - rf_m        (rf_m = 4%/12, as in r_e build)
  CSMB_{t+1} = VW return of bottom size quintile - top size quintile (MC_t breakpoints)
  CMOM_{t+1} = VW return of top mom_3m quintile - bottom (mom_3m = P_{t-1}/P_{t-4}-1,
               the section 2.3 definition, for internal consistency with the panel)

Factor rows are indexed by the RETURN month (t+1). Output:
03_data/phase3/ltw_factors_monthly.csv with columns month_end, cmkt, csmb, cmom,
rf_m, mkt_vw (gross), n_eligible, n_mom.
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
OUT.mkdir(exist_ok=True)

MC_MIN = 1e6
RET_CLIP = (-0.90, 3.00)
RF_M = 0.04 / 12


def vw(g, rcol="ret_fwd", wcol="mc"):
    w = g[wcol]
    return np.average(g[rcol], weights=w) if len(g) and w.sum() > 0 else np.nan


def main():
    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv")
    uni["month_end"] = pd.to_datetime(uni["month_end"])
    obs = uni[(uni.status == "observed") & uni.price.notna() & (uni.price > 0)]

    px = obs.pivot_table(index="month_end", columns="cmc_id", values="price").resample("ME").last()
    mc = obs.pivot_table(index="month_end", columns="cmc_id", values="market_cap").resample("ME").last()
    r = px.pct_change(fill_method=None)
    ret_fwd = r.shift(-1).clip(*RET_CLIP)          # return over t+1, winsorized
    mom3 = px.shift(1) / px.shift(4) - 1           # section 2.3 mom_3m at formation t

    rows = []
    for t in px.index[:-1]:
        m = pd.DataFrame({"mc": mc.loc[t], "ret_fwd": ret_fwd.loc[t], "mom3": mom3.loc[t]})
        m = m[m.mc.notna() & (m.mc >= MC_MIN) & m.ret_fwd.notna()]
        if len(m) < 20:
            continue
        t1 = px.index[px.index.get_loc(t) + 1]
        mkt = vw(m)
        q = pd.qcut(m.mc.rank(method="first"), 5, labels=False)
        smb = vw(m[q == 0]) - vw(m[q == 4])
        mm = m[m.mom3.notna()]
        if len(mm) >= 20:
            qm = pd.qcut(mm.mom3.rank(method="first"), 5, labels=False)
            cmom = vw(mm[qm == 4]) - vw(mm[qm == 0])
        else:
            cmom = np.nan
        rows.append(dict(month_end=t1, cmkt=mkt - RF_M, csmb=smb, cmom=cmom,
                         rf_m=RF_M, mkt_vw=mkt, n_eligible=len(m), n_mom=len(mm)))

    f = pd.DataFrame(rows).set_index("month_end").sort_index()
    f.to_csv(OUT / "ltw_factors_monthly.csv")

    # ---------- summary ----------
    btc = obs[obs.cmc_id == 1].set_index("month_end")["price"].sort_index()
    btc_r = btc.pct_change().rename("btc")
    j = f.join(btc_r, how="left")
    print(f"wrote {OUT/'ltw_factors_monthly.csv'}: {len(f)} months, "
          f"{f.index.min().date()}..{f.index.max().date()}")
    print(f"n_eligible: median {f.n_eligible.median():.0f}, "
          f"min {f.n_eligible.min()}, max {f.n_eligible.max()}")
    print("\nfactor summary (monthly):")
    for c in ("cmkt", "csmb", "cmom"):
        s = f[c].dropna()
        tstat = s.mean() / s.std() * np.sqrt(len(s))
        print(f"  {c.upper():5s} mean {s.mean():+.4f}  sd {s.std():.4f}  "
              f"t {tstat:+.2f}  min {s.min():+.3f}  max {s.max():+.3f}  n {len(s)}")
    print("\ncorrelations:")
    print(j[["cmkt", "csmb", "cmom", "btc"]].corr().round(3).to_string())


if __name__ == "__main__":
    main()
