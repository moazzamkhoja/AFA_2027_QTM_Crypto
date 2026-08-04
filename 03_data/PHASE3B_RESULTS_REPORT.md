# Phase 3b Results Report — Confirmatory Sorts, Coarse Sectors, Horse Race, Heterogeneity, Mechanisms

Session 044, 2026-08-04. Spec: `04_code/PHASE3_ANALYSIS_SPECIFICATION.md` §8 (Tasks A–E);
kickoff `CLAUDE_CODE_PHASE3B_KICKOFF_PROMPT.md`. Builders: `04_code/phase3b_*.py`.
Decisions: DATA_DECISIONS_LOG Entries 100–105. Everything specified was run; everything
run is reported here; nothing was tuned after seeing results.

**DISCLOSURE (Entry 97):** the conviction-quintile result in §2 was first found in an
EXPLORATORY, user-directed pass after the session-043 results were known. This session
pre-specified the full battery (spec §8.2, fixed before any 3b estimate was produced)
and ran it once. The paper must describe the quintile finding as exploratory-then-
confirmed-in-battery, not as pre-registered.

**Headline (honest summary):**
1. The token conviction quintile long-short earns **+1.71%/mo (t = 2.18)** LTW-adjusted,
   survives costs (+1.53%/mo net of 50 bps, t = 1.95), survives post-2023 (+1.48%/mo,
   t = 1.79), and — the make-or-break test — its alpha **strengthens to +2.53%/mo
   (t = 3.18)** when the token reversal long-short is added, and stays +2.34%/mo
   (t = 2.60) against the full four-competitor battery. It is NOT a repackaged reversal.
2. But the signal is **fragile in two informative directions**: the decile sort DIES
   (t = 0.02 — the Entry-97 "monotone sharpening" story does NOT extend), and the
   sector-neutralized quintile DIES (t = 0.39) — the premium lives BETWEEN coarse
   sectors, not within them. Per-sector sorts are all insignificant.
3. Horse race: no comparator kills the coin H2 interaction (**conv×val = −0.0176,
   t = −2.83** with all eight comparators in the regression). The token conviction
   slope, in contrast, attenuates to +0.32%/mo (t = 1.10) in the joint panel — in
   multivariate terms the token cross-sectional slope is NOT robust; only the
   portfolio-extremes result is.
4. Heterogeneity: the vote-escrow prediction is REJECTED (ve-token premium is
   *smaller*, not larger); fee-share makes no difference; Δλ adds nothing.
5. Mechanisms: M1 (attention) NOT supported — conv×turnover has the WRONG sign
   (premium is larger in HIGH-turnover tokens). M2 (denominator endogeneity) rejected
   — the token interaction does not revive under sector-demeaned valuation. M3:
   the token interaction stays ≈0 under raw NV/TVL and g-cap exclusion (not a
   measurement artifact). M4: the coin interaction SURVIVES staking-yield controls
   (t = −4.39) — the coin H2 result is not a seigniorage artifact.
6. Measurement caveats on the coin H2 result, reported at equal prominence: it is
   robust to MRP 20/40 (t ≈ −3.5) and stronger excluding conv-fallback months
   (t = −4.67), but attenuates with RAW NVT (−0.0060, t = −1.90) and loses
   significance (same magnitude, −0.0163, t = −0.97) when the 40% of coin months
   with capped g are dropped. Growth-levelization is load-bearing for the coin result.

---

## 1. Task A — Coarse sector remap (`sector_coarse_map.csv`, `tables/sector_coarse_sizes.csv`, `tables/h1h2_sector_fe_comparison.csv`)

Deterministic priority-rule map (Entry 100): first matching group in the order
DEX > Lending > Yield > Derivatives > Staking/LSD wins; tag-level case-insensitive
keyword match; no match → Other. Token counts: DEX 41, Other 21, Lending 16, Yield 15,
Derivatives 6, Staking/LSD 2. Median tokens per group-month: DEX 25, Other 9,
Lending 8, Yield 7, Derivatives 3, Staking/LSD 1. Share of months with ≥3 names:
DEX 89%, Other 79%, Yield 71%, Lending 69%, Derivatives 62%, Staking/LSD 0%.

Token ladder with coarse-sector FE, side-by-side with the 043 raw-7-group FE
(raw7 columns reproduce session 043 exactly — machinery check passed):

