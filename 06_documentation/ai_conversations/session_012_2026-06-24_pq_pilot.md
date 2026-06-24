# AI Conversation Log — Session 012
**Date:** June 24, 2026
**Model:** Claude (Anthropic) via Claude Code (Opus 4.8)
**Human:** Moazzam Khoja
**Working dir:** `C:\AFA_2027_QTM_Crypto`

---

## Topic: Phase 2 PQ — Etherscan Transfer-Volume Feasibility Pilot

### Summary
Executed the bounded diagnostic pilot defined in
`04_code/CLAUDE_CODE_PHASE2_PQ_PILOT_PROMPT.md` (written by Cowork session 011, which had no
network route to Etherscan). Goal: get *real numbers* on whether raw-Transfer-log transacted-value
PQ can be built at panel scale on the free Etherscan key, or whether DeFiLlama's reported volume
should be the working PQ source. Pulled all `Transfer` events (no counterparty filter) for UNI and
AAVE over May 2026, dollarized, cross-checked against DeFiLlama, and extrapolated. Outcome: cost is
*not* the binding constraint — **validity** is. Recommendation: Option (B), DeFiLlama reported
volume. Full write-up in `03_data/PHASE2_PQ_PILOT_REPORT.md`; decision in Decisions Log Entry 31.

---

## Key Discussion Points

### 1. Setup correction — the "two UNIs" problem
The prompt named "UNI (Uniswap governance token)". `universe_panel.csv` has **two** `UNI` rows:
cmc_id **4113** (a dead 2019 namesake, last observed 2020-12, price ~$1.43 — not Uniswap) and
cmc_id **7083** (the real Uniswap UNI, observed through 2026-05). Used 7083. AAVE = 7278 (matches
the Channel-1 escrow table). Both verified `status='observed'` for the window. Window = May 2026
(most recent complete month; panel max `month_end` = 2026-05-31).

### 2. Mechanism and a quick probe
Reused the `phase1_channel1_evm_locks.py` `getLogs` recursive block-bisection on the 1,000-log cap,
with the topic1/topic2 address filter dropped (all transfers, not escrow-only). A one-day probe
(UNI, 2026-05-15) returned 3,530 transfers in just **9 calls / 8.7 s** — immediately showing the
recent-window regime is cheap, contra a naive read of Entry 24 (which was about full multi-year
enumeration, a different regime). Processed day-by-day for clean per-day measurement + resumable
checkpoints + a per-token call/time budget guard.

### 3. Measured cost
- UNI: 133,350 transfers, **381 getLogs calls**, max depth 6, 345.6 s (0.91 s/call).
- AAVE: 116,910 transfers, **309 getLogs calls**, max depth 5, 305.1 s (0.99 s/call).
- ~345 calls/token-month, ~11 calls/day, ~0.9 s/call — trivial against the free 5 req/s & 100k/day
  caps. Refines Entry 24: the wall is full *multi-year* history, not a recent window.

### 4. The decisive finding — wrong quantity, not just cost
- **UNI** token-transfer volume = **$0.79B** (May) vs DeFiLlama **Uniswap DEX swap volume =
  $36.75B** → swap volume **46.6× larger**, daily correlation only **0.30**. Summing a governance
  token's own Transfer events does not measure the protocol's swap throughput (swaps move paired
  assets through pool contracts, not the gov token).
- **AAVE** raw sum came out **physically impossible** ($8.2×10¹⁹ vs a 15.4M-token supply): **6**
  transfers carried sentinel-scale values, one of **10¹⁸ tokens = 6.5×10¹⁰× supply**. Cleaned
  (outliers > supply removed) = **$2.75B**, still unrelated to Aave lending throughput (loans are
  in USDC/ETH/etc.). Extreme form of the spec §6 wash/internal-churn caveat.
- The correct on-chain swap-volume measure would require enumerating each protocol's pool `Swap`
  events — i.e. re-implementing DeFiLlama's adapter layer per protocol — out of scope on a free key.

### 5. Extrapolation
At ~345 calls/token-month, 0.9 s/call, 100k/day cap: 1 token full history ~23.5k calls (~6 h);
1 recent month × 127 DeFi-slug tokens ~44k calls (~11 h); **full history × 127 tokens ~1.75M calls
(~17.5 days)**; × 241 slugged assets ~3.3M (~33 days). Recent window or single flagship = feasible;
full-panel multi-year history = infeasible as a routine build.

### 6. Decision
**Option (B):** DeFiLlama reported sector-appropriate volume as the working PQ source; TVL + fees as
side diagnostics (Entry 30); raw Etherscan logs as occasional spot-check only. Ruled out (A)
[panel-scale raw] on validity + cost; ruled out pure (C) [flagship raw as a *source*] because it
still measures the wrong object — keep flagship raw only as a spot-check. Coin-side PQ (ETH/BTC
native transfers) was not in this pilot and faces the harder archive-state wall (Entries 21/24).

---

## Deliverables this session
- `03_data/PHASE2_PQ_PILOT_REPORT.md` — full report (cost, dollarization, cross-check, extrapolation, rec).
- `04_code/phase2_pq_pilot.py`, `04_code/phase2_pq_pilot_diag.py` — pilot + noise diagnostic.
- `03_data/raw/phase2_pilot/*` — cached numbers (gitignored; no large raw-log dumps committed).
- Decisions Log **Entry 31**; this log; `time_log.md` updated.

## Open / handoff
- Phase 2 build remains **paused pending human review** of the (B) recommendation. Do not build
  `phase2_pq.py` on raw Etherscan volume. Once (B) is confirmed, build PQ on DeFiLlama volume,
  sector-routed, with TVL/fees side columns.
