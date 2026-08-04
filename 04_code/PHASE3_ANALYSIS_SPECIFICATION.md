# Phase 3 Analysis Specification — Empirical Tests of H1, H2, H3

Status: DRAFT approved for build (Cowork session 2026-08-04).
Companion kickoff prompt: `CLAUDE_CODE_PHASE3_KICKOFF_PROMPT.md`.
Decisions: DATA_DECISIONS_LOG Entries 93–94.

---

## 0. Scope and standing constraints

- **No paid tier / no purchase.** Etherscan Pro lapsed 2026-07-30 (Entry 92). Any build
  requiring new Etherscan getLogs is out of scope; stored raw data and checkpoints under
  `03_data/raw/` may be used freely.
- All joins on `cmc_id`, never on `symbol`.
- Engine guards unchanged (VAL_CAP_MULT = CONTAM_MULT = 100; self-transfer skip stays).
- Every derived panel gets a builder script in `04_code/` and lands in `03_data/phase3/`.
- Nothing in this phase modifies Phase 0–2 outputs.

## 1. Samples and returns

| Sample | Assets | Asset-months | Window | Source of truth |
|---|---|---|---|---|
| Coin regression | 24 | 718 | 2020-12..2026-05 | λ (phase1/lambda_panel) × NVT_GL (phase2/nvt_gl_panel), PoS coins |
| Token regression | 101 | 2,771 | 2021-01..2026-05 | λ × NV/TVL_GL (phase2/nv_tvl_gl_panel), tokens |
| Combined | 125 | 3,489 | 2020-12..2026-05 | union of the two |
| Factor universe | 1,939 | 156,838 | 2015-08..2026-05 | universe_panel, status='observed' |

- **Forward return**: r_{j,t+1} = simple return from month-end t to month-end t+1 from
  universe_panel prices (observed rows only; no carry-forward rows ever enter returns).
- Returns winsorized at monthly cross-sectional 1%/99% for regressions (portfolios use
  raw returns; note both).
- Secondary horizons: cumulative t+1..t+3 and t+1..t+6 (overlapping; SEs must account —
  cluster by month; treat as descriptive).
- Delisting: an asset that disappears from observed rows contributes its last available
  return; no backfill.

## 2. Variable definitions

### 2.1 Conviction (x-axis)
- **Coins**: SoV/MoE ratio from the raw staking share where ch1 is available:
  `sov_moe = ln(λ_ch1 / (1 − λ_ch1))` (log-odds; λ_ch1 = raw_ch1_staking clipped to
  [0.001, 0.999]). Where ch1 is missing in a coin-month but λ_z exists (holding-channel
  months), fall back to λ_z and flag `conv_source`. Robustness: λ_z for all coin-months.
- **Tokens**: `conv = λ_z` (the composite index; SoV/MoE undefined — paper Section 2.2).
- Both standardized to zero mean / unit SD **within class-month** before entering
  regressions (`conv_std`).

### 2.2 Valuation (y-axis)
- **Coins**: `val = ln(NVT_GL)`; **Tokens**: `val = ln(NV_TVL_GL)`.
- Standardized within class-month (`val_std`). Winsorize ln-ratios at 1%/99% first
  (extreme tails exist: NV/TVL_GL p90 ≈ 265).

### 2.3 Controls
- `size = ln(market_cap)`.
- Momentum: `r_1m` (short-term reversal candidate), `mom_3m` (t−3..t−1), `mom_12_2`
  (t−12..t−2, skip most recent month).
- `beta36`: trailing 36-month beta vs BTC (reuse the column already in the phase2 panels).
- Token regressions add sector fixed effects from classification_table `sector`.

## 3. Test 1 — H1/H2 predictive regressions

Primary estimator: pooled OLS with month FE; SEs two-way clustered (asset, month).
Coin track and token track run separately; pooled version adds track FE and interacts
conviction with track as a robustness column.

Specification ladder (each track):

1. r_{t+1} = a + b·conv_std + month FE
2. \+ size, mom_3m, mom_12_2, r_1m, beta36
3. \+ val_std
4. \+ conv_std × val_std                          ← H2: coefficient < 0
5. Split-sample: spec 2 run separately for below/above median val (within class-month)
   ← H2: b_low > b_high, difference test via interacted pooled spec
6. Tokens only: + sector FE (repeat 1–5)
7. Tokens only: voting-weighted λ (ch3 sub-channels) alongside passive λ_z ← H1b second
   sentence

- H1a/H1b: b > 0 in specs 1–3.
- Fama-MacBeth as secondary for tokens only (coin cross-sections of 11–20 are too thin);
  report mean coefficient with Newey-West (3 lags) t-stats.
- Report standardized coefficients (all RHS standardized) so one unit = one SD.

## 4. Test 2 — H3 quadrant portfolio vs the LTW factor model

