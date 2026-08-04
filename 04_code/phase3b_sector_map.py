"""
phase3b_sector_map.py -- Phase 3b Task A (spec section 8.1): coarse sector remap.

Deterministic keyword mapping of raw DeFiLlama compound category strings to
{DEX, Lending, Yield, Derivatives, Staking/LSD, Other}.

Rule (Entry 99): split the raw string on ';'; a token is assigned to the FIRST coarse
group in priority order (DEX > Lending > Yield > Derivatives > Staking/LSD) that has at
least one matching tag; no match -> Other. Tag matching is case-insensitive substring
at the tag level:
  DEX          : tag contains 'dex'            (Dexs, DEX, DEX Aggregator)
  Lending      : tag contains 'lending' or tag == 'CDP'
  Yield        : tag contains 'yield' or 'farm'
  Derivatives  : tag contains 'derivatives', 'options' or 'perpetuals'
  Staking/LSD  : tag contains 'staking'        (Liquid Staking, Staking Pool, Restaking)
This is the literal reading of spec 8.1 'priority-ordered' (first matching rule wins).
Consequence logged: perp/derivative DEXes (GMX, PERP, SNX, dYdX-with-DEX-tag) land in
DEX when they carry any Dexs/DEX tag; only pure-derivatives strings land in Derivatives.

Outputs:
  03_data/phase3/sector_coarse_map.csv          (cmc_id, symbol, sector_raw, sector_coarse)
  03_data/phase3/tables/sector_coarse_sizes.csv (group sizes per month in the token panel)
"""
import pandas as pd
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

PRIORITY = ["DEX", "Lending", "Yield", "Derivatives", "Staking/LSD"]


def tag_group(tag):
    t = tag.strip().lower()
    if "dex" in t:
        return "DEX"
    if "lending" in t or t == "cdp":
        return "Lending"
    if "yield" in t or "farm" in t:
        return "Yield"
    if "derivatives" in t or "options" in t or "perpetuals" in t:
        return "Derivatives"
    if "staking" in t:
        return "Staking/LSD"
    return None


def coarse(sector_raw):
    if not isinstance(sector_raw, str) or not sector_raw.strip():
        return "Other"
    groups = {tag_group(tag) for tag in sector_raw.split(";")}
    for g in PRIORITY:
        if g in groups:
            return g
    return "Other"


def main():
    p = pd.read_csv(OUT / "regression_panel.csv")
    tok = p[p.track == "token"]
    m = tok.drop_duplicates("cmc_id")[["cmc_id", "symbol", "sector"]].copy()
    m = m.rename(columns={"sector": "sector_raw"})
    m["sector_coarse"] = m["sector_raw"].map(coarse)
    m = m.sort_values(["sector_coarse", "symbol"])
    m.to_csv(OUT / "sector_coarse_map.csv", index=False)

    print("=== token counts per coarse group (101 tokens) ===")
    print(m.sector_coarse.value_counts().to_string())

    # group sizes per month in the regression panel
    tok2 = tok.merge(m[["cmc_id", "sector_coarse"]], on="cmc_id")
    sizes = (tok2.groupby(["month_end", "sector_coarse"]).size()
             .unstack(fill_value=0).sort_index())
    sizes.to_csv(TAB / "sector_coarse_sizes.csv")
    print("\n=== tokens per coarse group per month (panel) ===")
    desc = sizes.agg(["median", "min", "max", "mean"]).T
    print(desc.to_string(float_format=lambda x: f"{x:.1f}"))
    ge3 = (sizes >= 3).mean()
    print("\nshare of months with >=3 tokens, by group:")
    print(ge3.to_string(float_format=lambda x: f"{x:.1%}"))
    print(f"\nwrote {OUT/'sector_coarse_map.csv'} and {TAB/'sector_coarse_sizes.csv'}")


if __name__ == "__main__":
    main()
