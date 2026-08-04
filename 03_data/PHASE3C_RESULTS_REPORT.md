# Phase 3c Results Report — Fee/Revenue DCF Comparators (tokens only) + Technical Battery Completion

Session 045, 2026-08-04. Spec: `04_code/PHASE3_ANALYSIS_SPECIFICATION.md` §8.7 (as
amended: tokens only, coin chain-fee build dropped) and §8.8. Kickoff:
`CLAUDE_CODE_PHASE3C_KICKOFF_PROMPT.md`. Builders: `04_code/phase3c_*.py`. Decisions:
DATA_DECISIONS_LOG Entries 111–114. Everything specified was run; everything run is
reported; nothing was tuned after seeing results.

**Headline (honest summary):**

1. **C1 verdict: the token H2 null survives its sixth and final measurement
   candidate.** With a fee-anchored valuation denominator — the one denominator that
   is earned in external assets and not mechanically linked to the token's own price —
   the conviction × valuation interaction is **conv × ln P/F = −0.0024 (t = −0.45)**
   and **conv × ln prev_gl = −0.0035 (t = −0.31)**. For the first time across all six
   conditioners the point estimates carry the H2 sign, and the split-sample slopes
   order the right way (cheap > expensive in both), but nothing is within a country
   mile of significance. The coverage-matched NV/TVL_GL baselines on the same
   subsamples are equally dead (+0.70 / −0.80), so there is no denominator effect to
   attribute. The paper can now state: the token conditioning null is not a
   measurement artifact of TVL, growth-levelization, sector composition, size,
   turnover, **or fee/revenue anchoring**.
2. **New fact the race turned up: the practitioner P/F multiple is the first
   valuation signal that actually works in the token panel.** ln P/F singles:
   −0.0103 (t = −2.50) full, −0.0148 (t = −2.70) sub-2024; with full controls in the
   s4 spec the level term is −0.0119 (t = −3.21); and it survives the completed joint
   battery (−0.0090, t = −2.32) where raw NV/TVL never did. Expensive-on-fees tokens
   underperform. The DCF-transformed version destroys this signal (prev_gl t = −0.42;
   pf_gl t = −0.68) — the growth-levelization machinery that is load-bearing for the
   coin result subtracts value here. As a quintile portfolio, however, P/F earns
   nothing (alpha −0.18%/mo, t = −0.10 at ~5–6 names/leg) — a panel-slope, not an
   extremes, phenomenon: the mirror image of conviction.
3. **Task D verdict: the token conviction quintile survives the COMPLETED technical
   battery.** Alpha vs LTW + all twelve competitor long-shorts (reversal, mom3,
   mom12, 52wk-high, size, raw NV/TVL, S2F, ma_dist, vol12, ivol, amihud, skew36):
   **+1.74%/mo (t = 2.45)**; adding the two fee-comparator long-shorts: +2.17%
   (t = 2.82). The two underpowered session-044 MA-cross cells are RESOLVED by the
   continuous ma_dist replacement: the "+all" cell goes from +0.99% (t = 0.99,
   n = 28) to **+1.66% (t = 2.73, n = 43)**, and the single-MA cell from +1.09%
   (t = 1.16, n = 31) to +1.83% (t = 2.46, n = 50). Vol and skew — the last plausible
   spanners — do not span it. Direction 2: no competitor earns alpha on LTW + q5.
4. **The coin interaction also survives the completed battery**: conv × val =
   −0.0235 (t = −2.68) full, −0.0188 (t = −3.17) sub-2024, with all twelve
   comparators in the regression (session 044's eight-comparator figure was
   t = −2.83). Amihud illiquidity is the strongest new coin single (−0.0223,
   t = −2.65; sub-2024 −3.23) and does not dent the interaction.
5. **Honest caveats at equal prominence.** (i) On the revenue-covered subsample
   (33 tokens, 846–915 obs, effectively 2023+) the conviction slope flips NEGATIVE
   (−0.0124, t = −2.01 in the joint spec without the fee column) — a composition
   fact about revenue-reporting DeFi blue-chips, present before any fee variable
   enters, and worth a sentence in the paper's external-validity discussion.
   (ii) Fee coverage is 55/101 tokens (revenue 51/101), histories mostly 2021+ —
   the fee-anchored tests speak for the covered half of the sample only.
   (iii) amihud uses month-end snapshot volume, not monthly aggregate volume — a
   noisy illiquidity proxy (logged, Entry 114). (iv) prev_gl portfolio months are
   all post-2023 by construction (the DCF needs ≥1y of prior fee history), so its
   full-sample and post-2023 rows coincide.

