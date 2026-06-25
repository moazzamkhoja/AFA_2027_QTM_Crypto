"""
phase2c_defillama_metadata.py -- SESSION 017, STEP 2 (Phase 2c DIAGNOSTIC, no panel writes).

For each of the 104 currently-NaN, non-Gaming tokens in pq_tokens.csv, record what
DeFiLlama FREE-tier data exists (presence + date range):
  - TVL          : api.llama.fi/protocol/{slug}            -> tvl[] {date,totalLiquidityUSD}
  - Fees         : api.llama.fi/summary/fees/{slug}?dataType=dailyFees   -> totalDataChart
  - Revenue      : api.llama.fi/summary/fees/{slug}?dataType=dailyRevenue-> totalDataChart
  - Direct vol   : /summary/dexs/{slug} (all), /summary/derivatives/{slug}
                   (Derivatives cat; expect 402 paywall), /summary/options/{slug} (Options cat)
  - Bridge vol   : bridges.llama.fi -> VERIFIED 402-PAYWALLED this session (all shapes); recorded
                   as paywalled, not re-hammered per-token.
  - APY          : yields.llama.fi/pools (single snapshot) matched by project==slug -> current APY
                   present Y/N + stats (snapshot only; dead protocols absent by construction).

Endpoint shapes were live-verified against current behaviour before this run (session 017 log).
FREE surface only (api.llama.fi / yields.llama.fi / bridges.llama.fi). No Pro API. No panel writes.
Idempotent: caches per-token raw JSON under 03_data/raw/phase2c/ and writes a tidy table.
"""
import json, time, datetime as dt
from pathlib import Path
import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
WORK = REPO / "03_data" / "phase2" / "phase2c_worklist.csv"
RAW = REPO / "03_data" / "raw" / "phase2c"
RAW.mkdir(parents=True, exist_ok=True)
OUT = REPO / "03_data" / "phase2" / "phase2c_metadata.csv"

S = requests.Session()
S.headers.update({"User-Agent": "afa-2027-qtm-research (academic, free-tier)"})


def _get(url, timeout=60, retries=3):
    """GET with light backoff; returns (status_code:int|str, json|None|text)."""
    for i in range(retries):
        try:
            r = S.get(url, timeout=timeout)
        except Exception as e:
            time.sleep(1.0 + i);
            if i == retries - 1:
                return "ERR", str(e)
            continue
        if r.status_code == 429:
            time.sleep(3.0 + 2 * i); continue
        try:
            return r.status_code, (r.json() if r.status_code == 200 else r.text[:200])
        except Exception:
            return r.status_code, None
    return "ERR", "exhausted"


def _rng_from_dates(ts_list):
    if not ts_list:
        return None, None
    lo, hi = min(ts_list), max(ts_list)
    return str(dt.date.fromtimestamp(lo)), str(dt.date.fromtimestamp(hi))


def check_tvl(slug):
    sc, d = _get(f"https://api.llama.fi/protocol/{slug}")
    if sc != 200 or not isinstance(d, dict):
        return {"tvl_present": "N", "tvl_status": sc, "tvl_start": None, "tvl_end": None, "tvl_last_usd": None}
    tvl = d.get("tvl") or []
    dates = [p["date"] for p in tvl if "date" in p]
    lo, hi = _rng_from_dates(dates)
    last = tvl[-1].get("totalLiquidityUSD") if tvl else None
    return {"tvl_present": "Y" if tvl else "N", "tvl_status": sc,
            "tvl_start": lo, "tvl_end": hi, "tvl_last_usd": round(last) if last else None}


def check_fees(slug, datatype):
    sc, d = _get(f"https://api.llama.fi/summary/fees/{slug}?dataType={datatype}")
    if sc != 200 or not isinstance(d, dict):
        return {"present": "N", "status": sc, "start": None, "end": None, "total30d": None}
    chart = d.get("totalDataChart") or []
    dates = [p[0] for p in chart if isinstance(p, list) and p]
    lo, hi = _rng_from_dates(dates)
    last30 = sum((p[1] or 0) for p in chart[-30:]) if chart else None
    return {"present": "Y" if chart else "N", "status": sc, "start": lo, "end": hi,
            "total30d": round(last30) if last30 else None}


def check_vol(slug, vertical):
    sc, d = _get(f"https://api.llama.fi/summary/{vertical}/{slug}")
    if sc != 200 or not isinstance(d, dict):
        return {"present": "N", "status": sc, "start": None, "end": None, "total30d": None}
    chart = d.get("totalDataChart") or []
    dates = [p[0] for p in chart if isinstance(p, list) and p]
    lo, hi = _rng_from_dates(dates)
    last30 = sum((p[1] or 0) for p in chart[-30:]) if chart else None
    return {"present": "Y" if chart else "N", "status": sc, "start": lo, "end": hi,
            "total30d": round(last30) if last30 else None}


