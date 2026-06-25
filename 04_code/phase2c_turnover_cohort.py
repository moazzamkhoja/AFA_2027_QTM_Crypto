"""
phase2c_turnover_cohort.py -- SESSION 017, STEP 3 (Phase 2c DIAGNOSTIC, no panel writes).

Build the turnover-calibration cohort to test whether TVL x turnover (conversion path 4)
is defensible. Reuses the validated Dune pattern from dune_dryrun_fullpanel.py but pulls the
FULL DISTINCT project lists:
  - Lending : lending.borrow, transaction_type='borrow', GROUP BY project, month  (25 projects)
  - Perps   : perpetual.trades, GROUP BY project, month, SUM(volume_usd)           (28 projects)
Then matches each Dune `project` to a DeFiLlama slug (VERIFIED per-project, not assumed), pulls
that protocol's TVL history (api.llama.fi/protocol/{slug}), and computes
   turnover = monthly_PQ / month_end_TVL   per protocol-month.
Reports the dispersion separately for lending vs perpetual (median, IQR, min/max, slug-match count).

A wide dispersion (> ~1 order of magnitude) is a legitimate finding, reported plainly.
"""
import json, time, datetime as dt, statistics as st
from pathlib import Path
import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
RAW = REPO / "03_data" / "raw" / "phase2c"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
H = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}
S = requests.Session(); S.headers.update({"User-Agent": "afa-2027-qtm-research"})


def dune(sql, label, perf="small", wait=200):
    t0 = time.time()
    r = requests.post(f"{BASE}/sql/execute", headers=H, json={"sql": sql, "performance": perf}, timeout=40)
    r.raise_for_status()
    eid = r.json()["execution_id"]; w = 0
    while w < wait:
        s = requests.get(f"{BASE}/execution/{eid}/results", headers=H, timeout=40).json()
        if s.get("is_execution_finished"):
            (RAW / f"cohort_{label}.json").write_text(json.dumps(s, indent=2))
            rows = (s.get("result") or {}).get("rows") or []
            print(f"  {label}: {s.get('state')} rows={len(rows)} wall={time.time()-t0:.1f}s")
            return rows
        time.sleep(4); w += 4
    print(f"  {label}: TIMEOUT"); return []


LEND_SQL = """
SELECT project,
       date_trunc('month', block_time) AS month,
       SUM(amount_usd) AS pq_usd,
       COUNT(*) AS n
FROM lending.borrow
WHERE transaction_type = 'borrow' AND amount_usd > 0
GROUP BY 1, 2
ORDER BY 1, 2
"""

PERP_SQL = """
SELECT project,
       block_month AS month,
       SUM(volume_usd) AS pq_usd,
       COUNT(*) AS n
FROM perpetual.trades
WHERE volume_usd > 0
GROUP BY 1, 2
ORDER BY 1, 2
"""

# Dune project -> DeFiLlama slug. Verified individually below (cmcId/name/category printed).
# None = no confident DeFiLlama TVL slug match (flagged, excluded from turnover).
LEND_MAP = {
    "aave": "aave-v3", "aave_etherfi": None, "aave_horizon": None, "aave_lido": None,
    "agave": "agave", "benqi": "benqi-lending", "compound": "compound-v3", "euler": "euler-v2",
    "fluxfinance": "flux-finance", "granary": "granary-finance", "layer_bank": "layerbank",
    "lodestar": "lodestar", "moola": "moola-market", "moonwell": "moonwell", "morpho": "morpho-blue",
    "pike": None, "radiant": "radiant-v2", "realt_rmm": "rmm-v3", "seamlessprotocol": "seamless-protocol",
    "sonne_finance": "sonne-finance", "spark": "spark", "strike": "strike", "uwulend": "uwu-lend",
    "venus": "venus-core-pool", "zerolend": "zerolend",
}
PERP_MAP = {
    "AVT": None, "FXDX": "fxdx", "Minerva Money": None, "Mummy Finance": "mummy-finance",
    "NEX": None, "OPX Finance": "opx-finance", "Perpetual": "perpetual-protocol", "Pika": "pika-protocol",
    "Synthetix": "synthetix", "Unidex": "unidex", "basemax_finance": None, "bmx": "bmx",
    "emdx": None, "gains_network": "gains-network", "gmx": "gmx-v2", "hubble_exchange": "hubble-exchange",
    "immortalx": None, "katanaperps": None, "leverup": None, "meridian": "meridian-trade",
    "mummy_finance": "mummy-finance", "mux_protocol": "mux-protocol", "nether_fi": None, "perpl": None,
    "tigris_trade": "tigris-trade", "vela_exchange": "vela-exchange", "voodoo_trade": None, "xena": None,
}


