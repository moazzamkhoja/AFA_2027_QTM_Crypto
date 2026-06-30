"""
phase1_p2p2_probe.py  --  SESSION 025, Task A (P2-2): mechanism VERIFICATION before build.

The 16 BSC/Base/Optimism/Linea tokens identified in session 022 as carrying ERC20Votes /
lock contracts but PAID-gated on getLogs (those chains needed Etherscan Pro). Now Pro is
purchased (Entry 61). Before building anything we re-apply the AKRO/Entry-55 discipline:
CONFIRM the mechanism actually fires non-trivially on-chain.

For the 15 Channel-3 candidates: count DelegateVotesChanged logs over full history (bounded
call cap -- we only need "fires and is non-trivial", not the full replay, which the builder
does with checkpointing). A token whose event NEVER fires, or fires only with zero newBalance,
is DORMANT -> skip (don't force a degenerate ratio).

For TNC (Channel-1 candidate, BSC): inspect the cached verified source for the Locked() event
shape (amount-bearing vs the bare AKRO/VSL pause flag) and count its Locked() logs.

Writes 03_data/phase1/_p2p2_probe.json + prints a verdict-input table. Does NOT build.
"""
import json, time, re
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = 0.21
SRC = REPO / "03_data" / "raw" / "etherscan_src"
OUT = REPO / "03_data" / "phase1" / "_p2p2_probe.json"

TOPIC_DVC_U256 = "0xdec2bacdd2f05b59de34da9b523dff8be42e5e38e818c82fdb0bae774387a724"
TOPIC_DVC_U96 = "0x664ef4a22338e827df5b675ec1747eac10c2ea611e1c575f3d96c38a2e24231e"

# cmc_id, symbol, chainid, address, kind
CH3 = [
    (10897, "ALT",     56,    "0x5ca09af27b8a4f1d636380909087536bc7e2d94d"),
    (4006,  "AWE",     8453,  "0x1B4617734C43F6159F3a70b7E06d883647512778"),
    (7064,  "BAKE",    56,    "0xE02dF9e3e622DeBdD69fb838bB799E3F168902c5"),
    (9891,  "BNX",     56,    "0x8C851d1a123Ff703BD1f9dabe631b69902Df5f97"),
    (23054, "CHEEL",   56,    "0x1F1C90aEb2fd13EA972F0a71e35c0753848e3DB0"),
    (5274,  "EDG",     56,    "0x4e0da40b9063dc48364c1c0ffb4ae9d091fc2270"),
    (37414, "ESPORTS", 56,    "0xF39e4b21c84e737Df08e2C3b32541d856f508E48"),
    (23635, "FORM",    56,    "0x5b73A93b4E5e4f1FD27D8b3F8C97D69908b5E284"),
    (27657, "LINEA",   59144, "0x1789e0043623282d5dcc7f213d703c6d8bafbb04"),
    (16946, "MCT",     56,    "0xdf677713a2c661ecd0b2bd4d7485170aa8c1eceb"),
    (8335,  "MDX",     56,    "0x9c65ab58d8d978db963e63f2bfb7121627e3a739"),
    (11840, "OP",      10,    "0x4200000000000000000000000000000000000042"),
    (29150, "PONKE",   8453,  "0x4a0c64af541439898448659aedcec8e8e819fc53"),
    (9020,  "TKO",     56,    "0x9f589e3eabe42ebc94a44727b3f3531c0c877809"),
    (35931, "ZORA",    8453,  "0x1111111111166b7fe7bd91427724b487980afc69"),
]
TNC = (5524, "TNC", 56, "0x02CAa44EB838Fc0E49b73213d9d22e5F23798fDa")

state = {"calls": 0}


def api(params, chainid, tries=4):
    state["calls"] += 1
    for t in range(tries):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, **params},
                             headers=H, timeout=60)
            j = r.json()
            time.sleep(SLEEP)
            return j
        except Exception:
            time.sleep(SLEEP * (t + 1) * 2)
    return {"status": "0", "result": []}


def count_logs(addr, topic0, chainid, lo, hi, cap, acc):
    """Bounded recursive count of logs; also tracks max newBalance seen (non-trivial check)."""
    if state["calls"] >= cap:
        acc["capped"] = True
        return
    j = api({"module": "logs", "action": "getLogs", "address": addr, "topic0": topic0,
             "fromBlock": lo, "toBlock": hi}, chainid)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        count_logs(addr, topic0, chainid, lo, mid, cap, acc)
        count_logs(addr, topic0, chainid, mid + 1, hi, cap, acc)
        return
    for lg in res:
        acc["n"] += 1
        try:
            data = lg["data"][2:]
            nb = int(data[64:128], 16) if len(data) >= 128 else 0
            if nb > acc["max_newbal"]:
                acc["max_newbal"] = nb
        except Exception:
            pass
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        count_logs(addr, topic0, chainid, lo, mid, cap, acc)
        count_logs(addr, topic0, chainid, mid + 1, hi, cap, acc)


