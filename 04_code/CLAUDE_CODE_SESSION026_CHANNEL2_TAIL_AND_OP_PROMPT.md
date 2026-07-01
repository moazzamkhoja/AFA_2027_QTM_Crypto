# Claude Code Kickoff Prompt — Session 026: Channel-2 Tail + OP Delegation

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`.

Context: Session 025 built Channel-2 for 197 tokens (≤3,000 holders) and P2-2 delegation for
5 tokens. λ is now 6,097 asset-months / 288 assets. The single biggest remaining λ gain is
adding ch2 to the 72 tokens that already have ch1 or ch3 — especially the 4 with BOTH ch1
and ch3 (CVX, SUSHI, FRAX, GMX), which become **3-channel assets** the moment ch2 lands. All
of these were deferred by the session-025 HOLDER_MAX=3,000 metadata filter. OP delegation
(46,974+ events, killed at >80 min) is the one unfinished P2-2 item.

---

```
You're working in the AFA 2027 QTM Crypto research repo. λ is currently 6,097 asset-months
/ 288 assets (session 025, Entry 64). The Etherscan Pro key (200k calls/day) is in
`.api_keys.json` under "etherscan". Two tasks this session, in order.

## Required reading before starting

- 04_code/DATA_DECISIONS_LOG.md Entries 59, 62–64 (Channel-2 design, P2-2 results, session
  025 close-out)
