# Claude Code Kickoff Prompt — Session 025: Etherscan Pro Channel-2 + P2-2 Build

Paste the prompt below as the first message in a new Claude Code session opened with working
directory `C:\AFA_2027_QTM_Crypto`. Moazzam has purchased Etherscan API Pro (Standard Plan,
$199/month, 200k calls/day, activated 2026-06-30). The Pro key is already in `.api_keys.json`
under `"etherscan"`. This session is the direct payoff of that purchase: build Channel 2
(holding duration) at panel scale, and run the 16 BSC/Base/Avax paid-gated tokens (P2-2)
through the session-022 getLogs method.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Moazzam has purchased Etherscan
API Pro (Standard Plan: 200k calls/day, 10 calls/sec, all chains including BSC/Base/Avax).
The Pro key is in `.api_keys.json` under "etherscan". Before anything else:

1. Verify the key works and is Pro-grade: call `eth_blockNumber` on Ethereum AND a getLogs
   probe on BSC (chain 56) — if BSC returns data rather than "Free API access is not
   supported for this chain", the Pro upgrade is confirmed. Log the result explicitly; do
   not assume the key is upgraded without verifying.

Read before starting work:
- 04_code/DATA_DECISIONS_LOG.md Entries 24, 57–60 (Channel-2 design decisions, session-024
  budget measurement, assembled λ state)
