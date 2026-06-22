"""
classify_assets.py  --  Phase 0, step 3

Functional coin-vs-governance-token classification per DATA_SPECIFICATION.md
Section 2.3 and main.tex Section 2.1. The cut is whether locking the asset earns
a security-/seigniorage-related benefit (b_t > 0 -> COIN, H1a) or only governance
rights / a fee-share unrelated to network security (b_t = 0 -> TOKEN, H1b).

Evidence source: the union of CMC tags observed across snapshots, cross-checked
against DeFiLlama's protocol category for governance tokens. IMPORTANT CAVEAT
(logged): CMC tags reflect the asset's *current* metadata, not its point-in-time
state -- e.g. ETH is tagged 'pos' today even though it was PoW before the Merge.
We therefore add explicit time-varying staking-start dates for known transition
cases (ETH being the worked example), and flag the limitation for the rest.

Classes:
  coin        native chain asset with a security/seigniorage consensus role (H1a)
  token       governance / DeFi protocol token, b_t = 0 or fee-share only (H1b)
  stablecoin  excluded from the universe; listed here for completeness only
  other       neither cleanly (wrapped, exchange, meme w/o consensus, LST, etc.) -> flagged

Output: 03_data/classification_table.csv
"""

import json
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "03_data"

# --- tag vocabularies (substring match against the lowercased tag set) ---
COIN_TAGS = ["pow", "pos", "proof-of", "mineable", "masternode", "staking",
            "dpos", "pos-nas", "sha-256", "scrypt", "equihash", "ethash",
            "x11", "randomx", "consensus", "layer-1", "layer-2", "smart-contracts"]
# note: 'smart-contracts'/'layer-1' catch native platform gas tokens that may lack
# an explicit consensus tag; consensus tags above take priority as direct evidence.
PURE_POW_TAGS = ["pow", "mineable", "proof-of-work", "sha-256", "scrypt",
                "equihash", "ethash", "randomx", "x11"]
POS_TAGS = ["pos", "dpos", "staking", "proof-of-stake", "pos-nas", "masternode"]
# Exact consensus-tag set used for the coin test (avoids substring false matches).
CONSENSUS_EXACT = {
    "pow", "pos", "dpos", "pure-pos", "pos-nas", "staking", "masternodes",
    "mineable", "sha-256", "scrypt", "equihash", "ethash", "randomx", "x11",
    "delegated-proof-of-stake", "hybrid-pow-pos", "proof-of-work", "proof-of-stake",
    "proof-of-authority", "proof-of-history",
}
TOKEN_TAGS = ["defi", "governance", "dao", "yield-farming", "lending-borowing",
            "lending-borrowing", "decentralized-exchange", "dex", "vote-escrow",
            "yield-aggregator", "amm", "derivatives", "real-world-assets",
            "liquid-staking", "perpetuals"]
OTHER_TAGS = ["wrapped-tokens", "centralized-exchange", "exchange-based-tokens",
            "tokenized", "memes", "fan-token", "nft"]

# Known time-varying staking onset (verified against the public historical record;
# spec flags these as the worked example to handle). Keyed by CMC id.
#   ETH (id 1027): Beacon Chain genesis 2020-12-01 (staking first possible);
#                  Merge to full PoS 2022-09-15.
STAKING_START = {
    1027: {"staking_start": "2020-12-01", "merge_date": "2022-09-15",
        "note": "PoW until Beacon Chain genesis 2020-12-01; full PoS at Merge 2022-09-15. "
                "No staking-based lambda channel before 2020-12."},
}

# DeFiLlama categories that actually evidence a *governance/DeFi token*. Categories
# like 'Liquid Staking', 'Foundation', 'Oracle', 'Services', 'Bridge', 'Chain' are NOT
# governance-token evidence and previously caused false promotions (e.g. DOT, LINK,
# LDO -> token). Only promote an 'other' asset to 'token' on one of these.
DEFI_TOKEN_CATEGORIES = {
    "Dexs", "Lending", "CDP", "Yield", "Yield Aggregator", "Derivatives",
    "Synthetics", "Options", "Insurance", "Leveraged Farming", "Algo-Stables",
    "Liquidity manager", "Farm", "Launchpad", "Reserve Currency", "Governance",
}

# Curated native-coin overrides (documented judgment call, logged in DATA_DECISIONS_LOG).
# Major native L1/L0 coins whose CMC tags are thin/absent so the tag rules miss them.
# Keyed by CMC id to avoid symbol collisions. These are coins by asset nature (native
# monetary/gas asset of their own chain); whether a staking lambda channel exists is a
# separate Phase 1 question.
# (ids verified from the snapshot data as the highest-peak-mcap instance of each symbol)
NATIVE_COIN_OVERRIDE = {
    52: "XRP", 6636: "DOT", 512: "XLM", 4642: "HBAR", 1765: "EOS",
    1720: "IOTA", 1376: "NEO", 3077: "VET", 8916: "ICP", 2280: "FIL",
    2011: "XTZ", 131: "DASH", 328: "XMR", 1437: "ZEC", 11419: "TON",
    20396: "KAS", 1958: "TRX", 3794: "ATOM", 5805: "AVAX", 4030: "ALGO",
    6892: "EGLD", 4558: "FLOW",
}


def load_defillama_symbols():
    """Map upper-case symbol -> set of DeFiLlama categories (governance-token evidence)."""
    try:
        r = requests.get("https://api.llama.fi/protocols",
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=40)
        cats = {}
        for p in r.json():
            sym = (p.get("symbol") or "").upper()
            cat = p.get("category")
            if sym and sym != "-" and cat:
                cats.setdefault(sym, set()).add(cat)
        print(f"  DeFiLlama: {len(cats)} symbols with categories")
        return cats
    except Exception as e:
        print(f"  DeFiLlama fetch failed ({e}); proceeding without it.")
        return {}


