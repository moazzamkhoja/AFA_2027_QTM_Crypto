"""
phase2_pq_tokens.py  --  Phase 2 PART A: token PQ = DeFiLlama sector-routed reported volume.

Per DATA_DECISIONS_LOG Entries 30/31/32 (resolved) and CLAUDE_CODE_PHASE2_PQ_BUILD_PROMPT.md
Part A. PQ for governance tokens = the protocol's *transacted value* (swap/DEX volume for AMMs,
options notional for options, aggregator routed volume for DEX aggregators), routed by the
protocol's DeFiLlama category. Raw gov-token Transfer logs were piloted and REJECTED (session
012, Entry 31: wrong object). Fees/TVL are SIDE DIAGNOSTICS only, never PQ.

Routing (token's DeFiLlama category / slug -> volume dimension):
  Dexs (or slug present in /overview/dexs)            -> /summary/dexs/{slug}        dailyVolume
  DEX Aggregator (or slug in /overview/aggregators)   -> /summary/aggregators/{slug} dailyVolume  (flagged: routed/double-counts underlying DEX)
  Options (or slug in /overview/options)              -> /summary/options/{slug}     dailyNotionalVolume
  Derivatives / perps                                 -> DeFiLlama volume is PAYWALLED (HTTP 402) -> PQ=NaN, flagged
  Lending/CDP/Yield/Farm/Bridge/Chain/Gaming/etc.     -> no free transacted-value volume object -> PQ=NaN (fees/TVL kept as diagnostics)

Fee->volume backout (Entry 32): applied ONLY when no volume series exists AND the protocol's fee
is a documented SINGLE, STABLE rate over the window (notional = fee/rate). NOT applied for
multi-tier fees, governance-variable fees, or lending reserve factors (a % of interest, not of
loan volume). Curated rate table FEE_BACKOUT_RATES below (empty unless a protocol is individually
verified). Where neither volume nor a confident rate exists -> PQ flagged NaN, never raw fee.

Output: 03_data/phase2/pq_tokens.csv  (long: cmc_id,symbol,dl_slug,month_end,pq_usd,pq_source,...)
        + per-token monthly TVL/fees diagnostics where available.
Caches raw DeFiLlama charts under 03_data/raw/defillama/phase2/ (gitignored).
"""
import json, time, os, calendar
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
H = {"User-Agent": "Mozilla/5.0"}
BASE = "https://api.llama.fi"
RAW = REPO / "03_data" / "raw" / "defillama" / "phase2"
OUT = REPO / "03_data" / "phase2"
OUT.mkdir(parents=True, exist_ok=True)
SLEEP = 0.15

# Curated fee->volume backout rates (Entry 32). Empty: no token protocol-month was individually
# verified to have a documented single, stable rate without circularity. Add entries only with a
# cited, flat, notional-proportional rate. (Reserve factors / multi-tier fees excluded by rule.)
FEE_BACKOUT_RATES = {}   # slug -> {"rate": float, "source": str}

sess = requests.Session(); sess.headers.update(H)
CALLS = {"n": 0}


def get(url, **params):
    for t in range(4):
        try:
            r = sess.get(url, params=params, timeout=40)
            CALLS["n"] += 1
            time.sleep(SLEEP)
            return r
        except Exception as e:
            time.sleep(SLEEP * (t + 1) * 2)
    return None


def cached_json(url, cache_name, **params):
    f = RAW / cache_name
    if f.exists():
        return json.loads(f.read_text())
    r = get(url, **params)
    if r is None or r.status_code != 200:
        f.write_text(json.dumps({"_status": (r.status_code if r else "err")}))
        return {"_status": (r.status_code if r else "err")}
    j = r.json()
    f.write_text(json.dumps(j))
    return j


def chart_to_monthly(chart):
    """[[unix_ts, value], ...] daily -> {month_end 'YYYY-MM-DD': sum_value}."""
    if not chart:
        return {}
    by_m = {}
    for row in chart:
        if not isinstance(row, list) or len(row) < 2 or row[1] is None:
            continue
        ts, val = row[0], row[1]
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:
            continue
        last = calendar.monthrange(dt.year, dt.month)[1]
        key = f"{dt.year:04d}-{dt.month:02d}-{last:02d}"
        by_m[key] = by_m.get(key, 0.0) + float(val)
    return by_m


def first_chart(j):
    """Pull the daily series out of a DeFiLlama /summary response."""
    if not isinstance(j, dict):
        return None
    for k in ("totalDataChart",):
        if isinstance(j.get(k), list) and j[k]:
            return j[k]
    return None


