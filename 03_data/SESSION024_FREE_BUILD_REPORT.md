# Session 024 — Free-source λ BUILD report (Phase 1 of the two-phase plan)

**Date:** 2026-06-30 · **Commit:** (this session) · **Decisions Log:** Entries 57–60
**λ before → after: 2,130 → 2,699 observed asset-months; 68 → 90 distinct assets (+569 / +22).**

This session turned session-022's free-source-confirmed identification map into actual λ series,
using **only free sources on free chains** (Phase 2 = paid, explicitly out of scope). Baseline
going in (session 023, commit b7ecb73): 2,130 asset-months / 68 assets.

---

## What was built (the λ-movers)

### Task A — Channel 3 on-chain governance DELEGATION (NEW sub-channel) — **+560 asset-months / +21 assets**
- **Worklist:** the 34 getLogs-CONFIRMED `ERC20Votes-ACTIVE` tokens (session-022 map).
- **Dedup vs Snapshot:** 10 already have a Snapshot Channel-3 turnout series (GTC, ENS, MNT, COMP,
  SUSHI, UNI, RGT, KP3R, STRK, HFT) → cross-check role. **24 NET-NEW** → primary role.
- **Method:** replay `DelegateVotesChanged` logs (uint256 topic `0xdec2bacd…`; uint96 `0x664ef4a2…`
  for DDX), track each delegate's latest `newBalance`, sum at each month-end block = delegated
  voting weight outstanding; ÷ circulating supply. Free chains only (ETH/Arbitrum/Blast).
- **Built:** 21 of 24 net-new (560 asset-months). 3 excluded with reasons: TOMI & UXLINK
  (all delegation events post-date their observed panel window → 0 in-window, block-verified);
  CYBER (2 events, 0 delegated). **ETHDYDX excluded on mechanism** (`DelegatedPowerChanged`/Aave
  auto-power, ratio≈1 — not opt-in delegation; the AKRO "verify the mechanism" discipline).
- **Construct decision (documented, not silently merged):** delegated-weight-outstanding is a
  STOCK of governance-*activated* supply — a DISTINCT sub-channel from Snapshot's per-proposal
  turnout FLOW. Written to its own `channel3_onchain_delegation.csv`, enters λ as channel
  `ch3_delegation` (z-scored in its own cross-section). **Governance-channel waterfall:** only
  `role=primary` (net-new) rows enter λ; the 10 overlap tokens are cross-check-only → no
  governance double-count (verified: ch3_delegation never co-occurs with ch3_voting).
- **Flag:** DDX `delegation_ratio` = 204% (CMC circulating excludes delegated locked/treasury,
  the Entry-49 pattern) — un-capped & flagged, λ uses z-scored rank.
- **Files:** `04_code/phase1_channel3_onchain_delegation.py`, `03_data/phase1/channel3_onchain_delegation.csv`,
  checkpoints `03_data/raw/phase1_onchain/delegation/`.

### Task B — Channel 1 free-build — **XAN BUILT, +9 asset-months / +1 asset**
- **XAN (cmc 38481) — BUILD.** XanV1 (Anoma, 2025): `lock()`→`lockedSupply += value; emit
  Locked(account,value)`, permanent (no decrement). Locked series = cumulative Σ`Locked.value`;
  **cross-check 7,500,000,010 == live `lockedSupply()` at 0.000000% drift** (Entry-26 bar).
  Denominator: locked (7.5B) > CMC circulating (2.5B) → Entry-49 artifact, `staking_ratio`=300%
  flagged, `locked_fraction_alloc`=75% written alongside (HEX precedent).
- **VSL — REJECT** (the AKRO pattern, as the kickoff anticipated): bare `Locked()` is a cyclic
  epoch transfer-pause flag (Lockable.checkLock, 5d-lock/25d-unlock per 30d), no amount/escrow.
- **NMR — DEFER (Phase 2):** Numerai tournament `Staked` amount is per-(staker,tag) cumulative
  with separate destroy/release events and a burn-on-stake (Erasure) flow; no aggregate global /
  escrow → no Entry-26 cross-check anchor.
- **stkAAVE (36246) — EXCLUDE:** the Staked-AAVE wrapper; its supply already = AAVE Safety-Module
  lock captured via AAVE (cmc 7278, Entry 26) → double-count; ratio≈1 degenerate.
- **Files:** `04_code/phase1_channel1_freebuild.py`, `03_data/phase1/channel1_freebuild.csv`.

## What was prototyped + measured (no λ change, by design)

### Task C — Channel 2 (coin-age / HODL) — engine built, free budget MEASURED → Phase-2 trigger
- **Engine (`phase1_channel2_holding.py`):** FIFO per-address coin-age from full `Transfer` replay
  (logs carry `timeStamp`); HODL-share = supply in lots older than a window ÷ circulating.
  Validated end-to-end on MET.
- **Address-class hygiene (the key Entry-24 caveat, shown empirically):** MET raw HODL-6m = **90.8%**
  → **1.3%** after removing 5 contract holders (eth_getCode) from the top >6m holders. Nearly all
  apparent "long-held" supply is contract-held (LP/treasury/staking), not EOA conviction; free
  labels don't cover CEX EOAs → residual bias = a Phase-2 paid-label task.
- **Call budget (`phase1_channel2_budget_probe.py`):** MET (small) 24,636 transfers / **79 getLogs
  calls** complete; RAD (mid-size) **204,428+ transfers / 700+ calls / DID NOT COMPLETE**. 793
  free-chain tokens × mid-size cost ≈ 555k calls ≈ 5.6 free-days, and the high-volume tail
  dominates → **panel-scale Channel-2 blows the free ~100k/day cap = the Phase-2 paid trigger.**
- **Decision:** engine proven, NOT scaled, NOT wired into λ (single token). Channel 2 stays the
  λ NaN column — gap now backed by numbers, not an open question.

## What was triaged (no free clean build — Phase-2 worklists)

### Task D — 22 EVM-non-Etherscan tokens
~19 are wrapped/native-gas tokens (conviction belongs to the gas coin, out of token-scope —
Entry-53 logic); only KSP and BORA (KAIA) are genuine DEX/governance candidates → flagged for a
Phase-2 KAIA Klaytnscope/Blockscout getLogs build. **0 free clean builds.**

### Task E — 92 non-EVM-indexed tokens (Solana 53, Neo 9, Tron 6, Osmosis 4, …)
Free indexers serve CURRENT state, not historical month-end snapshots — the Entry-21 archive wall
on non-EVM. Historical Channel-2 is effectively paid there; Channel-1/3 are per-project gas-coin
staking/gov (out of token-scope, low yield). Flagged for Phase 2. 284 NO-IDENTITY not chased
(Entry 56). **0 free clean builds.**

---

## Assembled λ panel (after)
- **2,699 observed asset-months, 90 distinct assets, 2019-12 → 2026-05.**
- Channels: ch1_staking 937 + ch3_voting 848 + **ch3_delegation 560 (new)** + (ch1+ch3_voting) 354.
- n_channels: 2,345 single-channel, 354 two-channel (unchanged — no governance double-count).
- By class: token 73, coin 9, other 8.
- Channel 2 (`ch2_holding`): still NaN at panel scale (Entry 24/59 — Phase-2 trigger measured).

## Method compliance
Numerators from real events/balances (no guessing); Entry-26 cross-check cleared for XAN at
0.0000%; cmc_id joins only; logs-not-eth_call (Entry 21); staking_start respected; assembler
z-score/standardizability/equal-weight logic untouched (only channel inputs widened); no paid
tier used. DATA_DECISIONS_LOG appended 57–60 (append-only).
