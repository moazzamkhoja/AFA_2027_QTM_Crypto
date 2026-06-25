"""
phase2c_verdicts.py -- SESSION 017, STEP 4 (diagnostic, no panel writes).
Combine the DeFiLlama metadata (phase2c_metadata.csv) with the session's verified special
findings (SUN direct-volume recovery; NVT/VELO collision rulings; the 4 Dune-spell-covered
tokens; the turnover-dispersion verdict) into a per-token feasibility verdict table.
Produces 03_data/phase2/phase2c_verdicts.csv (feeds the report). NO pq_tokens.csv write.
"""
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
md = pd.read_csv(REPO / "03_data" / "phase2" / "phase2c_metadata.csv")

# --- session-verified special cases (by cmc_id) ---
DUNE_SPELL = {7278: "lending.borrow project=aave",
              8911: "lending.borrow project=strike",       # STRK cmc_id 8911 = Strike Finance (verified, not Starknet)
              8000: "Lido events x canonical-WETH price",
              13663: "gains DeFiLlama-feed table"}          # GNS
DIRECT_VOL = {10529: "SunSwap v1+v2+v3 DEX volume (sun.io AMM), 2020-08->2026-06"}
COLLISION = {5906: "dexs 'nerve' is NRV/cmcId8755 (Nerve Finance), NOT NVT/cmcId5906 -- different project",
             7127: "dexs 'velodrome-*' is a different VELO (Optimism); velo-finance(7127)=Velo, Stellar payments"}

FARM_YIELD = {"Farm", "Yield", "Yield Aggregator"}
TVL_FLOW_CATS = {"Lending", "Derivatives", "Liquid Staking", "Uncollateralized Lending"}
BRIDGE_CATS = {"Bridge", "Canonical Bridge", "Cross Chain Bridge"}
# categories with no capital->flow channel and no direct-volume object (path = none by economic model)
NO_MODEL = {"Chain", "Services", "Launchpad", "Bridge", "Canonical Bridge", "Cross Chain Bridge",
            "Developer Tools", "Token Locker", "Domains", "Payments", "Charity Fundraising",
            "CEX", "SoFi", "Staking Pool", "NFT Marketplace", "Reserve Currency",
            "Prediction Market", "Risk Curators", "Restaking", "Indexes", "Trading App",
            "Liquidity Manager", "Leveraged Farming"}


def verdict(r):
    cid, cat = r.cmc_id, r.dl_category
    if cid in DUNE_SPELL:
        return "VIABLE_dune_spell", f"Dune free-tier normalized spell available: {DUNE_SPELL[cid]} (Entry 37)"
    if cid in DIRECT_VOL:
        return "VIABLE_direct_volume", f"Direct DEX volume recoverable: {DIRECT_VOL[cid]}"
    if cid in COLLISION:
        return "NaN_symbol_collision", COLLISION[cid]
    # path 3: TVL x APY for farm/yield -- only if a CURRENT yields snapshot exists (live protocol)
    if cat in FARM_YIELD:
        if r.tvl_present == "Y" and r.apy_present == "Y":
            return "WEAK_tvl_apy", (f"TVL present + {int(r.apy_npools)} live yields pool(s) "
                                    f"(APY current-snapshot only, no free historical APY series -> "
                                    f"monthly panel would require constant-APY assumption)")
        return "NaN_no_apy", ("Farm/Yield but absent from current yields.llama.fi snapshot "
                              "(dead/delisted protocol) -> no APY rate, TVL x APY infeasible")
    # path 4: TVL x turnover for capital->flow categories -- dispersion too wide (Step 3)
    if cat in TVL_FLOW_CATS:
        if r.tvl_present == "Y":
            return "NaN_turnover_undefensible", ("Only path is TVL x calibrated turnover, but Step-3 "
                "cohort dispersion is too wide to calibrate a level "
                "(lending per-project medians 0.0008-1.24, ~1455x; perps unbounded)")
        return "NaN_no_data", "No TVL and no transacted-value object on free DeFiLlama"
    # bridges: transfer-volume object EXISTS but the only free source (bridges.llama.fi) is 402-paywalled
    if cat in BRIDGE_CATS:
        return "NaN_bridge_vol_paywalled", ("Bridge transfer volume IS the right transacted-value object, "
            "but bridges.llama.fi is 402-paywalled across all endpoint shapes (verified this session); "
            "no free notional series. Reopens only if bridges API access is obtained")
    # everything else: no capital->flow channel, no direct-volume object
    return "NaN_no_economic_model", (f"Category '{cat}' has no capital->flow channel and no free "
                                     f"direct-volume series; no transacted-value object to measure")


rows = []
for _, r in md.iterrows():
    v, why = verdict(r)
    rows.append({**r.to_dict(), "verdict": v, "rationale": why})
out = pd.DataFrame(rows)
out.to_csv(REPO / "03_data" / "phase2" / "phase2c_verdicts.csv", index=False)

print("=== verdict counts (104 tokens) ===")
print(out.verdict.value_counts().to_string())
print("\n=== VIABLE / WEAK tokens ===")
for v in ["VIABLE_dune_spell", "VIABLE_direct_volume", "WEAK_tvl_apy"]:
    sub = out[out.verdict == v]
    print(f"\n{v} ({len(sub)}):")
    for _, x in sub.iterrows():
        print(f"   {x.symbol:8} {x.dl_category:18} {x.dl_slug}")
print("\n=== by category x verdict ===")
print(pd.crosstab(out.dl_category, out.verdict).to_string())
