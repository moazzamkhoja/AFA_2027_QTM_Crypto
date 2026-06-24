# Phase 2 (NVT_GL) — Status & Open PQ-Definition Decisions

**Date:** 2026-06-24
**Prepared by:** Claude Code session 010 (Opus 4.8), for human review in Cowork
**Status:** Part A (Phase 1 finishing touches) **complete and committed**; Part B (Phase 2
NVT_GL build) **paused at the PQ-definition decision point** pending the calls below.

> **Why this memo exists.** Building NVT_GL = MC / PQ\* requires first fixing what **PQ**
> (economic throughput) actually *is*, per asset. The human's stated instinct (TVL for
> tokens, on-chain transaction volume for coins) diverges from both the spec and what is
> free-data feasible in two specific ways. Rather than silently pick, this memo lays out the
> divergence, the feasibility wall, and a recommendation, so the call is made on the record
> (spec §0: "flag, don't guess") and can be discussed where the full project context lives.

---

## 1. Part A — DONE this session (committed)

All five required Phase 1 finishing touches plus the optional item are resolved. Full detail
in `04_code/DATA_DECISIONS_LOG.md` **Entry 29** and the updated
`03_data/PHASE1_COVERAGE_REPORT.md`.

| # | Item | Outcome |
|---|---|---|
| A1 | Finish ETH staking series | ✅ Complete: **66 months, 2020-12 → 2026-05**, cumulative deposits 2.17M → 86.16M ETH (ratio 0.019 → 0.714). Cumulative-deposit method kept as-is; no post-Shapella netting (new scope). Documented as monotone upper-envelope proxy. |
| A2 | Channel 2 free BTC coin-age check | ✅ Re-checked live. mempool.space/blockstream: no aggregate coin-age. blockchair: only a current 24h CDD snapshot. bitcoin-data.com/bgeometrics: real free CDD API **but capped to a trailing ~4 years and 10 req/hour** — can't reach pre-2020 depth. **Stays a documented gap; no paid source procured.** |
| A3 | Confirm N=250 | ✅ Confirmed, no change. Coin-side gap is a *source* problem, not a universe-size problem. |
| A4 | Revisit 16 gray-zone classifications | ✅ All 16 stay `other`. None has a security-staking lock (only the 6 curated escrows were built). OP/MNT/RPL/SSV get a *voting*-λ but remain `other` (governance ≠ security lock). Evidence unchanged. |
| A5 | Reconcile coverage-report inconsistency | ✅ Fixed. Final figures **1,374 asset-months, 52 distinct assets** (the old 1,308 vs 1,326 mismatch is resolved; +66 = ETH's now-complete series). Every section reconciled. |
| A6 | (Optional) enrich identity map from CMC `platforms[]` | ⏸️ Deferred (explicitly optional, not required before Part B). |

**λ index final state:** 1,374 observed asset-months, 52 assets, 2020-08 → 2026-05.
1-channel 1,121 (voting-only 924, staking-only 197 incl. ETH's 66) + 2-channel 253 (the 6
vote-escrow tokens). By class: token 43, coin 5 (ETH, GNO, SAFE, JOE, DYDX), other 4 (SSV,
RPL, MNT, OP).

---

## 2. Part B — Phase 2 NVT_GL: what's already verified

`NVT_GL = MC / PQ*`, with PQ\* a levelized (PMT-style) present-value annuity of projected
throughput PQ (spec §4). Inputs: MC, PQ, g (PQ CAGR), r_e (CAPM-style discount rate),
g_inf (constant), n (horizon).

**Sources verified live and free this session (2026-06-24):**

- **MC** — already in `universe_panel.csv` (Phase 0 CMC backbone). ✅
- **DeFiLlama fees API** — free, keyless, historical, confirmed working:
  - Protocol-level fees `/summary/fees/{slug}?dataType=dailyFees` (e.g. Uniswap: 2,790 daily
    points back to 2018-11).
  - Chain-level fees `/overview/fees/{chain}` (e.g. Ethereum: 3,007 daily points back to
    2018-03); **339 chains** and **2,306 fee-bearing protocols** available.
  - DeFiLlama TVL is likewise free/keyless/historical (its core product, best coverage).
- **Coverage reality:** only **241 / 1,939** observed assets carry a DeFiLlama slug (sparse
  registry, per Entry 22): 127/448 tokens, 70/633 coins, 44/858 other. So PQ density will,
  like λ, be a DeFi-token + major-L1 phenomenon, thin in the early sample and the long tail.

The two decisions below are the **only** things blocking the build.

---

## 3. DECISION 1 — Token PQ: throughput flow vs. TVL

**Human instinct:** use **TVL** for tokens.

**The tension.** PQ in this paper is not "economic size" — it is **transaction throughput**,
straight from the quantity identity `M·V = P·Q` (PQ = nominal flow of transactions), and the
paper's Appendix A levelizes "projected transaction throughput." **TVL is a *stock*** (value
sitting locked), not a flow. If TVL goes in the denominator, `MC/TVL` is a legitimate and
familiar DeFi multiple — but it is **not NVT** in the paper's sense and would not carry the
meaning H2/H3 place on NVT_GL. The spec §4.1 agrees: for tokens it asks for "DEX volume,
total fees, or active-user counts" — all flows.

