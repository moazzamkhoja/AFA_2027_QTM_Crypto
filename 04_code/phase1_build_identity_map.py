"""
phase1_build_identity_map.py  --  Phase 1, step 0 (asset -> on-chain identity)

Builds the join backbone every lambda channel needs: a map from each in-universe
`cmc_id` to its canonical on-chain identity -- the token contract address + chain
(for ERC-20 staking/locking reconstruction) and its Snapshot governance space
(for the voting channel).

SOURCE-OF-DATA vs SOURCE-OF-METADATA (see DATA_DECISIONS_LOG.md Entry 21):
  DeFiLlama's /protocols list is used here ONLY as a registry/metadata directory
  -- it carries, per protocol, a `cmcId` (clean numeric join to our universe), a
  token `address` + `chain`, and a `governanceID` (the Snapshot space). The actual
  lambda NUMBERS are NOT taken from DeFiLlama; they are reconstructed from the
  canonical chain source (Etherscan V2 event logs) and from Snapshot's own API.
  Using an aggregator as an address book, not as the measurement, keeps the data
  itself sourced from the chain.

Join key: `cmcId` (numeric), never symbol (Phase 0 rule -- symbols collide).

Output:
  03_data/raw/defillama/protocols.json        (cached registry payload)
  03_data/phase1/asset_onchain_identity.csv    (one row per in-universe asset)
"""

import json
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CLASS_TABLE = REPO / "03_data" / "classification_table.csv"
RAW_DIR = REPO / "03_data" / "raw" / "defillama"
OUT_DIR = REPO / "03_data" / "phase1"
PROTOCOLS_URL = "https://api.llama.fi/protocols"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def load_protocols():
    """Fetch the DeFiLlama protocol registry once; cache raw payload for re-runs."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / "protocols.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = requests.get(PROTOCOLS_URL, headers=HEADERS, timeout=90)
    r.raise_for_status()
    data = r.json()
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


def parse_snapshot_space(gov_id):
    """governanceID is a list like ['snapshot:uniswapgovernance.eth'] or on-chain ids.
    Return the first snapshot-space id found, else ''."""
    if not gov_id:
        return ""
    if isinstance(gov_id, str):
        gov_id = [gov_id]
    for g in gov_id:
        if isinstance(g, str) and g.lower().startswith("snapshot:"):
            return g.split(":", 1)[1]
    return ""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    protocols = load_protocols()

    # Index protocols by cmcId. A cmcId can map to multiple protocol entries
    # (e.g. a token used across several protocol listings); keep the one with the
    # largest current TVL as the canonical entry, but record how many collided.
    by_cmc = {}
    for p in protocols:
        cmc = p.get("cmcId")
        if cmc in (None, "", "None"):
            continue
        try:
            cmc = str(int(float(cmc)))
        except (ValueError, TypeError):
            continue
        tvl = p.get("tvl") or 0
        rec = {
            "dl_slug": p.get("slug") or p.get("name"),
            "dl_name": p.get("name"),
            "dl_category": p.get("category"),
            "token_address": (p.get("address") or "").strip(),
            "token_chain": p.get("chain"),
            "token_chains": ";".join(p.get("chains") or []),
            "snapshot_space": parse_snapshot_space(p.get("governanceID")),
            "gecko_id": p.get("gecko_id") or "",
            "_tvl": tvl,
        }
        cur = by_cmc.get(cmc)
        if cur is None:
            rec["_n_dl_entries"] = 1
            by_cmc[cmc] = rec
        else:
            cur["_n_dl_entries"] += 1
            # prefer the higher-TVL entry; also backfill a snapshot space if missing
            if not cur["snapshot_space"] and rec["snapshot_space"]:
                cur["snapshot_space"] = rec["snapshot_space"]
            if not cur["token_address"] and rec["token_address"]:
                cur["token_address"] = rec["token_address"]
                cur["token_chain"] = rec["token_chain"]
            if tvl > cur["_tvl"]:
                rec["_n_dl_entries"] = cur["_n_dl_entries"]
                # keep already-found snapshot/address if the higher-tvl one lacks them
                rec["snapshot_space"] = rec["snapshot_space"] or cur["snapshot_space"]
                rec["token_address"] = rec["token_address"] or cur["token_address"]
                rec["token_chain"] = rec["token_chain"] or cur["token_chain"]
                by_cmc[cmc] = rec

    cls = pd.read_csv(CLASS_TABLE)
    inu = cls[cls["in_universe"] == True].copy()  # noqa: E712

    rows = []
    for _, a in inu.iterrows():
        cmc = str(int(a["cmc_id"]))
        m = by_cmc.get(cmc, {})
        rows.append({
            "cmc_id": int(a["cmc_id"]),
            "symbol": a["symbol"],
            "name": a["name"],
            "asset_class": a["asset_class"],
            "sector": a.get("sector", ""),
            "staking_start": a.get("staking_start", ""),
            "dl_slug": m.get("dl_slug", ""),
            "dl_category": m.get("dl_category", ""),
            "token_address": m.get("token_address", ""),
            "token_chain": m.get("token_chain", ""),
            "token_chains": m.get("token_chains", ""),
            "snapshot_space": m.get("snapshot_space", ""),
            "gecko_id": m.get("gecko_id", ""),
            "dl_matched": bool(m),
            "n_dl_entries": m.get("_n_dl_entries", 0),
        })
    out = pd.DataFrame(rows)
    out["has_address"] = out["token_address"].str.len() > 0
    out["has_snapshot"] = out["snapshot_space"].str.len() > 0

    out_path = OUT_DIR / "asset_onchain_identity.csv"
    out.to_csv(out_path, index=False)

    # Console summary (coverage diagnostics for the report)
    n = len(out)
    print(f"in-universe assets: {n}")
    print(f"  DeFiLlama-matched (cmcId): {out.dl_matched.sum()}")
    print(f"  with token address:        {out.has_address.sum()}")
    print(f"  with Snapshot space:       {out.has_snapshot.sum()}")
    print("\nby asset_class -- has_address / has_snapshot / n:")
    for cl, g in out.groupby("asset_class"):
        print(f"  {cl:6s}  addr={g.has_address.sum():4d}  snap={g.has_snapshot.sum():4d}  n={len(g)}")
    print("\ntoken_chain distribution (top 15, where address present):")
    print(out[out.has_address].token_chain.value_counts().head(15).to_string())
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
