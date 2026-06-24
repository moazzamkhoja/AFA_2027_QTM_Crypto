# Claude Code Pilot Prompt — PQ Definition: Etherscan Transfer-Volume Feasibility Pilot

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). This is a bounded **diagnostic
pilot**, not a full Phase 2 build — it answers one empirical question before Decision 1 and
Decision 2 in `06_documentation/PHASE2_PQ_DECISION_STATUS.md` can be finalized.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 0/0B/1 are complete; Phase 2
(NVT_GL) is paused on a PQ-definition question. Before doing anything else, read in full:

1. 06_documentation/PHASE2_PQ_DECISION_STATUS.md — the original Decision 1/2 framing
   (recommended fees for both coins and tokens; now superseded, see #2).
2. 04_code/DATA_DECISIONS_LOG.md Entry 30 — the Cowork-side theoretical resolution: fees is
   REJECTED as the PQ proxy. PQ = P·Q = nominal value of goods/services transacted (a flow) —
   fees are the cost/toll of facilitating that transaction, not the transaction's value
   itself, which is structurally the same error as treating a government's tax revenue as a
   proxy for GDP. TVL is also rejected as PQ (it's the capital stock that enables activity —
   an AMM's pooled inventory, a lending pool's loanable funds, a staking protocol's AUM — not
   the activity itself). The corrected target is **transacted value**: swap/DEX volume for
   AMMs, loan-origination/borrow flow for lending, notional volume for derivatives —
   sector-appropriate via the existing `sector` field in `03_data/classification_table.csv`
   (Entry 16). TVL and fees are demoted to side-column diagnostics (capital-stock control;
   cost-of-intermediation), not PQ itself.
3. 04_code/phase1_channel1_evm_locks.py — the existing, working Etherscan `getLogs`
   Transfer-log pattern (recursive block-range bisection on the API's 1,000-log-per-call
   cap). This pilot reuses that exact mechanism with one change: NO counterparty-address
   filter (you want ALL transfers of the token, not just transfers to/from one escrow).

## Why this pilot exists

The open question is **scale**, not mechanism. Channel 1's escrow approach is fast because
filtering for one specific counterparty address is sparse — most blocks have zero matching
logs. Pulling every Transfer event for an actively-traded token removes that filter, so the
same 1,000-log cap will be hit far more often, forcing much finer block-range bisection.
Entry 24 found full-supply Transfer enumeration "orders of magnitude beyond" the free
rate-limited key for a *different* purpose (HODL/coin-age, full multi-year history) — but
that finding has never been re-tested for *this* purpose (a recent-window swap-volume proxy)
or quantified with real numbers. The Cowork session that produced this prompt has no network
route to api.etherscan.io (confirmed directly, sandbox egress is allowlisted), so it could not
get those numbers itself. Get real numbers instead of extrapolating.

## What to do

Pick **two** representative tokens already in the universe with active trading and DeFiLlama
coverage: **UNI** (Uniswap governance token) and **AAVE** (cmc_id 7278, already in the
Channel-1 escrow table). Verify both are in `universe_panel.csv` with `status='observed'`
before proceeding.

For each token, over a recent, bounded **30-day window** (most recent complete month):

1. **Pull all Transfer events, no counterparty filter.** Same `getLogs` mechanism as
   `phase1_channel1_evm_locks.py` (topic0 = Transfer signature, address = token contract,
   fromBlock/toBlock = the 30-day block range), but drop the topic1/topic2 address filter.
   Reuse the existing recursive bisection on the 1,000-log cap.
2. **Record, precisely:** total API calls made, total wall-clock time, total raw Transfer
   event count, max bisection depth reached. If the call count or time balloons to a point
   where extrapolating to full multi-year history × the relevant token universe is clearly
   infeasible, you can stop early for that token and report the partial numbers — don't burn
   the whole rate-limit budget proving a point that's already clear, but say explicitly what
   "infeasible" means numerically (e.g. "X calls/token/month implies Y calls for the full
   panel, which would take Z hours even at the rate limit").
3. **Dollarize.** Sum raw transfer amounts (scaled by token decimals) by day, multiply by
   that day's USD price (already in `universe_panel.csv` from the Phase 0 CMC backbone) to
   get a daily dollar-transfer-volume series for the 30-day window.
4. **Cross-check against DeFiLlama.** Pull DeFiLlama's reported DEX/swap volume for the same
   protocol over the same 30-day window (verify the correct live endpoint, don't assume it).
   Compare the two series: ratio, correlation, and whether raw-Transfer-log volume is a
   multiple of DeFiLlama's reported volume (expected, since routing hops, wrapping, and
   exchange-internal transfers inflate raw Transfer counts — quantify the multiplier, don't
   just note that it exists).
5. **Extrapolate, with real numbers.** From the measured 30-day call count, estimate calls
   needed for (a) that token's full history (since launch/DeFiLlama-coverage start) and (b)
   scaling to however many tokens in the universe would need this approach (DEX/governance
   tokens with no better source). State plainly whether full-panel raw-Transfer-volume PQ is
   realistically buildable on the free rate-limited key, or should be ruled out in favor of
   DeFiLlama's own reported volume/fees series (with raw-Transfer-log spot-checks as a
   periodic sanity check rather than the primary source).

## What NOT to do

This is a diagnostic pilot, not Phase 2. Do **not** build `phase2_pq.py`, `phase2_nvt_gl.py`,
or attempt full-history/full-panel extraction. Do not commit any large raw-log dumps — cache
only what's needed to support the numbers in your report, same caching discipline as Phase 1.

## Deliverable

Write `03_data/PHASE2_PQ_PILOT_REPORT.md`: the measured call counts/timing for both tokens,
the dollarized 30-day volume series, the DeFiLlama cross-check and noise-multiplier estimate,
the full-panel extrapolation, and a clear recommendation — (A) raw Etherscan Transfer-log
volume is buildable at panel scale, (B) it is not, use DeFiLlama's reported volume/fees as the
working PQ source with TVL as a side column, or (C) something in between (e.g. buildable for a
small curated flagship subset only). Log this session as
`06_documentation/ai_conversations/session_012_*.md` (011 is the Cowork session that produced
this prompt), continue `DATA_DECISIONS_LOG.md` from Entry 31, and update
`06_documentation/time_log.md`. Commit and push to
github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end. Stop after the report —
do not resume the Phase 2 build until this is reviewed.
```
