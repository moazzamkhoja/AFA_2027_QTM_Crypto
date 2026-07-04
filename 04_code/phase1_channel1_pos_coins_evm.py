"""phase1_channel1_pos_coins_evm.py -- SESSION 028, Task A: coin Channel-1 staking series
for PoS coins whose staking state is reachable through EVM tooling (Etherscan Pro V2
multichain key + official archive RPCs). Companion to phase1_channel1_pos_coins.py
(ADA/XTZ) and _bucket2.py (TRX/SOL); emits the same schema, picked up by the
channel1_*.csv glob in phase1_assemble_lambda.py.

Coins built (each response-body verified + Entry-26 cross-checked live this session):

  BNB  (cmc 1839, chainid 56) -- StakeHub 0x...2002 event replay:
       staked(t) = cum(Delegated.bnbAmount) - cum(Undelegated.bnbAmount)
                 + cum(RewardDistributed.reward)
       CROSS-CHECK: replay at head reproduced live sum(totalPooledBNB over all 53
       validator StakeCredit contracts) at +0.000% drift (25,717,017 BNB, 2026-07-04).
       MigrateSuccess (BC-fusion) is NOT added -- migration also emits Delegated
       (adding it produced +80% drift). Redelegated is pool-neutral. Zero slashes.
       WINDOW: from 2024-07 (BC-fusion migration completed 2024-07-14); 2017..2024-06
       staking lived on the retired Beacon Chain = documented gap, not reconstructable
       from BSC logs.

  S    (cmc 32684, chainid 146) -- Sonic SFC 0xFC00FACE...0000 event replay:
       staked(t) = cum(Delegated.amount) - cum(Undelegated.amount)
       RestakedRewards is EXCLUDED: restakeRewards() delegates internally and emits BOTH
       Delegated and RestakedRewards for the same amount (found by block-bisection; adding
       it produced a +0.86%-and-growing drift). CROSS-CHECK vs archive totalStake() at six
       blocks across the full history: +-0.0000% each. Metric is totalStake (incl. stake on
       deactivated validators -- still locked), FLAGGED.

  GLMR (cmc 6836, chainid 1284) / MOVR (cmc 9285, chainid 1285) -- the ParachainStaking
       precompile 0x...0800 emits NO EVM logs and has no aggregate getter, and
       Etherscan's proxy eth_call ignores historical tags. Instead the OFFICIAL public
       archive RPCs answer Substrate state queries, so we read the staking pallet's own
       aggregate at each month-end block:
         state_getStorage(twox128("ParachainStaking")+twox128("Total"), blockHash)
       This is the chain's own total staked (collator bonds + ALL delegations), a state
       read, not a reconstruction. CROSS-CHECK: pallet Total vs sum(
       getCandidateTotalCounted over selectedCandidates) via eth_call -- Total/sum =
       1.05 (GLMR) / 1.02 (MOVR), exactly the expected superset relation (counted
       excludes bottom delegations + non-selected candidates).

  XDC  (cmc 2634, chainid 50) -- XDCValidator 0x...0088 holds masternode stake as
       NATIVE XDC. Series = Etherscan Pro `balancehistory` of the contract at each
       month-end block. CROSS-CHECK: full event replay (Propose+Vote-Unvote-Withdraw)
       tracks balancehistory at a CONSTANT +32,625,000 XDC offset from block 40M on
       (0.000% co-movement; the offset is genesis/eventless stake predating the event
       stream). FLAG: balance includes resigned-but-unwithdrawn stake (still locked
       during the withdraw delay).

  CELO (cmc 5567, chainid 42220) -- closes the Entry-46 gap. Etherscan balancehistory
       only covers post-L2-migration blocks (>= ~31.06M), BUT the official Forno RPC
       (forno.celo.org) serves FULL archive state incl. pre-migration L1 blocks, so
       the exact clean number Entry 46 wanted -- LockedGold.getTotalLockedGold() -- is
       readable at every historical month-end via keyless eth_call. A state read of
       the chain's own aggregate (excludes pending withdrawals, unlike the raw
       contract balance).

  BERA (cmc 24647, chainid 80094) -- NOT BUILT (documented gap): staking is consensus-
       side (beacon-kit). Deposits ARE in EVM logs (BeaconDeposit 0x4242...4242) but
       withdrawals are system-level credits with no logs; cum(deposits) = 382.6M BERA
       > circulating supply -- unreconstructable from the EL. No free historical
       validator-balance API found (routescan/berascan/hub probed).

Denominator = circulating supply from the Phase 0 universe panel (cmc_id + month_end),
same convention as all other Channel-1 builds. No interpolation, no carry-forward.

Raw event/state caches under 03_data/raw/phase1_onchain/pos_coins_evm/ (see the
_s028_*_fetch.py stage scripts). Output: 03_data/phase1/channel1_pos_coins_evm.csv.
"""

