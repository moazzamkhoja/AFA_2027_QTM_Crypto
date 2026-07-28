# Session 038 — SHIB ch2 (EVM DeFi Breadth Batch 3b)

**Date:** 2026-07-27
**Model/interface:** Claude Fable 5 via Claude Code (desktop app, Windows)
**Kickoff:** user pointed to `CLAUDE_CODE_SESSION038_SHIB_PROMPT.md` ("proceed")
**Mode:** autonomous after launch; standing end-of-session commit+push authorization
**Commit:** 263655a

---

## Initial user prompt (verbatim)

> read CLAUDE_CODE_SESSION038_SHIB_PROMPT.md in C:\AFA_2027_QTM_Crypto\04_code and proceed

No mid-session check-ins or decisions requested.

## Structured event log

1. **Pre-flight:** sleep/hibernate/monitor set to Never via powercfg; Windows
   Update paused via registry until 2026-08-03 (elevated shell OK).
2. **Task A — SHIB (5994/Ethereum) ch2 built:** `WORKLIST=5994` on the
   unchanged stream engine (VAL_CAP_MULT = CONTAM_MULT = 100, self-transfer
   skip intact). 53,683 getLogs actual vs 128k estimate = **0.42x** (the
   sessions 034–036 holder-count-overestimate pattern holds; first ~11M blocks
   produced ~88 getLogs). 17,845,462 transfers; 61 screened months
   (2021-05..2026-05); contract screen 13/81 candidates; ~2.1h wall at 8
   workers. **B2 pass** (zero months excluded by the 100× contamination
   guard). **B4 pass** (screened HODL-6m median 78.1% ≤ 80%; last 82.5%).
3. **Task B — TVL decision (verified, not just documented):** tvl_panel checked
   — the only shiba-related slug `shibaswap` is already assigned to BONE
   (cmc 11865, 59 months); SHIB has zero tvl_panel rows. SHIB excluded from
   NV/TVL regression — meme token, no direct protocol TVL; assigning
   `shibaswap` would double-count the DEX TVL against the wrong token.
   **SHIB → λ-only.** No slug written.
4. **Task C — assemble + coverage:** λ 13,449→**13,510** asset-months /
   462→**463** assets; channel2_holding.csv 423→424 tokens / 13,661→13,722
   rows; coverage 189 complete / 315 partial / 1,435 not_started (SHIB
   not_started→partial); **regression-ready 178 unchanged** (coins 22,
   tokens/other 156 — recomputed from same-month λ∩NVT / λ∩TVL overlap to
   confirm).
5. **Entry 89**, `03_data/SESSION038_SHIB_REPORT.md`, build log force-added
   (`.gitignore *.log` gotcha), committed + pushed (263655a).

## Data-access notes

- Etherscan Pro key (`.api_keys.json` "etherscan"), 8 workers @ 8/s; 53,683
  getLogs — well under the 185k daily cap and the 150k stop threshold.
- Engine gotcha (recurring): `phase1_assemble_lambda.py` final print crashes on
  the cp1252 console (λ char) without `PYTHONUTF8=1`; CSV written correctly
  either way — rerun with the env var for the full summary.

## Status after session

EVM DeFi breadth COMPLETE (batches 1, 2, 3a, 3b all done). Next (039): DOT/KSM
PQ source probe; TRX coin_staking_type fix (pow_only→DPoS); WARP identity
review.