| spec | raw7 conv (t) | coarse conv (t) | raw7 int. (t) | coarse int. (t) |
|---|---|---|---|---|
| s6_1 conv only | +0.0071 (+2.30) | +0.0063 (+1.95) | | |
| s6_2 + controls | +0.0069 (+1.93) | +0.0054 (+1.49) | | |
| s6_3 + val | +0.0077 (+2.01) | +0.0062 (+1.60) | | |
| s6_4 + conv×val | +0.0076 (+1.93) | +0.0060 (+1.52) | +0.0032 (+0.76) | +0.0035 (+0.78) |

**Reading.** Coarse-sector FE *attenuates* the token conviction slope (t drops from
1.9–2.3 to 1.5–2.0). Combined with the sector-neutral sort result (§2), the pattern is
consistent: part of the token conviction premium is a BETWEEN-coarse-sector effect
(high-conviction sectors outperform), which sector FE absorb. The interaction stays
dead under both FE sets. The paper's sector-FE column should use the coarse map (the
raw 7-group FE was built on the first tag only and carries many singletons), with the
attenuation reported.

## 2. Task B — Confirmatory conviction-only token sorts (`conv_sort_returns.csv`, `tables/convsort_*.csv`)

All sorts: formation on information through t, hold t+1, raw forward returns, NW-3
alphas vs monthly LTW (CMKT/CSMB/CMOM). Pre-2023 rows unavailable for token sorts
(only 10 pre-2023 formation months survive; sub-period minimum is 12).

| portfolio | mean/mo | alpha | t | Sharpe | n | post-23 alpha (t) |
|---|---|---|---|---|---|---|
| **q5_ew (PRIMARY)** | +2.28% | **+1.71%** | **+2.18** | 0.86 | 50 | +1.48% (+1.79) |
| q5_ew net 25 bps | | +1.62% | +2.06 | | 50 | |
| q5_ew net 50 bps | | +1.53% | +1.95 | | 50 | |
| q5_vw | +3.69% | +3.11% | +1.83 | 0.92 | 50 | +2.17% (+1.38) |
| d10_ew | +0.75% | +0.03% | +0.02 | 0.14 | 46 | +1.16% (+0.71) |
| t3_ew (043 continuity) | +0.80% | +0.36% | +0.37 | 0.21 | 50 | −0.68% (−0.88) |
| t3_vw | +2.23% | +1.88% | +0.99 | 0.47 | 50 | −0.26% (−0.12) |
| q5_ew sector-neutral | +0.88% | +0.40% | +0.39 | 0.24 | 50 | −0.75% (−0.89) |
| t3_ew DEX | +0.98% | +0.94% | +0.89 | 0.22 | 51 | −0.74% (−0.72) |
| t3_ew Other | −3.46% | −3.43% | −0.77 | −0.61 | 36 | (= full) |
| t3_ew Lending | +0.77% | −0.35% | −0.16 | 0.12 | 34 | (= full) |
| coin t3_ew (descriptive) | +1.11% | +0.24% | +0.16 | 0.24 | 40 | (= full) |

Leg breadth: quintile ~10.6/leg (1 month at the min-3 guard); decile ~5.8/leg.
Turnover (one-way, per leg-month): q5_ew 0.19/0.16 → the 50 bps haircut costs
~18 bps/mo. VW turnover is ~2× EW.

**Spanning — the make-or-break test** (`tables/convsort_spanning.csv`). q5_ew regressed
on LTW + identically-built quintile long-shorts on r_1m (reversal), mom_3m, 52-wk-high,
size:

| spec | alpha | t | key loadings |
|---|---|---|---|
| LTW only | +1.71% | +2.18 | csmb −0.32 (t −3.0) |
| + reversal LS | **+2.53%** | **+3.18** | rev_ls +0.18 (t +2.2) |
| + mom3 LS | +1.53% | +1.85 | |
| + high52 LS | +2.03% | +2.70 | |
| + size LS | +1.70% | +2.15 | |
| + all four | +2.34% | +2.60 | rev +0.31, mom3 +0.30, high52 −0.21 |

