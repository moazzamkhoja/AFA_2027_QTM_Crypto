"""phase1_channel1_pos_coins_native.py -- SESSION 029 (Entry 78): coin Channel-1
staking series for PoS coins reachable through NON-Etherscan native chain APIs
(none of these chains are in Etherscan V2's 64-chain list -- probed live).
Companion to phase1_channel1_pos_coins.py (ADA/XTZ), _bucket2.py (TRX/SOL) and
_pos_coins_evm.py (BNB/S/GLMR/MOVR/XDC/CELO/AVAX/POL); same schema, picked up by
the channel1_*.csv glob in phase1_assemble_lambda.py.

Coins (each source response-body verified live this session; fetch stage scripts
_s029_coin_fetch.py / _s029_coin_fetch2.py cache raw month-end reads):

  RON  (cmc 14101) -- ronin.drpc.org keyless FULL archive (official RPC is pruned).
       Metric = sum(Staking.getManyStakingTotals(ValidatorSet.getValidatorCandidates))
       at month-end blocks -- the staking contract's own per-candidate accounting.
       Contract identities verified against axieinfinity/ronin-dpos-contracts
       deployments. The contract's native balance runs ~+16% above the sum (pending
       undelegations incl. revoked candidates) -> recorded as superset cross-check,
       NOT the metric.

  KAIA/KLAY (cmc 4256) -- archive-en.node.kaia.io (official, keyless archive).
       Metric = klay_getStakingInfo(block): councilStakingAmounts sum (+ CL staking
       when present) = the node's OWN consensus-staking snapshot (units: KAIA).
       Cross-check: the amounts equal the CnStaking contracts' native balances.

  FLR  (cmc 7950) -- flare-api.flare.network (official, keyless archive).
       Metric = PChainStakeMirror.totalSupply() (address from FlareContractRegistry)
       = total P-chain stake mirrored on the C-chain. Cross-check: live mirror vs
       P-chain platform.getTotalStake at ~-0.2%.

  EGLD (cmc 6892) -- tools.multiversx.com/growth-api (official, keyless): daily
       totalStaked back to 2020-07-30, month-end sample. Cross-check: chart head vs
       live api.multiversx.com/economics .staked at ~-0.1% (snapshot timing).
       Same source-of-record treatment as AVAX/Koios/TzKT (Entries 41/73).

  STRK (cmc 22691) -- rpc.starknet.lava.build keyless archive starknet_call.
       Metric = staking contract get_total_stake() (address from
       docs.starknet.io chain-info; the kickoff's 0x04718f... is the STRK TOKEN and
       0x00ca1705... the MINTING CURVE -- both ABI-verified). Series starts 2024-11
       (staking launch; short series kept per kickoff).

  XRD  (cmc 11948) -- mainnet.radixdlt.com Babylon Gateway (official, keyless),
       /state/validators/list with HISTORICAL at_ledger_state timestamps.
       Metric = sum(stake_vault.balance) over all validators. Babylon era only
       (2023-10+); Olympia era (2021-07..2023-09) = documented gap (gateway retired).

  DASH etc. NOT built -- see Entry 78 gap register (TON Elector superset live-only,
       FLOW spork-bound, DFI ocean current-only, DASH no free masternode-count
       history, WAN explorer HTML-only, HYPE live-only, CRO Cosmos-side [ATOM gate],
       CHZ semantics anchor manual action, LSK no locatable staking contract,
       CORE openapi key-gated).

  PEAQ (cmc 14588) -- peaq.api.onfinality.io/public keyless archive. peaq's pallet
       is a KILT fork: ParachainStaking.TotalCollatorStake {collators, delegators}
       (Moonbeam's .Total is null on peaq -- probed). Metric = collators+delegators.

Denominator = circulating supply from the Phase 0 universe panel (cmc_id + month_end
join only). No interpolation, no carry-forward.
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_pos_coins_native.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"


def _load(name):
    cf = RAW / name
    if not cf.exists():
        raise RuntimeError(f"missing raw cache {cf} -- run the _s029 fetch scripts")
    return json.loads(cf.read_text())


def ron_series():
    cache = _load("ron_staking_history.json")
    ser, sup = {}, []
    for ym, v in cache.items():
        if v.get("total"):
            tot = int(v["total"])
            if tot > 0:
                ser[ym] = tot / 1e18
                if v.get("balance"):
                    sup.append(int(v["balance"]) / tot)
    if sup and not (0.99 <= min(sup) and max(sup) < 1.5):
        raise RuntimeError(f"RON balance/total superset broke [0.99,1.5): "
                           f"{min(sup):.3f}..{max(sup):.3f}")
    print(f"  RON superset: balance/candidate-stake in [{min(sup):.3f}, {max(sup):.3f}]")
    return ser, ("ronin.drpc.org archive: sum(Staking.getManyStakingTotals("
                 "getValidatorCandidates)) at month-end blocks; contract identities "
                 "from axieinfinity/ronin-dpos-contracts deployments"), \
        ("metric = stake on active validator candidates; contract native balance "
         "(stake + pending/revoked undelegations) recorded as superset cross-check "
         "~1.0-1.3x")


def kaia_series():
    cache = _load("kaia_staking_history.json")
    ser = {}
    for ym, v in cache.items():
        if v.get("council_sum"):
            ser[ym] = v["council_sum"] + (v.get("cl_sum") or 0)   # units: KAIA
    return ser, ("archive-en.node.kaia.io (official) klay_getStakingInfo at month-end "
                 "blocks: councilStakingAmounts sum (+CL staking when present) -- the "
                 "node's own consensus staking snapshot"), \
        ("governance-council staking (CnStaking contract balances the chain itself "
         "uses for GC weighting); cross-checked amounts == contract balances")


def flr_series():
    cache = _load("flr_staking_history.json")
    ser = {}
    for ym, v in cache.items():
        if v.get("total"):
            t = int(v["total"])
            if t > 0:
                ser[ym] = t / 1e18
    # live cross-check: mirror vs P-chain (Entry-26)
    p = requests.post("https://flare-api.flare.network/ext/bc/P", json={
        "jsonrpc": "2.0", "id": 1, "method": "platform.getTotalStake",
        "params": {"subnetID": "11111111111111111111111111111111LpoYY"}},
        timeout=25, headers={"content-type": "application/json"}).json()
    pv = int(p["result"]["stake"]) / 1e9
    last = ser[max(ser)]
    drift = (last - pv) / pv
    print(f"  FLR cross-check: mirror last-month {last:,.0f} vs live P-chain "
          f"getTotalStake {pv:,.0f} -> {drift:+.2%} (month-end vs live timing)")
    if abs(drift) > 0.10:
        raise RuntimeError("FLR mirror vs P-chain drift too large; not shipping")
    return ser, ("flare-api.flare.network archive eth_call PChainStakeMirror."
                 "totalSupply() at month-end blocks (address from the "
                 "FlareContractRegistry); live-verified vs P-chain "
                 "platform.getTotalStake ~0.2%"), \
        "P-chain validator+delegator stake as mirrored on the C-chain"


def egld_series():
    rows = _load("egld_staking_history.json")["rows"]
    import datetime as dt
    daily = {}
    for r in rows:
        d = dt.date.fromisoformat(r["time"][:10])
        daily[d] = r["value"]
    ser = {}
    for d in sorted(daily):
        nxt = d + dt.timedelta(days=1)
        if nxt.month != d.month:
            ser[f"{d.year:04d}-{d.month:02d}"] = daily[d]
    live = requests.get("https://api.multiversx.com/economics", timeout=25).json()["staked"]
    head = rows[-1]["value"]
    drift = (head - live) / live
    print(f"  EGLD cross-check: chart head {head:,} vs live economics.staked {live:,} "
          f"-> {drift:+.2%}")
    if abs(drift) > 0.02:
        raise RuntimeError("EGLD chart vs live economics drift >2%; not shipping")
    return ser, ("tools.multiversx.com/growth-api staking-metrics daily totalStaked, "
                 "month-end sample; cross-checked vs live api.multiversx.com/economics"), \
        "official first-party series (AVAX/Koios/TzKT source-of-record treatment)"


def strk_series():
    cache = _load("strk_staking_history.json")
    ser = {}
    for ym, v in cache.items():
        if ym.startswith("_"):
            continue
        if v.get("total"):
            ser[ym] = int(v["total"]) / 1e18
    return ser, ("rpc.starknet.lava.build archive starknet_call get_total_stake() on "
                 "the official staking contract (docs.starknet.io chain-info) at "
                 "month-end blocks"), \
        ("series starts 2024-11 (staking launch) -- short series kept per kickoff; "
         "STRK-only stake (v2 BTC staking power excluded)")


def xrd_series():
    cache = _load("xrd_staking_history.json")
    ser = {}
    for ym, v in cache.items():
        if v.get("total"):
            ser[ym] = v["total"]
    return ser, ("mainnet.radixdlt.com Babylon Gateway /state/validators/list with "
                 "historical at_ledger_state timestamps: sum(stake_vault.balance) "
                 "over all validators"), \
        ("Babylon era only (2023-10+); Olympia era 2021-07..2023-09 = documented gap "
         "(the retired Olympia gateway served that history)")


def peaq_series():
    cache = _load("peaq_staking_history.json")
    ser = {}
    for ym, v in cache.items():
        if ym.startswith("_"):
            continue
        if v.get("collators") is not None:
            ser[ym] = (int(v["collators"]) + int(v["delegators"])) / 1e18
    return ser, ("peaq.api.onfinality.io/public archive state_getStorage "
                 "ParachainStaking.TotalCollatorStake (KILT-fork pallet: collators + "
                 "delegators) at month-end blocks"), \
        ("chain's own staking-pallet aggregate (GLMR/MOVR state-read standard); early "
         "months staking_ratio>1 vs CMC circulating (genesis/vesting-locked stake CMC "
         "excludes) -- kept un-capped and flagged, the SOL/AERO/AVAX precedent")


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

    for cid, sym, fn in [(14101, "RON", ron_series), (4256, "KLAY", kaia_series),
                         (7950, "FLR", flr_series), (6892, "EGLD", egld_series),
                         (22691, "STRK", strk_series), (11948, "XRD", xrd_series),
                         (14588, "PEAQ", peaq_series)]:
        print(f"{sym}:")
        s, src, fl = fn()
        add(cid, sym, s, src, fl)

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
