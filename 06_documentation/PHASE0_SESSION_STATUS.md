# Phase 0 — Session Status Report

**Date:** 2026-06-22
**Session:** 006 (Phase 0 empirical pipeline)
**Model / interface:** Claude Opus 4.8 via Claude Code CLI
**Scope:** Phase 0 only (asset universe), per `04_code/CLAUDE_CODE_KICKOFF_PROMPT.md`
and `04_code/DATA_SPECIFICATION.md` Section 7.
**Status:** ✅ Phase 0 complete. Stopped for review before Phase 1, as instructed.

---

## 1. What was built

All scripts are reproducible and re-runnable; raw API payloads are cached so re-runs
don't re-hit the network.

| File | Purpose |
|------|---------|
| `04_code/fetch_cmc_snapshots.py` | Pulls CMC historical top-1000 listings for each month-end 2015-08→2026-05; caches raw JSON to `03_data/raw/cmc_snapshots/` (130 files). |
| `04_code/build_universe.py` | Applies the Section 2.1 inclusion rule; emits the membership panel + assets table + stablecoin-exclusion list + rank sensitivity. |
| `04_code/classify_assets.py` | Functional coin/token/other classification with evidence, ambiguity flags, and ETH's dated PoW→PoS transition. |
| `04_code/coverage_report.py` | Generates the coverage/feasibility report + by-month/by-year CSVs. |

**Data outputs (`03_data/`):** `universe_panel.csv` / `.parquet` (156,838 asset-months),
`universe_assets.csv` (1,939 qualifying assets), `universe_stablecoins_excluded.csv`
(71), `universe_rank_sensitivity.csv`, `classification_table.csv` (2,010 incl. excluded
stablecoins), `coverage_by_month.csv`, `coverage_by_year.csv`,
`PHASE0_COVERAGE_REPORT.md`.

**Logs:** `04_code/DATA_DECISIONS_LOG.md` (9 entries appended);
`06_documentation/ai_conversations/session_006_2026-06-22_phase0_pipeline.md`;
`06_documentation/time_log.md` updated.

---

## 2. Key feasibility findings (verified live, not assumed)

- **CoinGecko public API caps historical data at the past 365 days** → unusable as the
  historical-ranking backbone on the free tier.
- **CoinMarketCap free historical listings data-api** serves daily, point-in-time ranked
  snapshots back to ~2013, **including delisted coins** → adopted as the Phase 0 backbone
  (this is what makes the universe survivorship-bias-free).
- **DeFiLlama** free API works → used for governance-token classification evidence.
- **Artemis** has no accessible free API (410 / DNS failure) → deferred.

---

## 3. What the coverage report shows

- **Live (observed) cross-section:** ~290 assets/month in 2015 rising to ~540–630 in
  2020+. The observed top-250 count runs ~217–247/month (short of 250 because excluded
  stablecoins occupy real rank slots).
- **Class mix shifts exactly as the theory section anticipated:** observed governance
  **tokens** grow from ~19 (2015) → ~139 (2020) → ~233 (2025); **coins** dominate the
  early sample (196 of 288 observed in 2015).
- **Testability gates:** H1a (coins) has usable density from early in the sample; H1b /
  H2 / H3 (governance/voting-dependent) only become meaningfully testable from ~2020–2021.
  Treat earlier H1b/H2/H3 as out-of-support.
- **Classification:** of 1,939 distinct names, 618 coin / 447 token / 874 other. The
  "other" bucket is large by raw name count (dead microcap tail, oracle/exchange/wrapped
  tokens) but small weighted by *observed asset-months* — the persistent, higher-cap
  assets that drive the tests are predominantly coin/token, and all spot-checked majors
  classify correctly.

---

## 4. Judgment calls made this session (all logged)

1. CoinGecko → CoinMarketCap as the ranking source (human-approved).
2. Stablecoins excluded entirely from the universe, ranking-inclusive (human decision).
3. N=250 default; sensitivity at 200/250/300 reported.
4. Carry-forward (with last-observed price + status flag) for in-panel-but-unobserved
   months; death-return treatment deferred to Phase 3.
5. Tag-rules + DeFiLlama + a curated 22-id native-coin override for classification; every
   non-clean case flagged `ambiguous_flag=True`.
6. ETH treated as a dated PoW→PoS transition (staking from 2020-12-01, Merge 2022-09-15).

---

## 5. Open questions / decisions needed before Phase 1

1. **Carry-forward death returns:** how should assets that fall below rank 1000 be
   treated in return construction (final delisting return vs. constant carry)? (Phase 3,
   but decide the policy before λ/return work.)
2. **'other'/ambiguous classifications:** a manual confirmation pass is needed for any
   `other`/`ambiguous` asset that will actually enter the tests.
3. **Confirm N=250** vs. a tighter screen once λ-channel coverage is known.
4. **Artemis / paid CoinGecko:** obtain access if their fundamentals are wanted for the
   PQ series in Phase 2 (no free Artemis API; CoinGecko Pro key would enable the
   two-source market-cap cross-check the spec asks for).

**No Phase 1 (λ channels) or later work was started, per the kickoff instruction.**