def any_tag(tags, vocab):
    return [t for t in tags if any(v in t for v in vocab)]


def classify(tags):
    """Return (asset_class, basis, ambiguous_flag)."""
    tags = [t.lower() for t in tags]
    tagset = set(tags)

    # Stablecoin: EXACT tag match only. Substring matching wrongly catches
    # 'stablecoin-protocol' (governance tokens of stablecoin issuers) and
    # 'stablecoin-algorithmically-stabilized' (e.g. LUNC, which is the Terra *coin*,
    # not the UST stablecoin). True stablecoins carry the exact 'stablecoin' tag.
    if "stablecoin" in tagset:
        return "stablecoin", "exact 'stablecoin' tag", False

    coin_hits = any_tag(tags, COIN_TAGS)
    token_hits = any_tag(tags, TOKEN_TAGS)
    other_hits = any_tag(tags, OTHER_TAGS)

    # An explicit 'governance' or 'dao' tag is a strong governance-TOKEN signal that
    # should win over ecosystem 'layer-1'/'smart-contracts'/LST tags below (e.g. UNI
    # now carries 'layer-1' from Unichain, and LDO carries an LST ecosystem tag, yet
    # both are governance tokens).
    has_gov = ("governance" in tagset) or ("dao" in tagset)

    # liquid-staking derivatives & wrapped/exchange tokens are not clean coins/tokens
    if (not has_gov) and any(t in tagset for t in ["wrapped-tokens",
            "liquid-staking-derivatives", "liquid-staking-tokens", "tokenized-assets"]):
        return "other", f"wrapped/LST/tokenized ({other_hits or coin_hits})", True

    # Direct consensus evidence -> coin (takes priority over ecosystem 'defi' tags).
    # Use EXACT tag membership (plus the 'proof-of-*' family) so we don't false-match
    # substrings -- e.g. 'liquid-staking-derivatives' contains 'staking' but is NOT a
    # consensus mechanism (that is the LST governance token LDO, handled as a token).
    consensus = [t for t in tags if t in CONSENSUS_EXACT or t.startswith("proof-of")]
    if consensus:
        return "coin", f"consensus tags: {sorted(set(consensus))}", False

    # Native chain asset: 'layer-1' (or 'smart-contracts' without a governance/defi
    # tag) marks the chain's own gas token as a coin even when it also carries 'defi'
    # ecosystem tags (ATOM, AVAX, DOT, FTM) -- UNLESS an explicit governance/dao tag is
    # present, which marks a governance token (UNI).
    if "layer-1" in tagset and not has_gov:
        return "coin", "layer-1 native chain token (no governance/dao tag)", True
    if "smart-contracts" in tagset and not token_hits:
        return "coin", "smart-contract platform native token (no governance/defi tag)", True

    # Governance / DeFi token
    if token_hits:
        return "token", f"governance/defi tags: {sorted(set(token_hits))}", False

    if other_hits:
        return "other", f"other tags: {sorted(set(other_hits))}", True

    return "other", "no classifying tags", True


def main():
    assets = pd.read_csv(OUT_DIR / "universe_assets.csv")
    # include excluded stablecoins in the table for completeness
    excl = OUT_DIR / "universe_stablecoins_excluded.csv"
    if excl.exists():
        sdf = pd.read_csv(excl)
        sdf["in_universe"] = False
        assets["in_universe"] = True
        allrows = pd.concat([assets, sdf], ignore_index=True)
    else:
        assets["in_universe"] = True
        allrows = assets

    dl = load_defillama_symbols()

    out = []
    for _, r in allrows.iterrows():
        tags = [] if pd.isna(r.get("tags")) else str(r["tags"]).split(";")
        cls, basis, amb = classify(tags)
        cid = int(r["cmc_id"])
        sym = r["symbol"]
        dl_cats = dl.get(str(sym).upper(), set())
        # Promote a still-unclassified 'other' to 'token' ONLY on a genuine DeFi
        # governance-token category (not Liquid Staking / Oracle / Foundation / etc.).
        if cls == "other" and (dl_cats & DEFI_TOKEN_CATEGORIES):
            hit = sorted(dl_cats & DEFI_TOKEN_CATEGORIES)
            cls, basis, amb = "token", f"DeFiLlama governance/DeFi category: {hit}", True
        # Curated native-coin override (documented judgment call): force major native
        # coins with thin tags to 'coin' if the tag rules didn't already.
        if cid in NATIVE_COIN_OVERRIDE and cls not in ("coin", "stablecoin"):
            cls, basis, amb = "coin", "curated native-coin override (major L1/L0)", False
        sk = STAKING_START.get(cid, {})
        out.append({
            "cmc_id": cid, "symbol": sym, "name": r["name"],
            "in_universe": bool(r["in_universe"]),
            "asset_class": cls,
            "classification_basis": basis,
            "defillama_categories": ";".join(sorted(dl_cats)) if dl_cats else "",
            "ambiguous_flag": amb,
            "staking_start": sk.get("staking_start", ""),
            "transition_note": sk.get("note", ""),
            "tags": r.get("tags", ""),
        })

    df = pd.DataFrame(out).sort_values(["asset_class", "symbol"])
    df.to_csv(OUT_DIR / "classification_table.csv", index=False)

    inuni = df[df["in_universe"]]
    print("\nClassification (in-universe assets only):")
    print(inuni["asset_class"].value_counts().to_string())
    print(f"\nAmbiguous (flagged for review): {int(inuni['ambiguous_flag'].sum())}")
    print(f"Total rows (incl. excluded stablecoins): {len(df)}")


if __name__ == "__main__":
    main()
