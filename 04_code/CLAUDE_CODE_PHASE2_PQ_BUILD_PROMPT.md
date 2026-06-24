# Claude Code Kickoff Prompt — Phase 2 Build: PQ (tokens + coins), resuming Part B

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). This resumes Part B of
`CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md` (session 010), which paused at the PQ-definition
question. That question is now fully resolved (Entries 30-32) — this session builds on it.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 0/0B/1 are complete. Phase 2
(NVT_GL) Part A (token PQ theory/pilot) is complete; this session resumes Part B (the actual
build) of CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md, now that PQ is fully resolved. Before doing
anything else, read in full:

1. 04_code/DATA_DECISIONS_LOG.md Entries 30, 31, 32 — the full PQ resolution: fees rejected on
   theoretical grounds (toll, not transacted value); tokens resolved to DeFiLlama
   sector-appropriate reported volume (governance-token Transfer-log volume piloted and
   rejected — wrong object, e.g. UNI 46.6x off DeFiLlama's Uniswap volume, AAVE corrupted by
   sentinel-value transfers); coins resolved to a per-asset source ladder (Entry 32), not one
   global source.
2. 03_data/PHASE2_PQ_PILOT_REPORT.md — the token pilot's full empirical findings (session 012).
3. 06_documentation/PHASE2_PQ_DECISION_STATUS.md — original framing, now superseded by the
   entries above; read for context only, do not follow its §3-4 recommendations.
4. CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md Part B — the still-valid spec for the rest of NVT_GL
   (MC, g, r_e, g_inf, n) that this session resumes. Only step 2 (PQ) in that Part B is
   replaced — by the logic below — everything else there still applies as written.
5. 04_code/DATA_SPECIFICATION.md Section 4 (NVT_GL) and `03_data/classification_table.csv`
   (the `sector` and asset-class fields you'll route on).

## PART A — Tokens: build directly (fully resolved, no further verification needed)

PQ = DeFiLlama sector-routed reported volume, per Entry 31/32:
- DEX/swap volume for AMMs, perps notional for derivatives, borrow/origination flow for
  lending — routed by the `sector` field (Entry 16). Verify the live DeFiLlama endpoint per
  protocol before pulling (confirm slugs, don't assume).
- **Fee-to-volume backout (Entry 32), only when DeFiLlama has no volume series for a
  protocol-month:** check whether that protocol's fee is a confidently known, SINGLE, STABLE
  rate over the window (e.g. a documented flat swap fee) — if so, `notional = fee / rate`, use
  as PQ, and log the rate and its source inline per protocol. Do NOT do this when the rate is
  multi-tier (e.g. Uniswap V3's several fee-tier pools — the blended rate is itself unknown
  without volume, circular), governance-adjustable/variable across the window, or not a simple
  function of notional (e.g. a lending reserve factor, which is a % of interest, not of loan
  volume). If neither a DeFiLlama series nor a confident rate exists for a protocol-month,
  **flag PQ as missing (NaN)** — do not substitute the raw fee directly as PQ.
- TVL and fees stay as side diagnostic columns (+ Volume/TVL turnover), per Entry 30/31. Raw
  Etherscan Transfer logs are an occasional spot-check only, never primary.

## PART B — Coins: verify first, then build, same session

**Step B1 — bounded live verification (do this before writing any coin extraction code):**

1. **Artemis access.** Check artemisanalytics.com/products/api and the free "Lite" tier live —
   actually attempt the documented free-tier flow, don't infer from marketing copy. Determine:
   (a) is Settlement Volume exposed as a standalone series (not just bundled inside Total
   Economic Activity), (b) historical depth, (c) how many of the panel's coins/chains it
   actually covers. Phase 0 (Entry 2) found Artemis's API dead; a relaunch was found by
   web search but never live-verified — this is that verification.
2. **DeFiLlama chain-dexs coverage per coin.** For every coin in the panel, check
   `/overview/dexs/{chain}` live. Classify each as **non-degenerate** (material DeFi/DEX
   activity relative to the chain's real economic footprint — safe as Rung 1) vs.
   **degenerate** (negligible, bolted-on activity unrelated to the chain's real throughput —
   already confirmed for Bitcoin: $419,825/24h, $18.9M/30d, driven by 3 niche protocols,
   nowhere near BTC's actual settlement). Propose and state an explicit materiality threshold
   for this split (e.g. relative to market cap or a known tx-count baseline) rather than
   eyeballing case by case.
3. **BTC-specific fallback.** Verify blockchain.com's Charts API "Estimated Transaction Value
   (USD)" series live (endpoint, history depth, update cadence, confirm it excludes change
   outputs as documented).
4. **Produce a per-coin rung-assignment table** (Rung 1/2/3/4, per Entry 32's ladder) before
   any Part-B extraction code. **If Artemis turns out paid-only, or coverage is ambiguous for
   any coin that's material to the panel (large market cap or long history), STOP and report
   rather than guessing** — this is the one part of this session that should pause for human
   review if it isn't clean. If the picture is clean (Artemis usable as scoped, or the
   DeFiLlama/BTC-fallback combination covers the panel adequately), proceed straight into B2
   without waiting for a review round-trip — the ladder logic itself is already decided.

**Step B2 — build, applying Entry 32's ladder per coin:**

- **Rung 1** — DeFiLlama chain DEX volume, where non-degenerate.
- **Rung 2** — Artemis Settlement Volume, where Rung 1 is degenerate/unavailable and Artemis is
  confirmed accessible at adequate coverage/depth from B1. Use Settlement Volume ONLY — do not
  adopt the full Total Economic Activity composite (it bundles in Chain Fees & MEV and
  Application Fees, which are toll measures — the same flaw already rejected for token fees).
- **Rung 3** — coin-specific native fallback: blockchain.com's series for BTC; for other chains
  with no equivalent ready-made series, bounded native `value` block iteration over a **recent
  window only** (the archive-access objection was wrong per Entry 32, but full multi-year
  history per chain hits the same call-volume wall the token pilot found — just block-count-
  driven instead of log-count-driven; do not attempt it).
- **Rung 4** — DeFiLlama chain fees, last resort only, for any coin where 1-3 are all
  unavailable. Explicitly flag these rows in the output (a column noting "fallback: toll-based
  proxy, not transacted value") — do not let this blend in silently with Rungs 1-3.
- Log which rung every coin actually used, with the reason, in the coverage report.

## What NOT to do

Don't attempt full multi-year native block iteration across the whole coin panel. Don't adopt
Artemis's full Total Economic Activity composite. Don't silently fall to Rung 4 without
flagging it in the data. Don't resolve an ambiguous Artemis/coverage finding by guessing —
stop and report per B1 instead.

## Deliverable

Build the PQ construction for both tokens (Part A) and coins (Part B), then continue
CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md Part B's remaining steps (MC join, g, r_e, g_inf, n) to
produce NVT_GL per asset-month. Produce a Phase 2 coverage report: per-asset PQ source/rung,
where the token fee-backout rule fired and what rate was used, coin rung assignments and why,
and any coverage gaps (flagged NaN, not guessed). Log this session as
`06_documentation/ai_conversations/session_013_*.md`, continue `DATA_DECISIONS_LOG.md` from
Entry 33, and update `06_documentation/time_log.md`. Commit and push to
github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end. Do not start Phase 3
without review.
```
