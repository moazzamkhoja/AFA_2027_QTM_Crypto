# Session 036 — EVM DeFi Breadth Batch 3a: stETH + MEME

**Date:** 2026-07-26
**Engine:** `04_code/phase1_channel2_stream.py` (unchanged; VAL_CAP_MULT=CONTAM_MULT=100, self-transfer skip, B2/B4 guards)

## Per-token results

| | stETH (8085) | MEME (28301) |
|---|---|---|
| chain | Ethereum (1) | Ethereum (1) |
| getLogs actual | 13,365 | 9,079 |
| getLogs estimate | ~49k | ~61k |
| transfers | 4,529,175 | 2,932,933 |
| screened months | 50 | 31 |
| B2 (100x contamination) | pass | pass |
| B4 (HODL-6m median >80%) | pass (13.4%, last 13.1%) | pass (3.7%, last 15.4%) |
| TVL decision | excluded — LST receipt circularity | none — DL entry exists but TVL series empty |

Total getLogs: **22,444** vs ~110k estimated (~5x over-estimate; both tokens have long
sparse pre-activity block ranges). Runtime ~50 minutes vs 4–8h expected. Well under the
185k daily cap.

## TVL decisions

- **stETH**: excluded from NV/TVL regression (LST receipt circularity — NV≈TVL by
  construction, Entry 84 rule). λ months retained for the conviction-only analysis.
  No stETH → `lido` mapping created.
- **MEME**: DeFiLlama has a `memecoin` protocol listing with cmcId=28301 and the correct
  contract (0xb131f4A55907B10d1F0A50d8ab8FA09EC342cd74, category Farm, Ethereum), so it
  is *not* a symbol clash — but the TVL series has **zero data points** and empty
  currentChainTvls. No usable protocol TVL → λ-only. (The only other symbol match,
  Conflux MemeDex, is unrelated.)

## Post-assemble totals

| metric | after 035 | after 036 |
|---|---|---|
| λ asset-months / assets | 13,191 / 457 | **13,272 / 459** |
| regression-ready | 177 (coins 21, tokens/other 156) | **177 (unchanged: coins 21, tokens/other 156)** |
| channel2_holding | 421 / 13,580 | **423 / 13,661** |
| coverage (complete/partial/not_started) | 188/311/1,440 | **188/313/1,438** |

Regression-ready unchanged, as expected — both tokens are λ-only adds (TVL
circularity / no TVL data). The next regression-ready count movement requires user
actions: Subscan key → DOT/KSM, CORE key, Cosmos key.

## Next

Session 037 — SHIB (5994), ~128k getLogs estimated (likely a large over-estimate per
this session's pattern), λ-only.
