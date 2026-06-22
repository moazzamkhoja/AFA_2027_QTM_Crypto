# Transition Document — Phase 0 → Phase 1

**Written:** 2026-06-22, end of Session 006 (Phase 0 pipeline).
**For:** the next Claude Code session, which will run **Phase 1 (λ channels)**.

This document is the bridge between the completed universe build and the λ-index work.
Read it together with `06_documentation/PHASE0_SESSION_STATUS.md` (what happened) and
`04_code/DATA_SPECIFICATION.md` Sections 3 and 7 (what Phase 1 must produce).

---

## 1. State of the repo at handoff

- **Universe is built and frozen** in `03_data/universe_panel.csv` (asset × month,
  2015-08→2026-05). Each row: `cmc_id, symbol, month_end, status, price, market_cap,
  mcap_rank, circulating_supply, volume_24h`. `status ∈ {observed, carried_forward}`.
- **Asset list:** `03_data/universe_assets.csv` (1,939 names, with `entry_month`, tags).
- **Classification:** `03_data/classification_table.csv` — `asset_class ∈ {coin, token,
  other}`, `classification_basis`, `ambiguous_flag`, `staking_start`, `transition_note`,
  `defillama_categories`. Stablecoins are in this table with `in_universe=False`.
- **Raw snapshots cached** at `03_data/raw/cmc_snapshots/<date>.json` — re-runnable
  without new network calls. Each has a `_meta` block (requested vs served date, n).
- **Decisions log:** `04_code/DATA_DECISIONS_LOG.md`, 9 entries. Append, never edit.

## 2. The stable keys Phase 1 must use

- **Join on `cmc_id`**, never on `symbol` (symbols collide across dead/relisted coins;
  the universe deliberately keys on the numeric CMC id).
- The investable cross-section in month *t* = panel rows with `status='observed'`. The
  `carried_forward` rows are dead/fallen tails kept for anti-survivorship; **do not
  compute λ for carried_forward months** (no live supply data) — treat them per the
  Phase 3 death-return policy once decided.

## 3. What Phase 1 must produce (spec Section 3)

λ_t per asset-month as the **equal-weighted average of the standardized (z-scored within
each monthly cross-section) values of whichever of the three channels are observable**,
plus the count/identity of contributing channels. Do **not** impute missing channels.

1. **Channel 1 — staking/locking ratio** = staked-or-locked / circulating (or total).
   - Coins (PoS): chain staking dashboards / PoS explorers. **Respect transition dates**
     — e.g. ETH has *no* staking channel before `staking_start=2020-12-01`
     (`classification_table.csv` carries this). Pure-PoW coins have no staking channel at
     all (expected, not a bug).
   - Vote-escrow tokens (veCRV, veBAL, …): locked supply via protocol dashboards/DeFiLlama.
2. **Channel 2 — holding duration** (hardest): on-chain HODL-wave / coin-age proxy.
   Document the exact computation per chain and its limitations. This is realistically
   the *only* λ channel for early-sample (pre-2020) coins.
3. **Channel 3 — voting engagement** = voters / eligible supply, monthly. Snapshot /
   Tally / Boardroom for off-chain; on-chain Governor contracts otherwise. Essentially
   unavailable before ~2020 and absent for pure coins — expected.

Output a per-asset-month λ table **plus the channel-availability breakdown** (how many
and which channels contributed) — that breakdown is itself a required diagnostic for the
Phase 1 coverage report.

## 4. Source pointers verified / discovered in Phase 0

- **CoinMarketCap free historical data-api** is the working market-cap/supply backbone
  (CoinGecko free = 365-day limit only). Endpoint and parsing are in
  `fetch_cmc_snapshots.py`.
- **DeFiLlama free API** (`api.llama.fi/protocols`, and its TVL/locked endpoints) works
  and is the natural source for vote-escrow locked supply and protocol categories.
- **Per-chain explorers** (Etherscan/beaconcha.in, Solscan, Snowtrace, Arbiscan, …) and
  **Snapshot/Tally/Boardroom/DeepDAO** for governance — verify each one's current free
  access *before* building on it, exactly as Phase 0 did with CMC/CoinGecko/Artemis.
- **Artemis** has no free API as of 2026-06-22.

## 5. Carry these open decisions into Phase 1 planning

1. **Death-return / carry-forward policy** (Phase 3, but affects how you treat the tail).
2. **Manual classification confirmation** for `other`/`ambiguous` assets that enter tests.
3. **N=250 confirmation** once λ coverage is known (a tighter screen may be warranted).
4. **Watch for other PoW→PoS or mechanism-change transitions** beyond ETH while building
   the staking channel; log each with dates like ETH was.

## 6. Process reminders (AFA compliance)

- Log the Phase 1 session as `06_documentation/ai_conversations/session_007_*.md` (record
  model/interface), append `DATA_DECISIONS_LOG.md` as you go, and update `time_log.md`.
- Produce a **Phase 1 coverage report** before starting Phase 2 (spec Section 7).
- Commit + push to `github.com/moazzamkhoja/AFA_2027_QTM_Crypto` (main) at session end.
