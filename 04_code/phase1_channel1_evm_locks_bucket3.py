"""
phase1_channel1_evm_locks_bucket3.py  --  SESSION 020, Part B (Bucket 3): EVM token
Channel-1 locks reconstructed from Dune's free curated per-chain transfer tables, for
tokens whose escrow lives on a chain the free Etherscan-V2 key does NOT cover (Base, BNB)
or where block-range getLogs is impractically slow (Arbitrum) -- the gap that left GMX
unbuilt in Entry 41.

METHOD (the validated successor to the Entry-26 getLogs reconstruction):
  locked(month) = running sum over months of [ Σ amount of transfers INTO the escrow
                  - Σ amount of transfers OUT of the escrow ], from tokens_<chain>.transfers
  (Dune's curated, decimal-adjusted, pre-month-bucketed transfer table).
  Cross-checked: the final cumulative equals the live on-chain balanceOf(escrow) to <0.1%
  for every built token -- the same balanceOf == locked-supply identity the Entry-26 standard
  requires. (The kickoff named `balances_<chain>.daily_updates`; that table does not exist on
  Dune free tier -- verified live, QUERY FAILED "does not exist or is private". The correct
  free curated tables are `tokens_<chain>.transfers` (cumulate) and `tokens_<chain>.balances`
  (historical balance snapshots). BSC's schema is `tokens_bnb`, not `tokens_bsc`. Entry 43.)

BUILT (clean single-contract base-token lock, verified live this session):
  cmc   sym    chain     escrow (holds the BASE token)                          live lock        verdict
  11857 GMX    arbitrum  StakedGmxTracker 0x908C4D94...59dD4                     6.16M (~65%)     BUILD (was the Entry-41 deferral; first, as the method confidence-check -- recon 6.162M vs balanceOf 6.16M)
  29270 AERO   base      veAERO VotingEscrow 0xeBf418Fe...67e6B4                 968.4M / 1.926B = 50.3%   BUILD (vote-escrow of AERO; balanceOf via keyless Base RPC)
  7186  CAKE   bnb       veCAKE 0x5692DB81...EC1bAB                              5.90M (~1.5%, low)        BUILD w/ FLAG (clean ve-lock of CAKE but veCAKE adoption fell post-2024 -> small share; kept, flagged like RPL)

REJECTED / DEFERRED this session (documented, not silently dropped):
  AXS  (6783)  -- REJECT: AXS staking lives on the RONIN appchain, not on an EVM chain our free
                 tools index (no Etherscan-V2 free coverage, no Dune curated schema). The legacy
                 Ethereum AXS staking contract is abandoned. No clean reconstructable single-escrow.
  VELO (7127)  -- DEFER: v1->v2 migration split. The in-universe VELO (cmc 7127) maps to the v1
                 token 0x9560e827...; the live veVELO escrow locks the v2 token 0x3c8B6502...
                 (a different contract). Joining the v1 cmc_id to a v2-token lock is exactly the
                 cmcId/symbol collision the project forbids -- deferred pending an identity-map
                 resolution of which VELO the panel's cmc 7127 actually is.

The other ~287 tag-bearing candidates (see _bucket3_candidates.csv) are DEXes / lending / RWA /
memes / L1-L2 chains whose "governance" is delegation, farming (MasterChef-style), or off-chain
Snapshot voting -- none has a single contract that custodies a meaningful share of the base token
directly, so none passes the Entry-26 standard for a Channel-1 LOCK (many already have a Channel-3
voting value instead). This is the same small-clean-set outcome as Entry 26/41, not an oversight.

Output: 03_data/phase1/channel1_evm_locks_bucket3.csv (picked up by the channel1_*.csv glob).
        Raw monthly cum_locked per token cached under 03_data/raw/phase1_onchain/dune_locks/.
"""

import json
import time
from pathlib import Path

import requests
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["dune"]
PANEL = REPO / "03_data" / "universe_panel.csv"
OUT = REPO / "03_data" / "phase1" / "channel1_evm_locks_bucket3.csv"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "dune_locks"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://api.dune.com/api/v1"
HEAD = {"X-Dune-Api-Key": KEY, "Content-Type": "application/json"}

