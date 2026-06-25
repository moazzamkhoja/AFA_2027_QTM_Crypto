"""
dune_pilot_verify.py -- STAGE 4: fix the LDO price join (canonical WETH contract, not
symbol='WETH' which is contaminated by scam tokens -> $767/ETH artifact), and pull
INDEPENDENT cross-check references for all three from DeFiLlama (keyless, free), per the
Entry 31 "verify before trusting" standard.
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

WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"


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
                          "datapoints": meta.get("datapoint_count"), "ms": meta.get("execution_time_millis")})
            (OUTDIR / f"verify_{label}.json").write_text(json.dumps(data, indent=2))
            return data
        time.sleep(poll_s); waited += poll_s
    return {"state": "TIMED_OUT"}


def rows_of(d):
    return ((d.get("result") or {}).get("rows")) or []


# ---- LDO: corrected price join + show contaminated-vs-clean price side by side ----
LDO_SQL = f"""
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
  WHERE blockchain = 'ethereum' AND contract_address = {WETH}
    AND "timestamp" > NOW() - INTERVAL '32' DAY GROUP BY 1
)
SELECT
  COALESCE(SUM(s.eth_in), 0) AS eth_in,
  COALESCE(SUM(c.eth_out), 0) AS eth_out,
  COALESCE(SUM(s.eth_in * p.eth_usd), 0) AS usd_in,
  COALESCE(SUM(c.eth_out * p.eth_usd), 0) AS usd_out,
  AVG(p.eth_usd) AS avg_eth_px, MIN(p.d) AS d0, MAX(p.d) AS d1
FROM px p
LEFT JOIN submit s ON s.d = p.d
LEFT JOIN claim c ON c.d = p.d
WHERE p.d > CAST(date_trunc('day', NOW()) AS date) - INTERVAL '30' DAY
"""

# diagnostic: how many distinct contracts masquerade as symbol='WETH' and their price spread
WETH_CONTAM_SQL = """
SELECT COUNT(DISTINCT contract_address) AS n_contracts_symbol_weth,
       MIN(price) AS min_px, MAX(price) AS max_px, AVG(price) AS avg_px
FROM prices.day
WHERE blockchain='ethereum' AND symbol='WETH' AND "timestamp" > NOW() - INTERVAL '32' DAY
"""


def dl_get(url):
    try:
        r = requests.get(url, timeout=40)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:300])
    except Exception as e:
        return "ERR", str(e)


def main():
    print("=== LDO corrected (canonical WETH contract) ===")
    l = execute_sql("LDO_fixed", LDO_SQL)
    for r in rows_of(l):
        print("  ", r)

    print("\n=== WETH symbol contamination diagnostic ===")
    c = execute_sql("WETH_contam", WETH_CONTAM_SQL)
    for r in rows_of(c):
        print("  ", r)

    print("\n=== EXTERNAL CROSS-CHECKS (DeFiLlama, keyless) ===")
    refs = {}

    # ETH spot price (sanity for LDO price join)
    sc, body = dl_get(f"https://coins.llama.fi/prices/current/ethereum:{WETH}")
    refs["eth_price_now"] = {"status": sc, "body": body}
    print("ETH price now:", sc, body)

    # Aave v3 protocol (per-chain borrowed outstanding for order-of-magnitude on origination)
    sc, body = dl_get("https://api.llama.fi/protocol/aave-v3")
    if sc == 200 and isinstance(body, dict):
        cur = body.get("currentChainTvls", {})
        eth_borrowed = cur.get("Ethereum-borrowed")
        eth_tvl = cur.get("Ethereum")
        refs["aave_v3"] = {"status": sc, "Ethereum-borrowed": eth_borrowed, "Ethereum-tvl": eth_tvl,
                           "chains_with_borrowed": [k for k in cur if k.endswith("-borrowed")][:20]}
        print("Aave v3 currentChainTvls Ethereum-borrowed:", eth_borrowed, "| Ethereum TVL:", eth_tvl)
    else:
        refs["aave_v3"] = {"status": sc, "body": body if not isinstance(body, dict) else "dict"}
        print("Aave v3:", sc)

    # Gains derivatives summary (test whether perps dimension is 402 on the per-protocol endpoint too)
    for u in [
        "https://api.llama.fi/summary/derivatives/gains-network?dataType=dailyVolume",
        "https://api.llama.fi/overview/derivatives/gains-network",
    ]:
        sc, body = dl_get(u)
        key = "gains_" + u.split("/")[-1][:20]
        if sc == 200 and isinstance(body, dict):
            refs[key] = {"status": sc, "total30dVolume": body.get("total30d"),
                         "totalAllTime": body.get("totalAllTime"), "name": body.get("name")}
            print(f"{u} -> 200 total30d={body.get('total30d')}")
        else:
            refs[key] = {"status": sc, "body": body if not isinstance(body, dict) else "dict"}
            print(f"{u} -> {sc}")

    (OUTDIR / "verify_external_refs.json").write_text(json.dumps(refs, indent=2))
    (OUTDIR / "verify_calls.json").write_text(json.dumps(CALLS, indent=2))
    print("\n=== EXECUTE CALL LOG ===")
    for c in CALLS:
        print("  ", c)


if __name__ == "__main__":
    main()
