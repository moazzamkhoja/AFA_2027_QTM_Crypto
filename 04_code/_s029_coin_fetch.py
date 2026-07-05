"""_s029_coin_fetch.py -- Session 029 (Entry 78): RON / KAIA(KLAY) / FLR staking history.

None of these chains are in Etherscan V2's 64-chain list (probed live), so month-end
blocks are resolved by BINARY SEARCH on block timestamps over each chain's own RPC,
and the series are state reads of each chain's own aggregate (GLMR/MOVR/CELO standard):

RON  (cmc 14101) -- ronin.drpc.org (keyless FULL archive; the official
     api.roninchain.com RPC is pruned). Metric = sum(Staking.getManyStakingTotals(
     RoninValidatorSet.getValidatorCandidates(b), b)) -- stake actively delegated to
     validator candidates, the staking contract's own per-candidate accounting.
     Contract identities verified against axieinfinity/ronin-dpos-contracts
     deployments/ronin-mainnet (StakingProxy 0x545e..., RoninValidatorSetProxy
     0x617c...). The contract's NATIVE BALANCE runs ~+15.6% above the sum (pending/
     revoked-candidate undelegations awaiting withdrawal) -> balance recorded as the
     superset cross-check, NOT the metric.

KAIA (cmc 4256, KLAY listing observed 2021-03..2024-09) -- archive-en.node.kaia.io
     (official, keyless). Metric = klay_getStakingInfo(block): the node's OWN
     consensus staking snapshot (councilStakingAmounts are the AddressBook CnStaking
     contract balances the chain itself uses for GC weighting; units = KAIA).
     clStakingInfos (post-Kaia CL staking) added when present. Cross-check:
     stakingAmounts vs direct klay_getBalance of the councilStakingAddrs.

FLR  (cmc 7950) -- flare-api.flare.network/ext/C/rpc (official, keyless, archive).
     Metric = PChainStakeMirror.totalSupply() (address resolved live from the
     FlareContractRegistry 0xaD67...) = total P-chain stake mirrored to the C-chain.
     Cross-check: live mirror vs P-chain platform.getTotalStake (-0.2% probed).
"""

import calendar
import json
import time
from pathlib import Path

import requests

from _s028_evm import REPO, keccak_topic

RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"

RON_RPC = "https://ronin.drpc.org"
RON_VS = "0x617c5d73662282EA7FfD231E020eCa6D2B0D552f"
RON_ST = "0x545edb750eB8769C868429BE9586F5857A768758"
KAIA_RPC = "https://archive-en.node.kaia.io"
FLR_RPC = "https://flare-api.flare.network/ext/C/rpc"
FLR_REG = "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"


def rpc(url, method, params, tries=6, sleep=0.15):
    last = None
    for t in range(1, tries + 1):
        try:
            r = requests.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method,
                                         "params": params}, timeout=30).json()
            if "result" in r and r["result"] is not None:
                time.sleep(sleep)
                return r["result"]
            last = r.get("error")
            time.sleep(0.5 * t)
        except Exception as e:
            last = str(e)[:80]
            time.sleep(0.8 * t)
    raise RuntimeError(f"{url} {method} failed: {last}")


def block_ts(url, num_method, b, ts_key="timestamp"):
    blk = rpc(url, num_method, [hex(b), False])
    return int(blk[ts_key], 16)


