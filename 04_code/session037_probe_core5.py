import json, requests

core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]
A = "0x0000000000000000000000000000000000001011"

r = requests.get("https://openapi.coredao.org/api",
    params={"module": "account", "action": "balancehistory", "address": A,
            "blockno": 10000000, "apikey": core_key}, timeout=20)
print("balancehistory raw:", r.status_code, repr(r.text[:300]), "headers ct:", r.headers.get("content-type"))

# proxy eth_getBalance historical (archive?)
for tag in [hex(10000000), "latest"]:
    r2 = requests.get("https://openapi.coredao.org/api",
        params={"module": "proxy", "action": "eth_getBalance", "address": A,
                "tag": tag, "apikey": core_key}, timeout=20)
    print(f"proxy eth_getBalance {tag}:", r2.status_code, r2.text[:250])

# public RPC historical
r3 = requests.post("https://rpc.coredao.org",
    json={"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance",
          "params": [A, hex(10000000)]}, timeout=20)
print("rpc.coredao.org @10M:", r3.status_code, r3.text[:250])
r4 = requests.post("https://rpc.coredao.org",
    json={"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance",
          "params": [A, "latest"]}, timeout=20)
print("rpc.coredao.org latest:", r4.status_code, r4.text[:250])