def blocknum(chainid):
    j = api({"module": "proxy", "action": "eth_blockNumber"}, chainid)
    try:
        return int(j["result"], 16)
    except Exception:
        return 999_999_999


def src_blob(chainid, addr):
    f = SRC / f"{chainid}_{addr.lower()}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except Exception:
        return None


def find_event_sig(blob, name):
    """Search cached verified source for an `event <Name>(...)` declaration."""
    if not blob:
        return None
    txt = json.dumps(blob)
    m = re.search(r"event\s+" + re.escape(name) + r"\s*\(([^;]*?)\)", txt)
    return m.group(0).replace("\\n", " ").strip() if m else None


def main():
    findings = {"ch3": [], "tnc": {}}
    print("=== P2-2 Channel-3 mechanism verification (DelegateVotesChanged firing) ===")
    for cmc_id, sym, chainid, addr in CH3:
        bn = blocknum(chainid)
        # try the uint256-topic variant first (session-024 map records all under it); if 0, try u96
        acc = {"n": 0, "max_newbal": 0, "capped": False}
        state["calls"] = 0
        t0 = time.time()
        count_logs(addr, TOPIC_DVC_U256, chainid, 0, bn, 60, acc)
        topic_used = "u256"
        if acc["n"] == 0 and not acc["capped"]:
            acc = {"n": 0, "max_newbal": 0, "capped": False}
            count_logs(addr, TOPIC_DVC_U96, chainid, 0, bn, 60, acc)
            topic_used = "u96"
        secs = round(time.time() - t0, 1)
        verdict = "FIRES" if acc["n"] > 0 and acc["max_newbal"] > 0 else (
            "FIRES(capped,partial)" if acc["capped"] and acc["n"] > 0 else "DORMANT")
        rec = {"cmc_id": cmc_id, "symbol": sym, "chainid": chainid, "topic": topic_used,
               "logs_counted": acc["n"], "max_newbalance_raw": str(acc["max_newbal"]),
               "capped": acc["capped"], "calls": state["calls"], "secs": secs, "verdict": verdict}
        findings["ch3"].append(rec)
        print(f"  {sym:8} chain={chainid:<6} {topic_used} logs={acc['n']:>6} "
              f"max_newbal>0={acc['max_newbal']>0} capped={acc['capped']} "
              f"calls={state['calls']:>3} -> {verdict}")

    print("\n=== P2-2 TNC Channel-1 mechanism (Locked event shape + firing) ===")
    cmc_id, sym, chainid, addr = TNC
    blob = src_blob(chainid, addr)
    locked_sig = find_event_sig(blob, "Locked")
    print(f"  TNC cached-source Locked event decl: {locked_sig}")
    # count Locked(address) bare-topic AND Locked(address,uint256) amount-topic
    LOCKED_ADDR = "0x" + "".join(["%064x" % 0])  # placeholder, real topic computed below
    # keccak topic0 for Locked(address) and Locked(address,uint256)
    import hashlib
    def topic0(sig):
        # eth uses keccak256; hashlib doesn't have keccak. Use a known table instead.
        return None
    # Known topic0 values:
    T_LOCKED_ADDR = "0x9f1ec8c880f76798e7b793325d625e9b60e4082a553c98f42b6cda368dd60008"  # Locked(address,uint256) [XAN]
    T_LOCKED_BARE = "0x"  # bare Locked(address) computed at runtime not available; rely on source shape
    bn = blocknum(chainid)
    acc = {"n": 0, "max_newbal": 0, "capped": False}
    state["calls"] = 0
    count_logs(addr, T_LOCKED_ADDR, chainid, 0, bn, 40, acc)
    findings["tnc"] = {"cmc_id": cmc_id, "symbol": sym, "chainid": chainid,
                       "locked_event_decl": locked_sig,
                       "locked_amount_topic_logs": acc["n"], "capped": acc["capped"],
                       "calls": state["calls"]}
    print(f"  TNC Locked(address,uint256) amount-topic logs={acc['n']} (capped={acc['capped']})")

    OUT.write_text(json.dumps(findings, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
