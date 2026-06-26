# Session 019 — λ Scale-Up (Channels 1 & 3, tokens + PoS coins) + Real TVL Panel

**Date:** 2026-06-26
**Agent:** Claude Code / Opus 4.8 (local, normal network access)
**Prompt:** `04_code/CLAUDE_CODE_PHASE1_SCALE_LAMBDA_AND_TVL_PANEL_PROMPT.md` (drafted in the Entry-40 session)
**Scope:** λ scale-up + a real TVL panel for tokens. **Out of scope (unchanged):** PQ-for-coins, Channel 2
(holding duration), and the λ z-scoring/standardizability/weighting logic.
**Deliverable:** `03_data/PHASE1_LAMBDA_SCALE_AND_TVL_PANEL_REPORT.md` (+ this log, Decisions Log Entry 41, time_log).

## Step 0 — repo hygiene (per the prompt's mandatory check)
- No `git` process running; no `.git/index.lock` present. `git status` clean, `main` up to date with origin
  (HEAD `84a21e7`). No index rebuild needed (the Entry-40 stale-index incident did not recur locally).
- Re-derived the live next-numbers (the prompt warned twice about stale kickoff numbers): last Decisions Log
  entry = **40** → next **41**; last session file = **018** → next **019**; last time-log row = session 018.
  All matched the prompt's stated numbers, but were confirmed live, not trusted.

## What I did
1. **Read context first** — DATA_SPECIFICATION §3/§2.5/§4; DATA_DECISIONS_LOG Entries 21–30, 40; the five
   Phase-1 channel scripts; `phase2c_defillama_metadata.py::check_tvl()`. Confirmed live network reach to
   `api.llama.fi` (200), `hub.snapshot.org/graphql` (200), Etherscan V2 (OK) — the Cowork sandbox couldn't
   reach llama; this local session can.
2. **Re-derived all ceilings live**: 127/448 tokens dl_slug-matched, 123 has_address, 29 has_snapshot;
   curated voting map 56 spaces / 55 tokens; coin-side λ = ETH only (1/633). Matched the prompt.
3. **Part B (built first — most concrete):** new `phase2_build_tvl_panel.py` — full monthly TVL series for
   all 127 dl_slug-matched tokens → `tvl_panel.csv`. 97 non-empty, 4,895 asset-months, 0 fetch failures,
   30 expected empties (aggregators/DAOs/chains with no protocol TVL). Stretch goal: verified loose
   symbol+name matches → +AXL, +PERP (99 tokens / 4,999 asset-months); rejected CVP/POLS (cmcId-mismatch
   collision risk) and METIS/HONEY/PUMP/PYTH/WLFI (zero TVL).
4. **Part A.1 (token Channel 1):** live `balanceOf` sanity-check then `getLogs` reconstruction for the
   candidates. **VERIFIED + built:** PENDLE (vePENDLE 22.9%), LQTY (LQTYStaking 57.8%), 1INCH (St1inch
   15.8%), RPL (RocketVault 47.3%, flagged shared-vault). **VERIFIED mechanism but series DEFERRED:** GMX
   (StakedGmxTracker ~65%, Arbitrum) — full-history `getLogs` over Arbitrum's millions-of-blocks/month is
   impractically slow on the free tier (>60 s/month); GMX row left commented with rationale, to be built
   later via `account/tokentx` pagination. **REJECTED (documented):** MKR (DSChief holds 0.5% post-Sky),
   BAL (veBAL wrong token), COMP (delegation, no lock), RUNE (native L1, placeholder address), ANGLE (not
   in universe). New `phase1_channel1_evm_locks_ext.py` (4 assets, 214 asset-months); reconstructed
   latest-locked matched live balanceOf to rounding for all four.
5. **Part A.2 (token Channel 3):** governanceID cross-check yielded 0 new spaces (all 29 already in the
   curated map). Probed the Entry-25 gap list live on Snapshot (id_in + ranking search): **+ENA
   `ethenagovernance.eth`** and **+PERP `vote-perp.eth`** — both official, active, token-weighted
   (erc20-balance-of on the canonical token); added to the curated map and re-ran channel3 (now 57
   spaces / 53 vw_turnout assets). ONDO/WLD = spam-only; PENDLE top hit = StakeDAO's sdpendle (not
   official, and PENDLE is now C1-covered); MKR/LQTY/RUNE = no verifiable clean Governor → no VoteCast
   reconstruction (no-guess rule).
6. **Part A.3 (PoS-coin Channel 1):** Entry-21-style live audit across the reference PoS chains. **BUILT:**
   ADA via Koios `epoch_info.active_stake` (70 months, ratio 49→74%) and XTZ via TzKT
   `cycles.totalBakingPower` (95 months, flagged Paris-2024 redefinition). **Live-verified gaps:** Cosmos
   (`/pool` current-only), SOL/HBAR (current-only), ICP (ic-api 404), DOT/KSM (keyed), AVAX/NEAR/ALGO/
   TRX/EOS/SUI/APT (no free historical). New `phase1_channel1_pos_coins.py` (2 assets, 165 asset-months);
   no value guessed/interpolated.
7. **Reassembled λ** (`phase1_assemble_lambda.py`, logic untouched — it auto-globbed the new
   `channel1_*.csv` + the updated `channel3_voting.csv`). Wrote the report, this log, Entry 41, time_log.

## Outcome
- **λ: 1,374 → 1,688 observed asset-months; 52 → 58 distinct assets** (coin 5→7 [+ADA,+XTZ]; token 43→47
  [+PENDLE,+LQTY,+ENA,+PERP]; other 4). Channel 1: 7→13 assets (coins 1→3, EVM-escrow 6→10); Channel 3:
  51→53. Coin-side staking is now standardizable (ETH+ADA+XTZ co-occur).
- **TVL panel: `03_data/phase2/tvl_panel.csv` — 4,999 monthly asset-months across 99 tokens, 2019-12 →
  2026-05.** A valuation-multiple denominator (NV/TVL), NOT a PQ proxy (Entry 30 unchanged).
- Still NOT covered: coin PQ (deferred), Channel 2 (gap), GMX series (deferred), PoS coins beyond ADA/XTZ
  (no free historical), the 30 empty-TVL tokens (undefined by construction).

## Notes / landmines for the next session
- `phase1_assemble_lambda.py` crashes on the final console `print` under a cp1252 Windows console
  (`λ`/`→` chars) — **cosmetic only; the CSV is written before the print.** Run with
  `PYTHONIOENCODING=utf-8` to see the coverage summary. (Not "fixed" — out of the don't-touch-assembly scope.)
- bitinfocharts / DeFiLlama-Pro / Subscan / Solana-Beach all remain paid/keyed — no purchase made.
- Inherited caveat surfaced (not introduced): the TVL panel uses the identity map's one-slug-per-cmcId
  choice, so multi-version protocols capture only the mapped version (AAVE→aave-v2). Flag for the NV/TVL build.
- **Stop after the report** (per the prompt): no coin-PQ work started, Channel 2 untouched.
