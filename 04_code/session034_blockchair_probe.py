# Session 034 Task B probe: Blockchair XTZ (tezos) + MATIC (polygon) native transfer volume.
import requests, time, json, sys

def blockchair_get(url, params=None):
    r = requests.get(url, params=params, timeout=30,
                     headers={"User-Agent": "academic-research/1.0"})
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"raw": r.text[:300]}

print("=== Tezos entity probes ===")
for entity in ["calls", "operations", "transactions"]:
    url = f"https://api.blockchair.com/tezos/{entity}"
    st, r = blockchair_get(url, {"a": "sum(amount)", "q": "time(2024-01)", "limit": 1})
    ctx = r.get("context", {})
    print(f"tezos/{entity}: http={st} code={ctx.get('code')} error={ctx.get('error')} data={r.get('data')}")
    time.sleep(1.5)

print("=== Polygon probe ===")
st, r = blockchair_get("https://api.blockchair.com/polygon/transactions",
                       {"a": "sum(value)", "q": "time(2024-01)", "limit": 1})
ctx = r.get("context", {})
print(f"polygon/transactions: http={st} code={ctx.get('code')} error={ctx.get('error')} data={r.get('data')}")
time.sleep(1.5)

print("=== BTC-default guard reference (bitcoin sum(output_total) 2024-01) ===")
st, r = blockchair_get("https://api.blockchair.com/bitcoin/transactions",
                       {"a": "sum(output_total)", "q": "time(2024-01)", "limit": 1})
ctx = r.get("context", {})
print(f"bitcoin/transactions: http={st} code={ctx.get('code')} error={ctx.get('error')} data={r.get('data')}")