**Reading.** The conviction quintile is DISTINCT from reversal — emphatically so. The
top-conviction leg tilts toward recent winners (positive rev_ls loading), and since the
winner-minus-loser portfolio itself loses money (alpha −4.68%/mo, t = −3.02 — the
strong token reversal of the FM regressions, visible in portfolio space), controlling
for that exposure RAISES conviction's alpha. The result survives every single-competitor
control and the joint battery. Two honest qualifications. (i) The decile sort dying
(t = 0.02 at ~5.8 names/leg) breaks the Entry-97 "sharper sorts monotonically
strengthen" narrative: median t=0.38 → tercile t=0.37 → quintile t=2.18 → decile
t=0.02. The quintile is where breadth (~10/leg) and signal purity happen to balance;
the paper must show the whole progression, not just the quintile. (ii) The
sector-neutral quintile dying (t = 0.39, post-2023 negative) plus the coarse-FE
attenuation (§1) says the premium is substantially BETWEEN coarse sectors. Per-sector
terciles (DEX t = 0.89, Other t = −0.77, Lending t = −0.16) show no within-sector
power either — Moazzam's by-category test fails at current breadth. The coin tercile
analog is flat (t = 0.16), as expected from 043.

## 3. Task C — Horse race (`tables/horserace_panel.csv`, `tables/horserace_spanning.csv`, `tables/metcalfe_summary.csv`)

### 3.1 Panel race, singles (dep r_fwd1_w, month FE, two-way clustered; own coefficient)

| signal | coin full (t) | coin 2024+ (t) | token full (t) | token 2024+ (t) |
|---|---|---|---|---|
| conv | +0.0055 (+0.69) | +0.0090 (+1.22) | +0.0064 (+1.97) | +0.0064 (+1.88) |
| raw val (NVT / NV-TVL) | +0.0080 (+0.94) | +0.0162 (+1.68) | −0.0061 (−1.53) | −0.0051 (−1.05) |
| S2F (ln, flow>0) | +0.0023 (+0.28) | +0.0090 (+1.86) | +0.0045 (+1.03) | +0.0012 (+0.28) |
| supply growth 12m | −0.0075 (−0.94) | −0.0143 (−2.79) | +0.0005 (+0.14) | +0.0008 (+0.14) |
| 52-wk high | +0.0156 (+1.52) | +0.0236 (+2.06) | −0.0134 (−2.04) | −0.0047 (−0.67) |
| MA cross | +0.0023 (+0.20) | +0.0093 (+0.82) | −0.0094 (−1.85) | −0.0066 (−1.13) |
| r_1m | +0.0019 (+0.21) | −0.0026 (−0.25) | **−0.0142 (−2.39)** | **−0.0195 (−2.62)** |
| mom_3m | +0.0081 (+1.00) | +0.0082 (+0.87) | −0.0019 (−0.38) | −0.0017 (−0.28) |
| mom_12_2 | +0.0093 (+0.87) | +0.0190 (+2.10) | −0.0021 (−0.46) | +0.0069 (+1.47) |

### 3.2 Panel race, joint (all signals + conv)

Coins, full sample: nothing individually significant; conv +0.0061 (t = 0.67). Adding
val_std and conv×val to the joint spec: **conv×val = −0.0176 (t = −2.83)** — the coin
H2 interaction survives the entire comparator battery. (Sub-2024: −0.0104, t = −1.92,
with 52-wk-high the strongest coin signal at +0.0439, t = +3.12.)

Tokens, full sample: conv attenuates to +0.0032 (t = 1.10); the only signal that
survives jointly is reversal (r_1m −0.0166, t = −2.46; sub-2024 −0.0267, t = −3.95).

**Reading.** In the panel, the coin story is the interaction and it wins its race
outright. The token story does NOT win a multivariate panel race — the linear λ_z slope
is partially spanned by the technical signals (and by sector effects, §1), and what
remains concentrated in the sort extremes (§2) is invisible to a linear panel
coefficient. Report both facts; they are not contradictory, but they bound the claim:
*token conviction is a portfolio-extremes phenomenon, not a uniform cross-sectional
slope*. Scarcity signals: S2F is nothing anywhere; supply growth is a significant
NEGATIVE (i.e., scarcity-positive) coin signal post-2024 only.

### 3.3 Spanning, token track (both directions)

