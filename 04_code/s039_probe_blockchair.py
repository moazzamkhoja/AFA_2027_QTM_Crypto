# Session 039 Task A4: Blockchair Polkadot/Kusama stats + aggregation probe (keyless)
import requests, json, time

for chain in ["polkadot", "kusama"]:
    try:
        r = requests.get(f"https://api.blockchair.com/{chain}/stats", timeout=20)
        print(f"{chain}/stats: {r.status_code} {r.text[:400]}")
    except Exception as e:
        print(f"{chain}/stats EXC: {e}")
    time.sleep(2)
    try:
        r = requests.get(f"https://api.blockchair.com/{chain}/calls",
                         params={"a": "date(time),sum(value)", "q": "type(transfer)"},
                         timeout=30)
        print(f"{chain}/calls agg: {r.status_code} {r.text[:400]}")
    except Exception as e:
        print(f"{chain}/calls EXC: {e}")
    time.sleep(2)