def llama_tvl(slug):
    """Return {YYYY-MM: month_end_tvl_usd} and (name,cmcId,category) for verification."""
    if not slug:
        return None, None
    try:
        d = S.get(f"https://api.llama.fi/protocol/{slug}", timeout=60).json()
    except Exception as e:
        return None, ("ERR", str(e)[:60], "")
    if not isinstance(d, dict) or "tvl" not in d:
        return None, None
    monthly = {}
    for p in d.get("tvl") or []:
        ds = dt.date.fromtimestamp(p["date"])
        monthly[f"{ds.year}-{ds.month:02d}"] = p.get("totalLiquidityUSD")  # last write = month-end-ish
    return monthly, (d.get("name"), d.get("cmcId"), d.get("category"))


def build(rows, mapping, label):
    by_proj = {}
    for r in rows:
        by_proj.setdefault(r["project"], []).append(r)
    recs = []
    matched, unmatched = [], []
    print(f"\n--- {label}: {len(by_proj)} Dune projects ---")
    for proj in sorted(by_proj, key=str.lower):
        slug = mapping.get(proj, "MISSING")
        if slug == "MISSING":
            print(f"  [!] {proj}: not in map (treat as unmatched)"); unmatched.append(proj); continue
        tvl, meta = llama_tvl(slug)
        if not tvl:
            print(f"  [x] {proj:18}-> {str(slug):22} NO TVL ({meta})"); unmatched.append(proj); continue
        matched.append(proj)
        print(f"  [ok]{proj:18}-> {str(slug):22} TVL months={len(tvl)} name={meta[0]!r} cmcId={meta[1]}")
        for r in by_proj[proj]:
            mkey = r["month"][:7]
            t = tvl.get(mkey)
            if t and t > 0 and r["pq_usd"] and r["pq_usd"] > 0:
                recs.append({"cohort": label, "project": proj, "slug": slug, "month": mkey,
                             "pq_usd": r["pq_usd"], "tvl_usd": t, "turnover": r["pq_usd"] / t})
    return recs, matched, unmatched


def dispersion(recs, label):
    tos = [r["turnover"] for r in recs]
    if not tos:
        print(f"{label}: no turnover obs"); return
    tos_sorted = sorted(tos)
    q1 = tos_sorted[len(tos)//4]; q3 = tos_sorted[3*len(tos)//4]
    print(f"\n=== {label} turnover dispersion (n={len(tos)} protocol-months, "
          f"{len(set(r['project'] for r in recs))} projects) ===")
    print(f"  median={st.median(tos):.4f}  mean={st.mean(tos):.4f}")
    print(f"  IQR=[{q1:.4f}, {q3:.4f}]  ratio Q3/Q1={q3/q1:.1f}x" if q1 > 0 else f"  IQR=[{q1:.4f},{q3:.4f}]")
    print(f"  min={min(tos):.5f}  max={max(tos):.3f}  max/min={max(tos)/min(tos):.0f}x")
    # per-project median turnover (the cross-sectional spread that path-4 imputation borrows)
    pm = {}
    for r in recs:
        pm.setdefault(r["project"], []).append(r["turnover"])
    proj_meds = {p: st.median(v) for p, v in pm.items()}
    pv = sorted(proj_meds.values())
    print(f"  per-project median turnover: min={pv[0]:.4f} max={pv[-1]:.4f} "
          f"spread={pv[-1]/pv[0]:.0f}x across {len(pv)} projects")
    for p, m in sorted(proj_meds.items(), key=lambda x: x[1]):
        print(f"     {p:20} {m:.4f}")


def main():
    print("=== Pulling Dune cohorts (full DISTINCT project lists) ===")
    lend_rows = dune(LEND_SQL, "lending")
    perp_rows = dune(PERP_SQL, "perps")

    lend_recs, lm, lu = build(lend_rows, LEND_MAP, "lending")
    perp_recs, pm, pu = build(perp_rows, PERP_MAP, "perpetual")

    allrecs = lend_recs + perp_recs
    pd.DataFrame(allrecs).to_csv(REPO / "03_data" / "phase2" / "phase2c_turnover.csv", index=False)

    dispersion(lend_recs, "LENDING")
    dispersion(perp_recs, "PERPETUAL")

    print("\n=== slug-match summary ===")
    print(f"  lending : matched {len(lm)}/{len(set(r['project'] for r in lend_rows))} "
          f"projects; unmatched: {lu}")
    print(f"  perps   : matched {len(pm)}/{len(set(r['project'] for r in perp_rows))} "
          f"projects; unmatched: {pu}")


if __name__ == "__main__":
    main()