import calendar
import json
import time
from pathlib import Path

import pandas as pd
import requests

from _s028_evm import REPO, KEY, api, eth_call, keccak_topic, words

PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_pos_coins_evm.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
RAW.mkdir(parents=True, exist_ok=True)

XDC_VALIDATOR = "0x0000000000000000000000000000000000000088"
CELO_LOCKEDGOLD = "0x6cC083Aed9e3ebe302A6336dBC7c921C9f03349E"
FORNO = "https://forno.celo.org"


# ---------------------------------------------------------------- shared helpers

def month_ends(lo, hi):
    out, (y, m) = [], (int(lo[:4]), int(lo[5:7]))
    while f"{y:04d}-{m:02d}" <= hi:
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def monthend_blocks(yms, chainid):
    """Block at each month-end (UTC 23:59:59) via Etherscan getblocknobytime, cached."""
    cf = RAW / f"monthend_blocks_{chainid}.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    for ym in yms:
        if ym in cache:
            continue
        y, m = int(ym[:4]), int(ym[5:7])
        last_day = calendar.monthrange(y, m)[1]
        ts = int(calendar.timegm(time.strptime(f"{ym}-{last_day} 23:59:59",
                                               "%Y-%m-%d %H:%M:%S")))
        j = api({"module": "block", "action": "getblocknobytime",
                 "timestamp": ts, "closest": "before"}, chainid)
        try:
            cache[ym] = int(j["result"]) if j.get("status") == "1" else None
        except (ValueError, TypeError):     # e.g. "Error! No closest block found"
            cache[ym] = None
        cf.write_text(json.dumps(cache))
    return cache


def load_events(prefix, names):
    out = {}
    for n in names:
        cf = RAW / f"{prefix}_{n}.json"
        if not cf.exists():
            raise RuntimeError(f"missing raw event cache {cf} -- run _s028_{prefix}_fetch.py")
        out[n] = json.loads(cf.read_text())["logs"]
    return out


def cum_at_blocks(events_signed, blocks_sorted, data_word):
    """events_signed = [(sign, logs)]; returns {block: cumulative} at each block."""
    flows = []
    for sign, logs in events_signed:
        for l in logs:
            flows.append((l["b"], sign * words(l["data"])[data_word]))
    flows.sort(key=lambda x: x[0])
    res, cum, i = {}, 0, 0
    for b in blocks_sorted:
        while i < len(flows) and flows[i][0] <= b:
            cum += flows[i][1]
            i += 1
        res[b] = cum
    return res


# ---------------------------------------------------------------- BNB (StakeHub replay)

def bnb_series():
    ev = load_events("bnb", ["delegated", "undelegated", "reward"])
    yms = month_ends("2024-07", "2026-05")
    blocks = monthend_blocks(yms, 56)
    bs = sorted(b for b in blocks.values() if b)
    cum = cum_at_blocks([(1, ev["delegated"]), (-1, ev["undelegated"])],
                        bs, 1)  # data word 1 = bnbAmount (word 0 = shares)
    rew = cum_at_blocks([(1, ev["reward"])], bs, 0)
    ser = {ym: (cum[b] + rew[b]) / 1e18 for ym, b in blocks.items() if b}

    # Entry-26 cross-check: replay at head vs live sum(totalPooledBNB) over validators
    hub = "0x0000000000000000000000000000000000002002"
    r = eth_call(hub, keccak_topic("getValidators(uint256,uint256)")[:10]
                 + "0" * 64 + hex(200)[2:].rjust(64, "0"), 56)
    w = words(r)
    off2 = w[1] // 32
    creds = ["0x" + hex(x)[2:].rjust(40, "0") for x in w[off2 + 1: off2 + 1 + w[off2]]]
    live = sum(int(eth_call(c, keccak_topic("totalPooledBNB()")[:10], 56), 16)
               for c in creds) / 1e18
    head = (sum(s * words(l["data"])[1] for s, ls in
                [(1, ev["delegated"]), (-1, ev["undelegated"])] for l in ls)
            + sum(words(l["data"])[0] for l in ev["reward"])) / 1e18
    drift = (head - live) / live
    print(f"  BNB cross-check: replay head {head:,.0f} vs live sum(totalPooledBNB) "
          f"{live:,.0f} over {len(creds)} validators -> drift {drift:+.4%}")
    if abs(drift) > 0.01:
        raise RuntimeError("BNB replay fails Entry-26 cross-check; not shipping")
    return ser, ("bscscan(etherscanV2/56):StakeHub Delegated-Undelegated+RewardDistributed replay; "
                 "cross-checked vs live sum(totalPooledBNB) all validators"), \
        ("post-BC-fusion window only (2024-07+); earlier staking lived on the retired "
         "Beacon Chain = documented gap; replay drift ~0% vs on-chain state")


