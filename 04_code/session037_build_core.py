"""Session 037: CORE (cmc 23254) channel-1 via archive eth_call on Core chain.

Definition validated against the official staking API (staking-api.coredao.org
/staking/summary/overall): stakedCoreAmount == sum over ACTIVE validators
(ValidatorSet.getValidatorOps()) of CoreAgent.candidateMap(op).amount —
matched to the digit at probe time (315,775,339 CORE, 2026-07-27).

Pre-StakeHub-upgrade months (before CoreAgent 0x...1011 had code) fall back to
the legacy PledgeAgent.agentsMap(op) getter; the CORE-staked field index is
chosen by continuity across the upgrade boundary and printed for audit.

Archive RPC: Ankr (rpc.ankr.com/core), fallback dRPC (core.drpc.org).
"""
import calendar
import csv
import datetime as dt
import json
import time

import requests
from Crypto.Hash import keccak

RPCS = ["https://rpc.ankr.com/core", "https://core.drpc.org"]
VALIDATOR_SET = "0x0000000000000000000000000000000000001000"
PLEDGE_AGENT = "0x0000000000000000000000000000000000001007"
CORE_AGENT = "0x0000000000000000000000000000000000001011"
CMC_ID = 23254
START_YM, END_YM = "2023-01", "2026-06"


def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return "0x" + k.hexdigest()[:8]


S_OPS = sel("getValidatorOps()")
S_CVS = sel("currentValidatorSet(uint256)")
S_CMAP = sel("candidateMap(address)")
S_AMAP = sel("agentsMap(address)")

_rpc_i = 0


def rpc(method, params):
    global _rpc_i
    last = None
    for url in RPCS:
        for attempt in range(3):
            try:
                _rpc_i += 1
                r = requests.post(url, json={"jsonrpc": "2.0", "id": _rpc_i,
                                             "method": method, "params": params}, timeout=30)
                j = r.json()
                if "error" in j:
                    if "revert" in str(j["error"]).lower():
                        raise RuntimeError("execution reverted")  # no retry
                    raise RuntimeError(str(j["error"])[:200])
                return j["result"]
            except RuntimeError as ex:
                if "reverted" in str(ex):
                    raise
                last = ex
                time.sleep(1 + attempt)
            except Exception as ex:
                last = ex
                time.sleep(1 + attempt)
    raise RuntimeError(f"rpc failed: {method} {last}")


def call(to, data, block):
    return rpc("eth_call", [{"to": to, "data": data}, block])


def words(hexstr):
    b = hexstr[2:]
    return [int(b[i:i+64], 16) for i in range(0, len(b), 64)]


_ts_cache = {}


def block_ts(num):
    if num not in _ts_cache:
        b = rpc("eth_getBlockByNumber", [hex(num), False])
        _ts_cache[num] = int(b["timestamp"], 16)
    return _ts_cache[num]


def head_number():
    return int(rpc("eth_blockNumber", []), 16)


def block_at_ts(target, lo, lo_ts, hi, hi_ts):
    """Last block with timestamp <= target."""
    while hi - lo > 20:
        frac = (target - lo_ts) / (hi_ts - lo_ts)
        guess = lo + max(1, min(hi - lo - 1, int(frac * (hi - lo))))
        g_ts = block_ts(guess)
        if g_ts <= target:
            lo, lo_ts = guess, g_ts
        else:
            hi, hi_ts = guess, g_ts
    return lo, lo_ts


def month_ends(start_ym, end_ym):
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    while (y, m) <= (ey, em):
        last = calendar.monthrange(y, m)[1]
        ts = dt.datetime(y, m, last, 23, 59, 59, tzinfo=dt.timezone.utc).timestamp()
        yield f"{y:04d}-{m:02d}-{last:02d}", int(ts)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def get_ops(block):
    try:
        w = words(call(VALIDATOR_SET, S_OPS, block))
        n = w[1]
        return ["0x" + hex(x)[2:].rjust(40, "0") for x in w[2:2+n]]
    except RuntimeError:
        # pre-hardfork runtimes lack getValidatorOps(); walk the public
        # currentValidatorSet array (word0 of each entry = operator address)
        ops = []
        for i in range(50):
            try:
                w = words(call(VALIDATOR_SET, S_CVS + hex(i)[2:].rjust(64, "0"), block))
            except RuntimeError:
                break
            ops.append("0x" + hex(w[0])[2:].rjust(40, "0"))
        return ops


def core_agent_live(block):
    return rpc("eth_getCode", [CORE_AGENT, block]) not in (None, "0x")


