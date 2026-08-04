# Session 043 — 2026-08-04 — Claude Code (Fable 5): Phase 3 core empirical tests

Kickoff: `04_code/CLAUDE_CODE_PHASE3_KICKOFF_PROMPT.md`. Fully autonomous.
Spec followed: `04_code/PHASE3_ANALYSIS_SPECIFICATION.md` (pre-registered ladder,
no tuning after results). Decisions: Entries 95–96. Full readings:
`03_data/PHASE3_RESULTS_REPORT.md`.

## What happened

1. **Task A — regression panel.** `phase3_panel.py` → `03_data/phase3/regression_panel.csv`
   (3,489 rows). Funnel gate verified EXACTLY before proceeding: coins 24/718
   (2020-12..2026-05, median MC $823M, NVT_GL 0.017), tokens 101/2,771
   (2021-01..2026-05, median MC $98M, NV/TVL_GL 2.29 IQR 0.20–16.10). Key
   reconciliation: coin membership = coverage_status=='complete' & lambda_months>0
   (a naive coin_staking_type=='pos' filter gives 11/396 — wrong). Coin conviction:
   671 ch1 ln-odds months + 47 λ_z fallback. Assert() guards the funnel in the builder.
2. **Task B — factors.** `phase3_factors.py` → `ltw_factors_monthly.csv` (129 months).
   CMKT +6.0%/mo (t=2.9), corr 0.93 w/ BTC (sanity pass); CSMB +1.1% (t=0.6);
   CMOM **−4.6%/mo (t=−1.6)** — monthly analog of LTW momentum is negative
   (short-horizon reversal), documented deviation.
3. **Task C — H1/H2.** `phase3_regressions.py` → `tables/h1h2_coefficients.csv`,
   `h1h2_fm_tokens.csv`. **H1a REJECTED at t+1** (coin conv t ≤ 0.7 unconditional).
   **H2 SUPPORTED for coins**: conv×val −0.0169 (t=−3.54); split-diff −0.042
   (t=−3.99); conviction is +0.7%/SD in cheap coin-months, −3.0%/SD in expensive.
   **H1b weak support**: tokens +0.6–0.8%/mo per SD, t=1.5–2.3 (best with sector FE;
   FM NW-3 t=1.77/2.19). **H2 REJECTED for tokens** (interaction +0.003, wrong sign).
   **Voting-weighted λ NOT better than passive** (710-mo ch3 subsample, all |t|<0.6;
   low power — λ_z itself is ~0 there). Caveat recorded: 24 coin clusters; quote the
   interacted diff test, not the s5_high t=−10.9.
4. **Task D — H3 portfolio.** `phase3_portfolios.py` → `portfolio_returns.csv`,
   `tables/h3_alphas.csv`, `h3_stats.csv`. **H3 REJECTED**: no SMA variant has
   significant NW-3 alpha vs CMKT/CSMB/CMOM (best pooled VW +4.3%/mo, t=1.48; coin
   EW −3.4%/mo, t=−1.5). Breadth guard (≥4/leg) kills 45/65 coin class-months → 20
   non-contiguous months. Token EW alpha post-2023 is negative. Only VW Sharpe
   (0.66–0.75) beats EW-universe (0.61); EW primary (0.33–0.36) does not. Costs
   immaterial (turnover 0.10–0.28/leg-month). Single-dimension comparators also dead.
5. **Task E — probes (Entries 95–96).** E1: BitInfoCharts activeaddresses ETH
   end-to-end OK (4,003 daily obs 2015-08..2026-08; HTML cached to raw/bitinfocharts);
   TRX/ADA/SOL = HTTP-200 STUB pages, zero data — only ETH of the 24 sample coins
   covered → Metcalfe cannot enter the cross-sectional horse race. E2: realized-cap
   **NO for coin track** — the 24 coins have zero ch2 checkpoints (ch2 = EVM tokens);
   211/426 token checkpoints (events-schema) retain full raw transfers and ARE
   replayable locally, but only 12/101 sample tokens qualify (80 streamed = aggregates
   only) → MVRV dropped from horse race.

## Environment
statsmodels 0.14.6 + linearmodels 7.0 installed (were absent). No paid services used;
zero Etherscan calls; 6 BitInfoCharts fetches (free, keyless).

## Open items → Phase 3b / paper
- Write paper Section 5 from PHASE3_RESULTS_REPORT.md (H2-coins is the headline
  positive result; H1a/H2-tokens/H3 reported as nulls per honest-results clause).
- Horse race (Phase 3b): comparators reduce to raw NVT / raw NV/TVL, S2F, 52-wk high,
  MA cross, momentum family (Metcalfe ETH-only baseline; MVRV dropped).
- Robustness queue (spec sec. 7): λ_z vs ln-odds, raw vs GL ratios, MRP 20/40%,
  B4-flag drop, tercile splits, ex-top-3 MC, g-cap sensitivity (Entry 93 caveat).
- Consider (paper discussion, not respecification): H3 breadth guard redesign for the
  thin coin cross-section would be a DEVIATION requiring pre-logging.
