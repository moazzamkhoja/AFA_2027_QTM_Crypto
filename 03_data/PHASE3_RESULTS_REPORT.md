# Phase 3 Results Report — H1/H2/H3 Core Tests

Session 043, 2026-08-04. Spec: `04_code/PHASE3_ANALYSIS_SPECIFICATION.md` (pre-registered
ladder; no specification tuning). Builders: `04_code/phase3_panel.py`,
`phase3_factors.py`, `phase3_regressions.py`, `phase3_portfolios.py`.
Decisions: DATA_DECISIONS_LOG Entries 95–96.

**Headline (honest summary):** H1a (coins, 1-month) is NOT supported. H1b (tokens) has
weak-to-moderate support (~+0.6–0.8%/mo per SD of conviction, t ≈ 1.5–2.3). H2 is
STRONGLY supported for coins (interaction t = −3.5; the conviction premium lives
entirely in cheap-valuation coin-months) but NOT for tokens (interaction ≈ 0, wrong
sign). H3 is NOT supported: no Stars-minus-Avoid variant earns significant
factor-adjusted alpha. The voting-weighted-λ refinement of H1b is not supported on its
subsample. These results go into the paper as-is.

---

## 1. Regression panel (Task A) — `03_data/phase3/regression_panel.csv`

Funnel gate PASSED before any regression was run: coins 24 assets / 718 asset-months
(2020-12..2026-05), tokens 101 / 2,771 (2021-01..2026-05) — exact match to paper
Table 1/2, including medians (coin MC $823M vs paper $820M; NVT_GL 0.017; token MC
$98M; NV/TVL_GL 2.29, IQR 0.20–16.10). Coin sample membership operationalized as
`universe_coverage_status.coverage_status == 'complete' & lambda_months > 0` —
this is the definition that reproduces the funnel (includes `pos_possible` coins and
POL; a naive `coin_staking_type == 'pos'` filter yields only 11/396 and is WRONG).

Panel facts that condition everything downstream:

- Forward 1-month returns available for 96.7% of coin and 95.9% of token months
  (delisting tail, no backfill). **Median forward return is negative in both tracks**
  (coins −4.4%/mo, tokens −7.6%/mo): the sample is dominated by the post-2021
  contraction, especially for tokens. Cross-sectional tests are within-month and thus
  immune to the level, but portfolio LONG legs are not.
- Coin conviction: 671/718 months use raw ch1 staking ln-odds; 47 fall back to λ_z
  (`conv_source` flag). Token conviction is λ_z throughout.
- conv_vw (ch3 voting/delegation z-composite) exists for only 756/2,771 token-months
  and 47/718 coin-months — the H1b-second-sentence test runs on a ~27% subsample.
- Coin cross-sections are thin: median 11, max 22 assets per month. Token: median 53.

## 2. LTW monthly factors (Task B) — `03_data/phase3/ltw_factors_monthly.csv`

129 months (2015-09..2026-05), median 511 eligible assets/month (MC ≥ $1M, observed).

| factor | mean/mo | sd | t | corr w/ BTC |
|---|---|---|---|---|
| CMKT | +6.02% | 0.237 | +2.88 | 0.93 |
| CSMB | +1.05% | 0.211 | +0.56 | −0.16 |
| CMOM | −4.60% | 0.328 | −1.57 | −0.12 |

CMKT is BTC-heavy by construction (corr 0.93) — sanity check passed. CSMB has no
unconditional premium. **CMOM is negative at the monthly horizon** — a documented
deviation-consequence of using monthly analogs: LTW's weekly momentum premium does not
survive monthly aggregation in our universe (consistent with short-horizon reversal in
crypto). Factor-model alphas below should be read with this in mind: a "momentum"
control with a negative own-premium.

## 3. H1/H2 regressions (Task C) — `tables/h1h2_coefficients.csv`, `h1h2_fm_tokens.csv`

Dep: r_{t+1} winsorized 1/99 at the monthly cross-section; month FE; SEs two-way
clustered (asset, month). All RHS standardized within class-month.

### Coins (H1a REJECTED at t+1; H2 SUPPORTED)