# cmc_id, symbol, dune_schema, token_address, escrow_address, live_balanceOf (cross-check),
# since (block_time floor for partition-pruning on high-volume chains; None=full history),
# mechanism, flag.
# All built by cumulating tokens_<chain>.transfers in-out of the escrow. `since` is set to just
# before the escrow's deployment for high-volume tokens (e.g. CAKE on BSC) so Dune prunes the
# pre-escrow history and the query finishes inside the free-tier 2-min limit -- the escrow held
# ~0 before deployment, so flooring there does not drop any locked supply.
LOCKS = [
    (11857, "GMX", "tokens_arbitrum", "0xfc5a1a6eb076a2c7ad06ed22c90d7e710e35ad0a",
     "0x908c4d94d34924765f1edc22a1dd098397c59dd4", 6_160_000, None,
     "single-tracker stake (StakedGmxTracker, Arbitrum)", ""),
    (29270, "AERO", "tokens_base", "0x940181a94a35a4569e4529a3cdfb74e38fd98631",
     "0xebf418fe2512e7e6bd9b87a8f0f294acdc67e6b4", 968_403_885, None,
     "vote-escrow (veAERO VotingEscrow, Base)",
     "staking_ratio>1 in many months: CMC circulating_supply excludes veAERO-locked AERO, so "
     "locked/circulating exceeds 1 (vs total supply it is ~50%); kept un-capped & flagged, z-score "
     "uses relative rank not level"),
    (7186, "CAKE", "tokens_bnb", "0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82",
     "0x5692db8177a81a6c6afc8084c2976c9933ec1bab", 5_896_692, "2023-10-01",
     "vote-escrow (veCAKE, BNB Chain)",
     "veCAKE adoption fell post-2024 -> small lock share (~1.5%); clean single-contract lock kept, flagged like RPL"),
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
    """Monthly cumulative locked = cumulative (transfers IN - transfers OUT) of the escrow,
    from Dune's tokens_<chain>.transfers. Returns {ym: cum_locked}."""
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
    src = f"dune:{schema}.transfers cumulative in-out of escrow" + (f" (since {since})" if since else "")
    return {row["block_month"][:7]: float(row["cum_locked"]) for row in rows}, src


def dune_balances_monthly(schema, token, escrow):
    """Monthly end-of-month escrow balance straight from Dune's tokens_<chain>.balances
    historical snapshot table (one row per balance change; take the last per month). Used when
    the full transfers scan exceeds the free-tier 2-min limit. Returns {ym: balance}."""
    sql = f"""
    SELECT date_trunc('month', block_time) AS ym,
           max_by(balance, block_time) AS bal
    FROM {schema}.balances
    WHERE address = {escrow} AND token_address = {token}
    GROUP BY 1 ORDER BY 1
    """
    rows = _exec(sql)
    # forward-fill: a month with no balance change keeps the prior month's end balance
    raw = {row["ym"][:7]: float(row["bal"]) for row in rows if row["bal"] is not None}
    return raw, f"dune:{schema}.balances monthly-last escrow balance"


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
        # cross-check final value vs live balanceOf (the Entry-26 balanceOf==locked identity)
        final = series[max(series)] if series else 0
        ok = abs(final - live_bal) / live_bal < 0.02 if live_bal else False
        print(f"  {sym:5} {schema:16} months={len(series)}  recon_final={final:,.0f}  "
              f"balanceOf={live_bal:,.0f}  cross-check={'PASS' if ok else 'CHECK'} (d={abs(final-live_bal)/live_bal:.2%})")

        obs = panel[(panel.cmc_id == cmc_id) & (panel.status == "observed")][
            ["month_end", "ym", "circulating_supply"]].sort_values("ym")
        first_ym = min(series) if series else None
        last_val = None
        for _, r in obs.iterrows():
            if r.ym in series:
                last_val = series[r.ym]
            # forward-fill only AFTER the series begins (no value before the escrow existed)
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
    for sym in ["GMX", "AERO", "CAKE"]:
        d = nz[nz.symbol == sym]
        if len(d):
            print(f"  {sym}: ratio {d.staking_ratio.min():.2%}->{d.staking_ratio.max():.2%} "
                  f"(latest {d.sort_values('month_end').staking_ratio.iloc[-1]:.2%})")


if __name__ == "__main__":
    main()
