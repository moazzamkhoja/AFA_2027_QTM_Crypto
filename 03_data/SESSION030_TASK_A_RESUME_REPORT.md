# Session 030 — Task-A Resume Report (TRANSITION REPORT)

**Date:** 2026-07-05
**Status:** CUT SHORT at user departure (4:30 PM CST). 1 of 7 tokens built; 1 aborted mid-build; 5 untouched.
**Next session:** Monday 2026-07-13 — start from `04_code/CLAUDE_CODE_SESSION031_TASK_A_RESUME_PROMPT.md`.

---

## Per-token outcome

| symbol | cmc_id | chain | getLogs | months built | screened HODL-6m (median / last) | B2 | B4 | notes |
|--------|--------|-------|---------|--------------|----------------------------------|----|----|-------|
| SFUND | 8972 | BSC | 28,553 | 23/23 (2023-12..2025-10) | 20.6% / 18.6% | PASS (max 1.94x vs 100x) | PASS [12.3%, 24.9%], no nulls | Hidden giant: tf=3,415,005 vs ~4k-call estimate (7x). Screen 20/45. All 23 months TVL-overlap → regression-ready. |
| MYX | 36410 | BSC | ~120,440 (LOST) | 0 — ABORTED | — | — | — | MEGA-giant. Killed at batch 81/128 with tf=15,438,541 (on pace to pass MBOX's 21.2M record). ~10h to finish at kill time. No partial checkpoint (streamed engine, by design) → full restart next session. |
| ADF | 24796 | Polygon | 0 | not started | — | — | — | est 1,871 calls |
| AVNT | 38299 | Base | 0 | not started | — | — | — | est ~4k calls |
| KAITO | 35763 | Base | 0 | not started | — | — | — | est ~3k calls |
| VVV | 35509 | Base | 0 | not started | — | — | — | est ~1k calls |
| RAIN | 38341 | Arbitrum | 0 | not started | — | — | — | est 13,637 calls |

## Anomalies

1. **BSC estimates undershoot 7–30x.** SFUND est ~4k → actual 28,553. MYX est ~4k → 120k+ *unfinished*. The holder-count-based `est_getlogs_calls` is a lower bound on BSC (fast blocks + airdrop-farming volume). **Session 031 rule: build small chains first (Polygon/Base/Arbitrum), BSC last, and budget MYX a dedicated quota day (~250–300k calls).**
2. **MYX launch-region split storm:** batches 62–66 (BSC blocks ~49–53M, the Aug-2025 launch) ran ~2.5h with zero log output — the engine prints only every 5 batches and was binary-splitting dense windows the whole time. Not a hang; verified live via established Etherscan connections + CPU accrual. Expect the same silence pattern on the rebuild.
3. **Why MYX was killed rather than left running:** ~10h remained at the 4:30 PM departure; an unattended week-long run risks a sleep/reboot kill mid-token (same total loss) plus a week of unpushed state. Quota is daily-resetting and evidently non-binding (Entry 76), so the redo costs time only.

## Post-assemble totals

| metric | pre-030 | post-030 |
|--------|---------|----------|
| λ asset-months | 9,580 | **9,603** |
| λ assets | 337 | **338** |
| regression-ready | 138 | **139** (coins 20 + tokens/other 119) |
| tokens/other λ∩TVL months | 4,194 | **4,217** |
| channel2_holding.csv | 300 tokens | **301 tokens / 9,817 rows** |
| coverage | 149 complete | **150 complete / 235 partial / 1,554 not_started** |

## Quota used

~149k getLogs in one process (SFUND 28,553 + MYX ~120,440 aborted + startup probes). No API rejection at any point.

## Handoff state (what is committed)

- `03_data/phase1/channel2_holding.csv` — includes SFUND (aggregate re-run manually after kill).
- `03_data/phase1/lambda_panel.csv` — post-assemble (9,603 / 338).
- `03_data/universe_coverage_status.csv` — regenerated.
- `03_data/raw/phase1_onchain/holding/8972_SFUND.json` — SFUND checkpoint.
- `04_code/DATA_DECISIONS_LOG.md` — Entry 80.
- `04_code/CLAUDE_CODE_SESSION031_TASK_A_RESUME_PROMPT.md` — next-session pickup prompt.
- NO MYX artifacts exist (no checkpoint, no rows) — clean restart.
