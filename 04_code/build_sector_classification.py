"""
build_sector_classification.py  --  Phase 0 follow-up, deliverable 3
Implements DATA_SPECIFICATION.md section 2.6 / DATA_DECISIONS_LOG.md Entry 16.

Adds a SECOND, INDEPENDENT classification field `sector` to
03_data/classification_table.csv. This is orthogonal to the coin/token `asset_class`
cut -- it captures *what kind of economy* the asset is (L1/L2, DEX, Lending, Liquid
Staking, Bridge, Oracle, RWA, Gaming, Meme, DePIN, ...). It does NOT revise asset_class.

Sources (both kept where both fire; multi-value semicolon-separated):
  primary  : DeFiLlama protocol categories (already in `defillama_categories`),
             carried in as-is (Dexs, Lending, Derivatives, Liquid Staking, CDP, Bridge,
             RWA, Gaming, NFT Marketplace, ...).
  fallback : sector-like CMC tags -- chiefly layer-1 / layer-2 for base-layer coins
             that have no DeFiLlama protocol entry, plus oracle/privacy/depin/meme and
             other clearly sector-like tags. Ecosystem / portfolio / exchange-listing /
             governance-axis tags (e.g. 'binance-ecosystem', 'governance', 'dao',
             'defi') are deliberately NOT treated as sectors.

Leaves `sector` blank where neither source gives a usable signal (no guessing from the
asset name). Reports coverage by asset_class per spec 2.6.
"""

from pathlib import Path
import io
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "03_data"

# Curated CMC tag -> normalised sector label. Only clearly sector/economic-function
# tags are included. Governance-axis tags (governance/dao/defi) and ecosystem/
# portfolio/listing tags are intentionally excluded (not sectors).
SECTOR_TAG_MAP = {
    "layer-1": "Layer-1",
    "layer-2": "Layer-2",
    "smart-contracts": "Smart Contract Platform",
    "dag": "DAG",
    "modular-blockchain": "Modular Blockchain",
    "interoperability": "Interoperability",
    "zero-knowledge-proofs": "Zero Knowledge",
    "oracle": "Oracle",
    "privacy": "Privacy",
    "depin": "DePIN",
    "distributed-computing": "DePIN",
    "storage": "Storage",
    "filesharing": "Storage",
    "iot": "IoT",
    "meme": "Meme",
    "memes": "Meme",
    "gaming": "Gaming",
    "metaverse": "Metaverse",
    "play-to-earn": "Gaming",
    "collectibles-nfts": "NFT",
    "real-world-assets": "RWA",
    "ai-big-data": "AI/Big Data",
    "ai-agents": "AI Agents",
    "payments": "Payments",
    "medium-of-exchange": "Payments",
    "identity": "Identity",
    "dex": "DEX",
    "decentralized-exchange": "DEX",
    "derivatives": "Derivatives",
    "perpetuals": "Perpetuals",
    "yield-farming": "Yield",
    "lending-borrowing": "Lending",
    "liquid-staking-derivatives": "Liquid Staking",
    "restaking": "Restaking",
    "prediction-markets": "Prediction Market",
    "wrapped-tokens": "Wrapped Asset",
    "tokenized-assets": "Tokenized Asset",
    "centralized-exchange": "Exchange Token",
}


def dedup(seq):
    seen, out = set(), []
    for x in seq:
        x = x.strip()
        if x and x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return out


def build_sector(row):
    dl_parts, cmc_parts = [], []
    if pd.notna(row.get("defillama_categories")) and str(row["defillama_categories"]).strip():
        dl_parts = [c for c in str(row["defillama_categories"]).split(";") if c.strip()]
    if pd.notna(row.get("tags")) and str(row["tags"]).strip():
        for t in str(row["tags"]).split(";"):
            lab = SECTOR_TAG_MAP.get(t.strip().lower())
            if lab:
                cmc_parts.append(lab)
    sector = ";".join(dedup(dl_parts + cmc_parts))
    return pd.Series({
        "sector": sector,
        "_sector_has_dl": bool(dl_parts),
        "_sector_has_cmc": bool(cmc_parts),
    })


def main():
    ct = pd.read_csv(DATA / "classification_table.csv")
    flags = ct.apply(build_sector, axis=1)
    ct["sector"] = flags["sector"]
    ct.to_csv(DATA / "classification_table.csv", index=False)

    # ---- coverage report (in-universe, by post-confirmation asset_class) ----
    inu = ct[ct["in_universe"] == True].copy()
    inu = pd.concat([inu, flags.loc[inu.index, ["_sector_has_dl", "_sector_has_cmc"]]], axis=1)
    inu["has_sector"] = inu["sector"].fillna("").str.len() > 0

    buf = io.StringIO()
    w = lambda s="": buf.write(s + "\n")
    w("SECTOR / ECONOMIC-FUNCTION COVERAGE (deliverable 3, Entry 16, spec 2.6)")
    w("=" * 66)
    tot = len(inu)
    wsec = int(inu["has_sector"].sum())
    w(f"In-universe assets: {tot}")
    w(f"With a non-null sector: {wsec} ({100*wsec/tot:.1f}%)   "
      f"residual (no tag from either source): {tot-wsec} ({100*(tot-wsec)/tot:.1f}%)")
    w("")
    w("Coverage by asset_class (post-confirmation):")
    w(f"  {'class':6s} {'n':>5s} {'w/sector':>9s} {'cov%':>6s} "
      f"{'DLonly':>7s} {'CMConly':>8s} {'both':>6s} {'none':>6s}")
    for cls in ["coin", "token", "other"]:
        sub = inu[inu["asset_class"] == cls]
        n = len(sub)
        ws = int(sub["has_sector"].sum())
        dlo = int((sub["_sector_has_dl"] & ~sub["_sector_has_cmc"]).sum())
        cmo = int((~sub["_sector_has_dl"] & sub["_sector_has_cmc"]).sum())
        both = int((sub["_sector_has_dl"] & sub["_sector_has_cmc"]).sum())
        none = n - ws
        w(f"  {cls:6s} {n:5d} {ws:9d} {100*ws/n:5.1f}% "
          f"{dlo:7d} {cmo:8d} {both:6d} {none:6d}")
    w("")
    w("Source mix overall (in-universe):")
    w(f"  DeFiLlama category present: {int(inu['_sector_has_dl'].sum())}")
    w(f"  CMC sector tag present    : {int(inu['_sector_has_cmc'].sum())}")
    w(f"  both                      : {int((inu['_sector_has_dl'] & inu['_sector_has_cmc']).sum())}")
    w("")
    w("Top sector labels (in-universe, multi-count):")
    from collections import Counter
    cnt = Counter()
    for s in inu["sector"]:
        if isinstance(s, str) and s:
            for part in s.split(";"):
                cnt[part] += 1
    for lab, n in cnt.most_common(30):
        w(f"  {n:5d}  {lab}")

    diag = buf.getvalue()
    (DATA / "_sector_coverage.txt").write_text(diag, encoding="utf-8")
    print(diag)
    print("Wrote `sector` column to classification_table.csv.")


if __name__ == "__main__":
    main()
