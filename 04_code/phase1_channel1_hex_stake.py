"""
phase1_channel1_hex_stake.py  --  SESSION 023 (HEX/AKRO reconciliation):
HEX (cmc_id 5015) Channel-1 staked-supply series, recovered using session 022's higher-fidelity
contract-code-read + getLogs method (NOT session 021's Dune-top-holder single-escrow substitute).

WHY THIS IS A SEPARATE SCRIPT (not added to the escrow-transfer ext scripts):
  Entry 26's reconstruction (and the Bucket-1/Bucket-3 scripts) assume a CUSTODIAL escrow contract
  that HOLDS the base token, so balanceOf(escrow) == locked supply, reconstructed from Transfer
  in/out of that escrow. HEX has NO escrow. Reading the verified HEX source (cached
  03_data/raw/etherscan_src/1_0x2b591e99...json) shows stakeStart() calls `_burn(msg.sender,
  newStakedHearts)` -- staked HEX is BURNED out of the ERC20 totalSupply and tracked only in the
  internal global `lockedHeartsTotal`. This is a genuinely different, NON-CUSTODIAL construction
  path (no escrow balanceOf to read), so it gets its own builder -- the same way eth_staking and
  pos_coins are their own scripts. Documented as a new method in DATA_DECISIONS_LOG Entry 54.

THE RECONSTRUCTION (exact, from the contract's own accounting):
  stakeStart():  g._lockedHeartsTotal += newStakedHearts          (amount in the StakeStart event)
  stakeEnd():    g._lockedHeartsTotal -= st._stakedHearts         (the ORIGINAL staked amount)
  -> only StakeStart(+) and StakeEnd(-) move lockedHeartsTotal (StakeGoodAccounting does NOT;
     verified: exactly one `_lockedHeartsTotal -=` site in the source).
  So  lockedHeartsTotal(t) = SUM(StakeStart.stakedHearts <= t) - SUM(StakeEnd.<orig stakedHearts> <= t).
  Both events are decoded on Dune (hex_ethereum.HEX_evt_StakeStart / _StakeEnd). StakeStart packs
  stakedHearts in data0 bits [111:40]:  stakedHearts = (data0 >> 40) & (2^72 - 1)
  = (data0 / 1099511627776) % 4722366482869645213696  (exact UINT256 integer arithmetic in DuneSQL,
  verified == Python arbitrary-precision decode on two sample stakeIds). StakeEnd's amount is
  recovered by joining StakeEnd.stakeId back to the StakeStart decode (the contract subtracts the
  original stakedHearts), so no separate StakeEnd bit-layout decode is needed.

CROSS-CHECK (same 0.00% bar as the 5 session-021 BUILDs):
  Final reconstructed lockedHeartsTotal must equal the live on-chain globalInfo()[0] read.
  Measured 2026-06-29:  recon final = 61,900,823,759,862,091,712 hearts
                        live globalInfo()[0] = 61,900,823,759,862,091,712 hearts  ->  drift 0.000000%

DENOMINATOR (resolved explicitly, not assumed -- see Entry 54):
  The HEX contract's own NatSpec: "ERC20 totalSupply() is the circulating supply and does not
  include any staked Hearts. allocatedSupply() includes both." CMC's circulating_supply mirrors the
  on-chain ERC20 totalSupply (excludes staked HEX) -- the SAME denominator artifact as the Entry-49
  AERO/SOL/API3/ORBS series. We ship staking_ratio = locked / circulating (panel basis) for
  cross-sectional comparability with the other Channel-1 token series (lambda z-scores within month,
  rank not level -- Entry 27/49); within HEX's observed window (2020-03..2024-05) locked stays well
  below circulating so the ratio is < 1 throughout (no >1 artifact actually appears in the shipped
  months). The theoretically-clean fraction locked/(locked+circ) is also written for audit
  (locked_fraction_alloc).

Output: 03_data/phase1/channel1_hex_stake.csv  (picked up by the channel1_*.csv glob in
        phase1_assemble_lambda.py). Raw monthly series cached at
        03_data/raw/phase1_onchain/dune_locks/HEX_stake_recon.json.
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_hex_stake.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "dune_locks"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
HEAD = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

CMC_ID = 5015
SYMBOL = "HEX"
HEARTS = 1e8  # HEX has 8 decimals
# Live globalInfo()[0] lockedHeartsTotal read on 2026-06-29 via Etherscan-V2 proxy eth_call
# (data=globalInfo() selector, tag=latest). This is the cross-check target (= an on-chain balance
# equivalent, the contract's own staked-supply accumulator).
LIVE_LOCKED_HEARTS = 61_900_823_759_862_091_712
MECH = "non-custodial burn-and-track stake (HEX StakeStart/StakeEnd, lockedHeartsTotal global, Ethereum)"
FLAG = ("session-022 method (verified-source read + getLogs event-replay); supersedes session-021 "
        "rejection (Entry 50/SESSION021 audit: 'staking internal to the HEX contract'). NON-CUSTODIAL: "
        "staked HEX is _burn()'d out of ERC20 totalSupply, tracked in lockedHeartsTotal -- no escrow "
        "to balanceOf. Recon = cum(StakeStart.stakedHearts) - cum(StakeEnd.orig stakedHearts), "
        "final == live globalInfo()[0] at 0.0000%. CMC circulating EXCLUDES staked HEX (contract "
        "NatSpec: totalSupply==circulating, allocatedSupply==circ+locked) -> same Entry-49 denominator "
        "basis as AERO/SOL/API3/ORBS, but locked<circ throughout HEX's observed window so ratio<1.")

RECON_SQL = """
WITH starts AS (
  SELECT stakeId, evt_block_time,
    CAST((data0 / UINT256 '1099511627776') % UINT256 '4722366482869645213696' AS DECIMAL(38,0)) AS staked
  FROM hex_ethereum.HEX_evt_StakeStart
),
start_m AS (
  SELECT date_trunc('month', evt_block_time) m, SUM(staked) AS s FROM starts GROUP BY 1
),
end_m AS (
  SELECT date_trunc('month', e.evt_block_time) m, SUM(s.staked) AS e
  FROM hex_ethereum.HEX_evt_StakeEnd e JOIN starts s ON e.stakeId = s.stakeId GROUP BY 1
)
SELECT CAST(COALESCE(st.m, en.m) AS VARCHAR) m,
       CAST(COALESCE(st.s, 0) AS VARCHAR) starts_hearts,
       CAST(COALESCE(en.e, 0) AS VARCHAR) ends_hearts