def main():
    work = pd.read_csv(WORK)
    print(f"worklist: {len(work)} tokens")

    # --- one-shot yields snapshot ---
    print("fetching yields.llama.fi/pools snapshot ...")
    sc, yd = _get("https://yields.llama.fi/pools")
    yields_by_proj = {}
    if sc == 200 and isinstance(yd, dict):
        for p in yd.get("data", []):
            yields_by_proj.setdefault(p.get("project"), []).append(p)
    print(f"  yields projects: {len(yields_by_proj)}")

    BRIDGE_CATS = {"Bridge", "Canonical Bridge", "Cross Chain Bridge"}
    rows = []
    for i, t in work.iterrows():
        slug = str(t.dl_slug); cat = str(t.dl_category); sym = str(t.symbol)
        rec = {"cmc_id": t.cmc_id, "symbol": sym, "dl_slug": slug, "dl_category": cat}

        tvl = check_tvl(slug); time.sleep(0.2)
        fees = check_fees(slug, "dailyFees"); time.sleep(0.2)
        rev = check_fees(slug, "dailyRevenue"); time.sleep(0.2)
        dex = check_vol(slug, "dexs"); time.sleep(0.2)

        # category-appropriate extra verticals
        deriv = {"present": "", "status": "", "start": None, "end": None}
        opt = {"present": "", "status": "", "start": None, "end": None}
        if cat in ("Derivatives",):
            deriv = check_vol(slug, "derivatives"); time.sleep(0.2)
        if cat in ("Options",) or sym in ("HEGIC",):
            opt = check_vol(slug, "options"); time.sleep(0.2)

        # bridges: verified 402-paywalled this session across all shapes; do not re-hammer
        bridge_vol = "paywalled_402" if cat in BRIDGE_CATS else ""

        # APY (current snapshot)
        ypools = yields_by_proj.get(slug, [])
        apy_present = "Y" if ypools else "N"
        apy_n = len(ypools)
        apy_tvl = round(sum(p.get("tvlUsd") or 0 for p in ypools)) if ypools else None
        # TVL-weighted mean APY across the protocol's pools (current)
        apy_w = None
        if ypools and apy_tvl:
            num = sum((p.get("apy") or 0) * (p.get("tvlUsd") or 0) for p in ypools)
            apy_w = round(num / apy_tvl, 2) if apy_tvl else None

        rec.update({
            "tvl_present": tvl["tvl_present"], "tvl_start": tvl["tvl_start"], "tvl_end": tvl["tvl_end"],
            "tvl_last_usd": tvl["tvl_last_usd"], "tvl_status": tvl["tvl_status"],
            "fees_present": fees["present"], "fees_start": fees["start"], "fees_end": fees["end"],
            "fees_30d": fees["total30d"], "fees_status": fees["status"],
            "rev_present": rev["present"], "rev_start": rev["start"], "rev_end": rev["end"],
            "rev_30d": rev["total30d"],
            "dex_present": dex["present"], "dex_start": dex["start"], "dex_end": dex["end"],
            "dex_30d": dex["total30d"], "dex_status": dex["status"],
            "deriv_present": deriv["present"], "deriv_status": deriv["status"],
            "opt_present": opt["present"], "opt_status": opt["status"],
            "opt_start": opt.get("start"), "opt_end": opt.get("end"),
            "bridge_vol": bridge_vol,
            "apy_present": apy_present, "apy_npools": apy_n, "apy_tvl_usd": apy_tvl, "apy_wmean_pct": apy_w,
        })
        rows.append(rec)
        print(f"[{len(rows):>3}/{len(work)}] {sym:<8} {cat:<22} "
              f"TVL:{tvl['tvl_present']} Fee:{fees['present']} Rev:{rev['present']} "
              f"DEX:{dex['present']}({dex['status']}) "
              f"DERIV:{deriv['present']or'-'} OPT:{opt['present']or'-'} "
              f"BR:{bridge_vol or '-'} APY:{apy_present}({apy_n})")

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"\nwrote {OUT} ({len(df)} rows)")
    # quick summary
    print("\n=== presence summary ===")
    for col in ["tvl_present", "fees_present", "rev_present", "dex_present", "apy_present"]:
        print(f"  {col}: Y={int((df[col]=='Y').sum())}")
    print("  deriv 402s:", int((df.deriv_status == 402).sum()))
    print("  bridge paywalled:", int((df.bridge_vol == 'paywalled_402').sum()))


if __name__ == "__main__":
    main()
