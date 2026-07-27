import json, requests

core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]

for name, addr in [("PledgeAgent", "0x0000000000000000000000000000000000001007"),
                   ("StakeHub", "0x0000000000000000000000000000000000001010"),
                   ("CoreAgent", "0x0000000000000000000000000000000000001011")]:
    r = requests.get("https://openapi.coredao.org/api",
        params={"module": "contract", "action": "getabi", "address": addr,
                "apikey": core_key}, timeout=20)
    try:
        abi = json.loads(r.json()["result"])
        views = [f"{x['name']}({','.join(i['type'] for i in x.get('inputs', []))})"
                 for x in abi if x.get("type") == "function"
                 and x.get("stateMutability") in ("view", "pure")]
        keyw = [v for v in views if any(k in v.lower() for k in
                ("total", "amount", "stake", "pledge", "delegat"))]
        print(f"\n{name} {addr[-4:]}: {len(views)} views; relevant:")
        for v in keyw:
            print("   ", v)
    except Exception as ex:
        print(f"\n{name}: ABI fetch fail {r.status_code} {r.text[:150]} {ex}")
