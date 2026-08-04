# Claude Code Kickoff Prompt — Phase 3b: Confirmatory sorts, coarse sectors, horse race, heterogeneity

Paste the prompt below as the first message in a new Claude Code session, working directory
`C:\AFA_2027_QTM_Crypto`. Phase 3 core (session 043) is complete; results reviewed with
Moazzam (Entries 95–97). This session runs spec §8: the confirmatory conviction-only
sorts, the coarse sector remap, the horse race, and the pre-specified heterogeneity batch.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 3 core is complete
(session 043; regression_panel.csv, ltw_factors_monthly.csv, portfolio_returns.csv and
tables all built). Before doing anything else, read in full:

1. 04_code/PHASE3_ANALYSIS_SPECIFICATION.md — including §8 (Phase 3b), which is this
   session's spec. Where §8 and earlier sections conflict, §8 wins.
2. 04_code/DATA_DECISIONS_LOG.md Entries 93–97 — especially Entry 96 (MVRV dropped,
   Metcalfe restricted) and Entry 97 (the EXPLORATORY token quintile finding this
   session must treat confirmatorily: sharper sorts monotonically strengthen the token
   conviction signal; quintile EW alpha +1.71%/mo t=2.18, post-2023 +1.48%/mo t=1.79).
3. 03_data/PHASE3_RESULTS_REPORT.md — session 043 results and caveats.

## Standing rules (unchanged)
- NO paid services; NO new Etherscan getLogs (Pro lapsed). Free keyless web fetches
  (BitInfoCharts pattern) are allowed.
- Joins on cmc_id only. Phase 0–3 outputs are read-only; new outputs to
  03_data/phase3/, builders 04_code/phase3b_*.py.
- Log every decision (next entry: 98). Honest-results clause applies: run everything in
  the spec, report everything, tune nothing.

## Task A — Coarse sector remap (spec §8.1) [prerequisite]
Deterministic keyword mapping of raw DeFiLlama category strings to
{DEX, Lending, Yield, Derivatives, Staking/LSD, Other}; output
03_data/phase3/sector_coarse_map.csv; report group sizes per month. Then re-run the
token regression ladder (043 specs s6_1–s6_4) with coarse-sector FE and report
side-by-side with the raw-sector FE versions.

## Task B — Confirmatory conviction-only token sorts (spec §8.2) [the headline task]
Quintile EW primary; decile, tercile, VW secondary; min 3/leg; NW-3 alphas vs LTW
factors; sub-periods; 25/50bps haircuts; turnover. Sector-neutralized quintile (demean
conv within coarse sector-month where group n>=3, else within class-month). Per-sector
tercile long-shorts for the 2–3 largest coarse groups (single sort — this is Moazzam's
by-category power test; no valuation dimension). Coin tercile analog, descriptive.
CRITICAL: spanning regressions of the quintile SMA on LTW factors + identically-built
long-shorts on r_1m (reversal), mom_3m, 52-wk-high, size — the token reversal effect is
strong (FM t ≈ −3.4) and the conviction quintile must be shown distinct from it, or the
result dies here and that is the finding.

## Task C — Horse race (spec §8.3 / §5)
Panel race per track: each comparator signal singly then jointly (raw NVT, raw NV/TVL,
S2F, 52-wk-high, MA cross, momentum family — all derivable from existing panels).
Spanning tests both directions including the quintile portfolio. Metcalfe: ETH + PoW
baselines descriptive appendix only. MVRV: skip (Entry 96).

## Task D — Heterogeneity batch (spec §8.4) [run ALL, report ALL]
(1) Δλ 1m/3m levels+changes regressions and Δλ quintile sort; (2) vote-escrow vs plain
governance classification of the 101 tokens (from protocol documentation; log each with
source) and split regressions; (3) fee-share vs no-fee split; (4) size and turnover
tercile splits; (5) bull/bear (CMKT sign) and pre/post-2023 regime splits; (6)
measurement robustness: raw NV/TVL, g-cap-excluded, B4-excluded, conv_source-excluded,
MRP 20/40 re-derivations.

## Deliverables
03_data/PHASE3B_RESULTS_REPORT.md (every table + one-paragraph reading; negative results
at equal prominence; the paper will disclose Entry 97's exploratory origin — do not
launder it into a pre-registered result). Decisions log entries; session log
(session_044_...); time_log row; commit and push at session end.
```
