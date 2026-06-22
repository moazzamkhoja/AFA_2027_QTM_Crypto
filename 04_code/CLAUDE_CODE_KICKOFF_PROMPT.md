# Claude Code Kickoff Prompt — Phase 0 (Asset Universe)

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). Run Phase 0 to completion,
review the output, then come back for a kickoff prompt for Phase 1.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Before doing anything else,
read in full:

1. 04_code/DATA_SPECIFICATION.md — the full data specification. Don't skim it.
2. 04_code/DATA_DECISIONS_LOG.md — the append-only log you'll be writing to.
3. 05_paper/main.tex, Section 2 (the Locking Decision model) and Appendix A
   (Growth-Levelized NVT) — for the theoretical context behind the variables.

Your task right now is PHASE 0 ONLY, per Section 7 of the spec: build the asset
universe. Do not start Phase 1 (lambda channels) or any later phase in this session.

Deliverables for Phase 0:

1. A reproducible script (not a one-off manual pull, not hand-typed data) that builds a
   point-in-time monthly ranked universe of crypto assets from CoinGecko, DeFiLlama,
   and/or Artemis Analytics. Follow Section 2.1 exactly: rank by market cap each month
   using historical, point-in-time snapshots; an asset enters the panel the first month
   it's in the top 250 (this threshold is adjustable, report sensitivity if you change
   it); once in, it never leaves the panel even if it later falls out of the top 250,
   delists, or goes to zero. Before you build this, verify what these APIs actually
   support today (rate limits, whether a key is required, how far back historical
   snapshots go, whether delisted/dead coins are retrievable) — don't assume from
   general knowledge.

2. A classification table (coin vs. governance token) per Section 2.3, with the
   supporting evidence you used for each asset, and explicit flags for ambiguous or
   transition cases (e.g., an asset whose locking mechanism changed over time). The
   ETH proof-of-work-to-proof-of-stake transition in the spec is one illustrative
   example to check, not the only one — look for others as you go.

3. A coverage report: number of qualifying assets per month and per year across
   2015-08 through the most recent complete month. Call out where the panel is thin.
   Separately note how much further back pre-2015 native coins (BTC chiefly) could be
   extended, in case a coins-only robustness subsample becomes useful later.

4. Update 04_code/DATA_DECISIONS_LOG.md as you go, not at the end, for every deviation
   from the spec, every proxy substitution, and every threshold or judgment call.

When Phase 0 is done, stop. Summarize what you built, what the coverage report shows,
and any open questions or judgment calls that need a decision before Phase 1 starts.
Do not proceed past Phase 0 without that review.
```
