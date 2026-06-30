"""
phase1_channel3_onchain_delegation.py  --  SESSION 024, Task A: Channel-3 on-chain
governance-delegation sub-channel, reconstructed from `DelegateVotesChanged` event replay.

CONSTRUCT (decided & documented -- Entry 57):
  This is a DISTINCT sub-channel from the Snapshot voter-turnout of Channel 3 (Entry 25),
  NOT the same measure sourced differently. Snapshot `vw_turnout` is a FLOW (token-weighted
  voters who actually voted, per proposal, in a month). On-chain delegated voting weight is a
  STOCK: the share of supply that holders have *activated for governance* by delegating it
  (incl. self-delegation) -- in Governor/ERC20Votes systems tokens count toward votes ONLY
  once delegated, so "delegated weight outstanding / circulating" measures governance
  ACTIVATION, a conviction signal, not per-proposal participation. Because the construct
  differs it is written to its own file `channel3_onchain_delegation.csv` and enters lambda
  as a separate channel `ch3_delegation` (z-scored in its own monthly cross-section), NOT
  merged into channel3_voting.csv.

GOVERNANCE-CHANNEL WATERFALL (avoids double-counting governance in lambda):
  Of the 34 getLogs-CONFIRMED ERC20Votes-ACTIVE tokens (universe_lambda_channel_map.csv),
  10 ALREADY have a Snapshot Channel-3 turnout series (GTC/ENS/HFT/MNT/COMP/SUSHI/UNI/RGT/
  KP3R/STRK). For those, on-chain delegation is computed as a CROSS-CHECK only (role=
  cross_check) and is EXCLUDED from lambda -- a token already represented in governance-lambda
  via Snapshot turnout is not also counted via delegation. The remaining 24 are NET-NEW (no
  Snapshot turnout); their delegation series is the PRIMARY governance channel (role=primary,
  enters lambda). One of the 24 -- ETHDYDX -- is EXCLUDED on mechanism grounds (see below).

METHOD (Entry 21 "logs not eth_call"; same getLogs event-replay template as eth_staking):
  topic0(DelegateVotesChanged(address,uint256,uint256)) = 0xdec2bacd...a724  (22 tokens)
  topic0(DelegateVotesChanged(address,uint96,uint96))   = 0x664ef4a2...231e  (DDX)
  delegate = topic1 (indexed); data = previousBalance(32) ++ newBalance(32). Replay ALL logs
  in (block, logIndex) order tracking each delegate's latest newBalance; at each month-end
  block, total delegated weight = sum of latest newBalance over all delegates. Decimals read
  once via eth_call decimals() (immutable -> latest is correct). Free getLogs chains only
  (Ethereum 1 / Arbitrum 42161 / Blast 81457). Respects each asset's observed panel window.

EXCLUDED (mechanism, the AKRO/Entry-55 "verify before building" discipline):
  ETHDYDX (cmc 11156) -- its event is `DelegatedPowerChanged(address,uint256,uint8)` (Aave/
  dYdX governance-power model), where EVERY holder carries voting power by default (power is
  not opt-in via delegation; it tracks balance). Summed power outstanding ~= total supply
  every month -> ratio ~1, which measures "supply exists", NOT governance activation. It is
  NOT the opt-in ERC20Votes delegation construct, so it is flagged & excluded, not shipped as
  a degenerate ratio. Re-open in Phase 2 with a proper Aave-power treatment if needed.

Output: 03_data/phase1/channel3_onchain_delegation.csv  (role, delegation_ratio, ...)
        03_data/raw/phase1_onchain/delegation/<SYM>.json  (resumable per-token checkpoint)
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel3_onchain_delegation.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "delegation"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = 0.22

TOPIC_U256 = "0xdec2bacdd2f05b59de34da9b523dff8be42e5e38e818c82fdb0bae774387a724"
TOPIC_U96 = "0x664ef4a22338e827df5b675ec1747eac10c2ea611e1c575f3d96c38a2e24231e"

# cmc_id, symbol, chainid, address, topic0, role
#   role: 'primary'  -> NET-NEW (no Snapshot turnout); enters lambda as ch3_delegation
#         'crosscheck'-> already has a Snapshot Channel-3 series; computed for comparison only
TOKENS = [
    # ---- NET-NEW primary (24 ERC20Votes-ACTIVE without a Snapshot turnout series) ----
    (23121, "BLUR",   1,     "0x5283d291dbcf85356a21ba090e6db59121208b44", TOPIC_U256, "primary"),
    (11584, "BTRST",  1,     "0x799ebfabe77a6e34311eeee9825190b9ece32824", TOPIC_U256, "primary"),
    (38341, "RAIN",   42161, "0x25118290e6A5f4139381D072181157035864099d", TOPIC_U256, "primary"),
    (23246, "TOMI",   1,     "0x4385328cc4d643ca98dfea734360c0f596c83449", TOPIC_U256, "primary"),
    (32257, "UXLINK", 42161, "0x1a6b3a62391eccaaa992ade44cd4afe6bec8cff1", TOPIC_U256, "primary"),
    (11221, "BIT",    1,     "0x1A4b46696b2bB4794Eb3D4c26f1c55F9170fa4C5", TOPIC_U256, "primary"),
    (28480, "BLAST",  81457, "0xb1a5700fA2358173Fe465e6eA4Ff52E36e88E2ad", TOPIC_U256, "primary"),
    (11865, "BONE",   1,     "0x9813037ee2218799597d83D4a5B6F3b6778218d9", TOPIC_U256, "primary"),
    (6669,  "CVP",    1,     "0x38e4adb44ef08f22f5b5b76a8f0c2d0dcbe7dca1", TOPIC_U256, "primary"),
    (24781, "CYBER",  1,     "0x14778860e937f509e651192a90589de711fb88a9", TOPIC_U256, "primary"),
    (7228,  "DDX",    1,     "0x3a880652f47bfaa771908c07dd8673a787daed3a", TOPIC_U96,  "primary"),
    (5741,  "DMG",    1,     "0xEd91879919B71bB6905f23af0A68d231EcF87b14", TOPIC_U256, "primary"),
    (30494, "EIGEN",  1,     "0xec53bF9167f50cDEB3Ae105f56099aaaB9061F83", TOPIC_U256, "primary"),
    (14280, "EUL",    1,     "0xd9fcd98c322942075a5c3860693e9f4f03aae07b", TOPIC_U256, "primary"),
    (10508, "FLUID",  1,     "0x6f40d4A6237C257fff2dB00FA0510DeEECd303eb", TOPIC_U256, "primary"),
    (9421,  "FORTH",  1,     "0x77fba179c79de5b7653f68b5039af940ada60ce0", TOPIC_U256, "primary"),
    (2873,  "MET",    1,     "0x2Ebd53d035150f328bd754D6DC66B99B0eDB89aa", TOPIC_U256, "primary"),
    (21159, "ONDO",   1,     "0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3", TOPIC_U256, "primary"),
    (5354,  "PEAK",   1,     "0x630d98424efe0ea27fb1b3ab7741907dffeaad78", TOPIC_U256, "primary"),
    (6843,  "RAD",    1,     "0x31c8eacbffdd875c74b94b077895bd78cf1e64a3", TOPIC_U256, "primary"),
    (17751, "T",      1,     "0xCdF7028ceAB81fA0C6971208e83fa7872994beE5", TOPIC_U256, "primary"),
    (29587, "W",      1,     "0xB0fFa8000886e57F86dd5264b9582b2Ad87b2b91", TOPIC_U256, "primary"),
    (33251, "WLFI",   1,     "0xdA5e1988097297dCdc1f90D4dFE7909e847CBeF6", TOPIC_U256, "primary"),
    # ETHDYDX (11156) intentionally OMITTED -- DelegatedPowerChanged/Aave-power model, ratio~1.
    # ---- SESSION 025 P2-2: BSC/Base/Optimism/Linea ERC20Votes tokens, now buildable on the
    #      Etherscan Pro key (Entry 61). All 7 below VERIFIED FIRING via phase1_p2p2_probe.py
    #      (DelegateVotesChanged actually emits with newBalance>0). The other 8 P2-2 Ch-3
    #      candidates (BAKE/BNX/EDG/ESPORTS/MCT/MDX/PONKE/TKO) are DORMANT -- ERC20Votes ABI
    #      present but the delegation event NEVER fired (0 logs on both topics) -> NOT built
    #      (no conviction signal; the AKRO "verify the mechanism" discipline). All net-new
    #      (no Snapshot turnout series) -> role=primary.
    (10897, "ALT",     56,    "0x5ca09af27b8a4f1d636380909087536bc7e2d94d", TOPIC_U256, "primary"),
    (4006,  "AWE",     8453,  "0x1B4617734C43F6159F3a70b7E06d883647512778", TOPIC_U256, "primary"),
    (23054, "CHEEL",   56,    "0x1F1C90aEb2fd13EA972F0a71e35c0753848e3DB0", TOPIC_U256, "primary"),
    (23635, "FORM",    56,    "0x5b73A93b4E5e4f1FD27D8b3F8C97D69908b5E284", TOPIC_U256, "primary"),
    (27657, "LINEA",   59144, "0x1789e0043623282d5dcc7f213d703c6d8bafbb04", TOPIC_U256, "primary"),
    # OP (11840, Optimism) — VERIFIED FIRING but DEFERRED (session 025): its full
    # DelegateVotesChanged history is pathologically large (the native Optimism governance
    # token; the OP airdrop drove a very large self-delegation count). A full-history getLogs
    # replay did not complete in >80 min / 400MB+ and was killed; a PARTIAL history would give a
    # WRONG delegated-weight stock, so OP is NOT built this session (same "don't ship a partial
    # series" discipline as Channel-2 deferrals). Re-run alone with a large dedicated budget or a
    # block-windowed incremental fetch. Mechanism is confirmed (Entry 61/62) — this is a
    # throughput deferral, not a rejection.
    # (11840, "OP",    10,    "0x4200000000000000000000000000000000000042", TOPIC_U256, "primary"),
    (35931, "ZORA",    8453,  "0x1111111111166b7fe7bd91427724b487980afc69", TOPIC_U256, "primary"),
    # ---- CROSS-CHECK (already have a Snapshot Channel-3 turnout series; NOT in lambda) ----
    # NB: the session-022 universe map (empirical "got logs" record, Entry 53) reports ALL 10
    # of these under the uint256 DelegateVotesChanged topic -- trust the map over the source's
    # nominal uint96 declaration (the deployed contracts emit the uint256-topic variant).
    (10052, "GTC",    1,     "0xde30da39c46104798bb5aa3fe8b9e0e1f348163f", TOPIC_U256, "crosscheck"),
    (13855, "ENS",    1,     "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72", TOPIC_U256, "crosscheck"),
    (27075, "MNT",    1,     "0x3c3a81e81dc49a522a592e7622a7e711c06bf354", TOPIC_U256, "crosscheck"),
    (5692,  "COMP",   1,     "0xc00e94cb662c3520282e6f5717214004a7f26888", TOPIC_U256, "crosscheck"),
    (6758,  "SUSHI",  1,     "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2", TOPIC_U256, "crosscheck"),
    (7083,  "UNI",    1,     "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", TOPIC_U256, "crosscheck"),
    (7486,  "RGT",    1,     "0xd291e7a03283640fdc51b121ac401383a46cc623", TOPIC_U256, "crosscheck"),
    (7535,  "KP3R",   1,     "0x1ceb5cb57c4d4e2b2433641b95dd330a33185a44", TOPIC_U256, "crosscheck"),
    (8911,  "STRK",   1,     "0x74232704659ef37c08995e386a2e26cc27a8d7b1", TOPIC_U256, "crosscheck"),
    (22461, "HFT",    1,     "0xb3999F658C0391d94A37f7FF328F3feC942BcADC", TOPIC_U256, "crosscheck"),
]


def api(params, chainid, tries=5):
    for t in range(1, tries + 1):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, **params},
                             headers=H, timeout=60)
            j = r.json()
            time.sleep(SLEEP)
            return j
        except Exception as e:
            print(f"    retry {t}: {e}")
            time.sleep(SLEEP * t * 2)
    return {"status": "0", "result": []}


def block_at(date_str, chainid, tries=4):
    ts = int(time.mktime(time.strptime(date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
    for _ in range(tries):
        j = api({"module": "block", "action": "getblocknobytime",
                 "timestamp": ts, "closest": "before"}, chainid)
        try:
            return int(j["result"])
        except Exception:
            time.sleep(0.5)
    return None


def get_decimals(addr, chainid):
    j = api({"module": "proxy", "action": "eth_call", "to": addr,
             "data": "0x313ce567", "tag": "latest"}, chainid)
    try:
        return int(j["result"], 16)
    except Exception:
        return 18


import os as _os
DELEG_CAP = int(_os.environ.get("DELEG_CAP", "6000"))  # per-token getLogs cap; tail -> defer
_DCALLS = {"n": 0}


class DelegationCapHit(Exception):
    pass


def fetch_logs(addr, topic0, chainid, lo, hi, out):
    """Recursively page getLogs in [lo,hi], appending (block, logIndex, delegate, newBal).
    Aborts (raises DelegationCapHit) past DELEG_CAP calls so a pathologically large delegation
    history (e.g. OP) defers instead of hanging -- a partial replay would be a wrong stock."""
    _DCALLS["n"] += 1
    if _DCALLS["n"] > DELEG_CAP:
        raise DelegationCapHit(f">{DELEG_CAP} getLogs calls")
    j = api({"module": "logs", "action": "getLogs", "address": addr, "topic0": topic0,
             "fromBlock": lo, "toBlock": hi}, chainid)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_logs(addr, topic0, chainid, lo, mid, out)
        fetch_logs(addr, topic0, chainid, mid + 1, hi, out)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_logs(addr, topic0, chainid, lo, mid, out)
        fetch_logs(addr, topic0, chainid, mid + 1, hi, out)
        return
    for lg in res:
        try:
            data = lg["data"][2:]
            # data = previousBalance(word0) ++ newBalance(word1); uint96 right-aligned in word
            new_bal = int(data[64:128], 16) if len(data) >= 128 else 0
            delegate = lg["topics"][1]
            bn = int(lg["blockNumber"], 16)
            li = int(lg["logIndex"], 16)
        except (ValueError, KeyError, IndexError):
            continue  # skip malformed/pending log entries
        out.append((bn, li, delegate, new_bal))


def build_token(cmc_id, sym, chainid, addr, topic0, role, panel):
    ckf = RAW / f"{sym}.json"
    obs = panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")][
        ["month_end", "ym", "circulating_supply"]].sort_values("ym")
    if obs.empty:
        return [], {}
    months = list(obs.month_end)

    if ckf.exists():
        blob = json.loads(ckf.read_text())
        decimals = blob["decimals"]
        events = blob["events"]            # list of [bn, li, delegate, newbal_str]
        events = [(e[0], e[1], e[2], int(e[3])) for e in events]
        mblocks = blob["mblocks"]
    else:
        decimals = get_decimals(addr, chainid)
        # full-history block span: from genesis-ish to last observed month-end block.
        # Fall back to a high block if the month-end lookup fails (don't poison the whole fetch).
        last_block = block_at(months[-1], chainid) or 999_999_999
        events = []
        _DCALLS["n"] = 0
        fetch_logs(addr, topic0, chainid, 0, last_block, events)
        events.sort(key=lambda e: (e[0], e[1]))
        mblocks = {m: block_at(m, chainid) for m in months}
        ckf.write_text(json.dumps({"decimals": decimals,
                                   "events": [[e[0], e[1], e[2], str(e[3])] for e in events],
                                   "mblocks": mblocks}))
    print(f"  {sym:7} chain={chainid:<6} dec={decimals} events={len(events)} role={role}")

    # replay: advance an event pointer through each month-end block, snapshot the sum
    bal = {}
    running = 0   # running sum of latest newBalance over all delegates (raw units)
    idx = 0
    snap = {}     # ym -> total delegated (raw)
    for m in months:
        mb = mblocks.get(m)
        if mb is None:
            snap[m] = None
            continue
        while idx < len(events) and events[idx][0] <= mb:
            _, _, dele, nb = events[idx]
            running += nb - bal.get(dele, 0)
            bal[dele] = nb
            idx += 1
        snap[m] = running

    rows = []
    circ = dict(zip(obs.month_end, obs.circulating_supply))
    scale = 10 ** decimals
    first_event_ym = None
    if events:
        # ym of first event = first month whose block >= first event block
        fe = events[0][0]
        for m in months:
            if mblocks.get(m) and mblocks[m] >= fe:
                first_event_ym = m[:7]
                break
    for m in months:
        ym = m[:7]
        raw = snap.get(m)
        delegated = (raw / scale) if raw is not None else None
        c = circ.get(m)
        # before the first delegation event the channel does not exist -> NaN, not 0
        active = first_event_ym is not None and ym >= first_event_ym
        ratio = (delegated / c) if (active and delegated and c and c > 0) else None
        flag = ("delegated>circulating (CMC circ excludes delegated locked/treasury supply, "
                "the Entry-49 pattern); kept un-capped & flagged, lambda z-scores rank not level"
                if (ratio is not None and ratio > 1) else "")
        rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m, "ym": ym,
                     "role": role, "chain_id": chainid,
                     "delegated_supply": delegated if active else None,
                     "circulating_supply": c,
                     "delegation_ratio": ratio, "flag": flag,
                     "source": "etherscan getLogs DelegateVotesChanged replay"})
    info = {"sym": sym, "n_events": len(events), "decimals": decimals,
            "final_delegated": (snap.get(months[-1]) or 0) / scale,
            "final_ratio": rows[-1]["delegation_ratio"]}
    return rows, info


def main():
    import os
    # CROSSCHECK gate: 'none' (default) = build PRIMARY only (the lambda-moving set; the heavy
    # UNI/COMP/ENS/SUSHI delegation histories are skipped); 'light' = also the smaller crosschecks
    # that already have a checkpoint or are cheap; 'all' = every crosscheck token too.
    cc_mode = os.environ.get("CROSSCHECK", "none")
    HEAVY = {"UNI", "COMP", "ENS", "SUSHI"}
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    allrows, infos = [], []
    for cmc_id, sym, chainid, addr, topic0, role in TOKENS:
        if role == "crosscheck":
            ck = RAW / f"{sym}.json"
            if cc_mode == "none":
                continue
            if cc_mode == "light" and (sym in HEAVY and not ck.exists()):
                continue
        try:
            rows, info = build_token(cmc_id, sym, chainid, addr, topic0, role, panel)
            allrows.extend(rows)
            if info:
                infos.append(info)
        except Exception as e:
            print(f"  {sym}: ERROR {e}")
    out = pd.DataFrame(allrows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    nz = out[out.delegation_ratio.notna()]
    print(f"\nwrote {OUT}")
    print(f"  rows={len(out)}  with-ratio asset-months={len(nz)}  assets={nz.cmc_id.nunique()}")
    prim = nz[nz.role == "primary"]
    print(f"  PRIMARY (enter lambda): {len(prim)} asset-months, {prim.cmc_id.nunique()} assets")
    print(f"  CROSSCHECK: {nz[nz.role=='crosscheck'].cmc_id.nunique()} assets")
    for info in sorted(infos, key=lambda x: x["sym"]):
        fr = info["final_ratio"]
        print(f"    {info['sym']:7} events={info['n_events']:>6} "
              f"final_delegated={info['final_delegated']:,.0f} "
              f"final_ratio={('%.2f%%'%(fr*100)) if fr else 'NA'}")


if __name__ == "__main__":
    main()
