# Session 025 — Etherscan Pro BUILD: P2-2 + Channel-2 at panel scale

**Date:** 2026-06-30 → 2026-07-01 · **Agent:** Claude Code / Opus 4.8 · **Kickoff:** `CLAUDE_CODE_SESSION025_PRO_BUILD_PROMPT.md`
**Decisions Log:** Entries 61–64 · **Report:** `03_data/SESSION025_PRO_BUILD_REPORT.md`

## Mandate
The payoff of the Etherscan API Pro purchase ($199/mo, 200k calls/day, all chains): (A) run the
16 BSC/Base/Optimism/Linea paid-gated Channel-1/3 candidates (P2-2), and (B) build Channel 2
(holding duration / coin-age) — the Entry-24 "single highest-value addition", NaN since
inception — at panel scale. Baseline: 2,699 asset-months / 90 assets (session 024).

## Result
**λ 2,699 → 6,097 observed asset-months; 90 → 288 distinct assets (+3,398 / +198).**
Channel 2 is no longer the λ NaN column (Entry 24 closed for the ≤3,000-holder cross-section).

## What happened
- **Pro verified before any build:** getLogs returns real data on BSC/Base/Optimism/Linea/Avax
  (free tier refused these). Entry 61.
- **Task A — P2-2 (Entry 62):** mechanism-verified each token on-chain first. **5 BUILT**
  (AWE 15.25% delegation — material; CHEEL/FORM/LINEA/ZORA ~0% low-activation), ALT excluded
  (degenerate), **OP deferred** (verified firing, history too large for a correct full replay),
  8 DORMANT (event never fired), TNC rejected (bare `Locked(address)`, fails Entry-26).
  `ch3_delegation` 560→627 asset-months / 21→26 assets.
- **Task B — Channel 2 (Entries 63–64):**
  - **Denominator FIX:** prototype divided by CMC circulating → shares >100% (RAD 148–398%);
    corrected to on-chain supply → bounded [0,1]. Re-validated on RAD (screened 11–27%).
  - **All-month contract screen** (eth_getCode time-invariant → one pass cleans the series).
  - **Metadata sizing (per Moazzam's steer):** replaced fetch-until-cap hit-and-trial with a
    `tokenholdercount` pre-pass (1 call/token; all 793 sized). Build runs smallest-first,
    defers the tail by metadata, caches month-blocks per chain.
  - **Built 207 tokens / 3,413 asset-months** (median screened HODL 40.6%, 2/197 degenerate).
    The ~586 tokens > 3,000 holders are the resumable worklist.
- **Data-integrity incident:** an overnight network outage made the engine swallow DNS failures
  into empty getLogs results → silently dropped block ranges = corrupted coin-age. Fixed with a
  robust getLogs (RAISES on network failure, aborts+retries the token), non-caching of failed
  block lookups, and a circuit-breaker. Deleted + cleanly re-fetched all 65 suspect checkpoints
  (0 network failures on the re-run). Lesson: a swallowed network error corrupts silently — worse
  than a crash.

## Depth (the kickoff's headline metric), honestly
2-channel asset-months 354 → 435 (+81), but the 2-channel SHARE fell 13.1% → 7.1% because
breadth tripled with single-channel ch2. Channel 2 widened the panel (small/mid tokens) but
added a 2nd channel to only 4 already-in-λ assets — the large in-λ governance/staking tokens are
> 3,000 holders and were deferred. Lifting depth (toward 3-channel assets) is exactly what the
deferred tail run delivers next.

## Method compliance
Mechanism-verified-before-build (Entry 55); no partial/degenerate series shipped; Entry-26 bar
applied to TNC (rejected); denominator fix makes the HODL share interpretable; cmc_id joins only;
logs-not-eth_call; assembler z-score/equal-weight logic untouched (only a channel input added);
Pro key only, no other paid tier. Decisions Log 61–64 (append-only).

## Artifacts
`phase1_channel2_panel.py`, `phase1_channel2_sizeprobe.py`, `phase1_channel2_validate.py`,
`phase1_p2p2_probe.py`; `03_data/phase1/channel2_holding.csv` (207 tokens), `_channel2_sizes.csv`;
`channel3_onchain_delegation.csv` (+P2-2); `lambda_panel.csv` (re-assembled).

## Next session (resumable)
1. Channel-2 tail: ~586 tokens > 3,000 holders (esp. large in-λ governance/staking → creates
   3-channel assets). 2. OP delegation (block-windowed). 3. Checkpoints store raw events →
   `--aggregate --recompute` re-derives with no re-fetch.