Direction 1 (q5_ew on LTW + one competitor portfolio at a time): alpha ranges
+1.53%–+2.53%/mo (t = 1.85–3.18) across rev/mom3/mom12/high52/size/rawval/S2F. It
drops to +1.09% (t = 1.16) with the MA-cross long-short and +0.99% (t = 0.99) with all
seven — but those two cells have n = 31 and n = 28 months (the MA-cross portfolio
requires 10-month MAs plus min-3 binary legs), so they are underpowered comparisons,
not refutations; reported for completeness. Direction 2 (each competitor on LTW +
q5_ew): no competitor earns positive alpha on q5_ew (reversal −5.5%, t = −3.5;
MA-cross −3.3%, t = −2.9 — both are NEGATIVE-alpha strategies in this sample).

### 3.4 Metcalfe (descriptive appendix; Entry 96 restriction)

BitInfoCharts active addresses: 7 real series (BTC/ETH/LTC/DOGE/BCH/DASH/ETC). ZEC is
a stub page (0 data rows); "btg" silently redirects to the default btc-ltc-eth chart —
caught by a page-title guard (new landmine variant logged in Entry 101). Own-asset
regressions of r_{t+1} on z(ln MC − 2 ln AA), NW-3, full-sample z (descriptive only,
look-ahead acknowledged): BTC −0.050 (t = −3.69) — the classic overvaluation
mean-reversion; DOGE −0.095 (t = −1.61); ETH +0.096 (t = +1.34); others |t| < 1.5.
Metcalfe stays out of the cross-sectional race (ETH-only coverage in-sample).

## 4. Task D — Heterogeneity batch (`tables/heterogeneity.csv`, `tables/het_portfolios.csv`)

All cells below: token track unless noted; s2 = conv + controls, month FE, two-way
clustered. RUN ALL / REPORT ALL — no cell was dropped.

**(1) Δλ.** Levels + changes jointly: token Δ1m +0.0033 (t = 0.88), Δ3m +0.0060
(t = 1.31); coin Δ1m −0.0043 (t = −0.62), Δ3m −0.0122 (t = −1.20). Quintile sorts on
Δλ: Δ1m alpha +1.33%/mo (t = 1.11), Δ3m +0.53% (t = 0.34). **Conviction changes carry
no information beyond levels** in either direction.

**(2) Vote-escrow vs plain (101 tokens classified, `token_gov_classification.csv`).**
ve (31 tokens): conv slope +0.0016 (t = 0.21). Plain (70): +0.0047 (t = 1.21).
Pooled interaction conv×ve: −0.0023 (t = −0.27); excluding the 32 low-confidence
classifications: −0.0120 (t = −0.94). **The lock-mechanism hypothesis is REJECTED —
point estimates go the WRONG way** (premium, such as it is, sits in plain-governance
tokens). Classification rules and per-token sources: Entry 103.

**(3) Fee-share vs no-fee.** fee (66): +0.0052 (t = 0.94); nofee (35): +0.0056
(t = 0.87); interaction −0.0005 (t = −0.05); hi-conf −0.0072 (t = −0.50). **No
difference.** The "cleaner signal where b_t = 0" prediction finds no support, but note
the test is between-token (classification), not within-token (b_t variation), so it is
weak evidence against the model's comparative static — it rules out a large static
difference only.

**(4) Size / turnover terciles.** Size: lo +0.0022 (t = 0.37), mid +0.0019 (t = 0.32),
hi +0.0043 (t = 0.51) — flat. Turnover: lo +0.0028 (t = 0.36), mid +0.0042 (t = 0.55),
hi +0.0074 (t = 1.41). **The limits-to-arbitrage prediction (premium in small /
low-turnover names) is NOT supported; if anything the gradient tilts the other way.**

**(5) Regimes.** Token conv slope: bull +0.0052 (t = 1.44) vs bear +0.0057 (t = 0.96)
— symmetric; pre-2023 +0.0292 (t = 1.13, 334 obs) vs post +0.0037 (t = 1.42). Coin
interaction: bull −0.0241 (t = −1.83) vs bear −0.0088 (t = −0.98); pre-2023 +0.0750
(t = +1.88, 74 obs — sign flip on a tiny sample) vs **post-2023 −0.0205 (t = −4.32)**.
The coin H2 result is a post-2023 (and mildly bull-tilted) phenomenon in this sample;
the pre-2023 coin panel is too thin (74 obs) to interpret the flip.

**(6) Measurement robustness** (coin interaction / token interaction, s4 form):