- 03_data/SESSION025_PRO_BUILD_REPORT.md (full session 025 account — read entirely)
- 04_code/phase1_channel2_panel.py (the panel builder — extend, don't rewrite)
- 04_code/phase1_channel3_onchain_delegation.py (the delegation builder)
- 03_data/phase1/_channel2_sizes.csv (793 tokens sized; the deferred tail starts at
  holder_count > 3,000)
- 03_data/phase1/lambda_panel.csv (current λ panel — use to identify priority tokens)

## Priority token list (derive this before starting work)

From `lambda_panel.csv`, identify tokens with ch1 OR ch3 but NO ch2. Cross-reference against
`_channel2_sizes.csv`. This is the priority ordering for Task B:

**Tier 1 — 3-channel targets (already have BOTH ch1 AND ch3):**
CVX (31k holders), SUSHI (127k), FRAX (18k), GMX (299k)
Adding ch2 to these creates the first 3-channel observations in the panel.

**Tier 2 — high-value single upgrades (large governance/staking tokens):**
DDX (3k), ORBS (9k), RPL (12k), LQTY (14k), XAN (13k), API3 (24k), CAKE (21k),
AAVE (200k), CRV (100k), ENS (68k), LDO (65k), ARB (64k), UNI (385k),
COMP (220k), GRT (173k), BAL (49k), YFI (52k), PENDLE (73k), EIGEN (223k),
BLAST (273k), ENA (98k), WLFI (100k), GNS (21k), MNT (30k), CVX (31k), BAL (49k)

**Explicit skip — too large for any practical build:**
HEX (cmc_id 5015): 9,054,606 holders / ~724k getLogs calls. Do not attempt. Log as
permanently deferred in DATA_DECISIONS_LOG (the HEX Channel-2 gap is an acknowledged
limitation — its staking is already captured in ch1, so the absence of ch2 is a minor gap).

## Task A — OP delegation (block-windowed incremental fetch)

OP (cmc_id 11840, Optimism chain 10, ERC20Votes) was verified firing in session 025 (46,974+
`DelegateVotesChanged` events confirmed) but the full history download was killed at >80 min
due to volume. The fix is a block-windowed fetch.

a. Add a `BLOCK_WINDOW` parameter to `phase1_channel3_onchain_delegation.py` (or a separate
   OP-specific incremental script). Default 50,000 blocks per window; tune down if needed.
b. Fetch DelegateVotesChanged in windows from block 0 to current, stitching results. Store
   the raw event list in a checkpoint so the full replay doesn't re-fetch on rerun.
c. From the complete event list, replay the running-balance logic (same as all other
   delegation builds): track each delegate's latest `newBalance` via DelegateVotesChanged,
   sum at each month-end block = delegated weight outstanding, ÷ circulating supply.
d. The `DELEG_CAP` guard added in session 025 prevents a future repeat of this. For OP's
   backfill specifically, the guard must be lifted or set very high (OP is a verified
   build — just slow).
e. Fold the resulting series into `channel3_onchain_delegation.csv` (same schema) and
   re-run `phase1_assemble_lambda.py`. OP already has ch3_voting (Snapshot); this is the
   ch3_delegation sub-channel, which is governance-channel-waterfall: OP stays on Snapshot
   turnout as its primary (role=cross_check for the delegation series). Do NOT add OP's
   delegation as a second governance input to λ — the waterfall rule from Entry 57 applies.
f. Log in DATA_DECISIONS_LOG (Entry 65): OP delegation completed, method, event count, ratio.

## Task B — Channel-2 tail (>3,000 holders, priority-ordered)

The engine is already built (`phase1_channel2_panel.py`) and the per-token checkpoints in
`03_data/raw/phase1_onchain/holding/` let completed tokens re-aggregate instantly without
re-fetching. DO NOT re-run tokens already completed in session 025 — load their checkpoints
and skip.

**Step B1 — run the tail in priority order:**
Set `HOLDER_MAX` high enough to include the Tier 1 and Tier 2 tokens (start with
`HOLDER_MAX=250000` which covers everything except UNI, COMP, EIGEN, BLAST, GMX). Run
smallest-first within the worklist. Monitor calls/wall-clock and checkpoint.

The key targets to reach this session (in order of value):
1. CVX, FRAX, SUSHI, GMX → 3-channel assets (highest priority)
2. DDX, ORBS, RPL, LQTY, XAN, API3, CAKE → moderate size, ch1 governance tokens
3. CRV, AAVE, LDO, ENS, BAL, YFI, GNS, MNT, CVX, PENDLE → large, high-visibility tokens
4. ARB, EIGEN, BLAST, ENA, WLFI, UNI, COMP, GRT → very large, if budget allows

If the daily budget approaches DAILY_CAP before completing all tiers, checkpoint and stop.
Report how far down the priority list you reached.

**Step B2 — data integrity check (the overnight-outage lesson):**
Before aggregating, verify no new checkpoints have the network-failure corruption signature
(a checkpoint that shows 0 transfers for a mid-history block range on a token known to have
volume). The `_robust_getlogs` fix from session 025 should prevent this, but verify
explicitly by checking that completed tokens' checkpoint transfer counts are plausible
(not suspiciously low for large tokens). Delete and re-fetch any suspect checkpoint.

**Step B3 — aggregate and assemble:**
Re-run `phase1_channel2_panel.py --aggregate` to rebuild `channel2_holding.csv` from all
checkpoints (session 025 + session 026). Then re-run `phase1_assemble_lambda.py` to fold
the updated ch2 into `lambda_panel.csv`.

Report the new asset-month count, n_channels distribution, and specifically:
- How many 3-channel asset-months now exist?
- Which assets achieved 3-channel coverage?
- What is the new 2+ channel share?

**Step B4 — per-asset screened HODL-6m sanity check on large tokens:**
For any Tier 1 or large Tier 2 token newly completed, spot-check its screened HODL-6m
series looks economically reasonable (not 95%+ or 0.1% every month). If a series looks
degenerate, DO NOT fold it into λ — log as anomaly and report.

## Rules (unchanged)
- cmc_id joins only, never symbol.
- Entry-26 bar for any Channel-1 build (none here, but carry the rule).
- DATA_DECISIONS_LOG.md append-only. Continue from Entry 65. One entry per major decision
  cluster. Log: OP delegation (65), Channel-2 tail results including 3-channel count (66),
  session close-out with new λ count (67).
- No additional paid subscriptions.
- Track getLogs call budget. STOP and checkpoint before hitting DAILY_CAP (leave 20k
  headroom). Per-token checkpoints make every stop resumable.
- Run PYTHONUTF8=1.
- Update 06_documentation/time_log.md. Log session as
  06_documentation/ai_conversations/session_026_*.md. Commit and push at session end.

## Deliverables
1. OP delegation series in `channel3_onchain_delegation.csv`; role=cross_check (NOT added
   to λ as a channel per the governance waterfall rule).
2. Updated `channel2_holding.csv` with all newly completed tail tokens.
3. Updated `lambda_panel.csv` with new ch2 additions + OP delegation cross-check noted.
4. New λ asset-month count, n_channels distribution, **first 3-channel asset list**.
5. `03_data/SESSION026_TAIL_BUILD_REPORT.md` (parallel structure to SESSION025 report).
6. DATA_DECISIONS_LOG Entries 65–67. time_log.md updated. Session log written.
7. Commit and push.

STOP at end of session or when DAILY_CAP approaches. If Channel-2 tail is not fully
complete, checkpoint and report how many priority-tier tokens were completed. Do not start
other Phase-2 items (NMR, KAIA, non-EVM, Phase 2c NVT_GL) without review.
```
