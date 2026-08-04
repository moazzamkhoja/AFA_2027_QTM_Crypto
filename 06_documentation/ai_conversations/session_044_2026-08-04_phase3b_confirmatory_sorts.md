# Session 044 — 2026-08-04 — Claude Code (Fable 5): Phase 3b confirmatory sorts, coarse sectors, horse race, heterogeneity, mechanisms

Kickoff: `04_code/CLAUDE_CODE_PHASE3B_KICKOFF_PROMPT.md` (Task E / spec §8.6 added
mid-session by user note; picked up and run). Fully autonomous otherwise. Spec:
`04_code/PHASE3_ANALYSIS_SPECIFICATION.md` §8. Decisions: Entries 100–105 (Entries
98–99 were already written by the Cowork design session). Full readings:
`03_data/PHASE3B_RESULTS_REPORT.md`.

## What happened

1. **Task A — coarse sector remap.** `phase3b_sector_map.py` →
   `03_data/phase3/sector_coarse_map.csv` + `tables/sector_coarse_sizes.csv`.
   Priority-rule keyword map (Entry 100): DEX 41, Other 21, Lending 16, Yield 15,
   Derivatives 6, Staking/LSD 2; median names/group-month DEX 25 / Other 9 / Lending 8.
   `phase3b_regressions_coarse.py` re-ran the token ladder both ways
   (`tables/h1h2_sector_fe_comparison.csv`): raw7 columns reproduce 043 exactly;
   **coarse FE attenuates the conviction slope** (s6_1 t 2.30→1.95; s6_2 1.93→1.49) —
   part of the token premium is between-coarse-sector.
2. **Task B — confirmatory conviction sorts (headline).** `phase3b_sorts.py` →
   `conv_sort_returns.csv`, `tables/convsort_{alphas,stats,spanning}.csv`.
   **q5_ew: alpha +1.71%/mo (t=2.18)**, net-50bps +1.53% (t=1.95), post-2023 +1.48%
   (t=1.79), Sharpe 0.86, ~10.6 names/leg. **Spanning (make-or-break): SURVIVES —
   alpha strengthens to +2.53% (t=3.18) with the reversal LS controlled and +2.34%
   (t=2.60) vs the full four-competitor battery** (conviction leg tilts to recent
   winners; winner-minus-loser itself has alpha −4.68%, t=−3.02). Honest limits at
   equal prominence: decile DIES (t=0.02) — monotone-sharpening narrative does not
   extend; sector-neutral quintile DIES (t=0.39); per-sector terciles all null
   (DEX 0.89 / Other −0.77 / Lending −0.16); coin tercile analog flat (t=0.16).
3. **Task C — horse race.** `phase3b_signals.py` → `horserace_signals.csv` (raw val,
   S2F dual build, 52wk-high, MA cross); `phase3b_horserace.py` →
   `tables/horserace_{panel,spanning}.csv`. **Coin conv×val survives the full joint
   comparator race (−0.0176, t=−2.83)**; token conv attenuates to t=1.10 jointly (only
   reversal survives, t=−2.46) — token conviction is a portfolio-extremes phenomenon,
   not a robust linear panel slope. Spanning both directions: q5 survives every
   single-competitor control; underpowered n=28/31 joint cells reported as such; no
   competitor has positive alpha on LTW+q5. `phase3b_metcalfe.py` → descriptive
   ETH+PoW panel (7 real series; BTC Metcalfe mean-reversion t=−3.69). **New
   BitInfoCharts landmine: unknown tickers redirect HTTP-200 to the default
   btc-ltc-eth chart** — page-title guard added (Entry 101); ZEC = stub.
4. **Task D — heterogeneity (run all, report all).** `phase3b_gov_classification.py`
   → `token_gov_classification.csv` (101 tokens, ve 31/plain 70, fee 66/nofee 35,
   32 low-confidence; dominant-regime rule; Entry 103; EPIC = Ethernity Chain).
   `phase3b_heterogeneity.py` → `tables/heterogeneity.csv`, `het_portfolios.csv`.
   Δλ: nothing (levels or sorts). **ve split REJECTED — wrong direction** (ve t=0.21
   vs plain t=1.21; interaction negative). Fee split: no difference. Size flat;
   turnover gradient tilts WRONG way (hi t=1.41). Regimes: coin interaction is
   post-2023 (−0.0205, t=−4.32) and mildly bull-tilted. Measurement: coin interaction
   robust to MRP 20/40 (t≈−3.5) and stronger ex-conv-fallback (t=−4.67), but raw NVT
   shrinks it (−0.0060, t=−1.90) and ex-g-cap (40% of coin months) kills significance
   (t=−0.97) — growth-levelization is load-bearing (Entry 104).
5. **Task E — mechanisms M1–M4.** In `phase3b_heterogeneity.py` →
   `tables/mechanisms.csv`. **M1 NOT SUPPORTED (conv×turnover positive, wrong sign);
   M2 rejected (no revival under sector-demeaned val, panel or portfolio); M3 rejected
   (token null not a measurement artifact); M4: coin result SURVIVES staking-yield
   controls (conv×val −0.0188, t=−4.39)** — not a seigniorage artifact. Paper §2.3
   loses its M1 leg and must reframe (Entry 105). Staking-yield = supply_g12 /
   logistic(conv), ch1 months.

## Session facts

- No paid calls; 8 free keyless BitInfoCharts fetches (AA pages, cached under
  `03_data/raw/bitinfocharts/activeaddresses_*.html`; bogus btg cache deleted).
- Phase 0–3 outputs untouched; all new outputs in `03_data/phase3/`, builders
  `04_code/phase3b_*.py`.
- Sanity checks passed: raw7 ladder == session 043; q5_ew == Entry 97 exploratory
  numbers exactly (+1.71%/mo, t=2.18).
- Known non-blocking noise: pandas4 concat-sort deprecation warnings in
  phase3b_sorts.py; linearmodels sqrt warnings on some absorbed sector dummies
  (reported coefficients all have finite SEs).

## Next session candidates

- Paper integration: Section 5 sort battery + spanning table; Section 2.3 mechanism
  reframe (M1 reversed); coin-H2 caveat block (raw-NVT attenuation, g-cap subsample).
- Optional: logged-in verification pass on the 32 low-confidence governance
  classifications; per-sector tests once breadth grows.