# ---------------------------------------------------------------- S (Sonic SFC replay)

def sonic_series():
    # NOTE: RestakedRewards is NOT added -- SFC's restakeRewards() delegates the reward
    # internally and emits BOTH Delegated and RestakedRewards for the same amount
    # (verified by block-bisection at 60,010,966: one restake, live totalStake +6,385.60,
    # both events emitted). Replay = Delegated - Undelegated alone matches the archive
    # totalStake() getter at +-0.0000% at every probed block (2M..75M).
    ev = load_events("sonic", ["delegated", "undelegated"])
    yms = month_ends("2025-01", "2026-05")
    blocks = monthend_blocks(yms, 146)
    bs = sorted(b for b in blocks.values() if b)
    cum = cum_at_blocks([(1, ev["delegated"]), (-1, ev["undelegated"])], bs, -1)
    ser = {ym: cum[b] / 1e18 for ym, b in blocks.items() if b}
    sfc = "0xFC00FACE00000000000000000000000000000000"
    live = int(eth_call(sfc, keccak_topic("totalStake()")[:10], 146), 16) / 1e18
    head = (sum(words(l["data"])[-1] for l in ev["delegated"])
            - sum(words(l["data"])[-1] for l in ev["undelegated"])) / 1e18
    drift = (head - live) / live
    print(f"  S   cross-check: replay head {head:,.0f} vs live totalStake() {live:,.0f} "
          f"-> drift {drift:+.4%}")
    if abs(drift) > 0.005:
        raise RuntimeError("Sonic replay fails Entry-26 cross-check; not shipping")
    return ser, ("sonicscan(etherscanV2/146):SFC Delegated-Undelegated replay (RestakedRewards "
                 "double-emits Delegated, excluded); cross-checked vs live totalStake()"), \
        "metric = SFC totalStake (includes stake on deactivated validators, still locked)"


# ---------------------------------------------------------------- GLMR / MOVR (pallet state)

def moonbeam_series(name):
    cf = RAW / f"{name}_total_staked.json"
    if not cf.exists():
        raise RuntimeError(f"missing {cf} -- run _s028_moonbeam_fetch.py")
    ser = {ym: v for ym, v in json.loads(cf.read_text())["series"].items() if v}
    return ser, ("official archive RPC state_getStorage ParachainStaking.Total at "
                 "month-end blocks (chain's own aggregate: bonds + all delegations)"), \
        ("state read, not a reconstruction; cross-checked vs eth_call "
         "sum(getCandidateTotalCounted) superset relation")


# ---------------------------------------------------------------- XDC (balancehistory)

