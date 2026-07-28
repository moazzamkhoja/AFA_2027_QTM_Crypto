# Session 039 — DOT/KSM PQ probe; TRX staking-type fix; WARP identity review

**Date:** 2026-07-28
**Model/interface:** Claude Fable 5 via Claude Code (desktop app, Windows)
**Kickoff:** user pointed to `CLAUDE_CODE_SESSION039_DOTKSM_PQ_FIXES_PROMPT.md` ("proceed")
**Mode:** autonomous after launch; standing end-of-session commit+push authorization
**Commit:** (recorded post-push; see git log — session 039 commit)

---

## Initial user prompt (verbatim)

> read CLAUDE_CODE_SESSION039_DOTKSM_PQ_FIXES_PROMPT.md in C:\AFA_2027_QTM_Crypto\04_code and then proceed

No mid-session check-ins or decisions requested.

## Structured event log

1. **Pre-flight:** repo clean (only the kickoff prompt untracked); WU pause
   from session 036/038 still in effect (until ~2026-08-02); no long build
   this session so no powercfg changes needed.
2. **Task A1 — Subscan `/api/scan/daily`:** `format=month` rejected (HTTP 400,
   only day/hour/6hour exist). `format=day` over any multi-year window → HTTP
   403 `history_window_exceeded` for ALL categories (transfer/extrinsic/
   transaction/fee) on both polkadot and kusama endpoints. Window bisection:
   30-day range returns data; 90-day fails → free window ≈ 2 months (same wall
   as session 037's "Bonded" probe). The in-window payload is also degenerate
   (2026-06-01: total=3 transfers / 5.98 DOT — not network-wide volume).
3. **Task A3 skipped by rule:** raw multi-year block iteration forbidden
   (Entry 31/32); not attempted.
4. **Task A4 — Blockchair keyless:** `/polkadot/stats` + `/kusama/stats` = 200
   but **both indexes FROZEN** (best blocks 2025-05-26 / 2025-05-09);
   aggregation endpoint `/{chain}/calls?a=date(time),sum(value)&q=type(transfer)`
   = **404** on both (same no-aggregation-tables pattern as XTZ/MATIC,
   Entry 84). Stopped at 4 keyless calls (blacklist threshold). **Task A
   verdict: no free PQ source; DOT/KSM stay PARTIAL (gap = pq_nvtgl only);
   Blockchair ruled out permanently for DOT/KSM (stale index — paid key would
   not help); reopen only on Subscan Pro decision.**
5. **Task B — TRX (1958) label fix:** grep located `coin_staking_type` as a
   carry-forward column in `universe_coverage_status.csv` itself
   (build_coverage_status.py:33 reads the old file; static metadata from
   session 022). Edited the row `pow_only` → `pos`, re-ran the builder.
   Verified: TRX λ∩NVT same-month overlap = 58 months → stays `complete` via
   the proper pos path; regression-ready coins derive cleanly to **22 with TRX
   included** (33 complete coins − 11 pow_only-NVT-only); Entry-88's ±1
   bookkeeping discrepancy resolved; headline 178 unchanged.
6. **Task C — WARP (1166) identity review:** checkpoint (raw/phase1_onchain/
   holding/1166_WARP.json) shows 27,257 getLogs / **0 transfers** for
   `0x83e6...5Aa`. Cached CMC detail (raw/cmc_detail/1166.json) is decisive:
   id 1166 = warpcoin.com, **category "coin"**, added 2016-02-03, **inactive**
   since 2018-05-08, own chain explorer — never an ERC-20. dl_slug
   `polkastarter` traced to DeFiLlama's registry carrying wrong cmcId 1166
   (Polkastarter = POLS, 7208). **Closed as permanent identity mismatch:**
   (a) `BAD_DL_CMCID = {"1166"}` override added to
   `phase1_build_identity_map.py`; (b) identity CSV row cleared; (c) 54 bogus
   polkastarter TVL months purged from tvl_panel (8,120→8,066 mo,
   163→162 assets); (d) coverage → `not_started`. No λ impact (0 λ rows).
7. **Assemble + verify:** λ **13,510 / 463 unchanged** (PYTHONUTF8=1);
   coverage 189/314/1,436; regression-ready **178 (coins 22, tokens/other
   156)** re-derived from the coverage file.
8. **Record-keeping:** Entry 90 appended; SESSION039_DOTKSM_PQ_FIXES_REPORT.md
   written; this log + time_log entry; commit+push at session end.

## Files touched

- `04_code/s039_probe_subscan.py`, `s039_probe_subscan2.py`,
  `s039_probe_blockchair.py` (new probe scripts)
- `04_code/phase1_build_identity_map.py` (BAD_DL_CMCID override)
- `03_data/phase1/asset_onchain_identity.csv` (1166 row cleared)
- `03_data/phase2/tvl_panel.csv` (54 WARP rows purged)
- `03_data/universe_coverage_status.csv` (TRX pos; rebuilt twice)
- `04_code/DATA_DECISIONS_LOG.md` (Entry 90)
- `03_data/SESSION039_DOTKSM_PQ_FIXES_REPORT.md` (new)
