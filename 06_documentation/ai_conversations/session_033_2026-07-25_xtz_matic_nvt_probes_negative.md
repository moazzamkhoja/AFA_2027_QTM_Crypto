# Session 033 — XTZ/MATIC NVT_GL probes (both negative); JOE/SAFE closed

**Date:** 2026-07-25
**Model/interface:** Claude Fable 5 via Claude Code (desktop app, Windows)
**Kickoff prompt file:** `04_code/CLAUDE_CODE_SESSION033_XTZ_MATIC_NVT_PROMPT.md`
**Mode:** autonomous (always-allow permissions; standing end-of-session commit+push authorization)
**Commit:** 9d87213

---

## Initial user prompt (verbatim)

> read CLAUDE_CODE_SESSION033_XTZ_MATIC_NVT_PROMPT.md in C:\AFA_2027_QTM_Crypto\04_code and then proceed from there

All subsequent work was autonomous per the kickoff file; no further human input during the session.

## Structured event log

1. **Read kickoff prompt** (Task A: XTZ PQ via TzKT `totalTransferred`; Task B: MATIC
   bitinfocharts probe; Task C: JOE/SAFE/DYDX classification review; Task D: rebuild;
   Entry 83; report; commit+push). Read `phase2b_pq_coins.py`, `phase2_nvt_gl.py`, and the
   existing XTZ/MATIC/DYDX NaN-marker rows in `pq_coins.csv` before writing anything.
2. **Task A premise disproven at first probe.** Live GET of
   `api.tzkt.io/v1/statistics/daily` returned supply/staking fields only — **there is no
   `totalTransferred` field**. Rather than build from a nonexistent series, pivoted to an
   exhaustive free-source sweep for Tezos historical transfer value:
   - TzKT full swagger (287 paths): no historical volume/sum endpoint anywhere; the
     Statistics schema confirmed supply/staking-only.
   - `back.tzkt.io/v1/home` (works only with browser UA+Referer; plain requests 403):
     current-day volume aggregates + 30-day price chart — no history.
   - TzStats `api.tzstats.com`: DEAD (connection refused). TzPro: unreachable.
   - CoinMetrics community API: xtz exposes only TxCnt/TxTfrCnt; TxTfrValUSD → 403
     pro-gated. CM GitHub `csv/xtz.csv`: same community columns, no transfer value.
   - bitinfocharts `sentinusd-xtz`: EMPTY page (no series, not the BTC default).
   - Messari legacy keyless API: 404 (dead). CryptoCompare blockchain histo: 401 key-gated.
   Raw TzKT operation iteration forbidden (Entry 31/32). **Verdict: XTZ stays PQ=NaN**;
   marker refined to `NaN:xtz_no_free_native_series_s033` with the full probe list.
3. **Task B (MATIC):** bitinfocharts `sentinusd-matic` returned 5,852 days starting
   2010/07/17 with last value identical to the BTC reference — **BTC-default guard
   triggered** (Polygon launched 2020). CM community rejects value metrics for `matic`.
   **MATIC stays PQ=NaN**; marker refined to `NaN:polygon_native_volume_no_free_source`.
   Entry-79(g) "candidate 21st regression-ready coin" closed negative.
4. **Task C:** verified against `classification_table.csv`, `lambda_panel.csv`,
   `tvl_panel.csv`: JOE (6 λ mo) and SAFE (10 λ mo) are governance tokens classified
   `coin` via staking tags, with no native chain and 0 TVL rows → **permanently closed
   architectural gaps** (no NVT denominator exists in principle; no re-probe). DYDX
   legitimately a coin but 1 λ month (2024-03) → skip.
5. **Task D:** re-ran `phase2_nvt_gl.py` + `build_coverage_status.py` after the two
   marker-note edits. Output identical to session 032: NVT_GL 2,526 asset-months / 67
   assets; coins regression-ready (λ∩NVT_GL) 20 / 645 months; coverage 154/231/1,554;
   regression-ready total 143. No data changes.
6. **Records:** DATA_DECISIONS_LOG Entry 83 appended (rewritten to reflect the actual
   negative outcome, not the prompt's template); report
   `03_data/SESSION033_XTZ_MATIC_NVT_REPORT.md`; kickoff prompt committed.
7. **Commit + push** 9d87213 to origin/main per standing authorization.

## Deviations from the kickoff prompt

- Task A was **not executed as written** because the specified TzKT field does not exist.
  The prompt's A2–A5 build steps were replaced by the source sweep above and a refined
  NaN marker. The prompt's draft Entry 83 (which assumed a successful XTZ build) was
  rewritten accordingly.
- No API keys used; all probes free/keyless, read-only, and low-volume (~15 HTTP requests).

## Outcome

No new PQ data. Two NaN markers made precise; three gaps (XTZ paid-only, MATIC paid-only,
JOE/SAFE architectural) are now closed with live-verified documentation; DYDX deferred.
Open items for session 034: Entry-79 (b)–(e) — DOT/KSM Subscan key, CHZ manual anchor,
CORE key, WARP identity review, non-TVL breadth ch2.