| spec | conv | t | interaction | t |
|---|---|---|---|---|
| s1 conv only | +0.0055 | +0.69 | | |
| s2 + controls | −0.0019 | −0.25 | | |
| s3 + val | −0.0022 | −0.28 | | |
| s4 + conv×val | −0.0100 | −1.67 | **−0.0169** | **−3.54** |
| s5 below-median val | +0.0070 | +1.15 | | |
| s5 above-median val | −0.0303 | −10.89 | | |
| s5 diff (conv×high) | +0.0098 | +1.38 | **−0.0420** | **−3.99** |

Unconditional conviction does not predict coin returns (s1–s3: t ≤ 0.7). But the
H2 interaction is negative and significant (s4: −0.0169, t = −3.54; split-difference
−0.042, t = −3.99): a 1-SD higher staking ln-odds is worth +0.7%/mo among cheap
(below-median NVT_GL) coins and **−3.0%/mo among expensive coins**. This is exactly
the H2 asymmetry — conviction only predicts where the signal is not already in the
price — but with the unconditional average washed to zero, H1a as stated (positive
unconditional slope) fails at the 1-month horizon. At t+6 (descriptive, overlapping):
conv +0.061 (t = +1.90), interaction −0.090 (t = −2.99) — the pattern strengthens
with horizon and the unconditional slope turns marginally positive. Caveats: only 24
entity clusters (asymptotics strained; the s5_high t = −10.9 should not be quoted —
use the s5_diff test); 47 conv_source fallback months mix λ_z scale into the ln-odds
ranking.

### Tokens (H1b WEAK SUPPORT; H2 REJECTED)

| spec | conv | t | interaction | t |
|---|---|---|---|---|
| s1 conv only | +0.0064 | +1.97 | | |
| s2 + controls | +0.0056 | +1.51 | | |
| s3 + val | +0.0063 | +1.54 | | |
| s4 + conv×val | +0.0061 | +1.47 | +0.0034 | +0.79 |
| s6_1 sector FE | +0.0071 | +2.30 | | |
| s6_2 sector FE + controls | +0.0069 | +1.93 | | |
| s6_3 sector FE + val | +0.0077 | +2.01 | | |
| s6_4 sector FE + int. | +0.0076 | +1.93 | +0.0032 | +0.76 |
| FM s2 (NW-3) | +0.0070 | +1.77 | | |
| FM s4 (NW-3) | +0.0080 | +2.19 | +0.0024 | +0.56 |

Governance conviction carries a positive premium of ~0.6–0.8%/mo per SD, significant
at 5% only in the sector-FE and FM specifications, ~t = 1.5 otherwise. **The H2
interaction is ~zero with the WRONG sign (positive) for tokens** — conviction
predictability is NOT concentrated in cheap NV/TVL_GL token-months (split: b_low =
+0.002 vs b_high = +0.004, difference insignificant). H2 as stated holds for coins
only. Secondary horizons add nothing (t+3 conv t = +1.61; t+6 t = −0.35).

### Voting-weighted λ (H1b second sentence — NOT SUPPORTED)

On the 710-month ch3 subsample: conv_vw alone −0.0030 (t = −0.48); both together:
conv_vw −0.0058 (t = −0.58), conv_lz +0.0048 (t = +0.45); λ_z alone on the same
subsample −0.0002 (t = −0.03). The costlier-action-purer-signal refinement finds no
support — though note the subsample itself shows no λ_z premium either, so this is
a low-power test (documented, not excused).

### Pooled

Track-interacted pooled specs are uninformative (conv t = +0.5; conv×token ≈ 0;
interaction −0.0001) — consistent with the premium being token-specific and modest.

## 4. H3 quadrant portfolio (Task D) — `portfolio_returns.csv`, `tables/h3_alphas.csv`, `h3_stats.csv`

**H3 is NOT supported.** No Stars-minus-Avoid variant has significant NW-3 alpha
against the CMKT/CSMB/CMOM model:

