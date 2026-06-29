# Session 023 — HEX/AKRO Reconciliation + Survivorship-Bias Documentation
**Date:** 2026-06-29 · **Agent:** Claude Code / Opus 4.8 · **Working dir:** `C:\AFA_2027_QTM_Crypto`
**Kickoff:** `04_code/CLAUDE_CODE_HEX_AKRO_RECONCILIATION_AND_SURVIVORSHIP_PROMPT.md`
**Basis (stated, not re-litigated):** where session 022's verified-contract-read + `getLogs` method
conflicts with session 021's Dune-top-holder single-escrow substitute, **022's method governs.**

---

## Required reading (done first)
- DATA_DECISIONS_LOG Entry 26 (curated single-escrow standard) and Entry 53 (session 022 feasibility map).
- `SESSION021_TOKEN_BUCKET1_EXHAUSTIVE_AUDIT.md` — HEX rejected *"staking internal to the HEX contract"* /
  *"DL staking bucket reads 0"*; AKRO rejected in the *"no single contract reproduces the DL staked figure"*
  cluster (KAITO/ATH/SUPER…).
- `SESSION022_STATUS_AND_NEXT_SESSION.md` §2a — HEX "amount-bearing, build-ready"; AKRO "bare `Locked()`,
  need contract-balance reads."
- Cached session-022 artifacts: `universe_lambda_channel_map.csv` (HEX cmc 5015 StakeStart, AKRO cmc 4134
  `Locked()` logs=1), `_universe_lambda_findings.csv`, `03_data/raw/etherscan_src/` (verified source).

## Part 1 — HEX (cmc 5015): REJECT → **BUILD**
- Read verified HEX source: `stakeStart()` does `_lockedHeartsTotal += newStakedHearts` then
  `_burn(msg.sender, newStakedHearts)` → **non-custodial burn**, no escrow holds the tokens (so 021's
  single-escrow `balanceOf` probe and DeFiLlama correctly saw nothing). New construction path vs Entry 26.
- Custody resolved directly: staker `balanceOf` falls (burn), HEX contract `balanceOf` does not rise; staked
  quantity lives only in `lockedHeartsTotal`.
- Denominator checked, not assumed: contract NatSpec — `totalSupply()` = circulating, **excludes staked**;
  `allocatedSupply() = totalSupply + lockedHeartsTotal`. CMC circ mirrors `totalSupply` → same Entry-49
  artifact as AERO/SOL/API3/ORBS, not a new double-count. Live reads: locked 619.0B, liquid 57.0B, alloc
  676.0B; within HEX's observed window (2020-03..2024-05) locked<circ so ratio <1.
- Reconstruction: only `StakeStart`(+stakedHearts) and `StakeEnd`(−orig stakedHearts) move
  `lockedHeartsTotal` (single `-=` site; StakeGoodAccounting doesn't). Decoded on Dune
  `hex_ethereum.HEX_evt_StakeStart/_StakeEnd`, `stakedHearts=(data0>>40)&(2^72−1)` via exact UINT256
  arithmetic (verified == Python decode); StakeEnd amount via `stakeId` join.
- **Cross-check: recon final 61,900,823,759,862,091,712 hearts == live `globalInfo()[0]` → drift 0.000000%.**
- Built `04_code/phase1_channel1_hex_stake.py` → `03_data/phase1/channel1_hex_stake.csv` (50 asset-months,
  ratio 14.3%→43.5%). Re-assembled λ: **2,080→2,130 asset-months, 67→68 assets.** Logged **Entry 54**.

## Part 1 — AKRO (cmc 4134): REJECT **reconfirmed**
- Session 022's "GENUINE `Locked()`" is a **false positive** of its name-matching Ch1 classifier. AKRO's
  address is the **token contract itself** (`TokenProxy`→`AkropolisToken`); `Locked()` is from a `Lockable`
  base — `lock() onlyOwner { setLock(true); emit Locked(); }`, an **admin pause switch**, no amount, no
  escrow. Live `getLogs`: fired **exactly once** (block 8099298, `data=0x`).
- No mechanism to reconstruct → **REJECT**; 021 stands, now with the contract-level reason. No 021-vs-022
  contradiction remains. Logged **Entry 55**.

## Part 2 — Survivorship-bias (Entry 56)
- Re-derived live: `non_evm_lambda_recoverability.csv` class `NO-IDENTITY` = **284**. Reconciled to the
  penny against `universe_lambda_channel_map.csv`: 1,306 = 901 reachable + 405 off-Etherscan; the 405 ==
  exactly the non-reachable rows (overlap 405/405, 0 outside, 0 dupes); 405 = 284 + 92 + 22 + 7.
- Cohort: 83% asset_class "other"; 89% pre-2020; ~32 newer non-standard-chain tail. Documented as a
  **permanent, acknowledged survivorship-bias limitation**, with the bias *direction* (dead cohort is
  disproportionately low-conviction/no-governance → truncates the low-λ tail → survivors conditionally
  higher-λ). Wrote `03_data/SURVIVORSHIP_BIAS_NOTE.md` (paper-ready) + mirrored in
  `SESSION023_HEX_AKRO_RECONCILIATION.md` §3.

## Rules respected
No paid tier (free Etherscan key + free Dune `small`). Joins on `cmc_id`. No numerator guessed — HEX
reconstructed and reconciled to live chain state at 0.0000%. Log append-only (Entries 1–53 untouched;
continued 54/55/56). Did **not** touch the Ch3 dedup, the 16 BSC/Base/Avax paid-gated tokens, or the Ch2
prototype.

## Artifacts
- New: `04_code/phase1_channel1_hex_stake.py`, `03_data/phase1/channel1_hex_stake.csv`,
  `03_data/raw/phase1_onchain/dune_locks/HEX_stake_recon.json`,
  `03_data/SESSION023_HEX_AKRO_RECONCILIATION.md`, `03_data/SURVIVORSHIP_BIAS_NOTE.md`.
- Changed: `03_data/phase1/lambda_panel.csv` (re-assembled), `04_code/DATA_DECISIONS_LOG.md` (+54/55/56),
  `06_documentation/time_log.md`.
