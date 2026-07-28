# Session 038 Report — SHIB ch2 (EVM DeFi Breadth Batch 3b)

**Date:** 2026-07-27
**Engine:** `04_code/phase1_channel2_stream.py` (unchanged; VAL_CAP_MULT = CONTAM_MULT = 100)
**Build log:** `04_code/session038_build.log`

## Task A — Build

| metric | value |
|---|---|
| cmc_id / symbol | 5994 / SHIB (Ethereum, chainid 1) |
| getLogs calls | **53,683** |
| est. getLogs | 128,000 |
| actual / estimate | **0.42x** |
| transfers | 17,845,462 |
| screened months | 61 (2021-05-31 .. 2026-05-31) |
| contract screen | 13 contracts / 81 candidate addresses |
| wall time | ~2.1 h (8 workers, 32 block-batches) |

**Estimate note confirmed:** the holder-count-based estimate again overshot
(0.42x actual), consistent with the sessions 034–036 pattern (long sparse
pre-activity block ranges; SHIB's first 11M blocks produced ~88 getLogs).
Well under the 150k stop threshold and the 185k daily cap.

**Guards:**
- **B2 pass** — zero months excluded by the 100× contamination guard
  (no `excluded: onchain>100x circ` notes in the checkpoint; all 61 rows kept).
- **B4 pass** — screened HODL-6m **median 78.1% ≤ 80%** (last month 82.5%);
  no flag required.

## Task B — TVL decision

**SHIB excluded from NV/TVL regression — meme token, no direct protocol TVL.
`shibaswap` slug belongs to BONE (cmc_id=11865), not SHIB.**

Verified in `03_data/phase2/tvl_panel.csv`: the only shiba-related slug
(`shibaswap`, the ShibaSwap DEX) is already assigned to its governance token
BONE (cmc 11865, 59 months in panel); SHIB has zero tvl_panel rows. Assigning
`shibaswap` to SHIB would double-count the DEX TVL against the wrong token.
**SHIB → λ-only.**

## Task C — Post-assemble totals

| panel | before (post-037) | after (post-038) |
|---|---|---|
| λ panel | 13,449 asset-months / 462 assets | **13,510 asset-months / 463 assets** |
| channel2_holding.csv | 423 tokens / 13,661 rows | **424 tokens / 13,722 rows** |
| coverage | 189 / 314 / 1,436 | **189 complete / 315 partial / 1,435 not_started** |
| regression-ready | 178 (coins 22, tokens/other 156) | **178 — unchanged** (coins 22, tokens/other 156) |

SHIB moves not_started → partial (λ-only; `tvl_defillama` intentionally never
assigned). Regression-ready unchanged, as expected.

## Status

EVM DeFi breadth is complete (batches 1–3b all done).

**Next (Session 039):** DOT/KSM PQ source probe (would make them
regression-ready); TRX `coin_staking_type` mislabel fix (pow_only → DPoS w/
ch1); WARP identity review.
