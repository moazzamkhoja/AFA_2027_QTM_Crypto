# Session 020 — λ Recovery: Bucket 2 (non-EVM coin staking) + Bucket 3 (EVM token locks)

**Date:** 2026-06-26
**Agent:** Claude Code / Opus 4.8 (local, normal network access)
**Prompt:** `04_code/CLAUDE_CODE_LAMBDA_BUCKET2_BUCKET3_RECOVERY_PROMPT.md`
**Scope:** build everything in Bucket 2 + Bucket 3 that verifies **live, response-body**, and upgrade
Entry 42's docs-level findings to response-body-verified ones. **Out of scope (unchanged):** PQ-for-coins,
Channel 2, λ assembly logic, Bucket 1, Phase 3.
**Deliverables:** `03_data/SESSION020_BUCKET2_BUCKET3_COVERAGE_ADDENDUM.md`, Decisions Log Entries 43–49,
this log, time_log, the two new build scripts + their CSVs.

## Context read first (per the prompt)
DATA_DECISIONS_LOG Entries 26/41/42; PHASE1_LAMBDA_SCALE_AND_TVL_PANEL_REPORT §2–4; DATA_SPECIFICATION
§0 + §3.1; classification_table.csv + universe_panel.csv (to recompute the real uncovered-token list);
the existing channel scripts (`phase1_channel1_evm_locks_ext.py`, `phase1_channel1_pos_coins.py`,
`phase1_assemble_lambda.py`) and the Dune dry-run scripts.

## Headline
λ **1,688 → 1,880 observed asset-months; 58 → 62 distinct assets** (coin 7→9, token 47→49). Every build
cross-checks to a live on-chain `balanceOf`/aggregate; every non-build is a response-body-verified
rejection/gap, not a silent drop. **No paid tier used; no purchase made.**

## Part A — Bucket 2 (non-EVM coin staking)
- **TRX — BUILT, keyless.** TronScan `freezeresource` returns full daily history with **no API key**
  (`total_freeze_weight`); 78 months. **Corrects Entry 42** (no signup needed).
- **SOL — BUILT, keyless.** validators.app `/epochs?per=200&page=N` exposes `total_active_stake`
  **without a token** for every epoch it recorded (begins ~2023-01; earlier epochs null = data vintage,
  not paywall); 40 months. Refines Entry 42 to "free **and keyless**, ~2023-01+ depth".
- **DOT/KSM — NOT built (Entry-42 correction).** Subscan era_stat returns **HTTP 403** "API strictly
  requires an API key"; free key is self-serve but needs interactive email signup, not completable
  headless. So the docs-level "free-tier" could not be response-body confirmed. No Pro purchase.
- **HBAR / SUI — documented gaps (scoped).** Both have free current-state endpoints (HBAR network/stake
  14.6B; SUI sum stakingPoolSuiBalance 7.23B) but **no historical series** without per-account / per-pool
  aggregation that is keyless-intractable. Not partial-shipped.
- **CELO — documented gap (reclassification confirmed, build failed cross-check).** CELO **is** on
  Etherscan V2 (chainid 42220, existing key) and LockedGold is live (balanceOf 85.65M, getTotalLockedGold
  82.43M). But free getLogs reconstruction gives only 2.0M (GoldToken Transfer — native locking emits none)
  / 25.8M (LockedGold native events — L2-migration carried ~57M as state, no re-emitted events) vs 82.43M.
  Fails the Entry-26 cross-check → **not shipped** (flag-don't-ship). Clean number needs archive/PRO eth_call.
- **ATOM/INJ/SEI/KAVA/AVAX/NEAR/EOS/ICP/APT — open gaps (access checked, no purchase).** Cosmos =
  contact-sales (Mintscan) / trial-only points (Bitquery); AVAX = ambiguous pricing page; NEAR = key-gated/
  current-only; EOS/ICP/APT = no free historical source. ALGO unchanged structural gap.

Output: `03_data/phase1/channel1_pos_coins_bucket2.csv` (TRX+SOL, 118 asset-months, 2 assets).

## Part B — Bucket 3 (EVM token locks)
- **Candidate pool: 290** (asset_class='token', uncovered, gov/staking tag or DeFiLlama category, not the 5
  final rejects). Entry-26 clean-single-escrow test is the real filter — most are DEX/lending/RWA/meme/chain
  tokens with no base-token custody.
- **Dune method correction:** the kickoff's `balances_<chain>.daily_updates` **does not exist** on the free
  tier; the correct free tables are `tokens_<chain>.transfers` (cumulate in−out of escrow) and
  `tokens_<chain>.balances`. BSC schema = `tokens_bnb`. Etherscan V2 free key does **not** cover Base/BSC
  (does cover Ethereum/Arbitrum/Celo), so AERO/CAKE were verified via keyless public RPC `balanceOf` and
  built through Dune.
- **BUILT (each cross-checks final cumulative vs live balanceOf):** **GMX** (Arbitrum StakedGmxTracker,
  recon 6,162,450 vs 6,160,000 = 0.04% — retires the Entry-41 deferral; built first as the method check),
  **AERO** (Base veAERO, 968.4M vs 968.4M = 0.00%, 50% of supply; ratio>1 vs CMC circulating flagged),
  **CAKE** (BNB veCAKE, 5.897M vs 5.897M = 0.00%; small ~1.5% share flagged, RPL standard).
- **AXS REJECT** (staking on Ronin, no free EVM index). **VELO DEFER** (v1 cmc 7127 vs v2-token escrow —
  cmcId/symbol collision the project forbids).

Output: `03_data/phase1/channel1_evm_locks_bucket3.csv` (GMX+AERO+CAKE, 101 asset-months, 3 assets).

## Assembly
Re-ran `phase1_assemble_lambda.py` (untouched; auto-globs `channel1_*.csv`). 1,880 asset-months / 62
assets; coin 9, token 49, other 4; 2-channel months 322→354 (GMX's voting+lock); Ch1 standardizable
months 73→78. GMX upgraded 1→2-channel (it already had a Channel-3 Snapshot value).

## New/changed files
- `04_code/phase1_channel1_pos_coins_bucket2.py` (new) → `03_data/phase1/channel1_pos_coins_bucket2.csv`
- `04_code/phase1_channel1_evm_locks_bucket3.py` (new) → `03_data/phase1/channel1_evm_locks_bucket3.csv`
- `04_code/_celo_event_check.py` (kept: CELO reconstruction cross-check, reproducibility)
- `03_data/phase1/_bucket3_candidates.csv` (the 290-candidate pool)
- `03_data/phase1/lambda_panel.csv` (re-assembled)
- `03_data/SESSION020_BUCKET2_BUCKET3_COVERAGE_ADDENDUM.md`; DATA_DECISIONS_LOG Entries 43–49

## Stop point
Bucket 2 + Bucket 3 done. **Do not start Bucket 1 or Phase 3 without review.** Open items for Moazzam:
free Subscan key (DOT/KSM), the VELO v1/v2 identity call, and the Tier-5 access gates (no purchase made).
