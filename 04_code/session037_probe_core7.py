import json, requests
from Crypto.Hash import keccak

RPC = "https://rpc.ankr.com/core"
CANDIDATE_HUB = "0x0000000000000000000000000000000000001005"
PLEDGE_AGENT = "0x0000000000000000000000000000000000001007"
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


def get_candidates(block="latest"):
    res = call(CANDIDATE_HUB, sel("getCandidates()"), block)
    w = words(res)
    n = w[1]
    return ["0x" + hex(x)[2:].rjust(40, "0") for x in w[2:2+n]]


cands = get_candidates()
print(f"{len(cands)} candidates")

s_map = sel("candidateMap(address)")
tot_amount = tot_rt = 0
for c in cands:
    w = words(call(CORE_AGENT, s_map + c[2:].rjust(64, "0")))
    tot_amount += w[0]
    tot_rt += w[1]
print(f"CoreAgent sum amount      = {tot_amount/1e18:,.0f}")
print(f"CoreAgent sum realtime    = {tot_rt/1e18:,.0f}")

s_agents = sel("agentsMap(address)")
sums = None
for c in cands:
    w = words(call(PLEDGE_AGENT, s_agents + c[2:].rjust(64, "0")))
    if sums is None:
        sums = [0] * len(w)
        print("agentsMap word count:", len(w))
    for i, x in enumerate(w):
        sums[i] += x
print("PledgeAgent agentsMap field sums (1e18):", [f"{x/1e18:,.0f}" for x in sums])
print("\nStaking API stakedCoreAmount = 315,775,338 (at probe time)")
