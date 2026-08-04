"""
phase3_panel.py -- Phase 3 Task A: regression panel (spec PHASE3_ANALYSIS_SPECIFICATION.md sections 1-2).

One row per asset-month in the coin (24/718) and token (101/2,771) regression samples.

Sample membership (verified to reproduce paper Table 1 funnel exactly before build):
  - Coins : universe_coverage_status coverage_status=='complete' & lambda_months>0 &
            asset_class=='coin' (the 24 regression-ready coins, incl. pos_possible + POL),
            month has non-missing lambda_z AND positive NVT_GL.
  - Tokens: asset_class=='token' rows of nv_tvl_gl_panel with finite positive NV/TVL_GL
            AND non-missing lambda_z in the same month.

Variables (spec section 2):
  - Forward returns r_fwd1 (t..t+1) and cumulative r_fwd3 (t+1..t+3), r_fwd6 (t+1..t+6)
    from universe_panel OBSERVED rows only; consecutive calendar month-ends required for
    each monthly link (no carry-forward rows ever enter returns; no backfill).
    Winsorized versions (_w) at monthly cross-sectional 1/99 within the combined panel.
  - Conviction: coins conv = ln(l/(1-l)), l = raw_ch1_staking clipped [0.001,0.999],
    lambda_z fallback flagged in conv_source; tokens conv = lambda_z.
    conv_lz = lambda_z for all rows (coin robustness). conv_vw = equal-weight mean of
    ch3 sub-channel z-scores (voting, delegation; z over all asset-months per channel,
    same construction as the composite) -- spec section 3 item 7.
  - Valuation: val = ln(NVT_GL) [coins] / ln(NV_TVL_GL) [tokens], winsorized 1/99
    pooled within track before standardization.
  - Controls: size = ln(MC); r_1m = return of month t; mom_3m = P_{t-1}/P_{t-4}-1;
    mom_12_2 = P_{t-2}/P_{t-13}-1 (skip most recent months); beta36 reused from the
    phase2 panels.
  - _std columns: standardized to zero mean / unit SD within class-month (track x month).

Output: 03_data/phase3/regression_panel.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
OUT.mkdir(exist_ok=True)

CH1_CLIP = (0.001, 0.999)
WINSOR = (0.01, 0.99)


def winsorize(s, lo=0.01, hi=0.99):
    if s.notna().sum() < 3:
        return s
    return s.clip(s.quantile(lo), s.quantile(hi))


def main():
    # ---------- inputs ----------
    lam = pd.read_csv(REPO / "03_data" / "phase1" / "lambda_panel.csv")
    nvt = pd.read_csv(REPO / "03_data" / "phase2" / "nvt_gl_panel.csv")
    tvl = pd.read_csv(REPO / "03_data" / "phase2" / "nv_tvl_gl_panel.csv")
    cov = pd.read_csv(REPO / "03_data" / "universe_coverage_status.csv")
    ct = pd.read_csv(REPO / "03_data" / "classification_table.csv")[["cmc_id", "sector"]]
    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv")
    for df in (lam, nvt, tvl, uni):
        df["month_end"] = pd.to_datetime(df["month_end"])

    obs = uni[uni.status == "observed"].copy()
    obs = obs[obs.price.notna() & (obs.price > 0)].sort_values(["cmc_id", "month_end"])

    # ---------- return machinery (observed rows only, consecutive month-ends) ----------
    px = obs.pivot_table(index="month_end", columns="cmc_id", values="price")
    px = px.resample("ME").last()          # calendar month-end grid; non-observed = NaN
    r = px.pct_change(fill_method=None)    # r_t = month-t return; NaN unless both ends observed

    r_fwd1 = r.shift(-1)
    r_fwd3 = (1 + r).shift(-1).rolling(3).apply(np.prod, raw=True).shift(-2) - 1
    r_fwd6 = (1 + r).shift(-1).rolling(6).apply(np.prod, raw=True).shift(-5) - 1
    r_1m = r
    mom_3m = px.shift(1) / px.shift(4) - 1
    mom_12_2 = px.shift(2) / px.shift(13) - 1

    def melt(w, name):
        m = w.stack().rename(name).reset_index()
        m.columns = ["month_end", "cmc_id", name]
        return m

    rets = melt(r_fwd1, "r_fwd1")
    for w, name in ((r_fwd3, "r_fwd3"), (r_fwd6, "r_fwd6"), (r_1m, "r_1m"),
                    (mom_3m, "mom_3m"), (mom_12_2, "mom_12_2")):
        rets = rets.merge(melt(w, name), on=["month_end", "cmc_id"], how="outer")

    # ---------- ch3 sub-channel z-scores (same construction as composite lambda_z) ----------
    for ch in ("raw_ch3_voting", "raw_ch3_delegation"):
        v = lam[ch]
        lam[ch + "_z"] = (v - v.mean()) / v.std()
    lam["conv_vw"] = lam[["raw_ch3_voting_z", "raw_ch3_delegation_z"]].mean(axis=1)

    lam_keep = lam[["cmc_id", "month_end", "lambda_z", "raw_ch1_staking", "conv_vw"]]

    # ---------- coin sample ----------
    coin_ids = set(cov[(cov.asset_class == "coin") & (cov.coverage_status == "complete")
                       & (cov.lambda_months > 0)].cmc_id)
    nvt_ok = nvt[nvt.cmc_id.isin(coin_ids) & nvt.nvt_gl.notna() & (nvt.nvt_gl > 0)]
    coins = nvt_ok[["cmc_id", "symbol", "month_end", "market_cap", "nvt_gl", "beta"]].merge(
        lam_keep, on=["cmc_id", "month_end"], how="inner")
    coins = coins[coins.lambda_z.notna()].copy()
    coins["track"] = "coin"
    coins["val_raw"] = coins["nvt_gl"]

    l_clip = coins["raw_ch1_staking"].clip(*CH1_CLIP)
    coins["conv"] = np.where(coins.raw_ch1_staking.notna(),
                             np.log(l_clip / (1 - l_clip)), coins["lambda_z"])
    coins["conv_source"] = np.where(coins.raw_ch1_staking.notna(), "ch1_lnodds", "lambda_z")

    # ---------- token sample ----------
    tvl_ok = tvl[(tvl.asset_class == "token") & tvl.nv_tvl_gl.notna()
                 & np.isfinite(tvl.nv_tvl_gl) & (tvl.nv_tvl_gl > 0)]
    toks = tvl_ok[["cmc_id", "symbol", "month_end", "market_cap", "nv_tvl_gl",
                   "nv_tvl_raw", "beta"]].merge(lam_keep, on=["cmc_id", "month_end"], how="inner")
    toks = toks[toks.lambda_z.notna()].copy()
    toks["track"] = "token"
    toks["val_raw"] = toks["nv_tvl_gl"]
    toks["conv"] = toks["lambda_z"]
    toks["conv_source"] = "lambda_z"

    # ---------- funnel gate (paper Table 1) ----------
    nc, mc = coins.cmc_id.nunique(), len(coins)
    nt, mt = toks.cmc_id.nunique(), len(toks)
    assert (nc, mc) == (24, 718), f"coin funnel mismatch: {nc}/{mc} != 24/718"
    assert (nt, mt) == (101, 2771), f"token funnel mismatch: {nt}/{mt} != 101/2771"
    print(f"FUNNEL OK: coins {nc}/{mc}, tokens {nt}/{mt}")

    # ---------- assemble ----------
    panel = pd.concat([coins, toks], ignore_index=True, sort=False)
    panel = panel.rename(columns={"lambda_z": "conv_lz", "beta": "beta36"})
    panel = panel.merge(ct, on="cmc_id", how="left")
    panel = panel.merge(rets, on=["cmc_id", "month_end"], how="left")
    panel["size"] = np.log(panel["market_cap"])

    # valuation: ln ratio winsorized 1/99 pooled within track
    panel["val"] = np.log(panel["val_raw"])
    panel["val"] = panel.groupby("track")["val"].transform(winsorize)

    # forward returns winsorized at monthly cross-section (combined panel)
    for c in ("r_fwd1", "r_fwd3", "r_fwd6"):
        panel[c + "_w"] = panel.groupby("month_end")[c].transform(winsorize)

    # class-month standardization
    def zs(s):
        sd = s.std()
        return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * np.nan
    for c in ("conv", "conv_lz", "conv_vw", "val", "size", "r_1m",
              "mom_3m", "mom_12_2", "beta36"):
        panel[c + "_std"] = panel.groupby(["track", "month_end"])[c].transform(zs)

    cols = ["cmc_id", "symbol", "track", "month_end", "sector", "market_cap",
            "r_fwd1", "r_fwd3", "r_fwd6", "r_fwd1_w", "r_fwd3_w", "r_fwd6_w",
            "conv", "conv_source", "conv_lz", "conv_vw", "val_raw", "val",
            "size", "r_1m", "mom_3m", "mom_12_2", "beta36",
            "conv_std", "conv_lz_std", "conv_vw_std", "val_std", "size_std",
            "r_1m_std", "mom_3m_std", "mom_12_2_std", "beta36_std"]
    panel = panel[cols].sort_values(["track", "cmc_id", "month_end"])
    panel.to_csv(OUT / "regression_panel.csv", index=False)

    # ---------- summary ----------
    print(f"\nwrote {OUT/'regression_panel.csv'}: {len(panel):,} rows")
    for tr, g in panel.groupby("track"):
        print(f"\n[{tr}] {g.cmc_id.nunique()} assets, {len(g)} months, "
              f"{g.month_end.min().date()}..{g.month_end.max().date()}")
        print(f"  r_fwd1 non-missing: {g.r_fwd1.notna().sum()} "
              f"({g.r_fwd1.notna().mean():.1%}); median {g.r_fwd1.median():+.4f}")
        print(f"  conv_source: {g.conv_source.value_counts().to_dict()}")
        print(f"  conv_vw non-missing: {g.conv_vw.notna().sum()}")
        print(f"  beta36 non-missing: {g.beta36.notna().sum()}  "
              f"mom_12_2 non-missing: {g.mom_12_2.notna().sum()}")
        print(f"  median MC: ${g.market_cap.median()/1e6:,.0f}M  "
              f"median val_raw: {g.val_raw.median():.3f}")


if __name__ == "__main__":
    main()