| portfolio | months | alpha/mo | t | Sharpe (ann.) |
|---|---|---|---|---|
| SMA coin EW | 20 | −0.0338 | −1.54 | −0.47 |
| SMA coin VW | 20 | +0.0535 | +1.39 | +0.75 |
| SMA token EW | 49 | +0.0119 | +0.84 | +0.36 |
| SMA token VW | 49 | +0.0276 | +1.13 | +0.52 |
| SMA pooled EW | 49 | +0.0097 | +0.67 | +0.33 |
| SMA pooled VW | 49 | +0.0432 | +1.48 | +0.66 |
| EW universe benchmark | 129 | | | +0.61 |

- **Breadth guard binds hard for coins**: 45 of 65 coin class-months fail the ≥4-per-leg
  guard (median cross-section is 11 coins → ~2–3 per quadrant), leaving 20
  non-contiguous months (2023-05..2026-04). The coin H3 test is effectively
  underpowered by design; the EW point estimate is negative, the VW positive — sign
  instability consistent with noise.
- Token/pooled SMA point estimates are positive but insignificant, and the full-sample
  estimate is carried by pre-2023 months: token EW alpha post-2023 is −0.79%/mo
  (t = −0.73). Sub-period stability fails.
- Only the VW variants' Sharpe (0.66–0.75) exceeds the EW-universe benchmark (0.61);
  the EW-primary variants (0.33–0.36) do not.
- Costs barely matter (turnover ~0.10–0.28 one-way per leg-month; 50 bps shaves
  ~9 bps/mo off SMA EW): the problem is the gross alpha, not implementation.
- Single-dimension comparators are equally dead (conviction-only EW: coin t = +0.63,
  token t = +0.36; valuation-only: coin t = −1.76 — wrong sign for a "value" premium —
  token t = +0.29). The quadrant construction adds nothing over either dimension
  alone, because neither dimension alone works as a sort at this breadth.

Reconciliation with Task C: the regression H2 result (coins) survives within-month
with continuous conviction; the median-split quadrant discards most of that variation
and the coin breadth guard discards most of the months. A cross-sectional signal of
~0.7%/mo per SD in half the sample is simply too small to surface as portfolio alpha
in 20–49 months of data with 4–15 names per leg.

## 5. Probes (Task E) — full detail in Entry 96

- **E1 BitInfoCharts active addresses:** feasible end-to-end for ETH (4,003 daily obs
  2015-08..2026-08, parsed and month-averaged with the existing sentinusd pattern) —
  but ETH is the ONLY coin of the 24-coin sample with a real series; TRX/ADA/SOL
  return stub pages with no data. Metcalfe comparator is therefore restricted to
  ETH + PoW baselines (BTC/LTC/DOGE/…) and cannot enter the cross-sectional horse
  race. Scale if pursued for baselines: ~10 pages, one fetch each, minutes.
- **E2 ch2 realized-cap probe: NO for the coin track.** The 24 regression coins have
  ZERO ch2 checkpoints (ch2 covered EVM tokens; coin conviction is ch1 staking).
  Within tokens, 210 of 426 checkpoints (events-schema) retain full raw transfer
  lists — last-move attribution IS replayable locally with zero API calls — but only
  12 of the 101 sample tokens are events-schema (80 are streamed aggregates,
  unrecoverable; 9 have no checkpoint). MVRV drops from the horse race; a 12-token
  MVRV panel is retained as a possibility but is too thin as a comparator.

## 6. What goes to the paper (Section 5 skeleton)

1. Table: H1 ladder per track (s1–s4 + sector FE + FM) — conviction premium exists
   for tokens (weak), not coins.
2. Table: H2 split + interaction — the paper's central conditional claim survives for
   coins with the strongest statistics of the session, and fails for tokens; the
   Section 2.4 asymmetric-conditioning story holds in exactly one track.
3. Table: H3 portfolios incl. sub-periods, cost haircuts, single-dimension
   comparators — reported as a null result with the breadth-guard power caveat.
4. Factor construction note: monthly CMOM premium is negative (deviation from weekly
   LTW documented).
5. Honest-results clause satisfied: no re-specification was performed after seeing
   results; the ladder above is exactly the pre-registered spec.
