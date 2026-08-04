# Claude Code Kickoff Prompt — Phase 3: Empirical Tests (H1, H2, H3 core)

Paste the prompt below as the first message in a new Claude Code session, working directory
`C:\AFA_2027_QTM_Crypto`. Phase 3 turns the completed data panels into the paper's empirical
results. This session covers the **core tests** (regression panel, LTW factors, H1/H2
regressions, H3 portfolio). The horse race (Test 3) is Phase 3b — this session only runs its
two data probes at the end if quota/time allows.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phases 0–2 are complete: lambda panel
(467 assets), NVT_GL panel (coins), NV/TVL_GL panel (tokens) are built and committed. This
session runs the core empirical tests. Before doing anything else, read in full:

1. 04_code/PHASE3_ANALYSIS_SPECIFICATION.md — the complete spec for this session. Follow it;
   where it is silent, decide conservatively and log the decision.
2. 04_code/DATA_DECISIONS_LOG.md Entries 92–94 — current state, Etherscan lapse, NV/TVL_GL
   adoption, Phase 3 design decisions.
3. 05_paper/main.tex Sections 2–4 — the hypotheses (H1a, H1b, H2, H3) exactly as stated, and
   the sample definitions the results must match (24 coins/718 mo; 101 tokens/2,771 mo).

## Standing rules
- NO paid services. Etherscan Pro lapsed 2026-07-30 — no new getLogs calls at all. Stored
  data under 03_data/raw/ may be read freely.
- All joins on cmc_id, never symbol.
- Do not modify any Phase 0–2 output file. New outputs go to 03_data/phase3/ and builders to
  04_code/phase3_*.py.
- Returns come from universe_panel observed rows only (never carry_forward rows).
- Log every methodological decision in DATA_DECISIONS_LOG.md (next entry: 95).

## Task A — Regression panel (spec §1–2)
Build 03_data/phase3/regression_panel.csv: one row per asset-month in the coin (24/718) and
token (101/2,771) samples with forward returns r_{t+1} (and cumulative t+3, t+6), conviction
(coins: ln-odds of raw_ch1_staking with lambda_z fallback + conv_source flag; tokens:
lambda_z), valuation (ln NVT_GL / ln NV_TVL_GL, winsorized 1/99), controls (ln MC, r_1m,
mom_3m, mom_12_2, beta36), sector, class-month standardized versions. Verify row counts
reproduce the paper's Table 1 funnel numbers exactly before proceeding; if they do not,
STOP and reconcile first — do not run regressions on a panel that disagrees with the paper.

## Task B — Monthly LTW factors (spec §4.1)
Build 03_data/phase3/ltw_factors_monthly.csv (CMKT, CSMB, CMOM as monthly analogs of
Liu–Tsyvinski–Wu 2022 JF, constructed from our 1,939-asset universe; MC ≥ $1M filter,
winsorized constituent returns). Report factor summary stats and correlation with BTC.

## Task C — H1/H2 regressions (spec §3)
Run the specification ladder per track (pooled OLS, month FE, two-way clustered SEs;
tokens add sector FE and the voting-weighted-lambda column; FM secondary for tokens only).
Output coefficient tables to 03_data/phase3/tables/ as CSV. Key cells: sign/significance of
conviction (H1a, H1b) and of the conviction × valuation interaction (H2, expected negative),
plus the below/above-median-valuation split.

## Task D — H3 portfolio (spec §4.2–4.3)
Median-split quadrants within class-month (≥4 assets per leg guard), Stars-minus-Avoid EW
and VW, monthly rebalanced. Time-series alpha vs the Task-B factors (Newey-West 3 lags),
Sharpe vs EW benchmark, sub-periods pre/post 2023-01, turnover and 25/50 bps cost haircuts,
and the conviction-only / valuation-only single-dimension comparators.

## Task E (only if time/quota remain) — Phase 3b probes (spec §5.3)
E1: BitInfoCharts active-addresses scrape feasibility for the 24 sample coins (one test
coin end-to-end, then stop and report scale estimate). E2: ch2 checkpoint realized-cap
probe — determine from 03_data/raw/phase1_onchain/ checkpoint schema whether last-move
attribution is recoverable without new API calls; answer YES/NO with evidence, build
nothing yet. Log both as Entry 95 (or 95–96).

## Deliverables and record-keeping (house style)
- 03_data/PHASE3_RESULTS_REPORT.md — every table with a one-paragraph reading; report
  negative and anomalous results with the same prominence as positive ones. Do NOT tune
  specifications to produce significance; the spec's ladder is the pre-registration.
- DATA_DECISIONS_LOG.md entries; session log in 06_documentation/ai_conversations/
  (session_043_...); time_log.md row.
- Commit and push at session end (delete permission for the folder is enabled; git works
  normally; commit_and_push.bat exists if needed).

## Honest-results clause
The paper's hypotheses are falsifiable and the results section will report whatever comes
out. If conviction does not predict returns, or the interaction has the wrong sign, that is
a finding — document it cleanly, do not iterate on variable definitions until something
works. Any deviation from the spec must be logged with its rationale BEFORE results are
produced, not after.
```
