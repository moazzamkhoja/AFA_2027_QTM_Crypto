# Claude Code Kickoff Prompt — λ Recovery: Bucket 2 (non-EVM coin staking) + Bucket 3 (EVM token locks)

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`. This builds on a Cowork session's live verification of Bucket 2
(Entry 42) and the three-bucket coverage taxonomy built earlier that session. Run to completion,
review the output, then come back before touching Bucket 1 or Phase 3.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 0/0B/1/2/2b/2c are complete;
session 019 scaled λ to 58 assets / 1,688 asset-months. A Cowork session then decomposed the
1,023 uncovered coin+token assets (94.6% of the 1,081-asset universe) into three buckets:

  - Bucket 1 (~783 assets) — no plausible staking/locking/voting mechanism exists at all. Out
    of scope for this session. Do not touch.
  - Bucket 2 (~170 coins) — non-EVM PoS coins needing a chain-specific indexer. A live
    verification pass (DATA_DECISIONS_LOG.md Entry 42) found free paths for some of these that
    Part A.3's native-RPC-only check had missed, an engineering (not payment) gap for two more,
    a genuine structural dead-end for one, and left several unconfirmed.
  - Bucket 3 (~73 tokens + GMX) — EVM tokens with a plausible governance/staking tag where the
    bottleneck is finding/verifying a clean single-escrow lock contract, not payment.

This session's job is to BUILD everything in Bucket 2 and Bucket 3 that verifies live, and to
upgrade Entry 42's docs-level Bucket-2 findings to response-body-verified ones. Before doing
anything else, read in full:

1. 04_code/DATA_DECISIONS_LOG.md Entries 26, 41, 42 — the EVM clean-escrow standard, the Part
   A.1/A.3 verdict lists, and this session's starting point (Bucket 2 live verification).
2. 03_data/PHASE1_LAMBDA_SCALE_AND_TVL_PANEL_REPORT.md §2–4 — Part A.1 (token Channel-1
   verdicts: built vs. rejected vs. deferred) and Part A.3 (coin staking-source audit).
3. 04_code/DATA_SPECIFICATION.md §0 (flag, don't guess) and §3.1 (Channel 1 definition).
4. 03_data/classification_table.csv and 03_data/universe_panel.csv — the universe, tags, and
   which asset-months already have a Channel-1 or Channel-3 value (use this directly to compute
   the actual "not yet recovered by any channel" token list for Part B — don't take 73 as exact).
5. 04_code/phase1_channel1_evm_locks.py, phase1_channel1_evm_locks_ext.py,
   phase1_channel1_pos_coins.py, phase1_channel1_eth_staking.py — extend these, don't rebuild.

## Part A — Bucket 2: non-EVM coin staking (~170 coins)

Goal: turn Entry 42's docs-level findings into built series or honest, response-body-verified
rejections. Do not re-derive from scratch — Entry 42 already did the desk research; this session
does the live signup + call + build.

**Tier 1 — build now (free, high confidence in Entry 42):**
- SOL: sign up for a free validators.app API token, call `/api/v1/epochs/mainnet.json` live,
  confirm the `total_active_stake` field and per-epoch depth, build the monthly bonded-stake
  series.
- TRX: sign up for TronScan's free API tier (60 req/hr, auto-approved), call `freezeresource`
  with date ranges, build the monthly frozen-TRX series.

**Tier 2 — verify live FIRST, build only if confirmed (medium confidence in Entry 42):**
- DOT, KSM: sign up for a free Subscan API key, call the validator era-statistics endpoint live.
  Confirm the response body actually contains per-era bonded totals — Entry 42's "free" read was
  inferred from the absence of a `[PRO]` tag in the docs, never pixel-confirmed. If the live call
  is gated or empty, log that as a correction to Entry 42 and stop. Do not pay for Subscan Pro.

**Tier 3 — engineering, not payment (build the aggregation):**
- HBAR: iterate Hedera Mirror Node `/api/v1/accounts` (and the balances endpoint's `timestamp`
  fallback to 15-minute snapshot files) to sum `staked_node_id`/`staked_account_id`-linked
  balances per historical snapshot, producing a network-wide staked-total series. Free, public,
  no key. Scope the compute cost (accounts × snapshots) before committing to a full build; if
  genuinely intractable, log it as a documented gap rather than ship a partial series.
- SUI: query the `staking_pool` module's per-epoch exchange-rate-history table via free public
  RPC/GraphQL for every active validator pool since each pool's activation epoch; sum across
  pools per epoch for the network-wide total. Free, public, no key.

**Tier 4 — reclassification check, not a coin-side build:**
- CELO: confirm whether the legacy LockedGold/Election locking contract is still live after the
  March 2025 L2 migration, and whether Celoscan exposes its Transfer/event logs the way Etherscan
  does for EVM tokens. If yes, build CELO with the SAME `getLogs` method as Entry 26 instead of
  treating it as a non-EVM coin. If no, leave it as an open Bucket-2 gap.

**Tier 5 — check access live, build/pay nothing without Moazzam (ATOM, INJ, SEI, KAVA, AVAX, NEAR):**
- Visit the actual signup/pricing flow (not just docs or search results) for Mintscan/Cosmostation
  (ATOM/INJ/SEI/KAVA), Bitquery, AvaCloud Metrics API (AVAX), and Pikespeak/NearBlocks (NEAR).
  Attempt a free-tier signup only where one is genuinely self-serve and free. Report exactly what
  each gate looks like (self-serve free / self-serve paid with disclosed price / contact-sales
  only). Do NOT purchase or commit to any paid tier — that decision is Moazzam's alone.

**Tier 6 — keep searching (EOS, ICP, APT):** no historical source found yet, free or paid. If
nothing turns up this session, leave as a documented gap.

**Excluded (ALGO):** confirmed structural gap, Entry 42 — no vendor, paid or free, has this.
Don't spend time here.

## Part B — Bucket 3: EVM tokens with a plausible governance/staking tag (~73 + GMX)

Already built (Entry 26 + Part A.1): CRV, CVX, FXS, SUSHI, AAVE, YFI, PENDLE, LQTY, 1INCH, RPL.
Already rejected, final (Part A.1, re-read before excluding): MKR, BAL, COMP, RUNE, ANGLE.

1. From classification_table.csv, take every `asset_class='token'` row not already recovered by
   any channel in universe_panel.csv and not one of the 5 final rejects above, that carries a
   staking/governance/vote/lock-relevant tag or `defillama_categories` value. Log the resulting
   count — don't force it to match the ~73 estimate.
2. For each candidate, apply the Entry-26 standard: a single, verified contract that holds a
   meaningful share of token supply via direct custody — not a wrapped/composite asset (like
   veBAL's 80/20 BPT), not in-wallet delegation (like COMP), not a collateral/C-ratio system
   (like SNX). Use the protocol's own docs, its DefiLlama page, and the verified contract on the
   relevant chain's explorer. Classify each: BUILD / REJECT (specific reason) / DEFER (specific
   blocker).
3. For every BUILD candidate, reconstruct the historical locked-supply series from Dune's free
   curated `balances_<chain>.daily_updates` table (confirmed free-tier accessible across 20 EVM
   chains including Arbitrum) — query the escrow contract's balance over time directly from this
   table, NOT via Etherscan `getLogs` (which hit the free-tier result-window cap on Arbitrum for
   GMX). Use the existing Dune key in `04_code/.api_keys.json` under `"dune"`; stay inside the
   free-tier query-credit budget (2,500/month, prior usage <4%) and flag any query that would
   meaningfully eat into it instead of just running it.
4. GMX specifically: mechanism already verified (StakedGmxTracker, Arbitrum, ~65% of supply,
   Part A.1) — skip straight to step 3 for this one. Build it first, as a confidence check on the
   Dune-Balances method before working the rest of the queue.

## Rules (unchanged from the spec and prior entries)
- Never sign up for or pay for any paid tier of anything. Flag a priced, self-serve option and
  report back to Moazzam — he executes any purchase himself.
- Verify every source live (actual signup + actual call + actual response body) before treating
  it as built. Docs language is not sufficient — that's exactly the gap between Entry 42's
  inference and a real verification.
- Join everything on `cmc_id`, never `symbol`.
- Never guess or interpolate a numerator. Flag as a documented gap if it can't be verified live.
- DATA_DECISIONS_LOG.md is append-only — never edit or delete Entries 1–42. Continue at Entry 43,
  one entry per chain/token group (not one giant entry).

## Deliverables
1. Built series for whichever Bucket-2 chains verify live, in `phase1_channel1_pos_coins.py` (or
   a new `phase1_channel1_pos_coins_bucket2.py`).
2. Built series for whichever Bucket-3 tokens verify BUILD, plus GMX, in
   `phase1_channel1_evm_locks_ext.py` (or a new file), using the Dune-Balances method.
3. Re-run `phase1_assemble_lambda.py` to fold the new Channel-1 series into λ; report new
   asset/asset-month counts against the session-019 baseline (58 assets / 1,688 asset-months).
4. A short coverage addendum (markdown) listing, per chain/token: built / rejected-with-reason /
   deferred-with-reason / still-open-gap — the response-body-verified successor to Entry 42.
5. DATA_DECISIONS_LOG.md continued from Entry 43. Log this session as
   `06_documentation/ai_conversations/session_020_*.md`; update `06_documentation/time_log.md`.
6. Commit and push to github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end.

Stop when Bucket 2 and Bucket 3 are done. Do not start Bucket 1 work or Phase 3 without review.
```
