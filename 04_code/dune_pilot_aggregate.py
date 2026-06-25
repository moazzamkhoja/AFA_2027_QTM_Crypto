"""
dune_pilot_aggregate.py -- STAGE 3: the actual trailing-30d aggregations, on the
manually-mapped NORMALIZED tables (see dune_pilot_explore.py for how these were chosen):

  AAVE -> lending.borrow            (spell; project='aave', blockchain='ethereum'; amount_usd)
  GNS  -> dune.gains.result_g_trade_stats_defi_llama  (gains' own DeFiLlama-feed; daily_volume)
  LDO  -> lido_ethereum.steth_evt_submitted (stake ETH in)
          + lido_ethereum.withdrawalqueueerc721_evt_withdrawalclaimed (unstake ETH out)
          x prices.day WETH/ethereum  (ETH->USD)

Every /sql/execute is logged with tier + datapoint_count + ms so credits can be reported.
"""
import json, time
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
OUTDIR = REPO / "03_data" / "raw" / "dune_pilot"
BASE = "https://api.dune.com/api/v1"
HEADERS = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

CALLS = []


def execute_sql(label, sql, performance="small", max_wait_s=180, poll_s=2):
    r = requests.post(f"{BASE}/sql/execute", headers=HEADERS,
                      json={"sql": sql, "performance": performance}, timeout=40)
    r.raise_for_status()
    eid = r.json()["execution_id"]
    waited = 0
    while waited < max_wait_s:
        s = requests.get(f"{BASE}/execution/{eid}/results", headers=HEADERS, timeout=40)
        data = s.json()
        st = data.get("state", "")
        if data.get("is_execution_finished") or st.endswith("COMPLETED") or st.endswith("FAILED"):
            meta = (data.get("result") or {}).get("metadata") or {}
            CALLS.append({"label": label, "tier": performance, "state": st,
                          "datapoints": meta.get("datapoint_count"),
                          "ms": meta.get("execution_time_millis")})
            (OUTDIR / f"agg2_{label}.json").write_text(json.dumps(data, indent=2))
            return data
        time.sleep(poll_s); waited += poll_s
    CALLS.append({"label": label, "tier": performance, "state": "TIMED_OUT"})
    return {"state": "TIMED_OUT", "execution_id": eid}


def rows_of(d):
    return ((d.get("result") or {}).get("rows")) or []


AAVE_SQL = """
SELECT transaction_type, version, COUNT(*) AS n, SUM(amount_usd) AS usd
FROM lending.borrow
WHERE project = 'aave' AND blockchain = 'ethereum'
  AND block_time > NOW() - INTERVAL '30' DAY
GROUP BY 1, 2
ORDER BY usd DESC
"""

GNS_SQL = """
SELECT blockchain, COUNT(*) AS n_days, MIN(day) AS d0, MAX(day) AS d1,
       SUM(daily_volume) AS total_vol, SUM(crypto_volume) AS crypto, SUM(forex_volume) AS forex,
       SUM(stocks_volume) AS stocks, SUM(indices_volume) AS indices,
       SUM(commodities_volume) AS commodities, SUM(trades) AS trades
FROM dune.gains.result_g_trade_stats_defi_llama
WHERE day > NOW() - INTERVAL '30' DAY
GROUP BY 1
ORDER BY total_vol DESC
"""

LDO_SQL = """
WITH submit AS (
  SELECT evt_block_date AS d, SUM(CAST(amount AS double))/1e18 AS eth_in
  FROM lido_ethereum.steth_evt_submitted
  WHERE evt_block_time > NOW() - INTERVAL '30' DAY GROUP BY 1
),
claim AS (
  SELECT evt_block_date AS d, SUM(CAST("amountOfETH" AS double))/1e18 AS eth_out
  FROM lido_ethereum.withdrawalqueueerc721_evt_withdrawalclaimed
  WHERE evt_block_time > NOW() - INTERVAL '30' DAY GROUP BY 1
),
px AS (
  SELECT CAST(date_trunc('day', "timestamp") AS date) AS d, AVG(price) AS eth_usd
  FROM prices.day
  WHERE blockchain = 'ethereum' AND symbol = 'WETH'
    AND "timestamp" > NOW() - INTERVAL '32' DAY GROUP BY 1
)
SELECT
  COALESCE(SUM(s.eth_in), 0) AS eth_in,
  COALESCE(SUM(c.eth_out), 0) AS eth_out,
  COALESCE(SUM(s.eth_in * p.eth_usd), 0) AS usd_in,
  COALESCE(SUM(c.eth_out * p.eth_usd), 0) AS usd_out,
  MIN(p.d) AS d0, MAX(p.d) AS d1
FROM px p
LEFT JOIN submit s ON s.d = p.d
LEFT JOIN claim c ON c.d = p.d
WHERE p.d > CAST(date_trunc('day', NOW()) AS date) - INTERVAL '30' DAY
"""


def main():
    print("=== AAVE (lending.borrow, ethereum) ===")
    a = execute_sql("AAVE", AAVE_SQL)
    for r in rows_of(a):
        print("  ", r)

    print("\n=== GNS (gains defillama-feed) ===")
    g = execute_sql("GNS", GNS_SQL)
    for r in rows_of(g):
        print("  ", r)

    print("\n=== LDO (submit + withdrawalclaimed x WETH price) ===")
    l = execute_sql("LDO", LDO_SQL)
    for r in rows_of(l):
        print("  ", r)

    print("\n=== CALL LOG (executes) ===")
    for c in CALLS:
        print("  ", c)
    (OUTDIR / "agg2_calls.json").write_text(json.dumps(CALLS, indent=2))


if __name__ == "__main__":
    main()
