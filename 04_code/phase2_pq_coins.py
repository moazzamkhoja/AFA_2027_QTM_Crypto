"""
phase2_pq_coins.py  --  Phase 2 PART B: coin PQ via the Entry 32 source ladder (covered rungs).

Per CLAUDE_CODE_PHASE2_PQ_BUILD_PROMPT.md Part B + the Step-B1 verification
(03_data/PHASE2_COIN_PQ_VERIFICATION_B1.md, rung table 03_data/phase2_coin_rung_table.csv):

  Rung 1  -> DeFiLlama chain DEX volume  /overview/dexs/{chain}  (non-degenerate: 30d vol/mcap>=0.01)
  Rung 3  -> blockchain.com Estimated Transaction Value (USD), BTC only (change-excluded)
  GAP-R2  -> 81 material coins whose only ladder option was Artemis Settlement Volume, which is
             PAID-ONLY (B1). PQ=NaN, flagged 'GAP: Artemis paid-only' -> deferred to Phase 2b.
  NaN     -> non-material coins with no free transacted-value source (expected).

Rung 4 (DeFiLlama chain fees) is NOT auto-applied here: per Entry 30/32 it is a toll proxy of
last resort that must be explicitly approved, never blended in silently. No coin is dropped to
Rung 4 in this build; uncovered coins are flagged for Phase 2b instead.

Output: 03_data/phase2/pq_coins.csv (long: cmc_id,symbol,month_end,pq_usd,pq_source,rung,note)
Caches raw charts under 03_data/raw/defillama/phase2/ (gitignored).
"""
import json, time, calendar
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
H = {"User-Agent": "Mozilla/5.0"}
RAW = REPO / "03_data" / "raw" / "defillama" / "phase2"
OUT = REPO / "03_data" / "phase2"
OUT.mkdir(parents=True, exist_ok=True)
SLEEP = 0.15
sess = requests.Session(); sess.headers.update(H)
CALLS = {"n": 0}


def get_json(url, cache_name, **params):
    f = RAW / cache_name
    if f.exists():
        return json.loads(f.read_text())
    for t in range(4):
        try:
            r = sess.get(url, params=params, timeout=50)
            CALLS["n"] += 1
            time.sleep(SLEEP)
            if r.status_code == 200:
                j = r.json(); f.write_text(json.dumps(j)); return j
            f.write_text(json.dumps({"_status": r.status_code})); return {"_status": r.status_code}
        except Exception:
            time.sleep(SLEEP * (t + 1) * 2)
    return {"_status": "err"}


def chart_to_monthly(chart, vidx=1):
    out = {}
    for row in chart or []:
        if not isinstance(row, list) or len(row) <= vidx or row[vidx] is None:
            continue
        try:
            dt = datetime.fromtimestamp(int(row[0]), tz=timezone.utc)
        except Exception:
            continue
        last = calendar.monthrange(dt.year, dt.month)[1]
        out[f"{dt.year:04d}-{dt.month:02d}-{last:02d}"] = out.get(
            f"{dt.year:04d}-{dt.month:02d}-{last:02d}", 0.0) + float(row[vidx])
    return out


def main():
    rung = pd.read_csv(REPO / "03_data" / "phase2_coin_rung_table.csv")
    rows = []

    # ---- Rung 1: DeFiLlama chain DEX daily volume -> monthly ----
    r1 = rung[rung.rung == "R1"]
    chains = sorted(r1.dl_chain.dropna().unique())
    chain_monthly = {}
    for ch in chains:
        j = get_json(f"https://api.llama.fi/overview/dexs/{ch}",
                     f"dexchart_{ch.replace('/','_').replace(' ','_')}.json",
                     excludeTotalDataChartBreakdown="true")
        chain_monthly[ch] = chart_to_monthly(j.get("totalDataChart")) if isinstance(j, dict) else {}
        print(f"  R1 chain {ch:18} months={len(chain_monthly[ch])}")
    for _, c in r1.iterrows():
        mm = chain_monthly.get(c.dl_chain, {})
        if mm:
            for m, v in sorted(mm.items()):
                rows.append({"cmc_id": int(c.cmc_id), "symbol": c.symbol, "month_end": m,
                             "pq_usd": v, "pq_source": "defillama_chain_dex", "rung": "R1",
                             "note": f"chain={c.dl_chain}; mat_ratio={c.mat_ratio:.4f}"})
        else:
            rows.append({"cmc_id": int(c.cmc_id), "symbol": c.symbol, "month_end": None,
                         "pq_usd": float("nan"), "pq_source": "NaN:r1_chart_empty", "rung": "R1",
                         "note": f"chain={c.dl_chain} had no daily DEX chart"})

    # ---- Rung 3: BTC blockchain.com Estimated Transaction Value (USD) ----
    btc = rung[rung.rung == "R3-BTC"]
    if len(btc):
        j = get_json("https://api.blockchain.info/charts/estimated-transaction-volume-usd",
                     "btc_etv_usd.json", timespan="all", format="json", sampled="false")
        vals = j.get("values", []) if isinstance(j, dict) else []
        mm = chart_to_monthly([[v["x"], v["y"]] for v in vals]) if vals else {}
        # blockchain.com daily-sampled: chart_to_monthly summed per-day points -> monthly tx value
        cid = int(btc.iloc[0].cmc_id)
        for m, v in sorted(mm.items()):
            rows.append({"cmc_id": cid, "symbol": "BTC", "month_end": m, "pq_usd": v,
                         "pq_source": "blockchain.com_est_tx_value", "rung": "R3-BTC",
                         "note": "Estimated Transaction Value USD, change-excluded"})
        print(f"  R3 BTC months={len(mm)}")

    # ---- GAP-R2 + NaN: flag, do not fabricate ----
    for _, c in rung[rung.rung.isin(["GAP-R2", "NaN"])].iterrows():
        src = "GAP:artemis_paid_only" if c.rung == "GAP-R2" else "NaN:no_free_source"
        rows.append({"cmc_id": int(c.cmc_id), "symbol": c.symbol, "month_end": None,
                     "pq_usd": float("nan"), "pq_source": src, "rung": c.rung,
                     "note": c.rung_reason})

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "pq_coins.csv", index=False)
    have = df[df.pq_usd.notna()]
    print(f"\nCoins with >=1 PQ month: {have.cmc_id.nunique()}  ({have.symbol.nunique()} symbols)")
    print("By rung (distinct coins, with PQ):")
    print(have.groupby('rung').cmc_id.nunique())
    print(f"\nTotal API calls this run: {CALLS['n']}")
    print(f"Wrote {OUT/'pq_coins.csv'} ({len(df)} rows)")


if __name__ == "__main__":
    main()