### 4.1 Factor construction (monthly analogs of Liu–Tsyvinski–Wu 2022 JF)
LTW factors are weekly in the original; we build **monthly analogs** from our own
universe (documented deviation — our panel is monthly, and self-built factors cover
through 2026-05):

- Eligible universe per month: observed rows with price > 0, MC ≥ $1M.
- `CMKT` = value-weighted return of eligible universe minus 1-month T-bill (use monthly
  rf = 4%/12 constant, consistent with the r_e build; robustness: FRED TB4WK if trivially
  fetchable — do not build a fetcher for it).
- `CSMB` = VW return of bottom size quintile − top size quintile (quintiles formed on
  prior month-end MC).
- `CMOM` = VW return of top prior-mom_3m quintile − bottom quintile (formed monthly).
- Sanity: correlations with BTC return; CMKT ≈ BTC-heavy by construction; report factor
  summary stats in output. Winsorize constituent monthly returns at (−90%, +300%) as in
  the beta build before aggregating (penny-token blowup guard).
- Output: `03_data/phase3/ltw_factors_monthly.csv`.

### 4.2 Portfolio construction
- Each month t, within each class (coin / token) with non-missing conv and val:
  median split on conv and on val → Stars (high conv, low val), Avoid (low conv, high
  val).
- Hold t+1; rebalance monthly. EW primary, VW secondary.
- `SMA` (Stars minus Avoid) per class and pooled (pooled = union of class-level
  memberships, not re-sorted).
- Minimum breadth guard: a class-month enters only if ≥ 4 assets on each leg; log
  excluded months.

### 4.3 Evaluation
- Time-series regression: SMA_t = α + β·CMKT + s·CSMB + m·CMOM + ε, Newey-West (3 lags).
  H3: α > 0, significant.
