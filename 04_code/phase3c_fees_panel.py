"""
phase3c_fees_panel.py -- Phase 3c Task A: monthly protocol fees + revenue panel
for the 101 regression-sample tokens (spec 8.7 as amended: TOKENS ONLY).

Source: DeFiLlama fees API (free/keyless, verified live 2026-08-04):
  api.llama.fi/summary/fees/{slug}?dataType=dailyFees     -> what users pay the protocol
  api.llama.fi/summary/fees/{slug}?dataType=dailyRevenue  -> share accruing to protocol/treasury/holders
Both return totalDataChart = [[unix_ts, usd], ...] daily. A 400 means no fee adapter
exists for that slug (protocol does not report) -- recorded, not an error.

Slug identity: cmc_id -> dl_slug from 03_data/phase2/tvl_panel.csv (the authoritative
map actually used in the NV/TVL build, incl. the Entry-68/84 chain-level entries).
Joins on cmc_id only. 'chain:{Name}' slugs map to the DL chain fee adapters
(verified live: arbitrum, metis, apechain, blast) -- flagged chain_level in
source_notes; for L2 gov tokens chain fees = sequencer fees (DAO-accruing),
consistent with the chain-level TVL denominator precedent.

Monthly sum by calendar month, labeled by calendar month-end (universe_panel
convention). The trailing (incomplete) calendar month is dropped. n_days kept
as a diagnostic column so downstream can see partial launch months.

Output: 03_data/phase3/fees_revenue_panel.csv
  (cmc_id, symbol, month_end, fees_usd, revenue_usd, n_days_fees, n_days_rev,
   dl_fees_slug, source_notes)
Raw cache: 03_data/raw/phase3c/fees/{slug}__{dataType}.json
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "03_data" / "raw" / "phase3c" / "fees"
RAW.mkdir(parents=True, exist_ok=True)
OUT = REPO / "03_data" / "phase3" / "fees_revenue_panel.csv"
COV = REPO / "03_data" / "phase3" / "tables" / "fees_coverage.csv"

S = requests.Session()
S.headers.update({"User-Agent": "afa-2027-qtm-research (academic, free-tier)"})

CHAIN_SLUG = {"chain:Arbitrum": "arbitrum", "chain:Metis": "metis",
              "chain:ApeChain": "apechain", "chain:Blast": "blast"}


def fetch(slug, data_type):
    """Return (status, [[ts, usd], ...] or None); caches to RAW."""
    cf = RAW / f"{slug}__{data_type}.json"
    if cf.exists():
        payload = json.loads(cf.read_text())
        return payload["status"], payload.get("chart")
    for i in range(3):
        try:
            r = S.get(f"https://api.llama.fi/summary/fees/{slug}?dataType={data_type}",
                      timeout=90)
        except Exception:
            time.sleep(2.0 + 2 * i)
            continue
        if r.status_code == 429:
            time.sleep(5.0 + 3 * i)
            continue
        chart = r.json().get("totalDataChart") if r.status_code == 200 else None
        cf.write_text(json.dumps({"status": r.status_code, "chart": chart}))
        time.sleep(0.4)
        return r.status_code, chart
    return "ERR", None


def monthly(chart):
    """Daily [[ts, usd]] -> DataFrame(month_end, usd, n_days); drops incomplete last month."""
    if not chart:
        return pd.DataFrame(columns=["month_end", "usd", "n_days"])
    df = pd.DataFrame(chart, columns=["ts", "usd"])
    df["date"] = pd.to_datetime(df["ts"], unit="s")
    df["month_end"] = df["date"] + pd.offsets.MonthEnd(0)
    g = df.groupby("month_end").agg(usd=("usd", "sum"), n_days=("usd", "size")).reset_index()
    last_date = df["date"].max()
    if last_date < last_date + pd.offsets.MonthEnd(0):  # month in progress
        g = g[g.month_end < last_date + pd.offsets.MonthEnd(0)]
    return g


def main():
    rp = pd.read_csv(REPO / "03_data" / "phase3" / "regression_panel.csv")
    tok_ids = sorted(rp[rp.track == "token"].cmc_id.unique())
    tvl = pd.read_csv(REPO / "03_data" / "phase2" / "tvl_panel.csv")
    smap = (tvl[tvl.cmc_id.isin(tok_ids)][["cmc_id", "symbol", "dl_slug"]]
            .drop_duplicates().set_index("cmc_id"))
    assert len(smap) == len(tok_ids), "slug map must be 1:1 on the token sample"

    rows, cov = [], []
    for cmc_id in tok_ids:
        sym, dl_slug = smap.loc[cmc_id, "symbol"], smap.loc[cmc_id, "dl_slug"]
        chain_level = dl_slug.startswith("chain:")
        slug = CHAIN_SLUG[dl_slug] if chain_level else dl_slug
        st_f, chart_f = fetch(slug, "dailyFees")
        st_r, chart_r = fetch(slug, "dailyRevenue")
        mf, mr = monthly(chart_f), monthly(chart_r)
        note = ("chain_level_sequencer_fees" if chain_level else "protocol_fees")
        if st_f != 200:
            note += f";fees_http_{st_f}"
        if st_r != 200:
            note += f";revenue_http_{st_r}"
        m = mf.rename(columns={"usd": "fees_usd", "n_days": "n_days_fees"}).merge(
            mr.rename(columns={"usd": "revenue_usd", "n_days": "n_days_rev"}),
            on="month_end", how="outer").sort_values("month_end")
        m["cmc_id"], m["symbol"], m["dl_fees_slug"], m["source_notes"] = cmc_id, sym, slug, note
        rows.append(m)
        cov.append({"cmc_id": cmc_id, "symbol": sym, "slug": slug,
                    "chain_level": chain_level,
                    "fees_status": st_f, "rev_status": st_r,
                    "fees_months": len(mf), "rev_months": len(mr),
                    "fees_start": mf.month_end.min() if len(mf) else pd.NaT,
                    "rev_start": mr.month_end.min() if len(mr) else pd.NaT})
        print(f"{sym:8s} {slug:28s} fees {st_f} {len(mf):3d}m  rev {st_r} {len(mr):3d}m")

    panel = pd.concat(rows, ignore_index=True)
    panel = panel[["cmc_id", "symbol", "month_end", "fees_usd", "revenue_usd",
                   "n_days_fees", "n_days_rev", "dl_fees_slug", "source_notes"]]
    panel.to_csv(OUT, index=False)
    covdf = pd.DataFrame(cov)
    COV.parent.mkdir(parents=True, exist_ok=True)
    covdf.to_csv(COV, index=False)

    print(f"\ntokens with fees: {(covdf.fees_months > 0).sum()}/101   "
          f"with revenue: {(covdf.rev_months > 0).sum()}/101")
    print(f"fees but NO revenue: {((covdf.fees_months > 0) & (covdf.rev_months == 0)).sum()}")
    have = covdf[covdf.fees_months > 0]
    print(f"months/token (fees): median {have.fees_months.median():.0f}  "
          f"min {have.fees_months.min()}  max {have.fees_months.max()}")
    print(f"earliest fee start: {have.fees_start.min()}  latest: {have.fees_start.max()}")
    print(f"\nWrote {OUT} ({len(panel):,} rows) and {COV}")


if __name__ == "__main__":
    main()
