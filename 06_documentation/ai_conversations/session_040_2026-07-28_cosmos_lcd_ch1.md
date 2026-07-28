# Session 040 — 2026-07-28 — CRO/INJ/KAVA/SEI ch1 via Cosmos Archive LCD

**Model:** Claude Fable 5 (Claude Code desktop)
**Prompt:** `04_code/CLAUDE_CODE_SESSION040_COSMOS_LCD_PROMPT.md`
**Mode:** fully autonomous; one unrelated user interjection (a WRDS/IBES
connection error from a different project, user then said to ignore it).
**Keys:** none — keyless LCD endpoints only.

## Course of the session

1. Pre-flight: sleep=Never confirmed (AC/DC 0x0), Windows Update paused
   through 2026-08-03.
2. Wrote `04_code/session040_cosmos_lcd.py` (Tasks A–D in one script).
3. **Run 1:** prompt's CRO candidates DNS-dead; only KAVA passed via
   cosmos.directory proxy; crashed on wrong panel column name
   (`cmc_supply_circ` → actual `circulating_supply`).
4. Refreshed candidates from chains.cosmos.directory registry (5–8 REST
   endpoints per chain).
5. **Run 2:** CRO found a real archive (rest.mainnet.crypto.org, 11 months
   built); INJ all pruned; KAVA died on HTTP 420 rate limits (not retried);
   SEI's pocket.network "pass" exposed as a **fake archive** (year-old bonded
   identical to live → height header ignored). Run also crashed at final
   `to_csv` — pandas half-uninstalled by an interrupted upgrade elsewhere.
6. Fixes: fake-archive probe guard (old bonded == live bonded → FAIL);
   binary-search guard for months predating the earliest stored block (KAVA's
   chain restarted at height 1 on 2022-05-25 — previously would have
   mis-attributed block-1 state to 2019–2022 months); 420 → retry with 15–45 s
   backoff; no-retry on deterministic `invalid denom`; per-chain search pacing;
   stdlib-csv output. Reinstalled pandas (3.0.5) after finding the `~andas`
   remnant.
7. **Run 3 (clean):** CRO 11 months, KAVA 17 months, 28 rows; CRO drift 1.81%
   PASS; KAVA drift 23.06% WARN.
8. **KAVA retry passes (2):** gentler pacing (1.5 s) recovered all 9
   rate-limited months → KAVA 26 months, CSV 37 rows. Drift diagnostic showed
   bonded 99.1M (Jun 30) → 103.1M (Jul 14) → 127.8M (live): genuine mid-July
   staking surge, WARN accepted.
9. Task E: CRO + KAVA `pos_possible` → `pos`.
10. Task F: assemble + coverage rebuild ran clean under pandas 3.0.5.
11. Entry 91, this log, report, time_log; commit + push at session end.

## Outcome

- λ 13,510 → **13,547** asset-months / 463 → **465** assets
- Regression-ready 178 → **180** (coins 22 → 24: CRO, KAVA; tokens/other 156)
- Coverage 191 complete / 312 partial / 1,436 not_started
- INJ + SEI ch1: **closed as blocked** — no free archive LCD exists; SEI
  additionally hazarded by fake-archive gateways. Reopen only on paid indexer
  decision.

## Gotchas recorded

- Cosmos public "archive" gateways can silently ignore
  `x-cosmos-block-height` — always verify old-state != live-state.
- `invalid denom:` from staking/pool at old heights = SDK codec boundary
  (deterministic; do not retry). CRO decodes from ~2025-06, KAVA from ~2024-Q2.
- api.data.kava.io rate-limits with HTTP **420** (not 429).
- kava_2222-10 height reset (2022-05-25) means pre-2022-05 KAVA months are
  unreachable on the current chain regardless of archive depth.