- Sharpe ratios: SMA vs EW-universe benchmark; annualized from monthly.
- Sub-periods: pre/post 2023-01 (natural break: post-FTX regime).
- Turnover per leg; net-of-cost alpha at 25 and 50 bps per side.
- Single-dimension comparators: conviction-only long-short and valuation-only long-short
  (H3's "incremental over either dimension alone").

## 5. Test 3 — Horse race

### 5.1 Comparator signals
Coins (all free, existing or specified builds):

| Signal | Definition | Data status |
|---|---|---|
| Raw NVT | MC / PQ0_annual | have (nvt_gl_panel) |
| Metcalfe ratio | ln(MC) − 2·ln(active_addresses), monthly avg AA | **build: BitInfoCharts scrape** |
| MVRV | MC / realized cap (each supply unit at price of last on-chain move) | **probe: ch2 checkpoints, EVM only, no new API calls** |
| Stock-to-flow | circulating_supply / trailing-12m Δsupply | build from universe_panel |
| 52-wk high | price / trailing-12m max price | build from universe_panel |
| MA cross | 1[MA3 > MA10] (monthly MAs) | build from universe_panel |
| Momentum / reversal | mom_3m, mom_12_2, r_1m | §2.3 |

Tokens: raw NV/TVL (have), momentum family, 52-wk high, MA cross. (Fee-multiple
comparators are paid-data — excluded, note in paper.)

### 5.2 Designs
- (a) **Panel horse race**: r_{t+1} on each standardized signal singly (month FE,
  two-way clustered), then all jointly per track. Does conv_std / the interaction survive?
- (b) **Spanning tests**: SMA regressed on LTW factors + competitor long-short portfolios
  (median-split portfolios built identically per signal); and each competitor portfolio
  regressed on LTW + SMA. Report both directions.
- (c) **Sub-period stability** as the OOS proxy: signals are sorts (no estimation), so
  report (a) and (b) for 2024-01..2026-05 alone, sorts formed on information through t.

### 5.3 New data builds
1. **Active addresses** (coins in the 24-coin sample + BTC/major PoW for baselines):
   BitInfoCharts historical daily active-addresses charts, monthly average, same scrape
   pattern as the sent-in-USD build. Output `03_data/phase3/active_addresses.csv`
   (cmc_id, month_end, aa_avg, source).
2. **Realized cap probe** (EVM assets): determine whether ch2 checkpoints
   (`03_data/raw/phase1_onchain/`) retain per-unit last-move attribution sufficient to
   price supply at last-move-month price. If yes → `03_data/phase3/realized_cap.csv` and
   MVRV joins the race; if no → document infeasibility (no new getLogs; Etherscan lapsed)
   and drop MVRV. Decide and log either way (Entry 95).
3. **S2F, 52-wk high, MA cross, momentum**: pure derivations from universe_panel.

## 6. Outputs

- `03_data/phase3/` panels: regression panel (one row per asset-month with all variables),
  ltw_factors_monthly.csv, portfolio_returns.csv, horse-race signal panel.
- `04_code/phase3_*.py` builders: `phase3_panel.py`, `phase3_factors.py`,
  `phase3_portfolios.py`, `phase3_horserace.py` (+ scrapers/probes).
- Results tables as CSV in `03_data/phase3/tables/` (tex conversion happens at
  paper-writing time, not in this phase).
- `03_data/PHASE3_RESULTS_REPORT.md`: every table with a one-paragraph reading, plus all
  negative/anomalous findings.

## 7. Robustness checklist (run if time permits, else queue for 3b)

- λ_z (index) vs ln-odds SoV/MoE for coins.
- Raw NVT / raw NV/TVL replacing GL versions (does growth-levelization matter — this
  doubles as a horse-race cell).
- MRP 20%/40% re-derivation of NVT_GL and NV/TVL_GL from emitted beta (no rebuild needed).
- Drop B4-flagged (HODL-6m > 80%) asset-months.
- Tercile instead of median splits for H3.
- Exclude top-3 MC assets per class (mega-cap dominance).

---

## 8. Phase 3b — confirmatory sorts, coarse sectors, horse race, heterogeneity

Added Cowork 2026-08-04 after review of session-043 results (Entries 95–97).
Kickoff: `CLAUDE_CODE_PHASE3B_KICKOFF_PROMPT.md`.

### 8.1 Coarse sector remap (prerequisite for everything sector-related)
Map the raw DeFiLlama compound category strings (median 1 token/sector-month — unusable)
to coarse groups by deterministic keyword rules, priority-ordered:
`DEX` (Dexs, DEX Aggregator), `Lending` (Lending, CDP), `Yield` (Yield, Yield
Aggregator, Farm), `Derivatives` (Derivatives, Options, Perps), `Staking/LSD` (Liquid
Staking, Staking), `Other` (all else). One group per token (modal/priority rule for
compound strings); output `03_data/phase3/sector_coarse_map.csv` (cmc_id, sector_raw,
sector_coarse) and log the rule. Re-run token regression ladder with coarse-sector FE
(replaces raw-sector FE columns).

### 8.2 Confirmatory conviction-only token sorts (upgraded from Entry 97 exploratory)
Pre-specified here; the paper will disclose the exploratory origin (Entry 97).
- Primary: conviction quintile long-short (top − bottom), EW, monthly, min 3/leg.
- Secondary: decile (min 3/leg — expect ~5/leg, flag thin months), VW variants,
  tercile (for continuity with 043).
- Sector-neutralized primary: demean conv within coarse sector-month (groups with ≥3
  names; else demean within class-month), then quintile-sort the full token
  cross-section.
- By-category power check: per-coarse-sector tercile long-shorts for the two or three
  largest groups (single sort only — no valuation dimension; that is what restores
  breadth within sector).
- Evaluation identical to §4.3: NW-3 alpha vs monthly LTW factors, Sharpe, sub-periods
  (pre/post-2023), 25/50 bps haircuts, turnover.
- Spanning (critical given the strong token reversal): regress the quintile SMA on LTW
  factors PLUS long-shorts built identically on r_1m (reversal), mom_3m, 52-wk-high,
  and size. The claim "conviction is a distinct signal" lives or dies here.
- Coins: quintiles infeasible (11–20/month); run tercile min-3 EW as the coin analog,
  descriptive only.

### 8.3 Horse race (§5 as specified, amended)
- MVRV: DROPPED as cross-sectional comparator (Entry 96: 12 recoverable tokens);
  optional 12-token descriptive appendix only.
- Metcalfe: ETH + PoW baselines descriptive panel only (Entry 95: BitInfoCharts has no
  AA for TRX/ADA/SOL); not in the cross-sectional race.
- Panel race and spanning tests otherwise as §5.2; add the conviction quintile
  portfolio (8.2) to the spanning set.

### 8.4 Pre-specified heterogeneity batch (run all, report all — no selective reporting)
1. Δλ: 1m and 3m changes in conviction as regressors (levels + changes jointly) and as
   a token quintile sort.
2. Vote-escrow vs plain governance: classify each of the 101 tokens by lock mechanism
   (ve/locked-staking vs non-lock voting) from protocol documentation; H: premium
   concentrated in lock-type tokens. Log per-token classification with source.
3. Fee-share (b_t > 0) vs no-fee tokens: same classification pass; H: cleaner signal
   where b_t = 0.
4. Size terciles and turnover (volume_24h/MC) terciles: limits-to-arbitrage prediction —
   premium larger in small/low-turnover tokens.
5. Regime: bull vs bear months (sign of CMKT), and pre/post-2023, for the token
   conviction slope and the coin interaction.
6. Measurement robustness: raw NV/TVL in place of NV/TVL_GL; exclude g-cap-binding
   months; exclude B4-flagged months; exclude the 47 coin conv_source-fallback months;
   MRP 20%/40% re-derivations.

### 8.5 Outputs
`03_data/phase3/tables/` extended; `03_data/PHASE3B_RESULTS_REPORT.md` in the same
honest-results format; Entry 98+ for every decision; builders `04_code/phase3b_*.py`.
