"""
dune_dryrun_fullpanel.py -- SESSION 016, STEP 2: full-history, full-panel grouped
queries on the FREE `small` engine ONLY. This is the actual feasibility data point:
does `small` finish a multi-year monthly-grouped scan (the pilot only tested 30 days)?

Covered protocols (from Step 1 coverage check):
  Lending      -> lending.borrow, GROUP BY project, month, project IN ('aave','strike')
                  (AAVE + STRK are our covered NaN lending tokens; full history)
  Liquid Stk   -> Lido submit + withdrawalclaimed x prices.day on CANONICAL WETH contract
                  (never symbol='WETH' -- Entry 36 trap), GROUP BY month, full history
  Derivatives  -> dune.gains.result_g_trade_stats_defi_llama, GROUP BY month, full history

Records wall-clock seconds, engine ms, and row count for each. Notes explicitly any
timeout / row cap / Dune error -- that is the result this dry-run exists to produce.
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

WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
CALLS = []


def execute_sql(label, sql, performance="small", max_wait_s=290, poll_s=5):
    t0 = time.time()
    try:
        r = requests.post(f"{BASE}/sql/execute", headers=HEADERS,
                          json={"sql": sql, "performance": performance}, timeout=40)
        r.raise_for_status()
    except requests.HTTPError as e:
        body = e.response.text[:400] if e.response is not None else str(e)
        rec = {"label": label, "tier": performance, "state": "HTTP_ERROR",
               "http_status": e.response.status_code if e.response is not None else None,
               "body": body, "wall_s": round(time.time() - t0, 1)}
        CALLS.append(rec); print("  HTTP ERROR:", rec); return {"state": "HTTP_ERROR"}
    eid = r.json()["execution_id"]
    waited = 0
    while waited < max_wait_s:
        s = requests.get(f"{BASE}/execution/{eid}/results", headers=HEADERS, timeout=40)
        data = s.json()
        st = data.get("state", "")
        if data.get("is_execution_finished") or st.endswith("COMPLETED") or st.endswith("FAILED"):
            res = data.get("result") or {}
            meta = res.get("metadata") or {}
            rec = {"label": label, "tier": performance, "state": st,
                   "rows_returned": len(res.get("rows") or []),
                   "total_row_count": meta.get("total_row_count"),
                   "result_set_truncated": meta.get("result_set_bytes_truncated") or meta.get("datapoints_truncated"),
                   "datapoints": meta.get("datapoint_count"),
                   "engine_ms": meta.get("execution_time_millis"),
                   "wall_s": round(time.time() - t0, 1),
                   "error": data.get("error")}
            CALLS.append(rec)
            (OUTDIR / f"full_{label}.json").write_text(json.dumps(data, indent=2))
            print(f"  {st} | rows={rec['rows_returned']} total={rec['total_row_count']} "
                  f"engine_ms={rec['engine_ms']} wall_s={rec['wall_s']}")
            if data.get("error"):
                print("  ERROR payload:", data.get("error"))
            return data
        time.sleep(poll_s); waited += poll_s
    rec = {"label": label, "tier": performance, "state": "CLIENT_TIMED_OUT_290s",
           "wall_s": round(time.time() - t0, 1)}
    CALLS.append(rec); print("  CLIENT TIMEOUT:", rec)
    return {"state": "TIMED_OUT"}


def rows_of(d):
    return ((d.get("result") or {}).get("rows")) or []


LEND_SQL = """
SELECT project,
       date_trunc('month', block_time) AS block_month,
       COUNT(*) AS n_borrows,
       SUM(amount_usd) AS borrow_usd
FROM lending.borrow
WHERE blockchain = 'ethereum'
  AND project IN ('aave', 'strike')
GROUP BY 1, 2
ORDER BY 1, 2
"""

GNS_SQL = """
SELECT date_trunc('month', day) AS block_month,
       COUNT(*) AS n_days,
       SUM(daily_volume) AS notional_usd,
       SUM(trades) AS trades
FROM dune.gains.result_g_trade_stats_defi_llama
GROUP BY 1
ORDER BY 1
"""

LDO_SQL = f"""
WITH submit AS (
  SELECT evt_block_date AS d, SUM(CAST(amount AS double))/1e18 AS eth_in
  FROM lido_ethereum.steth_evt_submitted GROUP BY 1
),
claim AS (
  SELECT evt_block_date AS d, SUM(CAST("amountOfETH" AS double))/1e18 AS eth_out
  FROM lido_ethereum.withdrawalqueueerc721_evt_withdrawalclaimed GROUP BY 1
),
px AS (
  SELECT CAST(date_trunc('day', "timestamp") AS date) AS d, AVG(price) AS eth_usd
  FROM prices.day
  WHERE blockchain = 'ethereum' AND contract_address = {WETH}
  GROUP BY 1
)
SELECT date_trunc('month', p.d) AS block_month,
       COALESCE(SUM(s.eth_in), 0) AS eth_in,
       COALESCE(SUM(c.eth_out), 0) AS eth_out,
       COALESCE(SUM(s.eth_in * p.eth_usd), 0) AS usd_in,
       COALESCE(SUM(c.eth_out * p.eth_usd), 0) AS usd_out
FROM px p
LEFT JOIN submit s ON s.d = p.d
LEFT JOIN claim c ON c.d = p.d
GROUP BY 1
ORDER BY 1
"""


def main():
    print("=== [1/3] LENDING full history: lending.borrow GROUP BY project,month (aave,strike) ===")
    d = execute_sql("lending_fullhist", LEND_SQL)
    rs = rows_of(d)
    if rs:
        proj = {}
        for r in rs:
            proj.setdefault(r["project"], []).append(r)
        for p, lst in proj.items():
            months = [r["block_month"][:7] for r in lst]
            tot = sum((r["borrow_usd"] or 0) for r in lst)
            print(f"   {p}: {len(lst)} months {min(months)}..{max(months)}  sum_borrow=${tot/1e9:.2f}B")

    print("\n=== [2/3] DERIVATIVES full history: gains defillama-feed GROUP BY month ===")
    d = execute_sql("gns_fullhist", GNS_SQL)
    rs = rows_of(d)
    if rs:
        months = [r["block_month"][:7] for r in rs]
        tot = sum((r["notional_usd"] or 0) for r in rs)
        print(f"   GNS: {len(rs)} months {min(months)}..{max(months)}  sum_notional=${tot/1e9:.2f}B")

    print("\n=== [3/3] LIQUID STAKING full history: Lido submit+claim x canonical-WETH price ===")
    d = execute_sql("ldo_fullhist", LDO_SQL)
    rs = rows_of(d)
    if rs:
        months = [r["block_month"][:7] for r in rs]
        tin = sum((r["usd_in"] or 0) for r in rs)
        tout = sum((r["usd_out"] or 0) for r in rs)
        print(f"   LDO: {len(rs)} months {min(months)}..{max(months)}  stake=${tin/1e9:.2f}B unstake=${tout/1e9:.2f}B")

    (OUTDIR / "fullpanel_calls.json").write_text(json.dumps(CALLS, indent=2))
    print("\n=== EXECUTE LOG (the feasibility data point) ===")
    for c in CALLS:
        print("  ", c)


if __name__ == "__main__":
    main()