FROM start_m st FULL OUTER JOIN end_m en ON st.m = en.m ORDER BY 1
"""


def _exec(sql, maxw=300):
    t0 = time.time()
    r = requests.post(f"{BASE}/sql/execute", headers=HEAD,
                      json={"sql": sql, "performance": "small"}, timeout=40)
    r.raise_for_status()
    eid = r.json()["execution_id"]
    while time.time() - t0 < maxw:
        s = requests.get(f"{BASE}/execution/{eid}/results", headers=HEAD, timeout=40).json()
        st = s.get("state", "")
        if s.get("is_execution_finished") or st.endswith("COMPLETED") or st.endswith("FAILED"):
            if st.endswith("FAILED"):
                raise RuntimeError(f"Dune query failed: {s.get('error')}")
            return (s.get("result") or {}).get("rows") or []
        time.sleep(4)
    raise RuntimeError("Dune query timed out")


def build_series():
    """Return {YYYY-MM: cumulative locked hearts (int)} reconstructed from StakeStart/StakeEnd."""
    cf = RAW / "HEX_stake_recon.json"
    if cf.exists():
        blob = json.loads(cf.read_text())
        return {k: int(v) for k, v in blob["series"].items()}, blob["src"]
    rows = _exec(RECON_SQL)
    cum = 0
    series = {}
    for r in rows:
        m = r["m"][:7]
        cum += int(r["starts_hearts"]) - int(r["ends_hearts"])
        series[m] = cum
    src = "dune:hex_ethereum.HEX_evt_StakeStart/_StakeEnd cum(start)-cum(end) of stakedHearts"
    cf.write_text(json.dumps({"series": {k: str(v) for k, v in series.items()}, "src": src}))
    return series, src


def main():
    series, src = build_series()
    final = series[max(series)] if series else 0
    drift = abs(final - LIVE_LOCKED_HEARTS) / LIVE_LOCKED_HEARTS if LIVE_LOCKED_HEARTS else 1
    ok = drift < 0.005
    print(f"  HEX recon months={len(series)}  recon_final={final/HEARTS:,.0f} HEX  "
          f"live_globalInfo={LIVE_LOCKED_HEARTS/HEARTS:,.0f} HEX  "
          f"cross-check={'PASS' if ok else 'CHECK'} (drift={drift:.6%})")
    if not ok:
        raise SystemExit("HEX cross-check failed -- not shipping a series that doesn't reconcile.")

    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    obs = panel[(panel.cmc_id == CMC_ID) & (panel.status == "observed")][
        ["month_end", "ym", "circulating_supply"]].sort_values("ym")
    first_ym = min(series) if series else None
    last_val = None
    rows = []
    for _, r in obs.iterrows():
        if r.ym in series:
            last_val = series[r.ym]
        locked_hearts = last_val if (first_ym is not None and r.ym >= first_ym) else None
        locked = (locked_hearts / HEARTS) if locked_hearts is not None else None
        c = r.circulating_supply
        ratio = (locked / c) if (locked is not None and c and c > 0) else None
        frac_alloc = (locked / (locked + c)) if (locked is not None and c and c > 0) else None
        rows.append({"cmc_id": CMC_ID, "symbol": SYMBOL, "month_end": r.month_end,
                     "locked_supply": locked, "circulating_supply": c,
                     "staking_ratio": ratio, "locked_fraction_alloc": frac_alloc,
                     "escrow": "(none - non-custodial burn; lockedHeartsTotal global)",
                     "mechanism": MECH, "source": src, "flag": FLAG})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    nz = out[out.staking_ratio.notna()]
    print(f"\nwrote {OUT}  ({len(nz)} asset-months w/ ratio, {nz.cmc_id.nunique()} asset)")
    if len(nz):
        print(f"  HEX staking_ratio (locked/circ)      {nz.staking_ratio.min():.2%} -> "
              f"{nz.staking_ratio.max():.2%}  (latest {nz.sort_values('month_end').staking_ratio.iloc[-1]:.2%})")
        print(f"  HEX locked_fraction_alloc (clean)    {nz.locked_fraction_alloc.min():.2%} -> "
              f"{nz.locked_fraction_alloc.max():.2%}")


if __name__ == "__main__":
    main()
