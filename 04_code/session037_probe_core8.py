import json, requests
from Crypto.Hash import keccak

RPC = "https://rpc.ankr.com/core"
CORE_AGENT = "0x0000000000000000000000000000000000001011"


def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return "0x" + k.hexdigest()[:8]


def call(to, data, block="latest"):
    r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                                 "params": [{"to": to, "data": data}, block]}, timeout=30)
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]


def words(hexstr):
    b = hexstr[2:]
    return [int(b[i:i+64], 16) for i in range(0, len(b), 64)]


v = requests.get("https://staking-api.coredao.org/staking/status/validators", timeout=20).json()
vl = v["data"]["validatorsList"]
print("api fields:", [k for k in vl[0].keys()])
s_map = sel("candidateMap(address)")

api_total_all = api_total_active = 0
n_active = 0
print(f"{'validator':22s} {'status':>7s} {'api_stakedCore':>16s} {'cm_amount':>14s} {'cm_realtime':>14s}")
for x in vl:
    op = x["operatorAddress"].lower()
    api_amt = int(x.get("stakedCoreAmount", 0)) / 1e18
    w = words(call(CORE_AGENT, s_map + op[2:].rjust(64, "0")))
    st = x.get("status")
    api_total_all += api_amt
    active = str(st) == "17"
    if active:
        api_total_active += api_amt
        n_active += 1
    print(f"{x['name'][:22]:22s} {str(st):>7s} {api_amt:16,.0f} {w[0]/1e18:14,.0f} {w[1]/1e18:14,.0f}")
print(f"\napi sum(all)={api_total_all:,.0f}  api sum(active n={n_active})={api_total_active:,.0f}")