def month_end_ts(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    d = calendar.monthrange(y, m)[1]
    return calendar.timegm(time.strptime(f"{ym}-{d} 23:59:59", "%Y-%m-%d %H:%M:%S"))


def month_ends(lo, hi):
    out, (y, m) = [], (int(lo[:4]), int(lo[5:7]))
    while f"{y:04d}-{m:02d}" <= hi:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def monthend_blocks_rpc(chain, url, yms, num_method="eth_getBlockByNumber"):
    """Binary-search the last block with timestamp <= month-end (UTC), cached."""
    cf = RAW / f"monthend_blocks_rpc_{chain}.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    head = int(rpc(url, num_method.replace("getBlockByNumber", "blockNumber"), []), 16) \
        if False else None
    # head via latest block object (works on all three RPC dialects)
    latest = rpc(url, num_method, ["latest", False])
    head_n, head_t = int(latest["number"], 16), int(latest["timestamp"], 16)
    for ym in yms:
        if ym in cache:
            continue
        target = month_end_ts(ym)
        if target >= head_t:
            cache[ym] = None
            continue
        lo, hi = 1, head_n
        while lo < hi:
            mid = (lo + hi + 1) // 2
            try:
                t = block_ts(url, num_method, mid)
            except RuntimeError:
                # very early pruned/absent block: move up
                lo = mid
                continue
            if t <= target:
                lo = mid
            else:
                hi = mid - 1
        cache[ym] = lo
        cf.write_text(json.dumps(cache))
        print(f"  {chain} {ym}: block {lo:,}", flush=True)
    return cache


# ---------------------------------------------------------------- RON

def ron_fetch():
    yms = month_ends("2023-02", "2026-05")
    blocks = monthend_blocks_rpc("ronin", RON_RPC, yms)
    cf = RAW / "ron_staking_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    sel_c = keccak_topic("getValidatorCandidates()")[:10]
    sel_m = keccak_topic("getManyStakingTotals(address[])")[:10]
    for ym in yms:
        b = blocks.get(ym)
        if b is None or ym in cache:
            continue
        try:
            r = rpc(RON_RPC, "eth_call", [{"to": RON_VS, "data": sel_c}, hex(b)])
        except RuntimeError as e:
            print(f"  RON {ym}: candidates call failed ({str(e)[:60]}) -> pre-DPoS, None")
            cache[ym] = {"block": b, "total": None, "balance": None, "n_cand": 0}
            cf.write_text(json.dumps(cache))
            continue
        if not r or r == "0x" or len(r) < 130:
            # pre-deployment: eth_call to a not-yet-deployed proxy returns 0x
            print(f"  RON {ym}: empty result -> pre-DPoS, None")
            cache[ym] = {"block": b, "total": None, "balance": None, "n_cand": 0}
            cf.write_text(json.dumps(cache))
            continue
        d = r[2:]
        n = int(d[64:128], 16)
        cands = ["0x" + d[128 + i * 64 + 24:128 + (i + 1) * 64] for i in range(n)]
        data = (sel_m + hex(32)[2:].rjust(64, "0") + hex(n)[2:].rjust(64, "0")
                + "".join(c[2:].rjust(64, "0") for c in cands))
        r2 = rpc(RON_RPC, "eth_call", [{"to": RON_ST, "data": data}, hex(b)])
        d2 = r2[2:]
        vals = [int(d2[128 + i * 64:128 + (i + 1) * 64], 16)
                for i in range(int(d2[64:128], 16))]
        bal = int(rpc(RON_RPC, "eth_getBalance", [RON_ST, hex(b)]), 16)
        cache[ym] = {"block": b, "total": str(sum(vals)), "balance": str(bal), "n_cand": n}
        cf.write_text(json.dumps(cache))
        tot = sum(vals) / 1e18
        print(f"  RON {ym} blk {b:,}: {n} cands total {tot:,.0f} "
              f"bal/total {int(bal)/max(sum(vals),1):.4f}", flush=True)


# ---------------------------------------------------------------- KAIA

def kaia_fetch():
    yms = month_ends("2021-03", "2026-05")
    blocks = monthend_blocks_rpc("kaia", KAIA_RPC, yms, "klay_getBlockByNumber")
    cf = RAW / "kaia_staking_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    for ym in yms:
        b = blocks.get(ym)
        if b is None or ym in cache:
            continue
        try:
            r = rpc(KAIA_RPC, "klay_getStakingInfo", [hex(b)])
        except RuntimeError as e:
            print(f"  KAIA {ym}: getStakingInfo failed ({str(e)[:60]}) -> None")
            cache[ym] = {"block": b, "council_sum": None, "cl_sum": None, "n": 0}
            cf.write_text(json.dumps(cache))
            continue
        amts = r.get("councilStakingAmounts") or []
        cl = sum(x.get("clStakingAmount", 0) for x in (r.get("clStakingInfos") or []))
        cache[ym] = {"block": b, "council_sum": sum(amts), "cl_sum": cl, "n": len(amts)}
        cf.write_text(json.dumps(cache))
        print(f"  KAIA {ym} blk {b:,}: council {sum(amts):,} (+cl {cl:,}) n={len(amts)}",
              flush=True)
    # cross-check: latest stakingAmounts vs direct balances of the staking addrs
    r = rpc(KAIA_RPC, "klay_getStakingInfo", ["latest"])
    addrs = r["councilStakingAddrs"]
    amts = r["councilStakingAmounts"]
    diffs = []
    for a, amt in list(zip(addrs, amts))[:8]:
        bal = int(rpc(KAIA_RPC, "klay_getBalance", [a, "latest"]), 16) / 1e18
        diffs.append(abs(bal - amt) / max(amt, 1))
    print(f"  KAIA cross-check (8 CnStaking addrs): max |balance-amount|/amount = "
          f"{max(diffs):.4%} (amounts are the contracts' balances in KAIA)")


# ---------------------------------------------------------------- FLR

def flr_fetch():
    yms = month_ends("2023-02", "2026-05")
    blocks = monthend_blocks_rpc("flare", FLR_RPC, yms)
    # resolve PChainStakeMirror from the registry (live)
    sel = keccak_topic("getContractAddressByName(string)")[:10]
    name = "PChainStakeMirror"
    enc = (hex(32)[2:].rjust(64, "0") + hex(len(name))[2:].rjust(64, "0")
           + name.encode().hex().ljust(64, "0"))
    psm = "0x" + rpc(FLR_RPC, "eth_call", [{"to": FLR_REG, "data": sel + enc}, "latest"])[-40:]
    print(f"  FLR PChainStakeMirror = {psm}")
    cf = RAW / "flr_staking_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    ts_sel = keccak_topic("totalSupply()")[:10]
    for ym in yms:
        b = blocks.get(ym)
        if b is None or ym in cache:
            continue
        try:
            r = rpc(FLR_RPC, "eth_call", [{"to": psm, "data": ts_sel}, hex(b)])
            v = int(r, 16) if r and r != "0x" else None   # 0x = pre-deployment
        except RuntimeError:
            v = None   # pre-deployment months
        cache[ym] = {"block": b, "total": str(v) if v is not None else None}
        cf.write_text(json.dumps(cache))
        print(f"  FLR {ym} blk {b:,}: {v/1e18 if v else None and 0:,.0f}" if v else
              f"  FLR {ym} blk {b:,}: None (pre-mirror)", flush=True)
    # cross-check: live mirror vs P-chain getTotalStake
    live = int(rpc(FLR_RPC, "eth_call", [{"to": psm, "data": ts_sel}, "latest"]), 16) / 1e18
    p = requests.post("https://flare-api.flare.network/ext/bc/P", json={
        "jsonrpc": "2.0", "id": 1, "method": "platform.getTotalStake",
        "params": {"subnetID": "11111111111111111111111111111111LpoYY"}},
        timeout=25, headers={"content-type": "application/json"}).json()
    pv = int(p["result"]["stake"]) / 1e9
    print(f"  FLR cross-check: mirror {live:,.0f} vs P-chain getTotalStake {pv:,.0f} "
          f"-> drift {(live-pv)/pv:+.3%}")


if __name__ == "__main__":
    print("=== RON ===")
    ron_fetch()
    print("=== KAIA ===")
    kaia_fetch()
    print("=== FLR ===")
    flr_fetch()
