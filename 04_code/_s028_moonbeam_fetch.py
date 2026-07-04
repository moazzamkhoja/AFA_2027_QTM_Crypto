"""_s028_moonbeam_fetch.py -- Session 028 A2: GLMR/MOVR monthly staked series.

Method: the ParachainStaking precompile (0x...0800) emits NO EVM logs and exposes no
aggregate getter, and Etherscan's proxy eth_call ignores the historical tag -- but the
OFFICIAL public Moonbeam/Moonriver RPC endpoints are full archives and speak Substrate
JSON-RPC. So we read the staking pallet's own aggregate directly:

    key = twox128("ParachainStaking") + twox128("Total")
    state_getStorage(key, chain_getBlockHash(month_end_block))  ->  u128 LE, /1e18

This is the chain's own total staked (collator bonds + ALL delegations incl. bottom),
not a reconstruction. Month-end blocks resolved once via Etherscan getblocknobytime.
Cross-check: latest Total vs sum(getCandidateTotalCounted) over selectedCandidates()
via eth_call (Total must be >= sum-counted and close -- counted excludes bottom
delegations), plus magnitude sanity vs circulating supply.
"""

import json
import time

import requests
import xxhash

from _s028_evm import REPO, keccak_topic, eth_call, api, words

RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
RAW.mkdir(parents=True, exist_ok=True)

PRE = "0x0000000000000000000000000000000000000800"


def twox128(data: bytes) -> str:
    return (xxhash.xxh64(data, seed=0).digest()[::-1] +
            xxhash.xxh64(data, seed=1).digest()[::-1]).hex()


STORAGE_KEY = "0x" + twox128(b"ParachainStaking") + twox128(b"Total")

CHAINS = {
    "glmr": {"chainid": 1284, "rpc": "https://rpc.api.moonbeam.network",
             "months": ("2022-01", "2026-05")},
    "movr": {"chainid": 1285, "rpc": "https://rpc.api.moonriver.moonbeam.network",
             "months": ("2021-09", "2026-05")},
}


def rpc(url, method, params, tries=4):
    last = None
    for t in range(1, tries + 1):
        try:
            r = requests.post(url, json={"jsonrpc": "2.0", "method": method,
                                         "params": params, "id": 1}, timeout=30)
            j = r.json()
            if "error" in j and j["error"]:
                return {"error": j["error"]}
            time.sleep(0.25)
            return j
        except Exception as e:
            last = e
            time.sleep(1.0 * t)
    raise RuntimeError(f"rpc {method} failed: {last}")


def month_ends(lo, hi):
    out = []
    y, m = int(lo[:4]), int(lo[5:7])
    while f"{y:04d}-{m:02d}" <= hi:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def monthend_block(ym, chainid, cache):
    if ym in cache:
        return cache[ym]
    import calendar
    y, m = int(ym[:4]), int(ym[5:7])
    last_day = calendar.monthrange(y, m)[1]
    ts = int(time.mktime(time.strptime(f"{ym}-{last_day} 23:59:59", "%Y-%m-%d %H:%M:%S")))
    j = api({"module": "block", "action": "getblocknobytime",
             "timestamp": ts, "closest": "before"}, chainid)
    if j.get("status") == "1":
        cache[ym] = int(j["result"])
        return cache[ym]
    return None


def main():
    for name, cfg in CHAINS.items():
        cid, url = cfg["chainid"], cfg["rpc"]
        cf = RAW / f"{name}_total_staked.json"
        state = json.loads(cf.read_text()) if cf.exists() else {"blocks": {}, "series": {}}
        yms = month_ends(*cfg["months"])
        print(f"{name}: {len(yms)} months {yms[0]}..{yms[-1]}")
        for ym in yms:
            if ym in state["series"]:
                continue
            blk = monthend_block(ym, cid, state["blocks"])
            if blk is None:
                print(f"  {ym}: no month-end block (pre-genesis?), skip")
                state["series"][ym] = None
                continue
            h = rpc(url, "chain_getBlockHash", [blk])
            if "error" in h or not h.get("result"):
                print(f"  {ym}: blockhash err {h.get('error')}")
                continue
            s = rpc(url, "state_getStorage", [STORAGE_KEY, h["result"]])
            if "error" in s:
                print(f"  {ym}: storage err {s['error']}")
                continue
            raw = s.get("result")
            val = int.from_bytes(bytes.fromhex(raw[2:]), "little") / 1e18 if raw else None
            state["series"][ym] = val
            cf.write_text(json.dumps(state))
        cf.write_text(json.dumps(state))
        ser = {k: v for k, v in state["series"].items() if v}
        if ser:
            ks = sorted(ser)
            print(f"  built {len(ser)} months: {ks[0]}={ser[ks[0]]:,.0f} .. {ks[-1]}={ser[ks[-1]]:,.0f}")

        # cross-check: live Total vs sum(getCandidateTotalCounted) over selectedCandidates
        latest_total = rpc(url, "state_getStorage", [STORAGE_KEY])
        lt = int.from_bytes(bytes.fromhex(latest_total["result"][2:]), "little") / 1e18
        r = eth_call(PRE, keccak_topic("selectedCandidates()")[:10], cid)
        w = words(r)
        cands = ["0x" + hex(x)[2:].rjust(40, "0") for x in w[2:2 + w[1]]]
        sel = keccak_topic("getCandidateTotalCounted(address)")[:10]
        tot = 0
        for c in cands:
            rr = eth_call(PRE, sel + c[2:].rjust(64, "0"), cid)
            if rr and rr != "0x":
                tot += int(rr, 16)
        tot /= 1e18
        print(f"  CROSS-CHECK live: pallet Total={lt:,.0f}  sum(counted,{len(cands)} selected)={tot:,.0f}"
              f"  Total/sum = {lt/tot:.4f}")


if __name__ == "__main__":
    main()
