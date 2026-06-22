# Claude Code Kickoff Prompt — Phase 1 (λ Channels)

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). Run Phase 1 to completion,
review the output, then come back for a Phase 2 kickoff prompt.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 0 (asset universe) is
complete. Before doing anything else, read in full:

1. 04_code/DATA_SPECIFICATION.md — Sections 1, 3 (the λ index), and 7 (phasing).
2. 04_code/DATA_DECISIONS_LOG.md — the append-only log (9 entries so far); you'll add to it.
3. 06_documentation/PHASE0_TO_PHASE1_TRANSITION.md — the handoff brief: repo state, stable
   keys, what Phase 1 must produce, and verified source pointers.
4. 06_documentation/PHASE0_SESSION_STATUS.md — what Phase 0 built and the open questions.
5. 05_paper/main.tex Section 2 (the Locking Decision model) for the theory behind λ.

Your task is PHASE 1 ONLY, per Section 7 of the spec: construct the λ locking/conviction
index per asset-month. Do not start Phase 2 (NVT_GL) or later in this session.

Build on the frozen Phase 0 universe — do not rebuild it. Join everything on `cmc_id`
(never `symbol`). Compute λ only for `status='observed'` asset-months in
03_data/universe_panel.csv; leave `carried_forward` tails alone.

Deliverables for Phase 1:

1. A reproducible script (cache raw API pulls, like Phase 0 did) producing a per-asset-
   month table of the three λ channels and the combined λ_t:
   - Channel 1 — staking/locking ratio (staked-or-locked / circulating-or-total).
   - Channel 2 — holding duration (on-chain HODL/coin-age proxy; document the exact
     computation and limits per chain).
   - Channel 3 — voting engagement (voters / eligible supply, monthly).
   λ_t = equal-weighted average of the standardized (z-scored within each monthly cross-
   section) values of whichever channels are observable for that asset-month. Do NOT
   impute missing channels — average only over channels that exist, and record how many
   and which contributed.

2. Respect time-varying mechanisms: read staking_start / transition_note from
   03_data/classification_table.csv (e.g. ETH has no staking channel before 2020-12-01).
   Watch for and log other PoW→PoS or mechanism changes you encounter, with dates.

3. Before building each channel, VERIFY the current free access of every source you plan
   to use (per-chain explorers, beaconcha.in-style staking dashboards, DeFiLlama locked
   supply, Snapshot/Tally/Boardroom for voting) — don't assume from general knowledge.
   Log dead/paywalled sources and the proxy you used instead.

4. A Phase 1 coverage report: per-asset-month channel-availability breakdown (how many of
   the three channels are populated, by year and by asset class), where each channel is
   thin or absent, and which hypotheses that gates. Update DATA_DECISIONS_LOG.md as you
   go, not at the end. Log this session as 06_documentation/ai_conversations/
   session_007_*.md and update 06_documentation/time_log.md.

When Phase 1 is done, stop. Summarize what you built, what the channel-availability report
shows, and any open questions before Phase 2. Commit and push to
github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end. Do not proceed past
Phase 1 without review.
```