| variant | coin conv×val (t) | token conv×val (t) | token conv (t) |
|---|---|---|---|
| baseline (043, GL, MRP 30) | −0.0169 (−3.54) | +0.0034 (+0.79) | +0.0061 (+1.47) |
| raw NVT / raw NV-TVL | −0.0060 (−1.90) | +0.0002 (+0.05) | +0.0051 (+1.35) |
| exclude g-capped months | −0.0163 (−0.97), n 406 | −0.0024 (−0.54), n 1,436 | +0.0053 (+1.26) |
| exclude B4 (HODL-6m>80%) | n/a (coins have no ch2) | +0.0023 (+0.55) | +0.0078 (+2.08) |
| coins excl. conv fallback | **−0.0181 (−4.67)** | | |
| MRP 20% | −0.0175 (−3.55) | +0.0033 (+0.78) | +0.0062 (+1.48) |
| MRP 40% | −0.0163 (−3.54) | +0.0035 (+0.80) | +0.0060 (+1.45) |

**Reading.** The coin interaction is bulletproof to the discount-rate assumption and
*strengthens* on the clean-conviction subsample, but (i) with RAW NVT it shrinks to a
third (−0.0060, t = −1.90): the interaction is substantially carried by the
growth-levelized valuation, and (ii) dropping the 40% of coin-months where the PQ CAGR
cap binds keeps the magnitude (−0.0163) but kills significance (t = −0.97, n = 406,
24 clusters). Both caveats go in the paper next to the headline t = −3.5. The token
interaction is dead in every variant (M3 verdict, §5). Token conv slope is stable
across variants (+0.005–0.008), marginally significant only ex-B4.

## 5. Task E — Mechanism discrimination M1–M4 (`tables/mechanisms.csv`)

| # | mechanism | test | result | verdict |
|---|---|---|---|---|
| M1 | attention-dependent absorption | token conv×turnover | +0.0069 (t = +1.21); D4 gradient larger in HIGH-turnover | **NOT SUPPORTED (wrong sign)** |
| M2 | denominator endogeneity | token conv×val, val demeaned in coarse sector-month | +0.0056 (t = +1.27), still positive; quadrant portfolio with sector-neutral val: alpha +1.50%/mo (t = 1.18), n.s. | **REJECTED (interaction does not revive)** |
| M3 | growth-adjustment measurement | token interaction, raw NV/TVL and ex-g-cap | +0.0002 (t = 0.05) and −0.0024 (t = −0.54) | **REJECTED → token-H2 null is NOT a measurement artifact** |
| M4 | seigniorage confound (coins) | coin s4 + staking-yield level + conv×yield | conv×val **−0.0188 (t = −4.39)** with yield controls; conv×sy −0.0163 (t = −1.58) | **COIN RESULT SURVIVES (not a b_t artifact)** |

Staking-yield construction (Entry 105): yield ≈ trailing-12m issuance rate ÷ staked
share, = supply_g12 / logistic(conv), ch1-months only, winsorized 1/99.

**Reading for the paper's Section 2.3.** The intended narrative was "M1 supported +
M2/M3 rejected → single theory, two absorption regimes." What the data delivered is
M2/M3/M4 exactly as that narrative needs, but **M1 with the wrong sign**: the token
premium is not concentrated where attention frictions are largest — it is (weakly) in
the most-traded tokens, and (per §1–§2) between sectors rather than within them. The
mechanism section must either drop M1 or reframe: the evidence pattern (between-sector,
high-turnover, extremes-only, spanned-by-nothing) reads more like *slow-moving sector-
level repricing of governance value* than individual-token attention neglect. M4 is the
session's best defensive result: the coin interaction is not a seigniorage artifact.

## 6. What changes in the paper

1. Section 5 gains the confirmatory sort battery: quintile EW headline with the
   Entry-97 disclosure, the full median→decile progression, cost/sub-period rows, and
   the spanning table (reversal-distinct is the punchline).
2. The claim language for tokens: "portfolio-extremes premium, robust to technical
   spanning, concentrated between coarse sectors; not a uniform cross-sectional slope
   and not robust in a joint panel race."
3. The coin H2 paragraph keeps t = −3.5 but adds the two D6 caveats (raw-NVT
   attenuation; g-cap subsample) and gains M4 as a robustness defense.
4. Section 2.3 mechanism table: M1 verdict reversed from the draft's expectation;
   reframe required (see §5).
5. Appendix: Metcalfe descriptive panel (BTC mean-reversion), horse-race singles
   table, coarse-sector map and per-sector nulls, ve/fee classification table with
   the null splits.
