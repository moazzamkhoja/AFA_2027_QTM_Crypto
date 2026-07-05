"""build_coverage_status.py -- regenerate 03_data/universe_coverage_status.csv from the
live panels (session 029, Entry 79; the previous file was generated inline pre-027 and
had gone stale). Re-runnable after any assemble.

Sources (all cmc_id joins):
  asset_onchain_identity.csv          identity (symbol/name/class/sector)
  universe_coverage_status.csv (OLD)  coin_staking_type CARRY-FORWARD ONLY (static
                                      chain metadata first classified in session 022;
                                      no live source carries this column)
  phase1/lambda_panel.csv             lambda months / channels
  phase2/nvt_gl_panel.csv             NVT_GL months + pq_source
  phase2/tvl_panel.csv                TVL months
  phase1/_channel2_sizes.csv          holder_count / est_getlogs_calls
  phase1/universe_lambda_channel_map.csv  evm chain + etherscan reachability

coverage_status: complete = lambda AND a valuation denominator (NVT_GL for coins,
TVL-or-NVT for tokens/other); partial = any coverage; not_started = none.
what_needed mirrors the pre-027 vocabulary (ch1_staking[type] | ch2_holding(Nh) |
ch3_governance | pq_nvtgl | tvl_defillama).
"""

import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = REPO / "03_data"
OUT = D / "universe_coverage_status.csv"


def main():
    ident = pd.read_csv(D / "phase1" / "asset_onchain_identity.csv")[
        ["cmc_id", "symbol", "name", "asset_class", "sector"]].drop_duplicates("cmc_id")
    old = pd.read_csv(OUT)[["cmc_id", "coin_staking_type"]].drop_duplicates("cmc_id")

    lam = pd.read_csv(D / "phase1" / "lambda_panel.csv")
    g = lam.groupby("cmc_id")
    lamagg = pd.DataFrame({
        "lambda_months": g.size(),
        "lambda_n_channels": g.n_channels.max(),
    })
    ch = lam.dropna(subset=["channels"]).groupby("cmc_id").channels.apply(
        lambda s: "|".join(sorted(set(c for row in s for c in str(row).split("|")))))
    lamagg["lambda_channels"] = ch
    for col, tag in [("has_ch1", "ch1_staking"), ("has_ch2", "ch2_holding"),
                     ("has_ch3_v", "ch3_voting"), ("has_ch3_d", "ch3_delegation")]:
        lamagg[col] = lamagg.lambda_channels.fillna("").str.contains(tag)

    nvt = pd.read_csv(D / "phase2" / "nvt_gl_panel.csv")
    nn = nvt[nvt.nvt_gl.notna()].groupby("cmc_id")
    nvtagg = pd.DataFrame({"nvt_months": nn.size()})
    nvtagg["pq_source"] = nn.pq_source.agg(
        lambda s: s.dropna().iloc[0] if s.notna().any() else None)

    tvl = pd.read_csv(D / "phase2" / "tvl_panel.csv")
    tvlagg = tvl[tvl.tvl_usd.notna()].groupby("cmc_id").size().rename("tvl_months")

    sizes = pd.read_csv(D / "phase1" / "_channel2_sizes.csv")[
        ["cmc_id", "holder_count", "est_getlogs_calls"]].drop_duplicates("cmc_id")

    cmap = pd.read_csv(D / "phase1" / "universe_lambda_channel_map.csv")[
        ["cmc_id", "chain", "etherscan_reachable"]].drop_duplicates("cmc_id").rename(
        columns={"chain": "evm_chain"})

    df = (ident.merge(old, on="cmc_id", how="left")
               .merge(lamagg, on="cmc_id", how="left")
               .merge(nvtagg, on="cmc_id", how="left")
               .merge(tvlagg, on="cmc_id", how="left")
               .merge(sizes, on="cmc_id", how="left")
               .merge(cmap, on="cmc_id", how="left"))
    df["lambda_months"] = df.lambda_months.fillna(0).astype(int)
    df["lambda_n_channels"] = df.lambda_n_channels.fillna(0).astype(int)
    df["nvt_months"] = df.nvt_months.fillna(0).astype(int)
    df["tvl_months"] = df.tvl_months.fillna(0).astype(int)
    for c in ["has_ch1", "has_ch2", "has_ch3_v", "has_ch3_d"]:
        df[c] = df[c].fillna(False)
    df["has_nvt_gl"] = df.nvt_months > 0
    df["has_tvl"] = df.tvl_months > 0

    # SAME-MONTH overlap (the regression-ready notion), not mere presence of both
    # panels -- matches the pre-027 file's semantics (BTC-class pow_only coins are
    # complete on NVT alone; pos coins need lambda∩NVT; tokens/other need lambda∩TVL).
    lc = lam[["cmc_id", "month_end"]]
    ov_nvt = set(lc.merge(nvt[nvt.nvt_gl.notna()][["cmc_id", "month_end"]],
                          on=["cmc_id", "month_end"]).cmc_id)
    ov_tvl = set(lc.merge(tvl[tvl.tvl_usd.notna()][["cmc_id", "month_end"]],
                          on=["cmc_id", "month_end"]).cmc_id)

    def status(r):
        if r.asset_class == "coin":
            if r.coin_staking_type == "pow_only":
                return "complete" if r.has_nvt_gl else (
                    "partial" if r.lambda_months > 0 else "not_started")
            if r.cmc_id in ov_nvt:
                return "complete"
        else:
            if r.cmc_id in ov_tvl:
                return "complete"
        if r.lambda_months > 0 or r.has_nvt_gl or r.has_tvl:
            return "partial"
        return "not_started"

    def needed(r):
        if status(r) == "complete":
            return "COMPLETE"
        parts = []
        if r.lambda_months == 0:
            if r.asset_class == "coin":
                t = r.coin_staking_type
                parts.append("ch1_staking" if t in (None, "pos") or pd.isna(t)
                             else f"ch1_staking[{t}]")
            else:
                if pd.notna(r.holder_count) and r.holder_count > 0:
                    parts.append(f"ch2_holding({int(r.holder_count)}h)")
                else:
                    parts.append("ch2_holding")
                parts.append("ch3_governance")
        if not (r.has_nvt_gl or r.has_tvl):
            parts.append("pq_nvtgl" if r.asset_class == "coin" else "tvl_defillama")
        return " | ".join(parts)

    df["coverage_status"] = df.apply(status, axis=1)
    df["what_needed"] = df.apply(needed, axis=1)
    cols = ["cmc_id", "symbol", "name", "asset_class", "sector", "coin_staking_type",
            "lambda_months", "lambda_n_channels", "lambda_channels", "has_ch1",
            "has_ch2", "has_ch3_v", "has_ch3_d", "has_nvt_gl", "nvt_months",
            "pq_source", "has_tvl", "tvl_months", "holder_count",
            "est_getlogs_calls", "evm_chain", "etherscan_reachable",
            "coverage_status", "what_needed"]
    df[cols].to_csv(OUT, index=False)
    print(f"wrote {OUT}: {len(df)} assets | "
          f"{(df.coverage_status=='complete').sum()} complete / "
          f"{(df.coverage_status=='partial').sum()} partial / "
          f"{(df.coverage_status=='not_started').sum()} not_started")


if __name__ == "__main__":
    main()
