"""
dune_pilot_explore.py -- STAGE 2 of the Dune feasibility pilot (manual column mapping).

The auto-picker in dune_pilot_test.py grabbed raw/wrong tables (Aave Polygon transfers,
Lido submit w/o USD, a Gains per-trade community table w/o amount_usd). This script does
the manual mapping the pilot prompt calls for: search for the correct NORMALIZED
(Spellbook) abstractions that carry amount_usd, and confirm their real columns with a
LIMIT-1 sample before any aggregation.

Catalog searches (/datasets/search) are NOT query-credit-metered; only /sql/execute is.
Every execute is logged with its performance tier so total credits can be reported.
"""
import json
import time
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
OUTDIR = REPO / "03_data" / "raw" / "dune_pilot"
OUTDIR.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
HEADERS = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

CALL_LOG = []  # (kind, detail, tier)


def search(query, limit=10):
    r = requests.post(f"{BASE}/datasets/search", headers=HEADERS,
                      json={"query": query, "limit": limit,
                            "include_schema": True, "include_metadata": True}, timeout=40)
    CALL_LOG.append(("search", query, "n/a"))
    r.raise_for_status()
    return r.json()


def show_search(query):
    res = search(query)
    print(f"\n[search] '{query}' -> {len(res.get('results', []))} results")
    for d in res.get("results", [])[:10]:
        print(f"   - {d.get('full_name')} | cat={d.get('category')} | chains={d.get('blockchains')}")
    return res


SEARCHES = [
    "lending borrows amount_usd",          # spellbook lending.borrows
    "aave borrow ethereum amount_usd",
    "perpetual trades amount_usd",          # spellbook perpetual.trades
    "gains gtrade defillama volume",        # gains' own defillama-feeding table
    "lido stETH submitted amount",          # confirm submit event
    "lido withdrawals claimed ethereum",    # withdrawal side
    "prices usd daily token",               # price join table
]

if __name__ == "__main__":
    for q in SEARCHES:
        res = show_search(q)
        (OUTDIR / f"search2_{q.replace(' ', '_')}.json").write_text(json.dumps(res, indent=2))
    print(f"\n[calls] {len(CALL_LOG)} search calls (no execute credits used in this stage)")
