"""
phase2_build_tvl_panel.py -- SESSION 019, Part B: build a real, persistent TVL panel.

Phase 2c's check_tvl() already fetched api.llama.fi/protocol/{slug}'s full tvl[] series
(`[{date: unix_ts, totalLiquidityUSD: float}, ...]`) but discarded everything except
presence/range/last-value. This script persists the FULL series at monthly grain (last
observation per calendar month, matching universe_panel.csv's calendar-month-end
convention) for EVERY token with a confirmed dl_slug match in asset_onchain_identity.csv
(127 tokens as of 2026-06-26; re-derived live below).

SCOPE / SEMANTICS (Decisions Log Entry 30, reaffirmed Entry 40): TVL is a STOCK. This
panel is a valuation-multiple DENOMINATOR (NV/TVL), NOT a PQ (transacted-value flow)
substitute. It is not a lambda channel. Nothing here touches PQ.

SOURCE: api.llama.fi (free, keyless). Per-token raw JSON cached under
03_data/raw/phase2/tvl/. time.sleep(0.2) between calls (phase2c pattern). Idempotent.

Join key: cmc_id (never symbol). dl_slug taken from the authoritative identity map.

Output: 03_data/phase2/tvl_panel.csv  (cmc_id, symbol, dl_slug, month_end, ym, tvl_usd)
"""
import json
import time
import datetime as dt
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IDENT = REPO / "03_data" / "phase1" / "asset_onchain_identity.csv"
PANEL = REPO / "03_data" / "universe_panel.csv"
RAW = REPO / "03_data" / "raw" / "phase2" / "tvl"
RAW.mkdir(parents=True, exist_ok=True)
OUT = REPO / "03_data" / "phase2" / "tvl_panel.csv"
DIAG = REPO / "03_data" / "phase2" / "tvl_panel_coverage.csv"

S = requests.Session()
S.headers.update({"User-Agent": "afa-2027-qtm-research (academic, free-tier)"})

# Optional widening (Part B, stretch goal): tokens the cmcId-keyed identity join MISSED
# (DeFiLlama left cmcId null or stale) but whose symbol AND name match a DeFiLlama protocol
# EXACTLY and were verified individually to (a) be the right protocol and (b) carry a real
# TVL series. Low yield as the prompt predicted -- of 321 unmatched tokens only these two
# clear the bar. (cmc_id, symbol, slug, verification note)
#   AXL  17799 -> axelar             ($135M TVL, 2022-10+; DeFiLlama cmcId null, symbol+name exact)
#   PERP 6950  -> perpetual-protocol ($0.4M TVL, 2021-06+; DeFiLlama cmcId stale=1301, but the
#                 slug is unambiguously "Perpetual Protocol"/PERP -- the same asset whose
#                 vote-perp.eth Snapshot space was verified in Part A.2)
# Rejected (cmcId mismatch + trivial/zero TVL -> collision risk not worth it): CVP, POLS.
# Rejected (zero protocol TVL -> nothing to add): METIS, HONEY, PUMP, PYTH, WLFI.
LOOSE_ADDS = [
    (17799, "AXL", "axelar"),
    (6950, "PERP", "perpetual-protocol"),
]

# SESSION 027 (Entry 68): asset_class=='other' lambda assets whose dl_slug IS the right
# protocol-level TVL (the token-class filter below excludes them; each verified individually --
# name + category + live TVL). NOT added: GBYTE (oswap-amm is a third-party DEX on Obyte, not
# GBYTE's protocol), PENGU (not Abstract's fee token -- no defensible TVL), OP/MNT (Foundation/
# treasury slugs = treasury holdings, not protocol TVL -> they get CHAIN-level TVL below).
OTHER_ADDS = [
    (2943, "RPL", "rocket-pool"),        # Liquid Staking, $899M
    (12999, "SSV", "ssv-network"),       # Staking Pool (DVT-secured ETH), $8.3B
    (23121, "BLUR", "blur"),             # parent: Blur Bids pool + Blur Lending
    (38341, "RAIN", "rain"),             # Prediction Market, $29M
    (17704, "MV", "gensokishi"),         # Gaming; small but real series
]

