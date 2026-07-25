# Session 034 Task C2: DeFiLlama slug lookup for the 102 Batch-1 tokens.
# Match priority: cmcId (authoritative) > token address > symbol+name corroboration.
# Symbol-only hits are rejected when the DL entry carries a DIFFERENT cmcId, and
# require name overlap (the ABC-validation lesson: raw symbol match ~16% wrong).
import json, re, requests
import pandas as pd
from pathlib import Path

REPO = Path(r"C:\AFA_2027_QTM_Crypto")
IDENT = REPO / "03_data" / "phase1" / "asset_onchain_identity.csv"
OUT = REPO / "03_data" / "phase2" / "session034_dl_slug_candidates.csv"

WL = [11461,33981,1888,2593,38417,5830,23177,3367,3418,17050,1882,2576,7672,35818,
      1768,39125,2503,29974,3325,3855,19843,2363,5007,12387,1660,29335,6833,4862,
      24760,2726,2277,2110,5798,5326,3083,37574,29035,18037,6748,38482,2559,1500,
      2826,19650,2296,2202,3053,33038,2772,8161,9308,2223,25147,39720,7224,16876,
      3928,33824,38408,8420,9444,28412,7501,5429,3296,3475,34104,15060,8075,1503,
      9674,12573,29242,33652,9640,29520,26997,34143,5617,2430,23711,28695,10407,
      2015,2700,2945,27566,4195,6511,1984,11289,12409,27565,8083,11156,29676,
      36458,16116,28933,2424,21535,1758]

STOP = {"protocol", "finance", "network", "token", "dao", "swap", "the", "v1", "v2", "v3"}

def words(s):
    return {w for w in re.split(r"[^a-z0-9]+", str(s).lower()) if len(w) > 2 and w not in STOP}

protos = requests.get("https://api.llama.fi/protocols", timeout=60).json()
print(f"DeFiLlama protocols: {len(protos)}")

ident = pd.read_csv(IDENT)
sub = ident[ident.cmc_id.isin(WL)].set_index("cmc_id")

by_cmc = {}
for p in protos:
    cid = p.get("cmcId")
    if cid:
        try:
            by_cmc.setdefault(int(str(cid)), []).append(p)
        except (ValueError, TypeError):
            pass

rows = []
for cmc_id in WL:
    t = sub.loc[cmc_id]
    sym = str(t.symbol)
    name = str(t["name"])
    addr = str(t.token_address).lower() if pd.notna(t.token_address) else ""
    existing = t.dl_slug if pd.notna(t.dl_slug) and str(t.dl_slug) else None
    nw = words(name)

    how, cands = "cmcId", by_cmc.get(cmc_id, [])
    if not cands and addr and addr != "nan":
        cands = [p for p in protos if addr in str(p.get("address", "")).lower()]
        how = "address"
    if not cands:
        raw = [p for p in protos if str(p.get("symbol", "")).lower() == sym.lower()]
        # reject entries claiming a DIFFERENT cmcId
        raw = [p for p in raw if not p.get("cmcId") or str(p.get("cmcId")) == str(cmc_id)]
        # require name-word overlap between our CMC name and the DL protocol name
        cands = [p for p in raw if nw & words(p.get("name", ""))]
        how = "symbol+name" if cands else ("symbol-rejected" if raw else "NONE")
        if how == "symbol-rejected":
            rows.append({"cmc_id": cmc_id, "symbol": sym, "name": name,
                         "asset_class": t.asset_class, "existing_slug": existing,
                         "match_how": how, "dl_slug": None, "dl_name": None,
                         "dl_category": None, "tvl_usd": None, "n_cands": 0,
                         "rejected": ";".join(f"{p['slug']}({p.get('name')})" for p in raw[:5])})
            continue
    if not cands:
        rows.append({"cmc_id": cmc_id, "symbol": sym, "name": name,
                     "asset_class": t.asset_class, "existing_slug": existing,
                     "match_how": "NONE", "dl_slug": None, "dl_name": None,
                     "dl_category": None, "tvl_usd": None, "n_cands": 0, "rejected": None})
        continue
    best = max(cands, key=lambda p: p.get("tvl") or 0)
    rows.append({"cmc_id": cmc_id, "symbol": sym, "name": name,
                 "asset_class": t.asset_class, "existing_slug": existing,
                 "match_how": how, "dl_slug": best["slug"], "dl_name": best.get("name"),
                 "dl_category": best.get("category"), "tvl_usd": best.get("tvl") or 0,
                 "n_cands": len(cands),
                 "rejected": ";".join(p["slug"] for p in cands[:6])})

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print(df.match_how.value_counts().to_string())
print(df[df.dl_slug.notna()][["cmc_id","symbol","name","asset_class","match_how","dl_slug","dl_name","dl_category","tvl_usd"]].to_string(max_colwidth=32))
print("\n--- symbol-rejected (collisions) ---")
print(df[df.match_how=="symbol-rejected"][["cmc_id","symbol","name","rejected"]].to_string(max_colwidth=60))