---

## 0. Coverage (Task A: `fees_revenue_panel.csv`, `tables/fees_coverage.csv`)

DeFiLlama fees API verified live in-session (`api.llama.fi/summary/fees/{slug}`,
`dataType=dailyFees|dailyRevenue`; `/overview/fees` for the adapter listing). Slug
identity = the authoritative cmc_id → dl_slug map actually used in the TVL build
(tvl_panel.csv), never symbol. Four tokens ride chain-level fee adapters (ARB, METIS,
APE, BLAST — same Entry-68/84 precedent as their chain-level TVL; sequencer fees are
DAO-accruing, unlike L1 validator tolls; flagged in `source_notes`).

| stat | fees | revenue |
|---|---|---|
| tokens covered (of 101) | **55** | **51** |
| regression asset-months with a defined ratio | 1,367 (P/F) | 976 (prev_gl) |
| tokens entering tests | 51 (P/F) | 35 (prev_gl) |
| median months per covered token | 44 | — |
| start dates | 10 pre-2021, 13 in 2021, 32 in 2022+ | later still |

The fees-but-no-revenue asymmetry the kickoff predicted: 4 tokens report fees with
NO revenue adapter at all (METIS, APE, RBN, MAV), 10 more have shorter revenue than
fee histories, and 13 tokens contribute pf_gl-only asset-months (202 rows) where
revenue is missing but fees exist. Revenue is the scarcer, later, more curated
series — reported as a finding: *what users pay is far better measured than what
holders could claim.* Non-covered misses are genuine adapter absences (HTTP 400 —
augur, loopring, hashflow, biconomy, aevo-perps, etc.); six candidate slug
resolutions were probed and all rejected (collision or zero usable months —
Entry 111). Known data limitation: DL's `dydx-v3` adapter covers only 2023-11..
2024-10, missing the protocol's 2021–22 fee peak.

## 1. Task B — comparators (`fee_comparators.csv`)

pf = MC / trailing-365D fee sum (≥6 monthly obs, PQ0 house convention). prev_gl =
MC / REV\*, F\* analog pf_gl = MC / F\* — both via the EXACT `phase2_nvt_gl.py`
machinery and PARAMS (rf 4%, MRP 30%, g_inf 3%, n 10, g ∈ [−50%, +200%] flagged,
beta36, r_e floor 5%), base = trailing-12m revenue (fees), g = trailing 3y CAGR of
the base (2y/1y fallback). ln, winsorized 1/99 pooled, standardized within
token-month.

Sanity: median P/F 12.1 (practitioner range), median prev_gl 23.0. g capped in 468
fee-base and 361 revenue-base rows. Correlations: corr(ln P/F, ln NV/TVL raw) =
0.48, vs GL version 0.32, corr(ln P/F, size) = −0.06 — the fee multiple is a
related-but-distinct valuation axis, not NV/TVL or size in disguise.

## 2. Task C1 — H2 with fee-anchored valuation (`tables/phase3c_c1_feeval.csv`)

Token spec s4: r_fwd1_w on conv + controls + val + conv×val, month FE, two-way
clustered. Coverage-matched = NV/TVL_GL s4 re-estimated on the identical subsample.

| val measure | n / tokens | conv | conv × val | val level | matched-baseline conv × val (NV/TVL_GL) |
|---|---|---|---|---|---|
| **ln P/F** | 1,282 / 49 | +0.0066 (+1.15) | **−0.0024 (−0.45)** | −0.0119 (−3.21) | +0.0046 (+0.70) |
| **ln prev_gl (primary DCF)** | 915 / 33 | −0.0009 (−0.11) | **−0.0035 (−0.31)** | −0.0014 (−0.25) | −0.0102 (−0.80) |
| ln pf_gl (flagged variant) | 1,104 / 41 | +0.0104 (+1.50) | +0.0060 (+0.73) | +0.0002 (+0.04) | +0.0042 (+0.42) |
| full-sample NV/TVL_GL reference | 2,592 / 97 | +0.0061 (+1.47) | +0.0034 (+0.79) | +0.0042 (+0.79) | — |

Split-sample (s2 by median of the fee valuation within month):