def month_reading(block):
    """Return dict with per-method sums at block."""
    ops = get_ops(block)
    out = {"n_ops": len(ops)}
    if core_agent_live(block):
        amt = 0
        for op in ops:
            w = words(call(CORE_AGENT, S_CMAP + op[2:].rjust(64, "0"), block))
            amt += w[0]
        out["core_agent_amount"] = amt
    else:
        sums = None
        for op in ops:
            w = words(call(PLEDGE_AGENT, S_AMAP + op[2:].rjust(64, "0"), block))
            if sums is None:
                sums = [0] * len(w)
            for i, x in enumerate(w):
                sums[i] += x
        out["pledge_fields"] = sums
    return out


def main():
    head = head_number()
    head_ts_ = block_ts(head)
    lo, lo_ts = 1, block_ts(1)
    print(f"Core head {head} ({dt.datetime.fromtimestamp(head_ts_, dt.timezone.utc):%Y-%m-%d}), "
          f"block1 {dt.datetime.fromtimestamp(lo_ts, dt.timezone.utc):%Y-%m-%d %H:%M}")

    readings = []
    for month_end, target in month_ends(START_YM, END_YM):
        if target <= lo_ts:
            print(f"  {month_end}: before chain start -- skipped")
            continue
        bn, bn_ts = block_at_ts(target, lo, lo_ts, head, head_ts_)
        lo, lo_ts = bn, bn_ts  # months ascend; reuse as lower bound
        try:
            r = month_reading(hex(bn))
        except RuntimeError as ex:
            print(f"  {month_end} (block {bn}): FAILED {str(ex)[:120]}")
            continue
        r.update(month_end=month_end, block=bn)
        readings.append(r)
        if "core_agent_amount" in r:
            print(f"  {month_end} (block {bn}): {r['core_agent_amount']/1e18:,.0f} CORE "
                  f"(CoreAgent.amount, {r['n_ops']} active)")
        else:
            print(f"  {month_end} (block {bn}): legacy fields "
                  f"{[f'{x/1e18:,.0f}' for x in r['pledge_fields']]} ({r['n_ops']} active)")

    # pick legacy field by continuity at the upgrade boundary
    legacy = [r for r in readings if "pledge_fields" in r]
    modern = [r for r in readings if "core_agent_amount" in r]
    field_idx = None
    if legacy and modern:
        first_modern = modern[0]["core_agent_amount"]
        last_legacy = legacy[-1]["pledge_fields"]
        diffs = [(abs(x - first_modern), i) for i, x in enumerate(last_legacy) if x > 0]
        diffs.sort()
        field_idx = diffs[0][1]
        print(f"\nLegacy field selection: idx {field_idx}; boundary "
              f"{last_legacy[field_idx]/1e18:,.0f} (legacy) vs {first_modern/1e18:,.0f} (modern), "
              f"gap {(first_modern-last_legacy[field_idx])/last_legacy[field_idx]:+.1%}")
        print("  all legacy sums at boundary:", [f"{x/1e18:,.0f}" for x in last_legacy])

    # fresh cross-check vs staking API
    api = requests.get("https://staking-api.coredao.org/staking/summary/overall", timeout=20).json()
    fresh = int(api["data"]["stakedCoreAmount"]) / 1e18
    ours_latest = modern[-1]["core_agent_amount"] / 1e18
    drift = (ours_latest - fresh) / fresh
    print(f"\nCross-check: ours({modern[-1]['month_end']})={ours_latest:,.0f} "
          f"fresh(API now)={fresh:,.0f} drift={drift:+.2%}")

    with open("03_data/universe_panel.csv", encoding="utf-8") as f:
        supply = {r["month_end"][:7]: r["circulating_supply"]
                  for r in csv.DictReader(f) if r["cmc_id"] == str(CMC_ID)}

    rows = []
    for r in readings:
        if "core_agent_amount" in r:
            staked = r["core_agent_amount"] / 1e18
            item = "CoreAgent.candidateMap.amount"
        else:
            staked = r["pledge_fields"][field_idx] / 1e18
            item = f"PledgeAgent.agentsMap[word{field_idx}] (legacy pre-StakeHub)"
        cs = supply.get(r["month_end"][:7], "")
        ratio = ""
        if cs:
            try:
                csf = float(cs)
                if csf > 0:
                    ratio = staked / csf
            except ValueError:
                cs = ""
        rows.append({
            "cmc_id": CMC_ID, "symbol": "CORE", "month_end": r["month_end"],
            "staked_native": staked, "circulating_supply": cs, "staking_ratio": ratio,
            "source": "core-archiveRPC(ankr/drpc) eth_call: sum stake of ValidatorSet.getValidatorOps() actives at month-end block; validated == staking-api.coredao.org stakedCoreAmount",
            "flag": f"read {item} at block {r['block']}; active-validator staked CORE (excludes inactive candidates); CORE-only (BTC/hash dual-staking excluded)",
        })

    with open("03_data/phase1/channel1_core.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cmc_id", "symbol", "month_end", "staked_native",
                                          "circulating_supply", "staking_ratio", "source", "flag"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows to 03_data/phase1/channel1_core.csv")


if __name__ == "__main__":
    main()
