# Session 040 Report — CRO/INJ/KAVA/SEI ch1 via Cosmos Archive LCD

**Date:** 2026-07-28
**Prompt:** `04_code/CLAUDE_CODE_SESSION040_COSMOS_LCD_PROMPT.md`
**Keys:** none (free, keyless LCD endpoints)
**Decisions Log:** Entry 91

## Headline

- **CRO ch1 BUILT:** 11 months (2025-07-31 .. 2026-05-31), staking ratio 0.309–0.370
- **KAVA ch1 BUILT:** 26 months (2024-04-30 .. 2026-05-31), staking ratio 0.091–0.127
- **INJ: NO ARCHIVE NODE** — all 7 registry LCDs pruned
- **SEI: NO ARCHIVE NODE** — all 8 registry LCDs pruned; two gateways detected as *fake archives*
- **λ 13,510 → 13,547 asset-months / 463 → 465 assets**
- **Regression-ready 178 → 180** (coins 22 → 24; tokens/other 156 unchanged)
- Coverage: 191 complete / 312 partial / 1,436 not_started

## Archive probe table

| Chain | Endpoint | Liveness | Archive (365d state) |
|-------|----------|----------|----------------------|
| CRO | rest.crypto.org (prompt) | DNS dead | — |
| CRO | api-cryptoorgchain-ia.cosmosia.notional.ventures (prompt) | DNS dead | — |
| CRO | **rest.mainnet.crypto.org** | LIVE | **PASS** |
| INJ | injective-api.highstakes.ch | LIVE | FAIL (no commit info) |
| INJ | rest.lavenderfive.com/injective | LIVE | FAIL (no commit info) |
| INJ | injective-rest.publicnode.com | LIVE | FAIL (IAVL version mismatch) |
| INJ | public.stakewolle.com/cosmos/injective/rest | LIVE | FAIL (IAVL version mismatch) |
| INJ | injective.rpc.uquad.org | LIVE | FAIL (IAVL version mismatch) |
| INJ | sentry.lcd.injective.network | LIVE | FAIL (no commit info) |
| INJ | rest.cosmos.directory/injective | LIVE | FAIL (no commit info) |
| KAVA | **api.data.kava.io** | LIVE | **PASS** (heavy 420 rate limits) |
| SEI | rest.lavenderfive.com/sei | LIVE | FAIL (pruned) |
| SEI | api-sei.stingray.plus | LIVE | FAIL (pruned) |
| SEI | lcd-sei.whispernode.com | DNS dead | — |
| SEI | sei.api.kjnodes.com | DNS dead (2nd run) | — |
| SEI | sei-rest.publicnode.com | LIVE | FAIL (pruned) |
| SEI | sei.api.pocket.network | LIVE | **FAKE ARCHIVE** (height header ignored) |
| SEI | rest.sei-apis.com | LIVE | FAIL (pruned) |
| SEI | rest.cosmos.directory/sei | LIVE | **FAKE ARCHIVE** (height header ignored) |

**Fake-archive detection (new probe guard):** a gateway that returns bonded
tokens at a year-old height *identical digit-for-digit to the live value* is
ignoring the `x-cosmos-block-height` header. Without this guard SEI would have
produced a flat series of today's value stamped onto 34 historical months.

## Months built

| Chain | Months | Range | Ratio range | Why not more |
|-------|--------|-------|-------------|--------------|
| CRO | 11 | 2025-07 .. 2026-05 | 0.309–0.370 | state before ~2025-06 fails `invalid denom` (codec boundary); blocks exist to genesis |
| KAVA | 26 | 2024-04 .. 2026-05 | 0.091–0.127 | chain restarted at height 1 on 2022-05-25 (no earlier blocks); state before ~2024-Q2 fails `invalid denom` |

KAVA needed three passes: the archive node rate-limits at HTTP 420; final
pacing 1.5 s/call with 15–45 s backoff recovered all 9 rate-limited months.

## Cross-check (Entry-26 standard)

| Chain | Built latest (2026-05-31) | Live (2026-07-28) | Drift | Verdict |
|-------|--------------------------|-------------------|-------|---------|
| CRO | 14,147,571,306 | 14,407,865,160 | 1.81% | PASS |
| KAVA | 98,300,526 | 127,765,970 | 23.06% | WARN — investigated, genuine |

KAVA drift investigation: bonded 99.1M at 2026-06-30 → 103.1M at ~2026-07-14 →
127.8M live. A real ~25M-KAVA staking surge occurred in mid-July 2026, after
our last panel month. Denom/decimals confirmed correct (ukava / 10^6).

## Coverage label changes

- CRO (3635): coin_staking_type `pos_possible` → `pos`
- KAVA (4846): coin_staking_type `pos_possible` → `pos`
- INJ (7226): already `pos` (unchanged, stays partial — no ch1 possible free)
- SEI (23149): stays `pos_possible` (nothing built)

## Post-assemble totals

- λ panel: 13,547 asset-months / 465 assets (+37 / +2)
- CRO: coverage `partial` → `complete` (11 λ months, λ∩NVT overlap)
- KAVA: coverage `partial` → `complete` (26 λ months, λ∩NVT overlap)
- Regression-ready: **180** (coins 24, tokens/other 156)

## Failures / gaps

- **INJ ch1:** blocked — no free archive LCD. Reopen only on a paid indexer
  decision or if a public archive endpoint emerges.
- **SEI ch1:** blocked — same, plus the fake-archive gateway hazard documented.
- KAVA 2022-05..2024-03 and CRO 2021-03..2025-06: state permanently
  undecodable on the available archive nodes (SDK codec boundaries).

## Environment incident

User-site pandas was broken mid-session (interrupted pip upgrade left a
`~andas` remnant; first `to_csv` lazy-import crashed, then `import pandas`
failed outright). Reinstalled pandas 3.0.5; `phase1_assemble_lambda.py` and
`build_coverage_status.py` ran unmodified under pandas 3. The session builder
writes its CSV via stdlib `csv` as defense.

## Artifacts

- `03_data/phase1/channel1_cosmos_lcd.csv` — 37 rows
- `03_data/phase1/session040_probe_results.json` — probe audit trail
- `03_data/phase1/session040_run.log`, `session040_kava_retry.log` — build logs (force-added past `.gitignore *.log`)
- `04_code/session040_cosmos_lcd.py`, `04_code/session040_kava_retry.py` — builders
