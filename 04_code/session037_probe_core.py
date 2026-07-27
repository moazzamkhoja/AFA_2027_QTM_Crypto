import json, requests

core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]

# Pattern A: apikey as query param (Etherscan-compatible)
try:
    r = requests.get(
        "https://openapi.coredao.org/api/stats/staking_summary",
        params={"apikey": core_key}, timeout=30
    )
    print("Pattern A:", r.status_code, r.text[:500])
except Exception as ex:
    print("Pattern A ERR:", ex)

# Pattern B: X-API-Key header
try:
    r2 = requests.get(
        "https://openapi.coredao.org/api/stats/staking_summary",
        headers={"X-API-Key": core_key}, timeout=30
    )
    print("Pattern B:", r2.status_code, r2.text[:500])
except Exception as ex:
    print("Pattern B ERR:", ex)
