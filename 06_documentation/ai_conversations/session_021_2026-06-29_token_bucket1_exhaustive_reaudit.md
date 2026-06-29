# Session 021 — Token Bucket-1 Exhaustive Re-Audit

**Date:** 2026-06-29
**Model:** Claude Code / Opus 4.8
**Working dir:** `C:\AFA_2027_QTM_Crypto`
**Kickoff:** `04_code/CLAUDE_CODE_TOKEN_BUCKET1_EXHAUSTIVE_REAUDIT_PROMPT.md`
**Scope:** Convert all 398 token-side "unrecoverable" cmc_ids (+ reconfirm the 6 already-rejected +
resolve VELO) into individually documented, source-checked verdicts. Token-side only. No paid tier,
no purchase.

## What was done

**Stage 0 — worklist rebuilt live.** In-universe `asset_class='token'` cmc_ids not in `lambda_panel.csv`,
minus VELO = **exactly 398** (448 − 49 in λ − 1 VELO; reconciled to the penny). Cached 290-file not trusted.
Found AXS/RUNE/MKR are inside the 398; BAL/COMP are already in λ via Channel-3 voting; ANGLE is out-of-universe.

**Stage 1 — bulk DeFiLlama triage, all 398, by cmcId never symbol.** Live `api.llama.fi/protocols`
(7,742 protocols). 92 of 398 have a clean cmcId-matched DL protocol; 306 have no DL protocol and no contract
on file ("no on-chain identity available to check"). Rejected the symbol-matched `defillama_categories` as the
Entry-20 collision landmine (it falsely promoted DOT-cmc814, HONEY, DRIFT, VOLT, LAYER to "Liquid Staking").

**Stage 2 — per-token check of all 92 DL-matched (no sampling).**
- 2a: `/protocol/{slug}` chainTvls → 36 expose a `staking` bucket carrying a raw **staked-token-quantity**
  series (stronger than the USD proxy the kickoff anticipated). Computed staked-qty ÷ circulating for all 36.
- 2b: Dune `tokens_<chain>.balances`/net-transfers top-holder query for every one of the 36 — does ONE
  contract hold the base token in the DL-reported staked amount (the Entry-26 identity)?
- 2c: Artemis re-tested live — `app.artemis.xyz` → `classic.artemis.ai`, JS SPA, no free per-asset data
  (reconfirms Entry 2/14). Not signed up, not paid.

**Result — 5 BUILDs**, each reconstructed via the Bucket-3 Dune transfers method and cross-checked to live
`balanceOf` at **0.00%**:

| cmc | sym | escrow | ratio |
|---|---|---|---|
| 7737 | API3 | Api3Pool (Ethereum) | ~74% |
| 3835 | ORBS | StakingContract (Ethereum) | ~42% |
| 2930 | IQ | HiIQ veIQ (Ethereum) | ~9% |
| 35509 | VVV | Venice staking (Base) | ~73% |
| 7127 | VELO | veVELO (Optimism) | ~7.4% |

**VELO — Entry-48 deferral RESOLVED.** DeFiLlama's own Velodrome V2 *and* V3 entries both carry
`address=optimism:0x9560e827…` — the exact cmc-7127 token. So it is the current canonical token (not a defunct
"v1"); CMC and DeFiLlama agree → the documented mapping the kickoff required. veVELO holds 1.296B base VELO.

**Rejections (393):** 367 REJECT-mechanism (multi-contract restaking like EIGEN; multi-pool like ILV; native/
delegation/farming/Snapshot/meme/stablecoin/wrapped-LST), 29 REJECT-no-data (non-EVM chains outside the free
EVM Dune method — HXRO/SUN/ORN/TLM/C98/BRISE; no single escrow reproduces the DL figure — BTCST/KAITO/ATH/…;
DL bucket 0 — HEX/SFUND/ADF; WARP cmcId-1166 collision artifact), 1 N/A (ANGLE out-of-universe). The 6
reconfirmed unchanged.

**λ impact:** `phase1_channel1_evm_locks_bucket1.py` → `channel1_evm_locks_bucket1.csv` (200 asset-months,
5 assets); re-ran `phase1_assemble_lambda.py` (logic untouched). **λ 1,880 → 2,080 observed asset-months,
62 → 67 distinct assets (token 49 → 54).**

## Decisions / deliverables
- `03_data/phase1/token_bucket1_full_audit.csv` — 402 rows (398 + VELO + BAL/COMP/ANGLE), one specific reason each.
- `03_data/SESSION021_TOKEN_BUCKET1_EXHAUSTIVE_AUDIT.md` — coverage addendum.
- `04_code/DATA_DECISIONS_LOG.md` Entries 50–52.
- Dune free tier: ~36 `small` executes (~15% of monthly budget). No purchase, no paid tier. Every join on cmcId.

## Flags / caveats
- API3 & ORBS show `staking_ratio>1` in some months (CMC circulating excludes pooled tokens — AERO/SOL artifact,
  Entry 49); kept un-capped & flagged, λ uses z-scored rank not level.
- GATED = 0: no priced self-serve option would recover any of the 398.

## Open follow-up
- The 456-coin Bucket-1 has NOT had this individual re-audit — candidate for the same treatment, not started.
- Do not start coin-side Bucket 1 or Phase 3 without review.
