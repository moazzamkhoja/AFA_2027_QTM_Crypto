"""
dune_pilot_test.py  --  Dune Analytics feasibility PILOT (not a Phase 2c build).

Purpose: test whether Dune's decoded tables can supply the protocol-level "transacted
value" PQ object that DeFiLlama does NOT have a volume dimension for -- one token per
category currently NaN in 03_data/phase2/pq_tokens.csv:

  AAVE  (Lending)         -- DeFiLlama category has TVL/fees, no borrow-volume series
  LDO   (Liquid Staking)  -- DeFiLlama category has TVL, no stake/unstake-flow series
  GNS   (Derivatives/perps) -- DeFiLlama perps dimension is paid-gated (HTTP 402)

Run this from an environment with normal internet access (Claude Code locally, or your
own terminal) -- NOT from the Cowork sandbox, whose outbound network is allowlisted to
dev-infra domains only (pypi/npm/github) and blocks api.dune.com.

Methodology, deliberately conservative (matches Entry 31's "verify before trusting"
standard -- see DATA_DECISIONS_LOG.md, where raw Etherscan Transfer logs looked plausible
but were 46.6x off for UNI and physically impossible for AAVE):

  STEP 1  Search Dune's dataset catalog (free-text) for each token's category to find the
          actual decoded table name(s). Do NOT assume Spellbook naming guesses are correct.
  STEP 2  Pull a small raw sample (LIMIT 5) from the top-matching table to see REAL column
          names before aggregating anything.
  STEP 3  Only if an obvious USD-denominated amount column exists, attempt a trailing-30-day
          SUM as a first-pass volume estimate. Otherwise stop and report the raw sample --
          do not guess at column semantics.

Outputs:
  03_data/raw/dune_pilot/search_<LABEL>.json   raw dataset-search response per token
  03_data/raw/dune_pilot/sample_<LABEL>.json   raw LIMIT-5 sample per token
  03_data/raw/dune_pilot/summary.json          final pass/fail + numbers (if any) per token
  Console: human-readable summary table at the end.

Requires: pip install requests
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

# label, search query, fallback search queries
TARGETS = [
    ("AAVE_lending",  "aave v3 ethereum pool borrow", ["aave borrow", "lending borrow aave"]),
    ("LDO_staking",   "lido steth submit withdrawal", ["lido stake unstake", "lido submitted"]),
    ("GNS_perps",     "gains network gtrade trade",   ["gains network perp trade", "gtrade open close"]),
]


def search_datasets(query, limit=8):
    r = requests.post(
        f"{BASE}/datasets/search",
        headers=HEADERS,
        json={"query": query, "limit": limit, "include_schema": True, "include_metadata": True},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def execute_sql(sql, performance="medium", max_wait_s=120, poll_s=2):
    r = requests.post(
        f"{BASE}/sql/execute",
        headers=HEADERS,
        json={"sql": sql, "performance": performance},
        timeout=30,
    )
    r.raise_for_status()
    execution_id = r.json()["execution_id"]
    waited = 0
    while waited < max_wait_s:
        s = requests.get(f"{BASE}/execution/{execution_id}/results", headers=HEADERS, timeout=30)
        data = s.json()
        state = data.get("state", "")
        if state.endswith("COMPLETED") or state.endswith("FAILED"):
            return data
        time.sleep(poll_s)
        waited += poll_s
    return {"state": "TIMED_OUT", "execution_id": execution_id}


def best_candidate(search_result):
    results = search_result.get("results", [])
    if not results:
        return None
    # prefer decoded/canonical category, then highest page_rank_score if present
    def score(d):
        cat_bonus = 1 if d.get("category") in ("decoded", "canonical") else 0
        pr = (d.get("metadata") or {}).get("page_rank_score") or 0
        return (cat_bonus, pr)
    return sorted(results, key=score, reverse=True)[0]


def main():
    summary = {}
    for label, primary_q, fallbacks in TARGETS:
        print(f"\n=== {label} ===")
        queries_tried = [primary_q] + fallbacks
        candidate = None
        search_used = None
        for q in queries_tried:
            res = search_datasets(q)
            (OUTDIR / f"search_{label}_{q.replace(' ', '_')}.json").write_text(json.dumps(res, indent=2))
            top5 = res.get("results", [])[:5]
            print(f"  query='{q}' -> {len(res.get('results', []))} results")
            for d in top5:
                print(f"    - {d.get('full_name')} | cat={d.get('category')} | chains={d.get('blockchains')}")
            cand = best_candidate(res)
            if cand and cand.get("full_name"):
                candidate = cand
                search_used = q
                break
        if not candidate:
            print(f"  NO CANDIDATE TABLE FOUND for {label} -- manual search needed on dune.com")
            summary[label] = {"status": "no_candidate"}
            continue

        table = candidate["full_name"]
        print(f"  -> using table: {table} (matched via query '{search_used}')")

        sample_sql = f"SELECT * FROM {table} LIMIT 5"
        sample = execute_sql(sample_sql, performance="small")
        (OUTDIR / f"sample_{label}.json").write_text(json.dumps(sample, indent=2))

        rows = (((sample.get("result") or {}).get("rows")) or [])
        cols = list(rows[0].keys()) if rows else []
        print(f"  sample columns: {cols}")

        usd_cols = [c for c in cols if "usd" in c.lower() and "amount" in c.lower()]
        time_cols = [c for c in cols if "time" in c.lower() or "block_date" in c.lower()]

        if not usd_cols or not time_cols:
            print(f"  NO obvious (amount_usd, time) column pair -- stopping here for manual review.")
            summary[label] = {
                "status": "needs_manual_column_mapping",
                "table": table,
                "columns": cols,
            }
            continue

        amt_col, t_col = usd_cols[0], time_cols[0]
        agg_sql = (
            f"SELECT SUM({amt_col}) AS total_usd, COUNT(*) AS n_events "
            f"FROM {table} WHERE {t_col} > NOW() - INTERVAL '30' DAY"
        )
        agg = execute_sql(agg_sql, performance="medium")
        (OUTDIR / f"agg_{label}.json").write_text(json.dumps(agg, indent=2))
        agg_rows = (((agg.get("result") or {}).get("rows")) or [])
        if agg_rows:
            total_usd = agg_rows[0].get("total_usd")
            n_events = agg_rows[0].get("n_events")
            print(f"  trailing-30d volume via {amt_col}: ${total_usd:,.0f}  ({n_events} events)" if total_usd else f"  agg returned: {agg_rows[0]}")
            summary[label] = {
                "status": "ok",
                "table": table,
                "amount_col": amt_col,
                "time_col": t_col,
                "trailing_30d_usd": total_usd,
                "n_events": n_events,
            }
        else:
            print(f"  aggregation query did not return rows: {agg}")
            summary[label] = {"status": "agg_failed", "table": table, "raw": agg}

    (OUTDIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    for label, s in summary.items():
        print(f"  {label}: {s.get('status')}  table={s.get('table')}  30d_usd={s.get('trailing_30d_usd')}")
    print(f"\nFull raw outputs in {OUTDIR}")


if __name__ == "__main__":
    main()