def main():
    idn = pd.read_csv(REPO / "03_data" / "phase1" / "asset_onchain_identity.csv")
    tok = idn[(idn.asset_class == "token") & (idn.dl_slug.notna())].copy()
    ovw = json.loads((RAW / "_dim_overviews.json").read_text())
    dex_slugs, agg_slugs, opt_slugs = set(ovw["dexs"]), set(ovw["aggregators"]), set(ovw["options"])
    # name->slug for fuzzy match within each dimension (lowercased, stripped of common suffixes)
    def normname(s):
        return str(s).lower().replace(" dex", "").replace(" finance", "").replace(" protocol", "").strip()

    rows = []
    diag = []
    for _, t in tok.iterrows():
        slug = t.dl_slug
        cat = str(t.dl_category)
        dim = None
        pq_source = None
        note = ""
        # route
        if cat == "Derivatives" or cat == "Derivatives Aggregator":
            pq_source = "NaN:derivatives_volume_paywalled_402"
            note = "DeFiLlama perps/derivatives volume dimension is paid-gated (HTTP 402); no free notional series"
        elif slug in dex_slugs or cat == "Dexs":
            dim = "dexs" if slug in dex_slugs else None
            pq_source = "defillama_dexs"
        elif slug in agg_slugs or cat == "DEX Aggregator":
            dim = "aggregators" if slug in agg_slugs else None
            pq_source = "defillama_aggregators"
            note = "aggregator routed volume (may double-count underlying DEX volume) - flagged"
        elif slug in opt_slugs or cat == "Options":
            dim = "options" if slug in opt_slugs else None
            pq_source = "defillama_options"
        else:
            pq_source = "NaN:no_transacted_value_object"
            note = f"category '{cat}' has no DeFiLlama transacted-value volume series"

        monthly = {}
        if dim is not None:
            dtype = "dailyNotionalVolume" if dim == "options" else "dailyVolume"
            j = cached_json(f"{BASE}/summary/{dim}/{slug}", f"vol_{dim}_{slug}.json",
                            dataType=dtype, excludeTotalDataChartBreakdown="true")
            ch = first_chart(j)
            if ch:
                monthly = chart_to_monthly(ch)
            else:
                # slug present in overview but summary empty, OR slug not in dim: try fee-backout
                if slug in FEE_BACKOUT_RATES:
                    pass  # handled below
                else:
                    pq_source = "NaN:volume_series_empty"
                    note = f"{dim} routed but /summary returned no chart"
        elif pq_source in ("defillama_dexs", "defillama_aggregators", "defillama_options"):
            # category said DEX/agg/options but slug not in that dimension overview -> no series
            pq_source = "NaN:slug_absent_from_volume_dimension"
            note = f"category '{cat}' but slug '{slug}' not in volume dimension overview"

        # fee-backout fallback (Entry 32) when no volume and a confident rate exists
        if not monthly and slug in FEE_BACKOUT_RATES:
            rate = FEE_BACKOUT_RATES[slug]["rate"]
            jf = cached_json(f"{BASE}/summary/fees/{slug}", f"fee_{slug}.json",
                             dataType="dailyFees", excludeTotalDataChartBreakdown="true")
            chf = first_chart(jf)
            if chf:
                feem = chart_to_monthly(chf)
                monthly = {m: v / rate for m, v in feem.items()}
                pq_source = "fee_backout"
                note = f"notional=fee/{rate} ({FEE_BACKOUT_RATES[slug]['source']})"

        # emit monthly PQ rows (or a single flagged-NaN marker row carrying the reason)
        if monthly:
            for m, v in sorted(monthly.items()):
                rows.append({"cmc_id": int(t.cmc_id), "symbol": t.symbol, "dl_slug": slug,
                             "dl_category": cat, "month_end": m, "pq_usd": v,
                             "pq_source": pq_source, "note": note})
        else:
            rows.append({"cmc_id": int(t.cmc_id), "symbol": t.symbol, "dl_slug": slug,
                         "dl_category": cat, "month_end": None, "pq_usd": float("nan"),
                         "pq_source": pq_source, "note": note})
        print(f"  {t.symbol:8} {slug:26} {pq_source:42} months={len(monthly)}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "pq_tokens.csv", index=False)
    # summary
    have = df[df.pq_usd.notna()]
    print(f"\nTokens total: {tok.shape[0]}")
    print(f"Tokens with >=1 PQ month: {have.cmc_id.nunique()}")
    print(f"PQ source breakdown (distinct tokens):")
    print(df.groupby('pq_source').cmc_id.nunique())
    print(f"\nTotal DeFiLlama API calls this run: {CALLS['n']}")
    print(f"Wrote {OUT/'pq_tokens.csv'}  ({len(df)} rows)")


if __name__ == "__main__":
    main()
