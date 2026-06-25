"""
phase2c_turnover_refine.py -- SESSION 017, STEP 3 refinement (diagnostic, no panel writes).

The first pass (phase2c_turnover_cohort.py) matched each Dune `project` to a SINGLE DeFiLlama
version-slug, but Dune's project aggregates ALL versions (project='aave' = v1+v2+v3+v4 borrow),
so single-version TVL mismatched scope and inflated dispersion for multi-version protocols.

This pass sums TVL across ALL of a protocol's version slugs (verified from the live /protocols list)
to test whether the extreme lending/perp turnover outliers converge once TVL scope is matched --
i.e. how much of the measured dispersion is artifact vs. real. Reuses CACHED Dune rows
(03_data/raw/phase2c/cohort_{lending,perps}.json); no new Dune query.
"""
import json, datetime as dt, statistics as st
from pathlib import Path
import requests, pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "03_data" / "raw" / "phase2c"
S = requests.Session(); S.headers.update({"User-Agent": "afa-2027-qtm-research"})

# project -> list of DeFiLlama slugs whose TVL sums to the Dune project's full scope.
# Verified against the live /protocols list (names/categories inspected). [] = no usable TVL.
LEND = {
    "aave": ["aave-v1", "aave-v2", "aave-v3", "aave-v4"],
    "compound": ["compound-v1", "compound-v2", "compound-v3"],
    "venus": ["venus-core-pool", "venus-isolated-pools", "venus-flux"],
    "euler": ["euler-v1", "euler-v2"],
    "lodestar": ["lodestar-v0", "lodestar-v1"],
    "agave": ["agave"], "benqi": ["benqi-lending"], "fluxfinance": ["flux-finance"],
    "granary": ["granary-finance"], "layer_bank": ["layerbank"], "moola": ["moola-market"],
    "moonwell": ["moonwell"], "morpho": ["morpho-blue"], "radiant": ["radiant-v2"],
    "seamlessprotocol": ["seamless-protocol"], "sonne_finance": ["sonne-finance"],
    "spark": ["spark"], "strike": ["strike"], "uwulend": ["uwu-lend"], "zerolend": ["zerolend"],
    "aave_etherfi": [], "aave_horizon": ["aave-horizon-rwa"], "aave_lido": [], "pike": [],
    "realt_rmm": [],  # realt-rmm-marketplace TVL is ~$0
}
PERP = {
    "gmx": ["gmx-v1-perps", "gmx-v2-perps"], "tigris_trade": ["tigris"],
    "bmx": ["bmx"], "FXDX": ["fxdx"], "gains_network": ["gains-network"],
    "hubble_exchange": ["hubble-exchange"], "meridian": ["meridian-trade"],
    "Mummy Finance": ["mummy-finance"], "mummy_finance": ["mummy-finance"],
    "mux_protocol": ["mux-protocol"], "OPX Finance": ["opx-finance"],
    "Perpetual": ["perpetual-protocol"], "Pika": ["pika-protocol"], "Synthetix": ["synthetix"],
    "Unidex": ["unidex"], "vela_exchange": ["vela-exchange"],
    "AVT": [], "basemax_finance": [], "emdx": [], "immortalx": [], "katanaperps": [],
    "leverup": [], "Minerva Money": [], "nether_fi": [], "NEX": [], "perpl": [],
    "voodoo_trade": [], "xena": [],
}

_cache = {}
def tvl_monthly(slug):
    if slug in _cache:
        return _cache[slug]
    try:
        d = S.get(f"https://api.llama.fi/protocol/{slug}", timeout=60).json()
        m = {}
        for p in d.get("tvl") or []:
            ds = dt.date.fromtimestamp(p["date"])
            m[f"{ds.year}-{ds.month:02d}"] = p.get("totalLiquidityUSD")
    except Exception:
        m = {}
    _cache[slug] = m
    return m

def summed_tvl(slugs):
    out = {}
    for s in slugs:
        for k, v in tvl_monthly(s).items():
            out[k] = out.get(k, 0) + (v or 0)
    return out

def build(rows, mapping, label):
    by = {}
    for r in rows:
        by.setdefault(r["project"], []).append(r)
    recs = []
    for proj, slugs in mapping.items():
        if not slugs:
            continue
        tv = summed_tvl(slugs)
        for r in by.get(proj, []):
            mk = r["month"][:7]; t = tv.get(mk)
            if t and t > 0 and r["pq_usd"] and r["pq_usd"] > 0:
                recs.append({"cohort": label, "project": proj, "month": mk,
                             "pq_usd": r["pq_usd"], "tvl_usd": t, "turnover": r["pq_usd"]/t})
    return recs

def report(recs, label):
    pm = {}
    for r in recs:
        pm.setdefault(r["project"], []).append(r["turnover"])
    meds = {p: st.median(v) for p, v in pm.items()}
    allt = sorted(r["turnover"] for r in recs)
    pv = sorted(meds.values())
    print(f"\n=== {label} (TVL scope-matched): {len(recs)} protocol-months, {len(meds)} projects ===")
    print(f"  pooled median monthly turnover = {st.median(allt):.4f}")
    print(f"  per-project median turnover: min={pv[0]:.4f}  max={pv[-1]:.4f}  spread={pv[-1]/pv[0]:.0f}x")
    # robust central band: drop top/bottom project
    core = pv[1:-1] if len(pv) > 4 else pv
    print(f"  trimmed (drop hi/lo project) spread={core[-1]/core[0]:.1f}x  band=[{core[0]:.3f},{core[-1]:.3f}]")
    for p, m in sorted(meds.items(), key=lambda x: x[1]):
        print(f"     {p:20} {m:.4f}  (n={len(pm[p])})")

def main():
    lend_rows = json.loads((RAW/"cohort_lending.json").read_text())["result"]["rows"]
    perp_rows = json.loads((RAW/"cohort_perps.json").read_text())["result"]["rows"]
    lr = build(lend_rows, LEND, "LENDING")
    pr = build(perp_rows, PERP, "PERPETUAL")
    pd.DataFrame(lr+pr).to_csv(REPO/"03_data"/"phase2"/"phase2c_turnover_scopematched.csv", index=False)
    report(lr, "LENDING")
    report(pr, "PERPETUAL")

if __name__ == "__main__":
    main()