| Option | What it means | Trade-off |
|---|---|---|
| **(A) Fees / DEX volume `[RECOMMENDED]`** | PQ = monthly protocol fees (or DEX volume) from DeFiLlama. **Also store TVL as a side column** for a later `MC/TVL` robustness cut. | Spec- and theory-aligned (a flow). Free, historical. TVL kept available without a rebuild. |
| **(B) TVL as the denominator** | PQ = TVL. | Cleanest DeFiLlama coverage, but conceptually a stock; turns NVT_GL into an MC/TVL multiple, departing from the paper's NVT definition. |
| **(C) Both as parallel denominators** | Build two NVT_GL series (fees-based and TVL-based). | Maximal optionality; ~2× the PQ plumbing and two coverage stories to maintain. |

**Recommendation: (A).** Keeps NVT_GL faithful to the paper while capturing TVL cheaply for
robustness. (Note: the project's own time-log already records a 2026-06-10 "TVL
disambiguation" discussion — worth recalling that context here.)

---

## 4. DECISION 2 — Coin PQ: chain fees vs. true on-chain transfer volume

**Human instinct:** on-chain transactions denominated in the coin, tracked from the
explorer (Etherscan) via the contract address.

**Where we agree:** the spec §4.1 *also* wants "on-chain transaction (transfer) volume" for
coins. This is the ideal.

**The feasibility wall (same one Phase 1 hit and you already approved — Entries 21/24):**

- For a **native coin** (ETH, BTC, SOL…), value transfers are **not** `Transfer` event logs
  — they live in the `value` field of every transaction in every block. Summing them across
  history requires **archive** access, which Entry 21 confirmed is paywalled on every free
  RPC and *silently latest-only* on free Etherscan.
- For an **ERC-20**, you *can* sum `Transfer` logs with the contract address (the human's
  point) — but that is the asset's **entire** transfer set (tens of millions of events for a
  major token), versus the *targeted* escrow-only logs Channel 1 used. Entry 24 flagged this
  as "orders of magnitude beyond" the free rate-limited key. Feasible for one token's recent
  window; **not** for 250 assets × 11 years.
- Raw transfer volume is also the classic NVT weak point (wash-trading / exchange-internal
  churn inflate it — spec §6).

| Option | What it means | Trade-off |
|---|---|---|
| **(A) DeFiLlama chain fees `[RECOMMENDED]`** | PQ(coin) = monthly chain-level gas fees (USD) from DeFiLlama. | Free, keyless, monthly history to ~2018 for major chains. Gas fees = revealed on-chain economic throughput; dodges wash-trade contamination. A documented proxy, not raw transfer volume. |
| **(B) True on-chain transfer volume** | Reconstruct per-chain transfer value from explorers. | Matches the spec ideal but hits the free-archive + rate-limit wall above; feasible only for a small curated subset, heavy even then; early-sample still missing. |
| **(C) Chain fees + flagship volume cross-check** | Chain fees across the panel; *additionally* attempt true on-chain volume for ETH (and maybe BTC) to sanity-check the fees proxy. | Best of both for a couple of names; bounded extra effort; the cross-check is informative even if it can't scale. |

**Recommendation: (A)** for the panel, optionally **(C)** if a flagship cross-check is wanted
on the record.

---

## 5. Other Phase 2 parameters (no decision needed now, flagged for awareness)

These follow the spec defaults and are built as **robustness parameters**, not estimated —
listed here only so nothing is a surprise during the build:

- **g** — trailing 3-year CAGR of PQ; shorter window flagged per asset where <3y history.
- **r_e** — CAPM-style discount rate: asset beta vs. a crypto market index (cap-weighted, or
  BTC as a simple alternative) + a risk-free rate. **Named distinctly in code from the
  Phase 3 portfolio-level CAPM** (spec §4.1 caveat). Note: crypto's realized market premium
  is extreme, so r_e values will be sensitivity-flagged.
- **g_inf** — single macro-anchored constant in 2–4% (default 3%); robustness param.
- **n** — horizon, default 10 years; robustness param.

Output will include NVT_GL **plus** the underlying g, r_e, and PQ series, so g_inf/n/k can be
varied later without rebuilding (spec §4.2).

---

## 6. What I need from the Cowork discussion

1. **Decision 1 (token PQ):** A, B, or C?  *(rec: A)*
2. **Decision 2 (coin PQ):** A, B, or C?  *(rec: A, or C if a flagship cross-check is wanted)*
3. Any objection to the §5 parameter defaults before I build.

Once these are set I will build `phase2_pq.py`, `phase2_market_index.py` (for r_e), and
`phase2_nvt_gl.py`, produce the Phase 2 coverage report, and log it — without starting
Phase 3 before review.