| val | cheap-half conv | expensive-half conv | s5_diff conv × high |
|---|---|---|---|
| ln P/F | +0.0085 (+0.94) | +0.0023 (+0.37) | −0.0068 (−0.89) |
| ln prev_gl | +0.0050 (+0.37) | −0.0096 (−0.65) | −0.0184 (−0.87) |

**Reading — the C1 verdict.** For the first time in six measurement variants the
interaction points the H2 way and the split-sample slopes order correctly
(cheap > expensive under both fee measures). But the t-stats are −0.45 and −0.31,
and the s5_diff tests −0.89/−0.87: this is a null, full stop. Because the
coverage-matched TVL_GL baselines on the same subsamples are equally dead, the flip
in sign is not attributable to the fee denominator specifically (on the prev_gl
subsample even the TVL_GL interaction goes negative, −0.80 — a sample-composition
effect). Verdict for the paper: **H2-in-tokens stays dead under the cleanest
available denominator; the conditioning failure is a fact about tokens, not about
measurement.** The six candidates now exhausted: TVL→raw TVL (M3), g-cap exclusion
(M3), sector-demeaned val (M2), size-as-delta (Entry 108), turnover (M1), and
fee/revenue anchoring (this session).

## 3. Task C2 — horse race with the fee columns (`tables/phase3c_race_panel.csv`)

Singles (own coefficient, month FE, two-way clustered):

| signal | token full (t) | token 2024+ (t) |
|---|---|---|
| **ln P/F** | **−0.0103 (−2.50)** | **−0.0148 (−2.70)** |
| ln prev_gl | −0.0019 (−0.42) | +0.0011 (+0.17) |
| ln pf_gl | −0.0032 (−0.68) | −0.0011 (−0.17) |

Joint (completed battery + fee column, fee-covered subsamples):

| spec | conv | fee column |
|---|---|---|
| completed + ln P/F (n = 1,145) | +0.0011 (+0.19) | **−0.0090 (−2.32)** |
| same subsample, no fee column | +0.0014 (+0.24) | — |
| completed + ln prev_gl (n = 846) | −0.0119 (−1.75) | +0.0020 (+0.35) |
| same subsample, no fee column | **−0.0124 (−2.01)** | — |

**Reading.** The practitioner multiple is a real token panel signal — the only
valuation ratio to survive a joint battery in any track so far — and it is
*unambiguously a level effect*: DCF-transforming it (pf_gl, prev_gl) kills it, and
portfolio-sorting it earns nothing (§4). Conviction's joint slope is unchanged by
the fee column on the P/F subsample (+0.24 → +0.19): the fee multiple neither spans
nor revives conviction. The negative conviction slope on the revenue subsample
(−2.01 *before* the fee column enters) is a composition caveat, reported in the
headline; it echoes the session-044 finding that the token linear slope is fragile
to conditioning, in contrast to the sort extremes.

## 4. Tasks C3/C4 — portfolios (`tables/phase3c_portfolios.csv`)

Quintile long-shorts, EW, min 3/leg, cheap-minus-expensive for the valuation pair;
NW-3 alpha vs monthly LTW. Post-2023 rows = C4.

| portfolio | mean/mo | alpha (t) | Sharpe | n | post-23 alpha (t) |
|---|---|---|---|---|---|
| pf cheap−expensive | +0.79% | −0.18% (−0.10) | 0.15 | 41 | +1.15% (+0.85) |
| prev_gl cheap−expensive | −0.60% | +0.98% (+0.55) | −0.23 | 38 | (= full; all months post-2023) |
| ma_dist (high−low) | −2.32% | −2.17% (−1.57) | −0.86 | 50 | −2.18% (−1.36) |
| vol12 | −1.25% | −1.06% (−0.73) | −0.48 | 50 | −1.51% (−0.89) |
| ivol | −1.24% | −0.56% (−0.43) | −0.52 | 50 | −1.81% (−1.17) |
| amihud (illiquid−liquid) | −0.65% | −1.47% (−0.82) | −0.25 | 50 | +1.44% (+0.95) |
| skew36 | −0.54% | +0.31% (+0.16) | −0.22 | 49 | −1.23% (−0.70) |
| q5_ew conviction (reference) | +2.28% | +1.71% (+2.18) | 0.86 | 50 | +1.48% (+1.79) |

**Reading.** All negative results. Neither fee comparator works as a sort (P/F's
panel significance does not translate at ~5–6 names/leg — thin-breadth quintiles on
a half-covered sample), and none of the five technicals earns a significant
long-short in either direction. C4 adds nothing: no cell that is null full-sample
revives post-2023.

