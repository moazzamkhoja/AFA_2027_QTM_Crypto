# Session 028 — Cowork: Coverage CSV + Session 028 Planning

**Date:** 2026-07-04
**Type:** Cowork (review + planning + tooling, no data build)
**Participants:** Moazzam Khoja, Claude (Sonnet 4.6 via Cowork)

---

## Context

Session started from a summarized context (prior conversation exceeded context window).
Summary covered sessions 001–027 and all standing project rules.

## Work done this session

### 1. Universe coverage CSV generated

User requested a comprehensive table of all ~1,939 in-universe assets showing current data
coverage and what remains needed per asset. Built `03_data/universe_coverage_status.csv`
(1,939 rows) by merging:

- `classification_table.csv` (master asset list: asset_class, sector, staking_start,
  classification_basis)
- `lambda_panel.csv` (current λ channel coverage: has_ch1, has_ch2, has_ch3_v, has_ch3_d,
  lambda_months, lambda_n_channels, lambda_channels)
- `nvt_gl_panel.csv` (PQ/NVT_GL coverage: has_nvt_gl, nvt_months, pq_source)
- `tvl_panel.csv` (TVL coverage: has_tvl, tvl_months)
- `universe_lambda_channel_map.csv` (EVM feasibility: evm_chain, etherscan_reachable,
  ucm_ch1, ucm_ch2, ucm_ch3)
- `_channel2_sizes.csv` (holder_count, est_getlogs_calls)

`what_needed` column logic:
- Coins: ch1_staking (if PoS; inferred from classification_basis PoS tags) + pq_nvtgl; ch2
  and ch3 excluded per framework decision (coins use NVT, not NV/TVL; ch3 governance N/A)
- Tokens/other: ch1_staking (if ucm_ch1 available) + ch2_holding (with holder count) +
  ch3_governance (if ucm_ch3 available) + tvl_defillama
- coin_staking_type column: pos / pos_possible / pow_only / unknown (derived from
  classification_basis tags)

`coverage_status`: complete / partial / not_started (stablecoins excluded from in_universe)

**Key finding: universe is 1,939 assets (858 other, 633 coin, 448 token — no stablecoins
in-universe per classification_table.csv filter).**

Post-session-027 counts (from actual lambda_panel.csv + tvl/nvt files):
- λ: 282 assets (9 coin, 128 token, 145 other)
- Token/other λ ∩ TVL (regression-ready): 80 assets
- Coin λ ∩ NVT_GL (regression-ready): 5 assets
- n_channels: 225 single / 48 two / 9 three

### 2. Session 027 review

Read `SESSION027_TVL_AND_CH2_REPORT.md` in full. Key outcomes:
- TVL: 99 → 130 tokens; all 9 three-channel assets now have TVL denominator
- ch2: all 43 remaining ch1-or-ch3-no-ch2 lambda tokens built (2+ channel share 11→24.4%)
- λ: 6,021 → 7,051 asset-months (282 assets unchanged — depth session)
- AAVE has 22 null ch2 months (spam-excluded, 2024-08→2026-05) — identified as a fix target

### 3. Next-steps discussion

Key insight: coin side is the regression bottleneck. 49 coins have NVT_GL but no λ.
Priorities:
1. Coin staking (ch1) for PoS chains — primarily BNB/BSC (Etherscan Pro in hand),
   DOT/KSM (free Subscan key needed), CELO (Pro balance history endpoint probe),
   AVAX (AvaCloud gate check), NEAR (NearBlocks probe), Cosmos alternatives
2. AAVE ch2 fix — per-token totalSupply denominator recovers 22 null months
3. Token breadth ch2 (~500 not-yet-lambda tokens) — lower priority, single-channel adds

### 4. Session 028 prompt drafted

`04_code/CLAUDE_CODE_SESSION028_COIN_STAKING_AND_AAVE_FIX_PROMPT.md` created.
Tasks:
- A1: BNB via BSC StakeHub contract getLogs (Etherscan Pro, chainid 56)
- A2: DOT/KSM via Subscan (check for key in .api_keys.json; flag if missing)
- A3: CELO via Etherscan Pro `balancehistory` endpoint on chainid 42220
- A4: AVAX via AvaCloud Metrics API gate check
- A5: NEAR via NearBlocks historical staking probe
- A6: Cosmos (ATOM/INJ/SEI/KAVA) via StakingRewards.com GraphQL + Numia
- B: AAVE ch2 fix using ERC20 `totalSupply()` at month-end blocks as denominator

## Files produced this session

- `03_data/universe_coverage_status.csv` (new — 1,939 asset coverage table)
- `04_code/CLAUDE_CODE_SESSION027_TVL_EXPANSION_AND_CH2_TAIL_PROMPT.md` (created earlier
  this session, committed with the session 028 prompt)
- `04_code/CLAUDE_CODE_SESSION028_COIN_STAKING_AND_AAVE_FIX_PROMPT.md` (new)
- `06_documentation/ai_conversations/session_028_2026-07-04_cowork_coverage_csv_and_session028_plan.md` (this file)
- `06_documentation/time_log.md` (to be appended)

## Standing rules confirmed

All standing rules in force:
- No paid tier without Moazzam executing the purchase himself
- cmc_id joins only
- Flag, don't guess
- DATA_DECISIONS_LOG append-only
- Etherscan Pro Standard active ($199/mo, activated 2026-06-30)
