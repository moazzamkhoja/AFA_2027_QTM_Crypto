# Claude Code Kickoff Prompt — Phase 2c Diagnostic: TVL/Fees/Volume Metadata Audit (111 NaN Tokens)

Paste everything below the line into a new Claude Code session with working directory `C:\AFA_2027_QTM_Crypto`.

---

You're working in the AFA 2027 QTM Crypto research repo (`github.com/moazzamkhoja/AFA_2027_QTM_Crypto`).

## Required reading (do this first, in full)

1. `04_code/DATA_DECISIONS_LOG.md` — Entry 30 (TVL is capital stock, not PQ — the original objection to
   treating TVL as a flow), Entry 31 (Etherscan token-transfer rejection — measuring the wrong quantity;
   verify every number before trusting it), Entry 32 (the token-side PQ source waterfall, including the
   **already-decided fee-inversion rule**: "back out volume from fee only when the fee is a confidently
   known single, stable rate (not multi-tier/variable/non-volume-linked), else flag PQ missing"),
   Entry 36 and Entry 37 (Dune pilot + full-panel dry-run: 4 of the original 17 token-side NaN tokens
   resolved via Dune — AAVE, STRK, LDO, GNS; the other 13 are absent from Dune's spellbook and money can't
   fix that), and Entry 38 (this session's framing — read this one closely, it sets the rules below).
2. `03_data/DUNE_DRYRUN_REPORT.md` §2 for the full `DISTINCT project` lists — **25 lending projects** and
   **28 perpetual.trades projects** — this is your turnover-calibration cohort in Step 3 below.
3. `03_data/phase2/pq_tokens.csv` — **re-derive live, do not trust a stale count.** Columns:
   `cmc_id, symbol, dl_slug, dl_category, month_end, pq_usd, pq_source, note`. A token counts as "covered"
   if it has at least one non-NaN `pq_usd` month. As of the last live check: 127 total tokens, 16 covered,
   111 NaN, breaking into categories: Yield 16, Derivatives 10, Farm 8, Gaming 7, Dexs 7, Services 7,
   Bridge 6, Lending 6, Launchpad 6, Chain 6, Yield Aggregator 4, Canonical Bridge 3, Cross Chain Bridge 2,
   Developer Tools 3, Token Locker 2, plus 17 singleton categories (1 token each). **Re-verify these counts
   yourself before proceeding** — this file may have changed since last checked.

## Funding / cost context

DeFiLlama's relevant data (TVL, Fees, Revenue, dex/derivatives volume, yields/APY) is on the **free,
keyless `api.llama.fi` / `yields.llama.fi` / `bridges.llama.fi` tier** per their public docs
(docs.llama.fi/api) — no subscription should be needed for anything in this session. DeFiLlama also sells
a **Pro API at ~$300/mo** (`pro-api.llama.fi`) for higher rate limits / extra endpoints. **Do not sign up
for, key into, or use the Pro API under any circumstance this session — flag it as a gap and stop, don't
work around it by paying.** Moazzam handles any purchase decision himself, after reviewing evidence, same
as the standing rule for Dune.

## The conceptual framework — read before doing anything, it defines what this session is actually checking

**This is a metadata/feasibility audit, not a PQ build.** For each of the 111 NaN tokens, the question is
*"what data exists, and given this protocol's actual economic model, could any of it plausibly become a
PQ (transacted-value) measure?"* — not "compute the number." **No `pq_tokens.csv` writes this session.**

Background the spec didn't previously need: PQ is a *flow* (transacted value per period); TVL is a
*stock* (locked capital). Entry 30 already established you cannot treat them as the same thing. The
question this session explores is whether a **calibrated conversion** from the stock to a flow proxy is
defensible — the same structure as the no-labor AK growth model, `Y = A·K`, where `A` ("turnover") is
flow ÷ stock, identical to the corporate-finance asset-turnover ratio. If `PQ ≈ A_protocol × TVL_protocol`
and `A` can be estimated with reasonable confidence, that is a usable proxy; if `A` is wildly dispersed
across comparable protocols, it isn't, and that finding should be reported plainly rather than forced.

Rank conversion paths in this order of preference (most direct and least assumption-laden first):

**(1) Direct volume — no conversion needed at all.** `pq_tokens.csv` was originally populated by checking
DeFiLlama's summary volume for each protocol's primary category, but DeFiLlama has *separate* verticals
for different activity types that may not have been checked: `dexs` (DEX swap volume), `derivatives`
(perps/options notional), `bridges` (cross-chain transfer volume). A token whose category is Dexs,
Derivatives, Bridge, Canonical Bridge, or Cross Chain Bridge may already have a directly-reported volume
series sitting in one of these verticals — check this FIRST, before reaching for any proxy. If found, the
token may not need a proxy at all (flag it as `direct_volume_available`, separate from the proxy-feasibility
verdicts below).

**(2) Fee inversion — Entry 32's existing rule, now extended from coins to the rest of the token set.**
If DeFiLlama's `summary/fees/{slug}` has a Fees series but no direct volume exists, and the protocol's fee
structure is a single, fixed, **confidently citable** rate (e.g., a stated 0.3% swap fee documented in the
protocol's own docs) — not variable, tiered, or usage-dependent — then `Volume ≈ Fees ÷ fee_rate`. Do not
guess a fee rate from a generic "typical AMM fee" assumption; either find the protocol's actual documented
rate or flag `fee_rate_not_confidently_known` and stop there for that token.

**(3) TVL × APY — for Farm / Yield / Yield Aggregator tokens specifically (28 tokens, the single largest
bucket).** For protocols where the entire "product" is a published yield on locked capital, realized APY
is a directly observed, protocol-specific rate (check `yields.llama.fi/pools`, matched by protocol/slug)
— a far better-grounded `A` than a cross-sectional turnover average, since it's specific to *that*
protocol rather than borrowed from others. `PQ_farm ≈ TVL × APY`.

**(4) TVL × calibrated turnover — for Lending, Derivatives, Liquid Staking, and any other category where
the protocol's activity genuinely flows through locked capital (NOT for Gaming, Launchpad, Chain,
Developer Tools, Services, Token Locker — these have no comparable capital→flow channel; don't force this
model where the economic model doesn't support it, leave NaN instead).** This path is only as credible as
the calibration in Step 3 below — do not propose a turnover rate for any token without first checking
whether the comparable-cohort dispersion (Step 3) is tight enough to trust.

**Gaming (7 tokens) is explicitly excluded from this entire audit. Skip them. They stay NaN by design —
this was a deliberate decision (Entry 38), not an oversight to fix.**

## What to do

**Step 1 — Re-derive the worklist.** From `pq_tokens.csv`, pull symbol + `dl_slug` + `dl_category` for
every currently-NaN token. Drop the 7 Gaming tokens (out of scope per above) — you should have 104 tokens
left to actually check. Group them by category for the steps below. **Watch for the NVT symbol
collision**: one of the NaN Dexs-category tokens has ticker `NVT` (Nerve Network) — this is unrelated to
the NVT *metric* used throughout this paper. Always key by `dl_slug`, never by bare ticker symbol, when
there's any ambiguity.

**Step 2 — Per-token DeFiLlama metadata check (all 104).** Before calling anything, confirm the *current*
exact endpoint shapes against `docs.llama.fi/api` — don't assume the paths below haven't shifted; verify,
the same discipline as every prior session in this log. Starting points to verify:
   - **TVL:** `https://api.llama.fi/protocol/{slug}` — `tvl` time series present? Date range?
   - **Fees / Revenue:** `https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees` (and
     `dailyRevenue`) — present? Date range?
   - **Direct volume**, where category-appropriate: the `dexs` vertical for Dexs-category tokens, the
     `derivatives` vertical for Derivatives-category tokens, `bridges.llama.fi` for the
     Bridge/Canonical Bridge/Cross Chain Bridge tokens (11 total).
   - **APY/yields**, for Farm/Yield/Yield Aggregator tokens (28 total): `yields.llama.fi/pools`, matched
     by protocol/slug (confirm the current matching key — it may be by pool ID, not slug directly).
   Use only the free `api.llama.fi` / `yields.llama.fi` / `bridges.llama.fi` surface. Record, per token:
   TVL Y/N + date range, Fees Y/N + date range, Revenue Y/N + date range, direct Volume Y/N + date range
   (and which vertical), APY Y/N + date range.

**Step 3 — Build the turnover-calibration cohort and test its dispersion.** Reuse the validated query
pattern from `dune_dryrun_fullpanel.py`, but pull the **full** `DISTINCT project` lists this time — all
25 lending projects and all 28 perpetual.trades projects (not just aave/strike/gains_network), full
history, `GROUP BY project, month`. For each project, find its matching DeFiLlama `slug` — **Dune's
`project` string and DeFiLlama's `slug` will not always match exactly; verify each mapping individually,
do not assume a string match is correct** — and pull that protocol's TVL history. Compute
`turnover = PQ / TVL` per protocol-month. Report the distribution **separately for lending vs.
perpetual**: median, interquartile range, min/max, and how many projects you could and couldn't confidently
slug-match. This dispersion is the actual evidence for whether category-level turnover imputation
(path 4 above) is defensible. **If it spans more than roughly an order of magnitude, say so plainly** —
a wide, unusable dispersion is a legitimate and useful finding, not a failure to fix.

**Step 4 — Per-token feasibility verdict (the actual deliverable).** For each of the 104 tokens, report:
what data exists (from Step 2), which conversion path (if any) looks viable given that protocol's
specific economic model, and a one-line rationale referencing the actual data found — not a blanket
category assumption. **Do not compute or insert an actual PQ value for any token this session.** This is
a feasibility map; an actual Phase 2c build is a separate, later, explicitly-authorized session.

## What NOT to do

- Do not write to `03_data/phase2/pq_tokens.csv` (or any panel CSV) — no PQ values, no `pq_source`
  changes, nothing. This is diagnostic-only, same standard as the Dune pilot and dry-run sessions.
- Do not sign up for, key into, or use DeFiLlama's Pro API — free tier only.
- Do not guess: not a fee rate, not a Dune-project-to-DeFiLlama-slug mapping, not a turnover figure.
  Flag low-confidence items and move on rather than forcing a number.
- Do not build the actual TVL×turnover (or TVL×APY) imputation pipeline yet — that's a follow-on session,
  gated on this report's findings and human review, exactly like Entry 36 gated Entry 37.
- Do not touch the 7 Gaming-category tokens.
- Do not purchase anything or take any financial action.

## Deliverable

Write `03_data/PHASE2C_DIAGNOSTIC_REPORT.md` containing: the per-token feasibility table (104 rows,
grouped by category, per Step 4), the turnover-dispersion analysis from Step 3 (lending and perpetual
reported separately), and a clear closing recommendation — which categories/tokens look promising for a
real Phase 2c build and via which path, which look hopeless given the economic model, and whether the
TVL×turnover idea is statistically defensible at all given the observed dispersion (or only defensible
for some categories and not others).

Then:
- Log this session as `06_documentation/ai_conversations/session_017_<date>_phase2c_diagnostic.md`
  (follow the existing session-log format/structure in that directory).
- Continue `04_code/DATA_DECISIONS_LOG.md` from **Entry 39** (Entry 38 is the last existing entry).
- Add a row to `06_documentation/time_log.md`.
- Commit and push to `main` on `github.com/moazzamkhoja/AFA_2027_QTM_Crypto`.

**Stop after the report.** Do not start an actual Phase 2c panel build, and do not write any PQ values,
before this diagnostic is reviewed.
