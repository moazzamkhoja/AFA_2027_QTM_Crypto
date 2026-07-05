"""_s029_coin_fetch2.py -- Session 029 (Entry 78): STRK / XRD / PEAQ staking history.

STRK (cmc 22691) -- Starknet staking contract (mainnet address from
     docs.starknet.io/learn/cheatsheets/chain-info/#staking):
     0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7
     Metric = starknet_call get_total_stake() (STRK, 1e18). The kickoff's address
     0x04718f... is the STRK TOKEN, and 0x00ca1705... is the MINTING CURVE (both
     ABI-verified live). rpc.starknet.lava.build is a keyless FULL archive (probed:
     block 1.0M -> 108.3M STRK, 1.4M -> 267M, head -> 1.417B; blastapi retired,
     drpc has no starknet_call). Month-end blocks by binary search on block
     timestamps. Contract not found pre ~block 950k = pre-deployment (2024-11
     staking launch) -> None months.

XRD  (cmc 11948) -- Radix Babylon Gateway (mainnet.radixdlt.com, official, keyless)
     /state/validators/list accepts at_ledger_state={"timestamp": ...} for HISTORICAL
     state. Metric = sum(stake_vault.balance) over all validators (single page, 245
     items, no cursor at probe time; guarded). Window = Babylon era only (2023-10+);
     the Olympia era (2021-07..2023-09) is a documented gap (old gateway retired).

PEAQ (cmc 14588) -- peaq's staking pallet is a KILT-fork: storage item is
     ParachainStaking.TotalCollatorStake (struct{collators: u128, delegators: u128}),
     NOT Moonbeam's .Total (probed: Total=null, TotalCollatorStake answers).
     peaq.api.onfinality.io/public is a keyless archive (block 1.0M answers).
     Metric = collators + delegators. Month-end blocks by binary search on the
     Timestamp.Now pallet storage (Substrate headers carry no timestamp).
"""

import calendar
import json
import struct
import time
from pathlib import Path

import requests
import xxhash
from Crypto.Hash import keccak as _keccak

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"

LAVA = "https://rpc.starknet.lava.build"
STRK_ST = "0x00ca1702e64c81d9a07b86bd2c540188d92a2c73cf5cc0e508d949015e7e84a7"
RADIX = "https://mainnet.radixdlt.com"
PEAQ = "https://peaq.api.onfinality.io/public"


def sn_keccak(s):
    k = _keccak.new(digest_bits=256)
    k.update(s.encode())
    return hex(int.from_bytes(k.digest(), "big") & ((1 << 250) - 1))


def twox128(d):
    return struct.pack("<QQ", xxhash.xxh64(d, seed=0).intdigest(),
                       xxhash.xxh64(d, seed=1).intdigest()).hex()


def rpc(url, method, params, tries=6, sleep=0.12, allow_error=False):
    last = None
    for t in range(1, tries + 1):
        try:
            r = requests.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method,
                                         "params": params}, timeout=30).json()
            if "result" in r:
                time.sleep(sleep)
                return r["result"]
            last = r.get("error")
            if allow_error:
                return {"__error__": last}
            time.sleep(0.5 * t)
        except Exception as e:
            last = str(e)[:80]
            time.sleep(0.8 * t)
    raise RuntimeError(f"{url} {method}: {last}")


