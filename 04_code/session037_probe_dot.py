import json, requests

key = json.loads(open("04_code/.api_keys.json").read())["subscan"]

r = requests.post(
    "https://polkadot.api.subscan.io/api/scan/staking/era_stat",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"row": 2, "page": 0}, timeout=30
)
print(json.dumps(r.json(), indent=2)[:3000])

r0 = requests.post(
    "https://polkadot.api.subscan.io/api/scan/block",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"block_num": 0}, timeout=30
)
print("DOT genesis block:", json.dumps(r0.json().get("data"), indent=2)[:2000])
