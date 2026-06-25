"""
dune_dryrun_coverage.py -- SESSION 016, STEP 1: catalog coverage check.

For each of the 14 not-yet-validated NaN-token protocols, search Dune's decoded/
Spellbook catalog (/v1/datasets/search, NOT query-credit-metered) with 2-3 phrasings
and report found/not_found + matched full_name. The 3 pilot-validated protocols
(Aave/AAVE, Lido/LDO, Gains/GNS) are NOT re-searched here -- already known covered.

Standard (Entry 31/36): do not force a match. If 2-3 reasonable phrasings return
nothing relevant, mark not_found and move on.
"""
import json
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
OUTDIR = REPO / "03_data" / "raw" / "dune_dryrun"
OUTDIR.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
HEADERS = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

# token -> (category, [search phrasings]). Protocol identities from CMC/category context.
TARGETS = {
    # --- Lending (5; AAVE already validated) ---
    "ANC":   ("Lending",     ["anchor protocol borrow", "anchor terra lending", "anchor anc deposit"]),
    "BZRX":  ("Lending",     ["bzx protocol loan", "fulcrum bzx borrow", "ooki bzx lending"]),
    "OM":    ("Lending",     ["mantra dao lending", "mantra om borrow", "mantra finance"]),
    "STRK":  ("Lending",     ["strike finance lending", "strike protocol borrow", "strk lending compound"]),
    "WXT":   ("Lending",     ["wirex wxt lending", "wirex token", "wxt borrow"]),
    # --- Derivatives (9; GNS already validated) ---
    "AVNT":  ("Derivatives", ["avantis perp trades", "avantis base perpetual", "avantis trade volume"]),
    "DDX":   ("Derivatives", ["derivadex trades", "derivadex perpetual", "ddx derivatives"]),
    "HAKKA": ("Derivatives", ["hakka finance", "blackholeswap hakka", "3f mutual hakka"]),
    "HXRO":  ("Derivatives", ["hxro network", "hxro derivatives", "hxro perpetual"]),
    "KP3R":  ("Derivatives", ["keep3r network jobs", "keep3r kp3r", "keep3r volume"]),
    "LINA":  ("Derivatives", ["linear finance synthetic", "linear lina perpetual", "linear finance trades"]),
    "MIR":   ("Derivatives", ["mirror protocol synthetic", "mirror terra mAsset", "mirror mir trade"]),
    "MYX":   ("Derivatives", ["myx finance perpetual", "myx perp trades", "myx finance volume"]),
    "NMR":   ("Derivatives", ["numerai numeraire", "erasure numerai", "numeraire stake"]),
}


def search(query, limit=10):
    r = requests.post(f"{BASE}/datasets/search", headers=HEADERS,
                      json={"query": query, "limit": limit,
                            "include_schema": False, "include_metadata": True}, timeout=40)
    r.raise_for_status()
    return r.json()


def main():
    out = {}
    n_calls = 0
    for token, (cat, phrasings) in TARGETS.items():
        print(f"\n===== {token} ({cat}) =====")
        hits = []
        for q in phrasings:
            try:
                res = search(q)
            except Exception as e:
                print(f"  [search ERR] '{q}': {e}")
                continue
            n_calls += 1
            results = res.get("results", []) or []
            for d in results[:8]:
                fn = d.get("full_name") or d.get("name")
                hits.append({"query": q, "full_name": fn,
                             "category": d.get("category"),
                             "blockchains": d.get("blockchains")})
            top = ", ".join((d.get("full_name") or d.get("name") or "?") for d in results[:5]) or "(none)"
            print(f"  '{q}' -> {len(results)} | {top}")
        out[token] = {"category": cat, "hits": hits}
    (OUTDIR / "coverage_search.json").write_text(json.dumps(out, indent=2))
    print(f"\n[done] {n_calls} catalog search calls (not query-credit-metered)")


if __name__ == "__main__":
    main()
