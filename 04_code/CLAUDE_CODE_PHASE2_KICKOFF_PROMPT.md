# Claude Code Kickoff Prompt — Phase 1 Finishing Touches + Phase 2 (NVT_GL)

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). This session has two parts:
close out Phase 1's open items, then move straight into Phase 2 in the same session.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 0, Phase 0B, and Phase 1
(λ channels) are complete. Before doing anything else, read in full:

1. 03_data/PHASE1_COVERAGE_REPORT.md — what Phase 1 built and its open items.
2. 04_code/DATA_DECISIONS_LOG.md Entries 21-28 — the λ-channel judgment calls and why,
   including Entry 28 (the scoping decisions behind this exact prompt).
3. 04_code/DATA_SPECIFICATION.md Section 4 (NVT_GL) and Section 7 (phasing) — for Part B.

This session has two parts. Do Part A first, then continue straight into Part B — these
are finishing touches plus the next phase, not a from-scratch rebuild of either.

## PART A — Phase 1 finishing touches

1. **Finish the ETH staking series.** `phase1_channel1_eth_staking.py` is resumable via
   monthly checkpoints under `03_data/raw/phase1_onchain/` — re-run it to completion
   through 2026-05. Keep the cumulative-deposit method as-is (do NOT add post-Shapella
   withdrawal netting — that needs a consensus-layer/beacon-chain data source, which is
   new scope, not a finishing touch). Keep documenting it as a monotone upper-envelope
   conviction proxy, not a net-stake figure, exactly as Entry 23 already does.

2. **Channel 2 (coin-age) — explore a free workaround before concluding it's
   infeasible.** Entry 24 found no free aggregator/API serving HODL-wave data across the
   panel. Before leaving it there, specifically check (verify live, don't assume):
   whether any Bitcoin-chain explorer (mempool.space, blockstream.info, blockchair)
   exposes a free UTXO-age or "coins last moved" metric usable as a coin-age proxy for
   BTC — BTC is the single highest-value pre-2020 coin to unlock. If something usable
   exists for BTC, check whether the same or a comparable explorer covers other major
   pre-2020 coins (LTC, XRP, DOGE, etc.) before building anything. If nothing free and
   credible turns up, leave Channel 2 as a documented gap (per the spec's "flag, don't
   guess" principle) and say so plainly in the updated coverage report — do not procure a
   paid source in this session; that decision is deferred.

3. **Confirm N=250.** Per the coverage report's own §7 point 5: λ density is
   governance-token-driven, and tightening the universe wouldn't fix the coin-side gap
   (it's a source problem, not a universe-size problem). No action needed — just state
   this confirmation explicitly in the updated coverage report so it's on record.

4. **Revisit the 16 gray-zone classifications** (OP, MNT, MANTA, IMX, RPL, ANKR, SSV,
   STRD, EWT, GBYTE, FCT, BLUR, LOOKS, ME, PNK, PTS — `classification_table.csv`,
   Entry 18) now that real Channel-1 lock data exists. Check whether any of these now
   show a clean security-staking lock (vs. governance-only/no lock) and reclassify with
   justification per the existing `classification_basis` convention if so. If the
   evidence is unchanged, leave them as `other` and say why in one line each.

5. **Fix the internal inconsistency in `PHASE1_COVERAGE_REPORT.md`** — §5's headline
   ("1,326 asset-months, 52 distinct assets") doesn't match §8 and Decisions Log Entry 27
   (1,308 asset-months, 51 assets). Reconcile every section of the report to whatever the
   final, post-ETH-resume numbers actually are.

6. **Optional, lower priority:** if time allows, enrich the identity map from CMC
   `detail.platforms[]` (Entry 22's noted next step) to widen Channel 1's EVM token
   coverage beyond the current curated 6. Not required before moving to Part B.

Log all of this in `DATA_DECISIONS_LOG.md` (next entry is 29 — Entry 28 is already used
by the Cowork-side scoping decision behind this prompt) and re-run
`phase1_assemble_lambda.py` if any of the above changes the underlying channel data.

## PART B — Phase 2: Growth-Levelized NVT (NVT_GL)

Per spec Section 4: `NVT_GL = MC / PQ*`, where PQ* levelizes projected transaction
throughput into a present-value annuity (PMT-style) using a CAGR growth rate g, a
CAPM-style discount rate r_e, a terminal growth rate g_inf, and a horizon n.

Build, per asset-month, on the frozen Phase 0 universe (join on `cmc_id`,
`status='observed'` rows only):

1. **MC** — market cap, same source as Phase 0 (already in `universe_panel.csv`).
2. **PQ** — nominal economic throughput.
   - Coins: on-chain transaction volume. VERIFY live free access of a transaction-volume
     source per chain before building (continue the project's preference for canonical
     chain data over aggregators where feasible — e.g. transaction volume directly from an
     explorer's logs — but DeFiLlama fees/revenue data is an acceptable source for
     protocol-level throughput per the spec; document whichever you use per asset). Flag
     and prefer an "adjusted" volume series netting out exchange-internal/self-churn
     transfers if available; otherwise use raw volume and flag it (a known NVT weak point).
   - Governance tokens: protocol throughput (DEX volume, fees, or active users — DeFiLlama
     fees/revenue is fine here). Use one consistent definition where possible; document
     where it had to vary across tokens.
3. **g** — trailing 3-year CAGR of PQ; flag and document a shorter window for assets with
   less history.
4. **r_e** — CAPM-style beta against a crypto market index (cap-weighted index or BTC as a
   simple alternative) plus a risk-free rate. Keep this discount-rate use of "CAPM"
   distinct in naming/code from the portfolio-level CAPM control in Phase 3 (spec §5) —
   don't conflate the two.
5. **g_inf** — a single macro-anchored constant in the 2-4% range, not estimated per
   asset; flag explicitly as a robustness parameter for later sensitivity testing.
6. **n** — projection horizon, default 10 years; also a robustness parameter, not
   estimated.

Output: NVT_GL per asset-month, plus the underlying g, r_e, and PQ series (so the
g_inf/n/k assumptions can be varied later without rebuilding). Verify every new source's
live free access before building on it, exactly as Phase 1 did, and log dead/paywalled
sources plus the substitute you used.

Produce a Phase 2 coverage report (coverage by year/asset class, where PQ had to fall
back to raw vs. adjusted volume, any source landmines hit) before stopping. Log this
session as `06_documentation/ai_conversations/session_010_*.md`, update
`DATA_DECISIONS_LOG.md` (continuing from wherever Part A left off) and
`06_documentation/time_log.md`. Commit and push to
github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end. Do not start Phase 3
without review.
```
