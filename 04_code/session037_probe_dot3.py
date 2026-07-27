import json, requests

key = json.loads(open("04_code/.api_keys.json").read())["subscan"]
H = {"Content-Type": "application/json", "X-API-Key": key}
BASE = "https://polkadot.api.subscan.io"

def post(path, payload):
    r = requests.post(BASE + path, headers=H, json=payload, timeout=30)
    return r.status_code, r.text[:1000]

for cat in ["Bonded", "Unbond", "XXXNONSENSE"]:
    code, body = post("/api/scan/daily",
        {"start": "2026-07-20", "end": "2026-07-26", "format": "day", "category": cat})
    print(f"\n=== daily {cat} -> {code}\n{body}")

# what window is allowed? binary-ish probe
for start in ["2026-07-01", "2026-06-01", "2026-04-01", "2026-01-01", "2025-07-01"]:
    code, body = post("/api/scan/daily",
        {"start": start, "end": "2026-07-26", "format": "day", "category": "Bonded"})
    ok = '"code":0' in body
    print(f"start {start}: {code} ok={ok} {'' if ok else body[:120]}")
