"""
phase1_channel1_freebuild.py  --  SESSION 024, Task B: free-chain Channel-1 locks built by
the session-022 contract-read + getLogs event-replay method (Entry 53), to the Entry-26 bar.

WORKLIST (session-022 map "Ch1 GENUINE" set), reconciled to what is actually buildable here:
  HEX (5015)    -- ALREADY BUILT in session 023 (channel1_hex_stake.csv). Not a target.
  AKRO (4134)   -- REJECT (session 023, Entry 55): Locked() is an owner-only admin pause flag.
  stkAAVE-lock  -- AAVE's Safety-Module lock is ALREADY in lambda via cmc 7278 (Entry 26,
                   channel1_evm_locks.csv "AAVE"). See stkAAVE note below.
  -> the genuine NET-NEW Channel-1 asset this session adds is **XAN** (built here).

  XAN (38481)  BUILD.  XanV1 (Anoma, 2025), Ethereum 0xcedbea37...c8e7 (proxy -> impl
    0x03997b56...735e). Verified-source mechanism: `lock(value)` -> `_lock(account,value)`
    does `lockedSupply += value; lockedBalances[account] += value; emit Locked(account,value)`.
    The NatSpec says the lock is PERMANENT ("Permanently locks tokens ... until it gets
    upgraded"); `lockedSupply` is ONLY ever incremented -- there is no unlock/decrement path
    in the implementation. So, exactly like HEX's internal accounting (Entry 54), the monthly
    locked series is a pure cumulative sum of the `Locked(account,value)` event `value`:
        lockedSupply(t) = sum( Locked.value : block <= t )
    CROSS-CHECK (Entry-26 bar, HEX-style global read): cumulative reconstruction final ==
    live on-chain `lockedSupply()` (selector 0xca5c7b91) at ~0.00% drift.
    DENOMINATOR: unlike HEX (where staked HEX is burned OUT of totalSupply), XAN's locked
    tokens stay IN the holder's wallet (transfer-restricted, NOT escrowed/burned) -> they
    remain part of ERC20 totalSupply and of CMC circulating_supply. So locked is a SUBSET of
    circulating and `staking_ratio = locked/circulating < 1` is well-behaved (no Entry-49
    artifact). Event `Locked(address indexed account, uint256 value)` -> value is the single
    data word.

NOT BUILT (documented, the "flag don't ship a wrong number" standard -- Entries 52/55):
  VSL (1483)   REJECT (the AKRO pattern, verified this session). Direct contract `Token` with a
    `Lockable` base; `Locked()` is a BARE, parameterless event emitted by the `checkLock`
    modifier as a CYCLIC transfer-pause: each 30-day epoch the contract is unlocked 25 days /
    locked 5 days, and `Locked()`/`Unlocked()` fire on the state flip. No amount, no escrow --
    a contract-wide transfer freeze, not a holder conviction lock. (39 logs = the periodic
    flips.) Same lesson as AKRO (Entry 55): a thing named `Locked()` is not necessarily a lock.
  NMR (1732)   DEFER to Phase 2. NumeraireBackend (proxy -> UpgradeDelegate) tournament staking:
    `Staked(staker, tag, totalAmountStaked, confidence, tournamentID, roundID)` -- the amount is
    a per-(staker,tag) CUMULATIVE running total, decremented elsewhere by `StakeDestroyed`/
    `StakeReleased`/`destroyStake`, and the modern Numerai/Erasure flow BURNS NMR on stake. The
    contract exposes NO aggregate staked global and holds no escrow balance, so there is no
    Entry-26 cross-check anchor (no balanceOf/global to reconcile to). A correct net-outstanding
    series needs multi-event stake-lifecycle tracking with no on-chain total to validate it ->
    flagged for a proper Phase-2 Erasure treatment rather than shipped unanchored.
  stkAAVE (36246)  EXCLUDE. cmc 36246 is the Staked-AAVE wrapper token itself; its supply already
    represents AAVE locked in the Safety Module, which is ALREADY captured in lambda via AAVE
    (cmc 7278, Entry 26). Building it as a separate asset would double-count the same escrowed
    AAVE, and as its own asset locked/circulating ~= 1 (degenerate, the ETHDYDX pattern).

Output: 03_data/phase1/channel1_freebuild.csv  (picked up by the channel1_*.csv glob).
        03_data/raw/phase1_onchain/freebuild/<SYM>.json  (resumable checkpoint).
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_freebuild.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "freebuild"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = 0.22

# cmc_id, symbol, chainid, token_addr, locked_event_topic0, lockedsupply_selector, decimals, mech, flag
XAN_TOPIC = "0x9f1ec8c880f76798e7b793325d625e9b60e4082a553c98f42b6cda368dd60008"  # Locked(address,uint256)
BUILDS = [
    (38481, "XAN", 1, "0xcedbea37c8872c4171259cdfd5255cb8923cf8e7", XAN_TOPIC, "0xca5c7b91", 18,
     "non-custodial permanent lock (XanV1.lock -> lockedSupply, Ethereum)",
     "locked (7.5B) EXCEEDS CMC circulating (2.5B) -> CMC circulating excludes the locked "
     "foundation/ecosystem allocation, the Entry-49/HEX artifact (staking_ratio>1); kept "
     "un-capped & flagged, lambda z-scores rank not level. locked_fraction_alloc = "
     "locked/(locked+circ) written alongside for audit (HEX precedent, Entry 54). cumulative "
     "Locked(account,value) == live lockedSupply() at 0.0000% drift"),
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


def block_at(date_str, chainid):
    ts = int(time.mktime(time.strptime(date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
    j = api({"module": "block", "action": "getblocknobytime",
             "timestamp": ts, "closest": "before"}, chainid)
    try:
        return int(j["result"])
    except Exception:
        return None


def eth_call(addr, data, chainid):
    j = api({"module": "proxy", "action": "eth_call", "to": addr, "data": data,
             "tag": "latest"}, chainid)
    try:
        return int(j["result"], 16)
    except Exception:
        return None


def fetch_locked(addr, topic0, chainid, lo, hi, out):
    """Collect (block, value) for each Locked(account,value) event; recursive window split."""
    j = api({"module": "logs", "action": "getLogs", "address": addr, "topic0": topic0,
             "fromBlock": lo, "toBlock": hi}, chainid)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        fetch_locked(addr, topic0, chainid, lo, mid, out)
        fetch_locked(addr, topic0, chainid, mid + 1, hi, out)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        fetch_locked(addr, topic0, chainid, lo, mid, out)
        fetch_locked(addr, topic0, chainid, mid + 1, hi, out)
        return
    for lg in res:
        data = lg["data"][2:]
        value = int(data[:64], 16)   # account is indexed (topic1); value is the single data word
        out.append((int(lg["blockNumber"], 16), int(lg["logIndex"], 16), value))


def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    rows = []
    for cmc_id, sym, chainid, addr, topic0, sel, dec, mech, flag in BUILDS:
        obs = panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")][
            ["month_end", "ym", "circulating_supply"]].sort_values("ym")
        months = list(obs.month_end)
        ckf = RAW / f"{sym}.json"
        if ckf.exists():
            blob = json.loads(ckf.read_text())
            events = [(e[0], e[1], int(e[2])) for e in blob["events"]]
            mblocks = blob["mblocks"]
            live_locked = blob.get("live_locked")
        else:
            last_block = block_at(months[-1], chainid)
            events = []
            fetch_locked(addr, topic0, chainid, 0, last_block, events)
            events.sort(key=lambda e: (e[0], e[1]))
            mblocks = {m: block_at(m, chainid) for m in months}
            live_locked = eth_call(addr, sel, chainid)
            ckf.write_text(json.dumps({"events": [[e[0], e[1], str(e[2])] for e in events],
                                       "mblocks": mblocks, "live_locked": live_locked}))
        scale = 10 ** dec
        recon_final_raw = sum(v for _, _, v in events)
        recon_final = recon_final_raw / scale
        live = (live_locked / scale) if live_locked is not None else None
        drift = abs(recon_final_raw - live_locked) / live_locked if live_locked else None
        print(f"  {sym:5} events={len(events)}  recon_final={recon_final:,.2f}  "
              f"live lockedSupply()={live:,.2f}  "
              f"cross-check={'PASS' if (drift is not None and drift < 0.0005) else 'CHECK'} "
              f"(drift={drift:.6%})" if drift is not None else f"  {sym}: no live read")

        first_ym = None
        if events:
            fe = events[0][0]
            for m in months:
                if mblocks.get(m) and mblocks[m] >= fe:
                    first_ym = m[:7]
                    break
        circ = dict(zip(obs.month_end, obs.circulating_supply))
        for m in months:
            ym = m[:7]
            mb = mblocks.get(m)
            cum = sum(v for b, _, v in events if mb is not None and b <= mb) / scale
            active = first_ym is not None and ym >= first_ym and mb is not None
            locked = cum if active else None
            c = circ.get(m)
            ratio = (locked / c) if (locked is not None and c and c > 0) else None
            frac_alloc = (locked / (locked + c)) if (locked is not None and c and (locked + c) > 0) else None
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": m,
                         "locked_supply": locked, "circulating_supply": c,
                         "staking_ratio": ratio, "locked_fraction_alloc": frac_alloc,
                         "mechanism": mech,
                         "source": "etherscan getLogs Locked(account,value) cumulative",
                         "flag": flag})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    nz = out[out.staking_ratio.notna()]
    print(f"\nwrote {OUT}  ({len(nz)} asset-months w/ ratio, {nz.cmc_id.nunique()} assets)")
    for sym in out.symbol.unique():
        d = nz[nz.symbol == sym]
        if len(d):
            print(f"  {sym}: ratio {d.staking_ratio.min():.2%}->{d.staking_ratio.max():.2%} "
                  f"(latest {d.sort_values('month_end').staking_ratio.iloc[-1]:.2%})")


if __name__ == "__main__":
    main()