# SESSION 027 (Entry 68): CHAIN-level TVL for canonical L2 governance tokens whose protocol
# entry on DeFiLlama is a Foundation/treasury or an empty parent (ARB's 'arbitrum' and APE's
# 'apecoin' serve empty tvl[]). Source: api.llama.fi/v2/historicalChainTvl/{chain} (daily
# {date, tvl}). dl_slug recorded as 'chain:{name}' so downstream can distinguish chain-level
# denominators from protocol-level ones. COINS are deliberately absent (they use NVT, not
# NV/TVL). 'Optimism' is a dead DL alias -- the live chain name is 'OP Mainnet'.
CHAIN_LEVEL = [
    (11841, "ARB", "Arbitrum"),
    (11840, "OP", "OP Mainnet"),
    (27075, "MNT", "Mantle"),
    (18876, "APE", "ApeChain"),
    (28480, "BLAST", "Blast"),
]


def _get(url, timeout=90, retries=3):
    """GET with light backoff; returns (status_code:int|str, json|None|text)."""
    for i in range(retries):
        try:
            r = S.get(url, timeout=timeout)
        except Exception as e:
            time.sleep(1.0 + i)
            if i == retries - 1:
                return "ERR", str(e)
            continue
        if r.status_code == 429:
            time.sleep(3.0 + 2 * i)
            continue
        try:
            return r.status_code, (r.json() if r.status_code == 200 else r.text[:200])
        except Exception:
            return r.status_code, None
    return "ERR", "exhausted"


def fetch_protocol(slug):
    """Return the cached/freshly-fetched protocol payload dict, or None."""
    cf = RAW / f"{slug}.json"
    if cf.exists():
        try:
            return json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            pass
    sc, d = _get(f"https://api.llama.fi/protocol/{slug}")
    time.sleep(0.2)
    if sc != 200 or not isinstance(d, dict):
        # cache the failure shape so re-runs don't re-hammer, but flag it
        return {"_fetch_status": sc, "_fetch_error": d if isinstance(d, str) else None}
    cf.write_text(json.dumps(d), encoding="utf-8")
    return d


def fetch_chain(chain_name):
    """Return the cached/freshly-fetched historicalChainTvl list [{date, tvl}], or None."""
    cf = RAW / f"chain_{chain_name.replace(' ', '_')}.json"
    if cf.exists():
        try:
            return json.loads(cf.read_text(encoding="utf-8"))
        except Exception:
            pass
    sc, d = _get(f"https://api.llama.fi/v2/historicalChainTvl/{chain_name}")
    time.sleep(0.2)
    if sc != 200 or not isinstance(d, list):
        return None
    cf.write_text(json.dumps(d), encoding="utf-8")
    return d


def monthly_last(tvl_series):
    """Collapse a [{date, totalLiquidityUSD}] series to {ym: last_value_in_month}.
    'Last observation per calendar month' = the entry with the max unix date within
    that YYYY-MM bucket (the series is daily and already sorted, but we max-by-date to
    be safe)."""
    by_ym = {}
    for p in tvl_series:
        d = p.get("date")
        v = p.get("totalLiquidityUSD")
        if d is None or v is None:
            continue
        ym = dt.datetime.utcfromtimestamp(int(d)).strftime("%Y-%m")
        cur = by_ym.get(ym)
        if cur is None or int(d) >= cur[0]:
            by_ym[ym] = (int(d), float(v))
    return {ym: val for ym, (_, val) in by_ym.items()}