def month_ends(lo, hi):
    out, (y, m) = [], (int(lo[:4]), int(lo[5:7]))
    while f"{y:04d}-{m:02d}" <= hi:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def me_ts(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    d = calendar.monthrange(y, m)[1]
    return calendar.timegm(time.strptime(f"{ym}-{d} 23:59:59", "%Y-%m-%d %H:%M:%S"))


# ---------------------------------------------------------------- STRK

def strk_fetch():
    sel = sn_keccak("get_total_stake")
    head = rpc(LAVA, "starknet_blockNumber", [])

    def blk_ts(b):
        r = rpc(LAVA, "starknet_getBlockWithTxHashes", [{"block_number": b}])
        return r["timestamp"]

    cf = RAW / "strk_staking_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    bl = cache.setdefault("_blocks", {})
    head_t = blk_ts(head)
    for ym in month_ends("2024-11", "2026-05"):
        if ym in cache:
            continue
        target = me_ts(ym)
        if target >= head_t:
            continue
        if ym not in bl:
            lo, hi = 1, head
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if blk_ts(mid) <= target:
                    lo = mid
                else:
                    hi = mid - 1
            bl[ym] = lo
            cf.write_text(json.dumps(cache))
        b = bl[ym]
        r = rpc(LAVA, "starknet_call",
                [{"contract_address": STRK_ST, "entry_point_selector": sel,
                  "calldata": []}, {"block_number": b}], allow_error=True)
        if isinstance(r, dict) and "__error__" in r:
            cache[ym] = {"block": b, "total": None,
                         "note": str(r["__error__"])[:60]}
            print(f"  STRK {ym} blk {b:,}: None ({str(r['__error__'])[:40]})", flush=True)
        else:
            v = int(r[0], 16)
            cache[ym] = {"block": b, "total": str(v)}
            print(f"  STRK {ym} blk {b:,}: {v/1e18:,.0f}", flush=True)
        cf.write_text(json.dumps(cache))
    live = int(rpc(LAVA, "starknet_call",
                   [{"contract_address": STRK_ST, "entry_point_selector": sel,
                     "calldata": []}, "latest"])[0], 16) / 1e18
    print(f"  STRK live get_total_stake = {live:,.0f}")


# ---------------------------------------------------------------- XRD

def xrd_fetch():
    cf = RAW / "xrd_staking_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    for ym in month_ends("2023-10", "2026-05"):
        if ym in cache:
            continue
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(me_ts(ym)))
        try:
            r = requests.post(RADIX + "/state/validators/list",
                              json={"at_ledger_state": {"timestamp": ts}},
                              timeout=40).json()
            v = r["validators"]
            if v.get("next_cursor"):
                raise RuntimeError("PAGINATED response -- extend fetch before shipping")
            tot = sum(float(it["stake_vault"]["balance"]) for it in v["items"])
            cache[ym] = {"n": len(v["items"]), "total": tot,
                         "state_version": r["ledger_state"]["state_version"]}
            print(f"  XRD {ym}: {tot:,.0f} over {len(v['items'])} validators", flush=True)
        except Exception as e:
            cache[ym] = {"n": 0, "total": None, "note": str(e)[:60]}
            print(f"  XRD {ym}: FAILED {str(e)[:60]}", flush=True)
        cf.write_text(json.dumps(cache))
        time.sleep(0.4)


# ---------------------------------------------------------------- PEAQ

def peaq_fetch():
    key = "0x" + twox128(b"ParachainStaking") + twox128(b"TotalCollatorStake")
    ts_key = "0x" + twox128(b"Timestamp") + twox128(b"Now")
    head = int(rpc(PEAQ, "chain_getHeader", [])["number"], 16)

    def blk_ts(b):
        h = rpc(PEAQ, "chain_getBlockHash", [b])
        res = rpc(PEAQ, "state_getStorage", [ts_key, h])
        return int.from_bytes(bytes.fromhex(res[2:]), "little") // 1000

    cf = RAW / "peaq_staking_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    bl = cache.setdefault("_blocks", {})
    head_t = blk_ts(head)
    for ym in month_ends("2024-11", "2026-05"):
        if ym in cache:
            continue
        target = me_ts(ym)
        if target >= head_t:
            continue
        if ym not in bl:
            lo, hi = 1, head
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if blk_ts(mid) <= target:
                    lo = mid
                else:
                    hi = mid - 1
            bl[ym] = lo
            cf.write_text(json.dumps(cache))
        b = bl[ym]
        h = rpc(PEAQ, "chain_getBlockHash", [b])
        res = rpc(PEAQ, "state_getStorage", [key, h])
        if res:
            d = bytes.fromhex(res[2:])
            coll = int.from_bytes(d[0:16], "little")
            dele = int.from_bytes(d[16:32], "little")
            cache[ym] = {"block": b, "collators": str(coll), "delegators": str(dele)}
            print(f"  PEAQ {ym} blk {b:,}: {(coll+dele)/1e18:,.0f}", flush=True)
        else:
            cache[ym] = {"block": b, "collators": None, "delegators": None}
            print(f"  PEAQ {ym} blk {b:,}: null (pre-pallet)", flush=True)
        cf.write_text(json.dumps(cache))


if __name__ == "__main__":
    print("=== STRK ===")
    strk_fetch()
    print("=== XRD ===")
    xrd_fetch()
    print("=== PEAQ ===")
    peaq_fetch()
