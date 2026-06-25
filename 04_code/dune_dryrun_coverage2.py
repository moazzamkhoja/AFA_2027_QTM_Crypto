"""
dune_dryrun_coverage2.py -- SESSION 016, STEP 1 (decisive coverage test).

Catalog text search (coverage1) only tells us a *decoded contract* exists. The useful
question -- the one that made AAVE/GNS usable in the pilot -- is whether the protocol is
in the NORMALIZED cross-protocol spell layer (pre-priced amount_usd), i.e. whether it
appears as a `project` value in:
    lending.borrow      (lending throughput)
    perpetual.trades    (derivatives notional)

A protocol that is only a raw decoded token/vault table (anchor_ethereum.anchorvault_*,
mantra_polygon.mantra_call_transfer, etc.) is NOT cleanly covered -- using it would mean
hand-rolling reconstruction + a price join (the AAVE-sentinel hazard the pilot warned of).

So: enumerate DISTINCT project in both spell tables (cheap `small` executes), then match
our target tokens' protocol names against that list. Also retries the rate-limited
catalog searches with throttling for the decoded-catalog colour.
"""
import json, time
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
OUTDIR = REPO / "03_data" / "raw" / "dune_dryrun"
OUTDIR.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
HEADERS = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

CALLS = []


def execute_sql(label, sql, performance="small", max_wait_s=180, poll_s=3):
    t0 = time.time()
    r = requests.post(f"{BASE}/sql/execute", headers=HEADERS,
                      json={"sql": sql, "performance": performance}, timeout=40)
    r.raise_for_status()
    eid = r.json()["execution_id"]
    waited = 0
    while waited < max_wait_s:
        s = requests.get(f"{BASE}/execution/{eid}/results", headers=HEADERS, timeout=40)
        data = s.json()
        st = data.get("state", "")
        if data.get("is_execution_finished") or st.endswith("COMPLETED") or st.endswith("FAILED"):
            meta = (data.get("result") or {}).get("metadata") or {}
            CALLS.append({"label": label, "tier": performance, "state": st,
                          "datapoints": meta.get("datapoint_count"),
                          "engine_ms": meta.get("execution_time_millis"),
                          "wall_s": round(time.time() - t0, 1)})
            (OUTDIR / f"cov2_{label}.json").write_text(json.dumps(data, indent=2))
            return data
        time.sleep(poll_s); waited += poll_s
    CALLS.append({"label": label, "tier": performance, "state": "TIMED_OUT",
                  "wall_s": round(time.time() - t0, 1)})
    return {"state": "TIMED_OUT"}


def rows_of(d):
    return ((d.get("result") or {}).get("rows")) or []


def throttled_search(query, limit=10, retries=4):
    for attempt in range(retries):
        r = requests.post(f"{BASE}/datasets/search", headers=HEADERS,
                          json={"query": query, "limit": limit,
                                "include_schema": False, "include_metadata": True}, timeout=40)
        if r.status_code == 429:
            time.sleep(4 * (attempt + 1))
            continue
        r.raise_for_status()
        return r.json()
    return {"results": [], "rate_limited": True}


LEND_PROJECTS_SQL = "SELECT DISTINCT project FROM lending.borrow ORDER BY 1"
PERP_PROJECTS_SQL = "SELECT DISTINCT project FROM perpetual.trades ORDER BY 1"

RETRY_SEARCHES = {
    "DDX":   ["ddx derivatives"],
    "HAKKA": ["hakka finance", "blackholeswap hakka"],
    "HXRO":  ["hxro network", "hxro perpetual"],
    "KP3R":  ["keep3r network", "keep3r kp3r"],
    "LINA":  ["linear finance synthetic", "linear lina"],
    "MIR":   ["mirror protocol synthetic", "mirror mir terra"],
    "MYX":   ["myx finance perpetual", "myx perp"],
    "NMR":   ["numerai numeraire", "erasure numerai"],
}


def main():
    print("=== DISTINCT project in lending.borrow ===")
    d = execute_sql("lending_projects", LEND_PROJECTS_SQL)
    lend = sorted({r.get("project") for r in rows_of(d) if r.get("project")})
    print(f"  {len(lend)} lending projects:")
    print("  ", lend)

    print("\n=== DISTINCT project in perpetual.trades ===")
    d = execute_sql("perp_projects", PERP_PROJECTS_SQL)
    perp = sorted({r.get("project") for r in rows_of(d) if r.get("project")})
    print(f"  {len(perp)} perp projects:")
    print("  ", perp)

    print("\n=== throttled catalog re-search (rate-limited ones) ===")
    retry_out = {}
    for token, phrasings in RETRY_SEARCHES.items():
        hits = []
        for q in phrasings:
            res = throttled_search(q)
            time.sleep(2.5)
            results = res.get("results", []) or []
            for x in results[:6]:
                hits.append(x.get("full_name") or x.get("name"))
            top = ", ".join((x.get("full_name") or x.get("name") or "?") for x in results[:5]) or "(none)"
            rl = " [RATE_LIMITED]" if res.get("rate_limited") else ""
            print(f"  {token} '{q}' -> {len(results)}{rl} | {top}")
        retry_out[token] = hits

    (OUTDIR / "coverage2_spell_projects.json").write_text(
        json.dumps({"lending_projects": lend, "perp_projects": perp,
                    "retry_searches": retry_out, "calls": CALLS}, indent=2))
    print("\n=== executes ==="); [print("  ", c) for c in CALLS]


if __name__ == "__main__":
    main()
