"""
phase2_pq_diagnostics.py  --  Phase 2 side diagnostics required by Entry 30/31:
TVL (capital stock) and Volume/TVL turnover, kept ALONGSIDE PQ (never AS PQ).

  Tokens : protocol TVL via /protocol/{slug}            (totalLiquidityUSD, month-end)
  Coins  : chain TVL    via /v2/historicalChainTvl/{chain}
  turnover = monthly PQ / month-end TVL   (a protocol/chain restatement of M*V=PQ, TVL ~ M)

Fees are also a named diagnostic (cost-of-intermediation/take-rate); token fee 30d totals are
already cached in _fees_overview.json (slug-level). Monthly fee series are not pulled here to keep
the call budget bounded -- TVL+turnover is the headline diagnostic Entry 30 specifies.

Output: 03_data/phase2/pq_diagnostics.csv  (cmc_id,symbol,month_end,pq_usd,tvl_usd,turnover,kind)
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
SLEEP = 0.15
sess = requests.Session(); sess.headers.update(H)


def get_json(url, cache_name):
    f = RAW / cache_name
    if f.exists():
        return json.loads(f.read_text())
    for t in range(4):
        try:
            r = sess.get(url, timeout=50); time.sleep(SLEEP)
            if r.status_code == 200:
                j = r.json(); f.write_text(json.dumps(j)); return j
            f.write_text(json.dumps({"_status": r.status_code})); return {"_status": r.status_code}
        except Exception:
            time.sleep(SLEEP * (t + 1) * 2)
    return {"_status": "err"}


def monthly_last(points, dkey, vkey):
    """list of {date/ts, value} -> {month_end: last value in month}."""
    out = {}
    for p in points or []:
        ts = p.get(dkey) if isinstance(p, dict) else None
        if ts is None:
            continue
        try:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:
            continue
        v = p.get(vkey) if isinstance(p, dict) else None
        if v is None:
            continue
        last = calendar.monthrange(dt.year, dt.month)[1]
        out[f"{dt.year:04d}-{dt.month:02d}-{last:02d}"] = float(v)  # last write wins = month-end
    return out


def main():
    tk = pd.read_csv(OUT / "pq_tokens.csv")
    cn = pd.read_csv(OUT / "pq_coins.csv")
    rung = pd.read_csv(REPO / "03_data" / "phase2_coin_rung_table.csv")
    rows = []

    # ---- token TVL ----
    for slug in tk[tk.pq_usd.notna()].dl_slug.dropna().unique():
        j = get_json(f"https://api.llama.fi/protocol/{slug}", f"tvl_token_{slug}.json")
        tvl = monthly_last(j.get("tvl") if isinstance(j, dict) else None, "date", "totalLiquidityUSD")
        sub = tk[(tk.dl_slug == slug) & tk.pq_usd.notna()]
        for _, r in sub.iterrows():
            t = tvl.get(r.month_end)
            rows.append({"cmc_id": int(r.cmc_id), "symbol": r.symbol, "month_end": r.month_end,
                         "pq_usd": r.pq_usd, "tvl_usd": t,
                         "turnover": (r.pq_usd / t if t and t > 0 else None), "kind": "token_protocol"})

    # ---- coin (chain) TVL ----
    r1 = rung[rung.rung == "R1"]
    cn_pq = cn[cn.pq_usd.notna()]
    for ch in r1.dl_chain.dropna().unique():
        j = get_json(f"https://api.llama.fi/v2/historicalChainTvl/{ch.replace(' ', '%20')}",
                     f"tvl_chain_{ch.replace('/','_').replace(' ','_')}.json")
        tvl = monthly_last(j if isinstance(j, list) else None, "date", "tvl")
        cids = r1[r1.dl_chain == ch].cmc_id.tolist()
        sub = cn_pq[cn_pq.cmc_id.isin(cids)]
        for _, r in sub.iterrows():
            t = tvl.get(r.month_end)
            rows.append({"cmc_id": int(r.cmc_id), "symbol": r.symbol, "month_end": r.month_end,
                         "pq_usd": r.pq_usd, "tvl_usd": t,
                         "turnover": (r.pq_usd / t if t and t > 0 else None), "kind": "coin_chain"})

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "pq_diagnostics.csv", index=False)
    have = df[df.turnover.notna()]
    print(f"diagnostics rows: {len(df)}  with turnover: {len(have)}  assets: {df.cmc_id.nunique()}")
    print(f"turnover (monthly PQ / month-end TVL): median {have.turnover.median():.3f}  "
          f"p90 {have.turnover.quantile(.9):.3f}")
    print(f"Wrote {OUT/'pq_diagnostics.csv'}")


if __name__ == "__main__":
    main()
