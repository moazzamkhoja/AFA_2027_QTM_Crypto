"""
phase1_channel1_evm_locks_bucket1.py  --  SESSION 021 (Token Bucket-1 exhaustive re-audit):
EVM token Channel-1 locks recovered from the 398-token "unrecoverable" pool, built by the same
validated Dune curated-transfers cumulative method as Bucket 3 (Entry 48), to the same Entry-26
single-clean-escrow standard.

HOW THESE FOUR WERE FOUND (the re-audit funnel, Entry 50):
  Stage 1  bulk DeFiLlama /protocols triage by cmcId (never symbol) -> 92 of 398 have a clean
           cmcId-matched DL protocol.
  Stage 2a /protocol/{slug} chainTvls inspection of all 92 -> 36 expose a 'staking' TVL bucket
           with a raw STAKED-TOKEN-QUANTITY series (chainTvls['staking']['tokens']).
  Stage 2b ratio filter (DL staked qty / panel circulating) + Dune top-holder cross-check
           (tokens_<chain>.balances / net-transfers) to test the Entry-26 identity: does ONE
           contract hold the base token in the DL-reported staked amount?
  -> Only these four pass cleanly (top holder == DL staked qty to ~0.00%, i.e. one contract
     custodies the base token):

  cmc   sym   chain     escrow (holds the BASE token)                 recon vs balanceOf    ratio
  7737  API3  ethereum  Api3Pool 0x6dd655...c76d76                    64,354,124 (0.00%)    ~74%
  3835  ORBS  ethereum  StakingContract 0x01d59a...656c3              1.841B (0.00%)        ~42%
  2930  IQ    ethereum  HiIQ veIQ 0x1bf545...e16ba                    2.416B (0.00%)        ~9%
  35509 VVV   base      Venice staking 0x321b7f...f340ff              33.28M (0.00%)        ~71%

  All four were in the 398 "unrecoverable" pool that session 020's category-level pass wrote off.
  API3/Api3Pool and ORBS/StakingContract are reward-staking (xSUSHI/stkAAVE-style, kept flagged via
  `mechanism`); IQ/HiIQ is a Curve-style vote-escrow; VVV is single-contract reward-staking on Base.

REJECTED at Stage 2b (DL shows a 'staking' bucket but NO single contract reproduces it -> fails the
Entry-26 cross-check, the CELO lesson; not shipped):
  EIGEN (multi-contract EigenLayer restaking, spread across strategy contracts; top holder 184M vs
        DL 296M), ILV (multi-pool core staking), ATH/AKRO/PEAK/MBOX/TIME/BTCST/ZBU (no single holder
        matches the DL staked figure; treasury/LP dominate top holders), KAITO (DL 18.2M staked maps
        to no single top holder -- treasury holders dominate Base balances).
Non-EVM material candidates (HXRO Solana, SUN Tron, ORN TON, TLM Wax) -> REJECT-no-data: outside the
free EVM Dune curated-transfers method. WARP cmc 1166 -> REJECT-no-data: DL maps slug 'polkastarter'
to cmcId 1166 giving an impossible 1764% ratio (cmcId collision, Entry 39 landmine).

Output: 03_data/phase1/channel1_evm_locks_bucket1.csv (picked up by the channel1_*.csv glob).
        Raw monthly cum_locked cached under 03_data/raw/phase1_onchain/dune_locks/.
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_evm_locks_bucket1.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "dune_locks"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
HEAD = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

# cmc_id, symbol, dune_schema, token_address, escrow_address, live_balanceOf, since(floor), mechanism, flag
LOCKS = [
    (7737, "API3", "tokens_ethereum", "0x0b38210ea11411557c13457d4da7dc6ea731b88a",
     "0x6dd655f10d4b9e242ae186d9050b68f725c76d76", 64_354_124, None,
     "single-pool reward stake (Api3Pool, Ethereum)",
     "reward-staking pool (xSUSHI/stkAAVE-style), single contract holding base API3; staking_ratio>1 "
     "in some months (CMC circulating excludes pooled API3) -- kept un-capped & flagged, z-score uses rank"),
    (3835, "ORBS", "tokens_ethereum", "0xff56cc6b1e6ded347aa0b7676c85ab0b3d08b0fa",
     "0x01d59af68e2dcb44e04c50e05f62e7043f2656c3", 1_841_060_162, None,
     "single staking contract (Orbs StakingContract, Ethereum)",
     "reward/governance stake, single contract holding base ORBS; staking_ratio>1 in early months "
     "(CMC circulating excludes staked ORBS) -- kept un-capped & flagged, z-score uses rank"),
    (2930, "IQ", "tokens_ethereum", "0x579cea1889991f68acc35ff5c3dd0621ff29b0c9",
     "0x1bf5457ecaa14ff63cc89efd560e251e814e16ba", 2_416_000_459, None,
     "vote-escrow (HiIQ veIQ, Ethereum)",
     "Curve-style vote-escrow lock of base IQ; clean single VotingEscrow contract"),
    (35509, "VVV", "tokens_base", "0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf",
     "0x321b7ff75154472b18edb199033ff4d116f340ff", 33_279_865, None,
     "single-contract reward stake (Venice staking, Base)",
     "young token (2025); single contract holding base VVV; balanceOf via Dune net-transfers (Base "
     "balances table times out on free tier)"),
    # VELO -- the Entry-48 DEFER, RESOLVED this session. Entry 48 deferred it believing cmc 7127's
    # token 0x9560e827 was a defunct "v1" token distinct from the v2 lock. DeFiLlama's OWN Velodrome
    # V2 AND V3 protocol entries both carry address=optimism:0x9560e827... (the exact token cmc 7127
    # maps to) -- i.e. 0x9560e827 is the CURRENT canonical Velodrome token, not defunct. CMC (7127->
    # 0x9560e827) and DeFiLlama (V2/V3->0x9560e827) agree => documented, non-guessed identity. The
    # veVELO VotingEscrow 0xfaf8fd17... holds 1.2956B of that token directly on Optimism (=7.4% of
    # circulating) -- a clean single-contract base-token lock. No cmcId/symbol collision remains.
    (7127, "VELO", "tokens_optimism", "0x9560e827af36c94d2ac33a39bce1fe78631088db",
     "0xfaf8fd17d9840595845582fcb047df13f006787d", 1_295_615_052, "2022-05-01",
     "vote-escrow (veVELO VotingEscrow, Optimism)",
     "Entry-48 deferral RESOLVED via documented CMC+DeFiLlama token identity (both map cmc 7127 to "
     "0x9560e827, Velodrome V2/V3 canonical token); single veVELO contract holds base VELO, ~7.4%"),
]


def _exec(sql, maxw=240):
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


def dune_cumlocked(schema, token, escrow, since=None):
    floor = f"AND block_time > timestamp '{since}'" if since else ""
    sql = f"""
    WITH flows AS (
      SELECT block_month,
             SUM(CASE WHEN to = {escrow} THEN amount ELSE 0 END) AS inflow,
             SUM(CASE WHEN "from" = {escrow} THEN amount ELSE 0 END) AS outflow
      FROM {schema}.transfers
      WHERE contract_address = {token}
        AND (to = {escrow} OR "from" = {escrow})
        {floor}
      GROUP BY 1
    )
    SELECT block_month,
           SUM(inflow - outflow) OVER (ORDER BY block_month) AS cum_locked
    FROM flows ORDER BY block_month
    """
    rows = _exec(sql)
    src = f"dune:{schema}.transfers cumulative in-out of escrow"
    return {row["block_month"][:7]: float(row["cum_locked"]) for row in rows}, src


def main():
    panel = pd.read_csv(PANEL)
    panel["ym"] = panel["month_end"].str[:7]
    rows = []
    for cmc_id, sym, schema, token, escrow, live_bal, since, mech, flag in LOCKS:
        cf = RAW / f"{sym}_locked.json"
        if cf.exists():
            blob = json.loads(cf.read_text())
            series, src = blob["series"], blob["src"]
        else:
            series, src = dune_cumlocked(schema, token, escrow, since)
            cf.write_text(json.dumps({"series": series, "src": src}))
        final = series[max(series)] if series else 0
        ok = abs(final - live_bal) / live_bal < 0.02 if live_bal else False
        print(f"  {sym:5} {schema:16} months={len(series)}  recon_final={final:,.0f}  "
              f"balanceOf={live_bal:,.0f}  cross-check={'PASS' if ok else 'CHECK'} "
              f"(d={abs(final-live_bal)/live_bal:.2%})")
        obs = panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")][
            ["month_end", "ym", "circulating_supply"]].sort_values("ym")
        first_ym = min(series) if series else None
        last_val = None
        for _, r in obs.iterrows():
            if r.ym in series:
                last_val = series[r.ym]
            locked = last_val if (first_ym is not None and r.ym >= first_ym) else None
            c = r.circulating_supply
            ratio = (locked / c) if (locked is not None and c and c > 0) else None
            rows.append({"cmc_id": cmc_id, "symbol": sym, "month_end": r.month_end,
                         "locked_supply": locked, "circulating_supply": c,
                         "staking_ratio": ratio, "escrow": escrow,
                         "mechanism": mech, "source": src, "flag": flag})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    nz = out[out.staking_ratio.notna()]
    print(f"\nwrote {OUT}  ({len(nz)} asset-months w/ ratio, {nz.cmc_id.nunique()} assets)")
    for sym in ["API3", "ORBS", "IQ", "VVV"]:
        d = nz[nz.symbol == sym]
        if len(d):
            print(f"  {sym}: ratio {d.staking_ratio.min():.2%}->{d.staking_ratio.max():.2%} "
                  f"(latest {d.sort_values('month_end').staking_ratio.iloc[-1]:.2%})")


if __name__ == "__main__":
    main()
