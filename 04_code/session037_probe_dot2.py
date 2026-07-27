import json, requests

key = json.loads(open("04_code/.api_keys.json").read())["subscan"]
H = {"Content-Type": "application/json", "X-API-Key": key}
BASE = "https://polkadot.api.subscan.io"

def post(path, payload):
    try:
        r = requests.post(BASE + path, headers=H, json=payload, timeout=30)
        return r.status_code, r.text[:800]
    except Exception as ex:
        return "ERR", str(ex)[:200]

candidates = [
    ("/api/scan/staking/eras", {"row": 2, "page": 0}),
    ("/api/v2/scan/staking/eras", {"row": 2, "page": 0}),
    ("/api/scan/staking/era_list", {"row": 2, "page": 0}),
    ("/api/scan/daily", {"start": "2024-01-01", "end": "2024-01-05", "format": "day", "category": "Bonded"}),
    ("/api/scan/daily", {"start": "2024-01-01", "end": "2024-01-05", "format": "day", "category": "bonded"}),
    ("/api/scan/staking/overview", {}),
]
for path, payload in candidates:
    code, body = post(path, payload)
    print(f"\n=== {path} {payload.get('category','')} -> {code}")
    print(body)

# block 1 timestamp (real genesis ts)
code, body = post("/api/scan/block", {"block_num": 1})
print("\n=== block 1:", code, body[:400])
