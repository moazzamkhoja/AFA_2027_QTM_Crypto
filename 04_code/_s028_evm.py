"""_s028_evm.py -- Session 028 shared EVM probe/build helpers (Etherscan V2 Pro key).

Small utilities used by the session-028 coin-staking probes and builders:
keccak event topics (pycryptodome), Etherscan V2 api() with retry, eth_call,
verified-contract ABI fetch, latest block, and a capped getLogs walker that
recursively splits on the 1000-log window like phase1_channel1_evm_locks_ext.
"""

import json
import time
from pathlib import Path

import requests
from Crypto.Hash import keccak as _keccak

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = 0.22


def keccak_topic(sig: str) -> str:
    k = _keccak.new(digest_bits=256)
    k.update(sig.encode())
    return "0x" + k.hexdigest()


def api(params, chainid, tries=5):
    last = None
    for t in range(1, tries + 1):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, **params},
                             headers=H, timeout=60)
            j = r.json()
            time.sleep(SLEEP)
            return j
        except Exception as e:
            last = e
            time.sleep(SLEEP * t * 2)
    raise RuntimeError(f"etherscan api failed after {tries} tries: {last}")


def latest_block(chainid):
    j = api({"module": "proxy", "action": "eth_blockNumber"}, chainid)
    return int(j["result"], 16)


def eth_call(to, data, chainid, tag="latest"):
    j = api({"module": "proxy", "action": "eth_call", "to": to, "data": data,
             "tag": tag}, chainid)
    return j.get("result")


def get_abi(addr, chainid):
    j = api({"module": "contract", "action": "getabi", "address": addr}, chainid)
    if j.get("status") == "1":
        return json.loads(j["result"])
    return None


def abi_events(abi):
    out = []
    for item in abi or []:
        if item.get("type") == "event":
            ins = item.get("inputs", [])
            sig = item["name"] + "(" + ",".join(i["type"] for i in ins) + ")"
            out.append((sig, keccak_topic(sig),
                        [(i["name"], i["type"], i.get("indexed", False)) for i in ins]))
    return out


def getlogs_window(address, topic0, lo, hi, chainid):
    """All logs for topic0 in [lo,hi], recursively splitting on the 1000-log cap."""
    params = {"module": "logs", "action": "getLogs", "address": address,
              "topic0": topic0, "fromBlock": lo, "toBlock": hi}
    j = api(params, chainid)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return []
        mid = (lo + hi) // 2
        return (getlogs_window(address, topic0, lo, mid, chainid) +
                getlogs_window(address, topic0, mid + 1, hi, chainid))
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        return (getlogs_window(address, topic0, lo, mid, chainid) +
                getlogs_window(address, topic0, mid + 1, hi, chainid))
    return res


def words(data_hex):
    d = data_hex[2:] if data_hex.startswith("0x") else data_hex
    return [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