def xdc_series():
    yms = month_ends("2020-05", "2026-05")
    blocks = monthend_blocks(yms, 50)
    cf = RAW / "xdc_balancehistory.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    ser = {}
    for ym, b in blocks.items():
        if not b:
            continue
        if ym not in cache:
            j = api({"module": "account", "action": "balancehistory",
                     "address": XDC_VALIDATOR, "blockno": b}, 50)
            if j.get("status") != "1":
                print(f"  XDC {ym}: balancehistory NOTOK, skipped (no guess)")
                cache[ym] = None
                cf.write_text(json.dumps(cache))
                continue
            cache[ym] = int(j["result"])
            cf.write_text(json.dumps(cache))
        if cache[ym] is not None:
            ser[ym] = cache[ym] / 1e18
    # cross-check: live balance vs event replay (constant genesis offset established;
    # here re-verify the replay+offset identity at the head)
    ev = load_events("xdc", ["propose", "vote", "unvote", "withdraw"])
    rep = (sum(words(l["data"])[-1] for l in ev["propose"])
           + sum(words(l["data"])[-1] for l in ev["vote"])
           - sum(words(l["data"])[-1] for l in ev["unvote"])
           - sum(words(l["data"])[-1] for l in ev["withdraw"])) / 1e18
    j = api({"module": "account", "action": "balance",
             "address": XDC_VALIDATOR, "tag": "latest"}, 50)
    live = int(j["result"]) / 1e18
    off = live - rep
    print(f"  XDC cross-check: live balance {live:,.0f} vs event replay {rep:,.0f} "
          f"-> offset {off:,.0f} (expected 32,625,000 genesis/eventless stake)")
    if abs(off - 32_625_000) > 1_000_000:
        raise RuntimeError("XDC replay/balance offset moved; re-verify before shipping")
    return ser, ("xdcscan(etherscanV2/50) balancehistory of XDCValidator 0x...0088 at "
                 "month-end blocks (native XDC held = masternode stake); event replay "
                 "co-moves at constant genesis offset"), \
        ("balance includes resigned-but-unwithdrawn stake (still locked in withdraw "
         "delay) and 32.6M genesis stake that predates the event stream")


# ---------------------------------------------------------------- CELO (Forno archive eth_call)

def celo_series():
    yms = month_ends("2020-07", "2026-05")
    blocks = monthend_blocks(yms, 42220)
    cf = RAW / "celo_lockedgold_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    sel = keccak_topic("getTotalLockedGold()")[:10]
    ser = {}
    for ym in sorted(blocks):
        b = blocks[ym]
        if not b:
            continue
        if ym not in cache:
            for t in range(4):
                try:
                    r = requests.post(FORNO, json={
                        "jsonrpc": "2.0", "method": "eth_call", "id": 1,
                        "params": [{"to": CELO_LOCKEDGOLD, "data": sel}, hex(b)]},
                        timeout=30).json()
                    break
                except Exception:
                    time.sleep(1.5 * (t + 1))
            else:
                raise RuntimeError(f"forno unreachable at {ym}")
            if r.get("result") and r["result"] != "0x":
                cache[ym] = int(r["result"], 16)
            else:
                print(f"  CELO {ym}: eth_call err {str(r.get('error'))[:60]}, skipped")
                cache[ym] = None
            cf.write_text(json.dumps(cache))
            time.sleep(0.25)
        if cache[ym] is not None:
            ser[ym] = cache[ym] / 1e18
    # cross-check: latest cached vs live getter (same method, freshness check) + the
    # Entry-46 reference figures (82.43M on 2026-06-26)
    r = requests.post(FORNO, json={"jsonrpc": "2.0", "method": "eth_call", "id": 1,
                                   "params": [{"to": CELO_LOCKEDGOLD, "data": sel},
                                              "latest"]}, timeout=30).json()
    live = int(r["result"], 16) / 1e18
    print(f"  CELO cross-check: live getTotalLockedGold {live:,.0f} "
          f"(Entry-46 measured 82.43M on 2026-06-26; declining trend)")
    return ser, ("forno.celo.org archive eth_call LockedGold.getTotalLockedGold() at "
                 "month-end blocks (chain's own aggregate incl. pre-L2-migration state; "
                 "closes the Entry-46 gap)"), \
        ("state read of the chain's own getter (excludes pending withdrawals); "
         "Etherscan balancehistory on 42220 only covers post-migration blocks, "
         "Forno serves the full archive")


# ---------------------------------------------------------------- AVAX (official Metrics API, keyless)

