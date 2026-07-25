# Session 032 — MYX Report

**Date:** 2026-07-24 (overnight session; build ran ~17:58–20:37 CDT)
**Status:** COMPLETE — MYX built and accepted; **session 029 Task A fully closed** (all 47 targets resolved: 41 built, 5 non-EVM skipped, 1 WARP deferred for identity review).
**Next session:** Entry-79 open items (b)–(g) — DOT/KSM Subscan key, CHZ anchor, CORE key, WARP review, non-TVL breadth ch2, MATIC NVT_GL probe.

---

## Per-token outcome

| symbol | cmc_id | chain | getLogs (vs est) | months built (coded/observed, screened) | screened HODL-6m (median / last) | B2 | B4 | notes |
|--------|--------|-------|------------------|------------------------------------------|----------------------------------|----|----|-------|
| MYX | 36410 | BSC | 67,233 (~250–300k budget, **0.25x**) | 10/10, 10 screened | 3.0% / 5.2% | PASS (max 10.5x vs 100x) | PASS | **tf=22,451,143 — 2nd-largest ch2 build ever** (beats MBOX 21.2M; VVV holds record at 27.8M), largest BSC build. Full observed window (Aug-2025 launch → May-2026). Contract screen 21/40. λ months all TVL-overlapped (myx-finance) → regression-ready immediately. |

## Anomalies

1. **tf > MBOX record:** 22.45M transfers confirms the session-030 mega-giant prediction; second only to VVV (27.79M, session 031).
2. **Call count 2.6x LOWER than the session-030 partial:** 030 logged ~120,440 gl by batch 81; this run reached the same batch with 46,346 gl and near-identical tf (15,459,154 vs 15,438,541 at the 030 kill — the rebuild reproduces the aborted data exactly). Engine unchanged; most plausible explanation is retry churn inflating the 030 counter during rate-limit storms. Treat 030-derived estimates as upper bounds.
3. **Wall-clock 2.7h vs 12–15h budget** — direct consequence of (2). The predicted post-batch-61 silent stretch occurred but lasted ~1h, not multi-hour.
4. **No OS interruption:** sleep=never held. Windows Update could not be paused (non-elevated shell; HKLM keys) — verified no pending reboot and that the July update wave had already installed the same morning; no restart occurred.

## Post-assemble totals

| metric | pre-032 (post-031) | post-032 |
|--------|--------------------|----------|
| λ asset-months | 9,638 | **9,648** |
| λ assets | 341 | **342** (net-new: MYX) |
| regression-ready | 142 | **143** (coins 20 + tokens/other 123) |
| tokens/other λ∩TVL months | 4,243 | **4,253** |
| channel2_holding.csv | 306 tokens / 9,857 rows | **307 tokens / 9,867 rows** |
| coverage | 153 complete / 232 partial / 1,554 not_started | **154 complete / 231 partial / 1,554 not_started** |

## Quota used

67,273 calls (67,233 getLogs + 40 getcode), single process, no API rejection at any point; DAILY_CAP=185k never approached. The dedicated quota day turned out unnecessary at this volume.

## Handoff state (what is committed)

- `03_data/phase1/channel2_holding.csv` — 307 tokens / 9,867 rows.
- `03_data/phase1/lambda_panel.csv` — post-assemble (9,648 / 342).
- `03_data/universe_coverage_status.csv` — regenerated (154/231/1,554).
- `03_data/raw/phase1_onchain/holding/36410_MYX.json` — checkpoint.
- `04_code/DATA_DECISIONS_LOG.md` — Entry 82.
- Build log: `03_data/phase1/_session032_stream.log`.
