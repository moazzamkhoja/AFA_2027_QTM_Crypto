import json, requests

core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]

def g(url, params=None):
    try:
        r = requests.get(url, params=params or {}, timeout=20)
        return r.status_code, r.text[:400]
    except Exception as ex:
        return "ERR", str(ex)[:150]

# Swagger/openapi discovery
for u in ["https://openapi.coredao.org/v2/api-docs",
          "https://openapi.coredao.org/swagger-ui.html",
          "https://openapi.coredao.org/api-docs",
          "https://openapi.coredao.org/swagger/v2/api-docs"]:
    c, t = g(u)
    print(f"{u} -> {c} {t[:150]}")

# Etherscan-style
c, t = g("https://openapi.coredao.org/api",
         {"module": "stats", "action": "coinsupply", "apikey": core_key})
print("etherscan-style coinsupply:", c, t)

# stats path variants
for path in ["stats/validators", "stats/list_of_validators", "stats/staking",
             "stats/core_staked", "stats/staking_info", "stats/summary"]:
    c, t = g(f"https://openapi.coredao.org/api/{path}", {"apikey": core_key})
    print(f"/api/{path} -> {c} {t[:200]}")
