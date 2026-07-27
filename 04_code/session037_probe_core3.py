import json, requests

core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]
B = "https://staking-api.coredao.org"

def g(path, params=None):
    try:
        r = requests.get(B + path, params=params or {}, timeout=20)
        return r.status_code, r.text[:600]
    except Exception as ex:
        return "ERR", str(ex)[:150]

print("overall:", *g("/staking/summary/overall"))
print("\nround:", *g("/staking/status/round"))
print("\nsummary/core:", *g("/staking/summary/core"))
print("\nsummary/rewards (no param):", *g("/staking/summary/rewards"))
print("\nsummary/rewards round=1000:", *g("/staking/summary/rewards", {"round": 1000}))
print("\nwith key overall:", *g("/staking/summary/overall", {"apikey": core_key}))