## 5. Task D — completed spanning battery (`tables/phase3c_spanning.csv`)

Direction 1: conviction q5_ew on LTW + competitor long-short(s).

| spec | alpha | t | n |
|---|---|---|---|
| + pf cheap LS | +1.22% | +1.67 | 41 |
| + prev_gl cheap LS | +1.54% | +1.84 | 38 |
| + ma_dist LS (supersedes 044 MA-cross cell: +1.09%, t=1.16, n=31) | **+1.83%** | **+2.46** | 50 |
| + vol12 LS | +1.69% | +2.10 | 50 |
| + ivol LS | +1.69% | +2.15 | 50 |
| + amihud LS | +1.74% | +2.14 | 50 |
| + skew36 LS | +1.66% | +2.11 | 49 |
| + all-7 (044 set, ma_dist for MA-cross; supersedes 044 +all: +0.99%, t=0.99, n=28) | **+1.66%** | **+2.73** | 43 |
| **+ completed battery (12 long-shorts)** | **+1.74%** | **+2.45** | 43 |
| + completed + both fee LS (14) | +2.17% | +2.82 | 35 |

Direction 2 (each new competitor on LTW + q5_ew): no positive alpha anywhere — pf
−0.72% (t = −0.42), prev_gl +0.79% (t = 0.32), ma_dist −2.37% (t = −1.86), vol12
−0.97% (−0.61), ivol −0.47% (−0.34), amihud −1.58% (−0.78), skew36 +0.09% (+0.04).

**Reading — the Task D verdict.** The token conviction quintile **survives the
completed battery**. The session-044 qualification ("the MA-cross and joint cells
are underpowered, not refutations") is now resolved in conviction's favor: with the
continuous MA-distance signal restoring full month overlap, the previously ambiguous
cells are significant (+2.73 / +2.46). Volatility and skewness — flagged in Entry 110
as the remaining plausible spanners — do not span it. The two alpha dips (pf and
prev_gl cells, t = 1.67/1.84) are fee-coverage subsample effects (n = 41/38 months),
consistent with §3's composition caveat, not with spanning: the competitor loadings
in those cells are small and insignificant.

Coin track (panel only; quintiles infeasible at 11–20 names/month): the interaction
survives the completed battery — conv × val −0.0235 (t = −2.68) full, −0.0188
(t = −3.17) sub-2024. New coin singles: amihud −0.0223 (t = −2.65; the illiquid-coin
discount), ivol −0.0146 (t = −1.67), vol12/ivol/amihud all significant sub-2024
(−2.29/−2.10/−3.23). None of them touches the interaction.

## 6. Exclusions sentence for the paper (Task D-d)

> Monthly RSI, MACD, and Bollinger-band signals are deterministic transformations of
> the momentum, moving-average-distance, and volatility measures already in the
> battery, and daily-native signals (the MAX effect, true 14-day RSI) require daily
> price histories that are unavailable at free-tier depth; we therefore omit the
> former as redundant and note the latter as a data limitation.

Amihud caveat for the text: our volume_24h is a month-end snapshot rather than a
monthly aggregate, so the Amihud measure is a noisy illiquidity proxy; its strong
coin-track performance should be read with that attenuation in mind.

## 7. What changes in the paper

1. Section 6 (robustness) gains the definitive C1 row set: the token H2 null now
   survives SIX measurement candidates, ending with the fee-anchored denominator —
   the strongest possible version of the M2 rebuttal. Sign-flip-but-null reported
   honestly.
2. Section 5 horse race: P/F enters as the one working valuation comparator (panel
   level effect, survives joint; no portfolio translation; DCF transform destroys
   it). Framing gift for the intro: *the practitioner fee multiple beats its own
   DCF refinement* — growth-levelization helps where the fundamental is a
   throughput flow (coins), hurts where it is a cash flow already netted (fees).
3. Section 5 spanning table upgraded to the completed battery: conviction quintile
   +1.74%/mo (t = 2.45) vs 12 competitors; the two 044 underpowered cells replaced
   (supersession footnote, Entry 110/114).
4. Coin H2 paragraph: interaction now survives a TWELVE-comparator battery
   (t = −2.68 / −3.17 sub-2024); amihud added to the comparator list with the
   snapshot caveat.
5. Limitations: fee coverage 55/101 with 2021+ histories; revenue scarcer than fees
   (a measurement asymmetry that is itself evidence on disclosure practice);
   revenue-subsample conviction sign flip as an external-validity note.