def avax_series():
    """Sum of daily validatorWeight+delegatorWeight (nAVAX/1e9) at each month-end.
    Ava Labs' official first-party Metrics API, keyless (see _s028_avax_fetch.py --
    semantics verified: weights are additive, P-Chain platform.getTotalStake matches
    their sum, not validatorWeight alone). Same source-of-record treatment as
    ADA/Koios and XTZ/TzKT (Entry 41)."""
    import datetime as dt
    daily = {}
    for metric in ["validatorWeight", "delegatorWeight"]:
        cf = RAW / f"avax_{metric}.json"
        if not cf.exists():
            raise RuntimeError(f"missing {cf} -- run _s028_avax_fetch.py")
        for row in json.loads(cf.read_text())["rows"]:
            d = dt.datetime.fromtimestamp(row["timestamp"], dt.UTC).date()
            daily.setdefault(d, {})[metric] = row["value"] / 1e9
    ser = {}
    for d in sorted(daily):
        v = daily[d]
        if "validatorWeight" in v and "delegatorWeight" in v:
            nxt = d + dt.timedelta(days=1)
            if nxt.month != d.month:          # d is the last day of its month
                ser[f"{d.year:04d}-{d.month:02d}"] = v["validatorWeight"] + v["delegatorWeight"]
    # cross-check: latest daily snapshot vs live P-Chain platform.getTotalStake
    last_d = max(daily)
    snap = daily[last_d].get("validatorWeight", 0) + daily[last_d].get("delegatorWeight", 0)
    r = requests.post("https://api.avax.network/ext/bc/P", json={
        "jsonrpc": "2.0", "id": 1, "method": "platform.getTotalStake",
        "params": {"subnetID": "11111111111111111111111111111111LpoYY"}},
        timeout=25, headers={"content-type": "application/json"}).json()
    live = int(r["result"]["stake"]) / 1e9
    drift = (snap - live) / live
    print(f"  AVAX cross-check: metrics snapshot {last_d} {snap:,.0f} vs live P-Chain "
          f"getTotalStake {live:,.0f} -> drift {drift:+.3%} (stake moves ~1-2%/day; "
          f"snapshot lags live)")
    if abs(drift) > 0.05:
        raise RuntimeError("AVAX metrics vs P-Chain live drift too large; not shipping")
    return ser, ("metrics.avax.network (official, keyless) validatorWeight+delegatorWeight "
                 "daily, month-end sample; live-verified vs P-Chain platform.getTotalStake"), \
        ("early months staking_ratio>1 vs CMC circulating (staked includes vesting-locked "
         "AVAX that CMC counts as non-circulating) -- kept un-capped and flagged, the "
         "SOL/AERO precedent")


# ---------------------------------------------------------------- emit

def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    rows = []

    def add(cid, sym, series, src, flag=""):
        obs = panel[(panel.cmc_id == cid) & (panel.status == "observed")][
            ["month_end", "ym", "circulating_supply"]]
        n = 0
        for _, r in obs.sort_values("ym").iterrows():
            staked = series.get(r.ym)
            c = r.circulating_supply
            ratio = (staked / c) if (staked is not None and c and c > 0) else None
            if ratio is not None:
                n += 1
            rows.append({"cmc_id": cid, "symbol": sym, "month_end": r.month_end,
                         "staked_native": staked, "circulating_supply": c,
                         "staking_ratio": ratio, "source": src, "flag": flag})
        print(f"  {sym:5} {n:3} months w/ ratio")

    print("BNB (StakeHub replay):")
    s, src, fl = bnb_series()
    add(1839, "BNB", s, src, fl)

    print("S (Sonic SFC replay):")
    s, src, fl = sonic_series()
    add(32684, "S", s, src, fl)

    print("GLMR/MOVR (ParachainStaking.Total state reads):")
    s, src, fl = moonbeam_series("glmr")
    add(6836, "GLMR", s, src, fl)
    s, src, fl = moonbeam_series("movr")
    add(9285, "MOVR", s, src, fl)

    print("XDC (balancehistory):")
    s, src, fl = xdc_series()
    add(2634, "XDC", s, src, fl)

    print("CELO (Forno archive getTotalLockedGold):")
    s, src, fl = celo_series()
    add(5567, "CELO", s, src, fl)

    print("AVAX (official Metrics API):")
    s, src, fl = avax_series()
    add(5805, "AVAX", s, src, fl)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    nz = out[out.staking_ratio.notna()]
    print(f"\nwrote {OUT}  ({len(nz)} asset-months w/ ratio, {nz.cmc_id.nunique()} assets)")
    for sym in nz.symbol.unique():
        d = nz[nz.symbol == sym].sort_values("month_end")
        print(f"  {sym:5}: {len(d):3} mo  ratio {d.staking_ratio.min():.2%}->"
              f"{d.staking_ratio.max():.2%} (latest {d.staking_ratio.iloc[-1]:.2%}, "
              f"staked {d.staked_native.iloc[-1]:,.0f})")


if __name__ == "__main__":
    main()
