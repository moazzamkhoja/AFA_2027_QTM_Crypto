# Claude Code Kickoff Prompt — Phase 3c: Fee/Revenue DCF Comparators (TOKENS ONLY)

Paste the prompt below as the first message in a new Claude Code session, working directory
`C:\AFA_2027_QTM_Crypto`. Phase 3 core (session 043) and 3b (session 044) are complete.
This session builds the DCF-style comparators the paper's introduction names as its foil
— price-to-fees and a revenue-DCF ratio — and runs them through the horse race and the
H2 interaction. TOKENS ONLY (Moazzam's directive: fee-DCF is not conceptually valid for
coins, where fees are the validator toll rejected as a fundamental in Entry 30).

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phases 0–3b complete. Before
doing anything else, read in full:

1. 04_code/PHASE3_ANALYSIS_SPECIFICATION.md §8.7 — this session's spec (as amended:
   tokens only, coin chain-fee build dropped).
2. 04_code/DATA_DECISIONS_LOG.md Entries 106–109 — current paper state, the DCF
   misattribution fix, size-as-delta results (Entry 108: the token H2 null has now
   survived five conditioning variables; THIS session provides the sixth and last
   measurement candidate).
3. 03_data/PHASE3B_RESULTS_REPORT.md §3 — the horse race machinery these comparators
   slot into.

## Standing rules (unchanged)
- NO paid services; NO new Etherscan getLogs. DeFiLlama endpoints are free/keyless —
  verify each live before building; log dead/changed endpoints.
- Joins on cmc_id only. Fees/revenue matched via the existing dl_slug identity map
  (03_data/ identity files used by phase2_build_tvl_panel.py) — NEVER by symbol.
- New outputs to 03_data/phase3/; builders 04_code/phase3c_*.py; log every decision
  (next entry: 110). Honest-results clause applies.

## Task A — Fee and revenue panel build
For each of the 101 regression-sample tokens with a dl_slug: pull daily protocol fees
AND daily revenue from the DeFiLlama fees API (check live: api.llama.fi
/summary/fees/{slug}?dataType=dailyFees and dataType=dailyRevenue; also the
/overview/fees listing to resolve slugs). Sum to monthly. Distinguish and keep BOTH
series: fees = what users pay the protocol; revenue = the share accruing to the
protocol/treasury/holders. Output 03_data/phase3/fees_revenue_panel.csv
(cmc_id, month_end, fees_usd, revenue_usd, dl_fees_slug, source_notes).
Report coverage explicitly (tokens covered, months per token, start dates); fee
histories mostly begin 2021+ and many protocols report fees but not revenue — that
asymmetry is a finding, report it.

## Task B — The two comparator measures (tokens only)
1. P/F (practitioner multiple): pf = MC / trailing-12m fees (>=6 monthly obs).
2. Revenue DCF ratio: prev_gl = MC / REV*, where REV* applies the EXACT PQ*/TVL*
   machinery (PARAMS of phase2_nvt_gl.py: rf 4%, MRP 30%, g_inf 3%, n 10, g cap
   [-50%,+200%], beta36, re_floor) to a base of trailing-12m revenue with g = trailing
   3y CAGR (2y/1y fallback). Where revenue is unreported but fees are, compute a
   fees-based variant pf_gl = MC / F* and flag; report both but keep prev_gl primary
   (DCF discounts what holders could claim, not what users pay).
Both ln-transformed, winsorized 1/99, standardized within token-month.

## Task C — Tests (the order matters; C1 is Moazzam's core question)
C1. **H2 with a fee-anchored delta proxy**: token spec s4 (conv + controls + val +
    conv×val, month FE, two-way clustered) with val = ln P/F and separately
    val = ln prev_gl. This is the sixth and cleanest measurement test of the token
    H2 null: fees/revenue are earned in external assets and are NOT mechanically
    linked to the token's own price the way TVL is. Also run the split-sample version
    and the coverage-matched baseline (NV/TVL_GL interaction re-estimated on the SAME
    subsample) so any revival is attributable to the denominator, not the sample.
C2. Horse race singles + joint: add ln P/F and ln prev_gl columns to the token panel
    race; report whether conviction's slope changes on the fee-covered subsample.
C3. Portfolios: quintile long-shorts on P/F and prev_gl (cheap minus expensive, EW,
    min 3/leg) vs LTW factors; spanning both directions against the conviction
    quintile (does the DCF comparator span conviction, or vice versa).
C4. Sub-periods (post-2023) for anything significant.

## Task D — Technical battery completion (both tracks; all from universe_panel, no new data)
Add five signals to the horse-race panel and portfolio machinery (spec §8.8):
1. ma_dist = price/MA10 − 1 (continuous; REPLACES the binary MA-cross in spanning —
   the binary version's long-shorts had only 28–31 overlapping months in session 044;
   re-run the two affected spanning cells with ma_dist quintile long-shorts and note
   the supersession).
2. vol12 = trailing 12m monthly-return SD (>=8 obs).
3. ivol = residual SD from trailing 36m regression of asset return on CMKT (>=12 obs).
4. amihud = trailing 12m mean of |r_month| / (month-end volume_24h), ln-transformed.
   FLAG in output and report: volume_24h is a month-end snapshot, not a monthly
   aggregate — noisy proxy, log as a caveat (Entry).
5. skew36 = trailing 36m monthly return skewness (>=18 obs).
All standardized within class-month. Run: (a) horse-race singles + joint columns per
track; (b) quintile long-shorts per signal; (c) ADD vol12, ivol, amihud, skew36,
ma_dist long-shorts to the conviction-quintile spanning battery (the key question:
does the token conviction quintile survive the completed battery); (d) one paper
sentence justifying exclusions: monthly RSI/MACD/Bollinger are transformations of the
momentum/MA-distance/volatility set; daily-native signals (MAX, true RSI) infeasible
without daily price histories (free-tier depth limits) — note as limitation.

## Deliverables
03_data/PHASE3C_RESULTS_REPORT.md — lead with the C1 verdict (H2-in-tokens under
fee-anchored valuation: revived or still dead), then the completed-battery spanning
verdict for the conviction quintile (Task D), coverage table, all tables with
one-paragraph readings, negative results at equal prominence. Decisions log entries;
session log (session_045_...); time_log row; commit and push at session end.
```