- 06_documentation/SESSION024_STATUS_AND_NEXT_SESSION.md (Phase-2 worklist, gotchas)
- 03_data/SESSION024_FREE_BUILD_REPORT.md (what was built, what was measured)
- 04_code/phase1_channel2_holding.py and phase1_channel2_budget_probe.py (the engine and
  budget measurement already built in session 024 — extend, don't rewrite)
- 03_data/phase1/universe_lambda_channel_map.csv (1,306-row identification map from session
  022 — use to drive the P2-2 token list)
- 04_code/.api_keys.json (confirm "etherscan" key before any API call)

## Task A — P2-2: the 16 BSC/Base/Avax paid-gated Channel-1/3 tokens

These tokens were identified in session 022 as having ERC20Votes or staking contracts on
BSC/Base/Avalanche, but getLogs on those chains required a paid plan. Now that the Pro key
covers those chains, run them through the same session-022 pipeline:

Tokens: ALT, AWE, BAKE, BNX, CHEEL, EDG, ESPORTS, FORM, LINEA, MCT, MDX, OP, PONKE, TKO,
ZORA (Channel-3 candidates), TNC (Channel-1 candidate).

For each:
a. Pull its row from universe_lambda_channel_map.csv to get chain + contract address.
b. Read the verified contract source (getsourcecode — already cached in
   03_data/raw/etherscan_src/ if session 022 got it; re-fetch only if missing).
c. Confirm the mechanism via getLogs (same method as session 022/024). For Channel-3:
   confirm DelegateVotesChanged actually fires and is non-trivial. For TNC Channel-1:
   apply the full Entry-26 test (single escrow, amount-bearing, cross-check to live balance).
d. Build any that pass (same scripts as session 024: phase1_channel3_onchain_delegation.py
   for delegation, phase1_channel1_freebuild.py for any Channel-1 pass). Skip/log those
   that are DORMANT or fail the mechanism test — do not force builds.
e. Log verdicts and any builds in DATA_DECISIONS_LOG (continue from Entry 61).

## Task B — Channel 2 panel-scale build (the main event)

The engine (phase1_channel2_holding.py) was proven on MET in session 024. The budget probe
showed RAD (mid-size) needed 700+ calls and didn't complete on the free 100k/day cap. With
200k/day Pro, a mid-size token completes in one day; the full 793-token panel runs in ~3
days. Do this as a resumable, checkpointed build — do NOT try to do it in one session.

**Step B1 — scope the build:**
From universe_lambda_channel_map.csv, extract the 793 free-chain EVM tokens (those with
chain in Ethereum/Polygon/Arbitrum/Blast AND reachable=True). Cross-check against the
current lambda_panel.csv to identify which of those 793 already have ANY λ channel (exclude
them from Channel-2 build only if they already contribute on Ch1 or Ch3 — Channel 2 can
ADD to an existing asset's lambda). The correct logic: build Channel 2 for ALL 793 where
Transfer log history exists, regardless of existing channels — it widens the channel count.

**Step B2 — run the build, respecting the budget:**
- Use phase1_channel2_holding.py with the Pro key. The session-024 gotchas apply:
  checkpoint per token; delete poisoned checkpoints (getblocknobytime→None on last month);
  retry transient getLogs errors.
- Stay within 200k calls/day. Track consumed calls and checkpoint after each token so the
  build is resumable across sessions. Do NOT burn through the monthly quota in one run.
- Contract-holder screening (eth_getCode): already implemented in session 024 — use it.
  CEX EOA wallets are NOT separately screened (no paid label feed); document this as a
  named limitation ("CEX custodial wallets not screened; contract addresses excluded via
  eth_getCode") in the output and flag column. Do not attempt CEX screening with any free
  heuristic that could introduce worse bias than the known limitation.
- HODL metric: share of supply held by EOA addresses unmoved for ≥ 6 months at each
  month-end, as a fraction of circulating supply. Compute at monthly granularity
  (month-end block, same as the rest of λ).

**Step B3 — address-class hygiene check (spot validation):**
Before wiring into λ, run the MET validation again (it had a v2 migration muddying the
12m window per session-024 note — pick a cleaner single-deployment token to validate
against; CRV or AAVE are good candidates since we already have their Channel-1/3 series).
Confirm the contract-screen step still collapses the contamination to a sensible range.
If the validated HODL series looks economically reasonable (not 95%+ or 0.1% for a normal
governance token), proceed to wire into λ. If it looks degenerate, STOP and report — do
not silently fold bad data into the panel.

**Step B4 — wire into λ assembler:**
Extend phase1_assemble_lambda.py to accept channel `ch2_holding` as an input (same z-score/
equal-weight logic, do not change assembler structure — add an input, don't rewrite).
Re-run the assembler and report the new asset-month count, n_channels distribution, and
the share of asset-months that now have 2 or 3 channels (the cross-section depth improvement
is the headline metric for the paper's data section).

## Rules (unchanged)
- cmc_id joins only, never symbol.
- Entry-26 bar for any Channel-1 build: single contract, amount-bearing, cross-checked to
  live balanceOf at 0.0x% drift.
- DATA_DECISIONS_LOG.md append-only. Continue from Entry 61. One entry per major decision
  cluster (not one per token). Log the Etherscan Pro purchase itself as an entry (date,
  plan, what it unlocks, cost) — it is a data-sourcing decision.
- No additional paid subscriptions. Do not sign up for Nansen, Glassnode, CoinMetrics,
  Alchemy, or any other service.
- Track getLogs call budget actively. If the build is consuming calls faster than expected,
  checkpoint and STOP rather than blowing the monthly quota. Report consumed vs remaining.
- Run PYTHONUTF8=1 (the → print crash fix from session 024).
- Update 06_documentation/time_log.md. Log session as
  06_documentation/ai_conversations/session_025_*.md. Commit and push at end of session.

## Deliverables
1. P2-2 verdict table: all 16 tokens with chain, contract, verdict (BUILD/REJECT/DORMANT),
   reason. Any builds folded into λ.
2. 03_data/phase1/channel2_holding.csv: per-asset-month HODL-6m series for all tokens
   where the build completed this session (may be partial — document what completed).
3. Updated lambda_panel.csv with ch2_holding wired in for completed tokens. New
   asset-month count and n_channels distribution reported.
4. 03_data/SESSION025_PRO_BUILD_REPORT.md: parallel structure to SESSION024 report —
   what was built, what was deferred (tokens not yet completed in the channel-2 batch),
   budget accounting (calls consumed vs remaining monthly quota), any anomalies.
5. DATA_DECISIONS_LOG.md Entries 61+, time_log.md updated, session log written.
6. Commit and push.

STOP at end of session or when the daily call budget approaches its limit (whichever comes
first). If Channel 2 is not complete in one session, checkpoint and report how many tokens
were completed — the next session continues from the checkpoint. Do not start any other
Phase-2 items (NMR, KAIA, non-EVM) without review.
```