def main():
    ident = pd.read_csv(IDENT)
    ident["dl_slug"] = ident["dl_slug"].fillna("").astype(str)
    tok = ident[(ident.asset_class == "token") & (ident.dl_slug.str.len() > 0)].copy()
    print(f"dl_slug-matched tokens (live): {len(tok)}")

    # append the individually-verified looser-match tokens (Part B stretch goal)
    sym_by_cmc = dict(zip(ident.cmc_id, ident.symbol))
    add_rows = pd.DataFrame([{"cmc_id": c, "symbol": sym_by_cmc.get(c, s), "dl_slug": slug,
                              "_loose": True} for c, s, slug in LOOSE_ADDS + OTHER_ADDS])
    tok["_loose"] = False
    tok = tok[~tok.cmc_id.isin(add_rows.cmc_id)]   # adds are authoritative for their cmc_ids
    tok = pd.concat([tok, add_rows], ignore_index=True)
    print(f"  + {len(add_rows)} individually-verified adds (loose + other-class) -> {len(tok)} total")

    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    ym_to_monthend = panel.groupby("ym")["month_end"].first().to_dict()
    valid_yms = set(ym_to_monthend)  # only emit months present in the universe panel

    rows, diag = [], []
    for i, (_, t) in enumerate(tok.iterrows(), 1):
        slug = t.dl_slug
        cmc_id = int(t.cmc_id)
        sym = t.symbol
        d = fetch_protocol(slug)
        if not isinstance(d, dict) or "_fetch_status" in d:
            st = d.get("_fetch_status") if isinstance(d, dict) else "ERR"
            diag.append({"cmc_id": cmc_id, "symbol": sym, "dl_slug": slug,
                         "status": st, "n_months": 0, "ym_start": None, "ym_end": None,
                         "note": "fetch failed"})
            print(f"[{i:>3}/{len(tok)}] {sym:<8} {slug:<28} FETCH FAIL ({st})")
            continue
        tvl = d.get("tvl") or []
        mser = monthly_last(tvl)
        # restrict to months present in the universe panel
        mser = {ym: v for ym, v in mser.items() if ym in valid_yms}
        for ym in sorted(mser):
            rows.append({"cmc_id": cmc_id, "symbol": sym, "dl_slug": slug,
                         "month_end": ym_to_monthend[ym], "ym": ym,
                         "tvl_usd": mser[ym]})
        yms = sorted(mser)
        diag.append({"cmc_id": cmc_id, "symbol": sym, "dl_slug": slug,
                     "status": 200, "n_months": len(yms),
                     "ym_start": yms[0] if yms else None,
                     "ym_end": yms[-1] if yms else None,
                     "note": "ok" if yms else "empty series"})
        print(f"[{i:>3}/{len(tok)}] {sym:<8} {slug:<28} "
              f"months={len(yms):>3}  {yms[0] if yms else '-'}->{yms[-1] if yms else '-'}")

    # SESSION 027: chain-level TVL for canonical L2 governance tokens (Entry 68)
    for cmc_id, sym, chain in CHAIN_LEVEL:
        ser = fetch_chain(chain)
        tag = f"chain:{chain}"
        if not ser:
            diag.append({"cmc_id": cmc_id, "symbol": sym, "dl_slug": tag, "status": "ERR",
                         "n_months": 0, "ym_start": None, "ym_end": None, "note": "fetch failed"})
            print(f"[chain] {sym:<8} {tag:<28} FETCH FAIL")
            continue
        mser = monthly_last([{"date": p.get("date"), "totalLiquidityUSD": p.get("tvl")}
                             for p in ser])
        mser = {ym: v for ym, v in mser.items() if ym in valid_yms}
        for ym in sorted(mser):
            rows.append({"cmc_id": cmc_id, "symbol": sym, "dl_slug": tag,
                         "month_end": ym_to_monthend[ym], "ym": ym, "tvl_usd": mser[ym]})
        yms = sorted(mser)
        diag.append({"cmc_id": cmc_id, "symbol": sym, "dl_slug": tag, "status": 200,
                     "n_months": len(yms), "ym_start": yms[0] if yms else None,
                     "ym_end": yms[-1] if yms else None, "note": "ok" if yms else "empty series"})
        print(f"[chain] {sym:<8} {tag:<28} months={len(yms):>3}  "
              f"{yms[0] if yms else '-'}->{yms[-1] if yms else '-'}")

    out = pd.DataFrame(rows).sort_values(["cmc_id", "ym"])
    out.to_csv(OUT, index=False)
    dg = pd.DataFrame(diag).sort_values(["status", "symbol"])
    dg.to_csv(DIAG, index=False)

    print(f"\nwrote {OUT}")
    print(f"  asset-months: {len(out)} | distinct tokens with TVL: {out.cmc_id.nunique()}")
    if len(out):
        print(f"  month range: {out.ym.min()} -> {out.ym.max()}")
    n_empty = int((dg.note == "empty series").sum())
    n_fail = int((dg.note == "fetch failed").sum())
    print(f"  empty series: {n_empty} | fetch failed: {n_fail}")
    print(f"wrote {DIAG}")


if __name__ == "__main__":
    main()
