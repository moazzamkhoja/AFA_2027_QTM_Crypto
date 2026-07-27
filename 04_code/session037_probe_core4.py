import json, requests

core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]
B = "https://staking-api.coredao.org"

def g(url, params=None):
    try:
        r = requests.get(url, params=params or {}, timeout=20)
        return r.status_code, r.text[:500]
    except Exception as ex:
        return "ERR", str(ex)[:150]

# round-parameterized probes on staking API (round 19500 = 2023-05-23)
for path, params in [
    ("/staking/status/validators", {"round": 19500}),
    ("/staking/status/validators", {}),
    ("/staking/summary/group_candidate_detail", {"round": 19500}),
    ("/staking/summary/group_candidate_detail", {}),
    ("/staking/summary/overall", {"round": 19500}),
]:
    c, t = g(B + path, params)
    print(f"{path} {params} -> {c}\n  {t[:350]}\n")

# CoreScan openapi balancehistory (Etherscan PRO-style)
for addr in ["0x0000000000000000000000000000000000001007",
             "0x0000000000000000000000000000000000001011"]:
    c, t = g("https://openapi.coredao.org/api",
             {"module": "account", "action": "balancehistory", "address": addr,
              "blockno": 10000000, "apikey": core_key})
    print(f"balancehistory {addr[-4:]} @10M -> {c} {t[:250]}")

# current balances via CoreScan
for addr in ["0x0000000000000000000000000000000000001007",
             "0x0000000000000000000000000000000000001010",
             "0x0000000000000000000000000000000000001011"]:
    c, t = g("https://openapi.coredao.org/api",
             {"module": "account", "action": "balance", "address": addr,
              "tag": "latest", "apikey": core_key})
    print(f"balance {addr[-4:]} -> {c} {t[:200]}")
