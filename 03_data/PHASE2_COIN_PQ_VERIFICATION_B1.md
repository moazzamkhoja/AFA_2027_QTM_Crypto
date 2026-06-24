# Phase 2 — Coin PQ Source Verification (Step B1)

**Date:** 2026-06-24
**Session:** 013 (Claude Code / Opus 4.8), working dir `C:\AFA_2027_QTM_Crypto`
**Scope:** the bounded live-verification gate (B1) that `CLAUDE_CODE_PHASE2_PQ_BUILD_PROMPT.md`
requires **before** any coin-PQ extraction code. Per that prompt, B1 must STOP and report — not
guess — if Artemis is paid-only OR coverage is ambiguous for any coin material to the panel.

**Outcome: STOP-and-report condition met.** Artemis REST API is paid-only, and that leaves
**81 material coins** (peak market cap ≥ $1B) — including XRP, DOGE, LTC, BCH, XMR, ZEC, DASH,
ATOM, DOT — with **no valid free transacted-value PQ source**. The DeFiLlama + BTC fallback does
**not** cover the coin panel adequately. Pausing for a human decision on the coin tier.

---

## 1. What was verified live

### 1a. Artemis Settlement Volume — **PAID-ONLY for the REST API** (Rung 2 unavailable)
- Old API hosts: `api.artemisxyz.com` → **HTTP 410** ("no longer available, see docs.artemis.ai");
  `api.artemisanalytics.com` / `api.artemis.xyz` → **DNS/connection failure**. Confirms Entry 2's
  dead-API finding is still the state of the old endpoints.
- Current product (docs.artemis.ai → artemis.ai/docs, pricing at about.artemis.ai/pricing,
  read live this session): `settlement_volume` **does** exist as a standalone metric (alongside
  `chain_spot_volume`, `chain_nft_trading_volume`, `p2p_transfer_volume`) — so the *object* is the
  right one (Entry 32). **But REST API access is not in the free "Lite" tier.** Lite ("Free
  Forever") = Terminal + Sheets plugin only (100k ART calls/mo, Google-Sheets-bound), 3 CSV
  downloads/mo. **Pro is $300/mo and still does not list REST API access**; the "Artemis API"
  product has no free/standalone self-serve tier. There is **no scriptable, reproducible free REST
  path** to Settlement Volume.
- **Verdict: Rung 2 is closed for a reproducible pipeline unless API access is procured.**

### 1b. DeFiLlama chain DEX volume per coin — materiality split (Rung 1)
- `/overview/dexs/{chain}` verified live for every chain the coin panel maps to (134 chains,
  mapped via DeFiLlama `/v2/chains` `cmcId`→chain join; cache `_chain_dex_overview.json`).
- **Explicit materiality threshold:** a chain qualifies for Rung 1 iff its **30-day DEX volume ÷
  the coin's latest market cap ≥ 0.01** (i.e. on-chain DEX turnover ≥ ~1% of market cap per month,
  ≈12%+ annualized) — the test for "DeFi/DEX activity is a *material* share of the chain's real
  economy," not a bolted-on niche. Calibration check: BTC = 9×10⁻⁶ (fails by ~1000×, correctly
  degenerate); ETH = 0.143, SOL = 1.04, BNB = 0.27 (clearly material). The big payment/SoV coins
  all fall decisively below: XRP 0.0023, DOGE/LTC no DeFiLlama DEX series at all, BCH 0.0, XMR
  unmapped, ZEC/DASH unmapped.
- **Result: 49 of 633 coins are Rung-1 valid (40 of them material).**

### 1c. blockchain.com Charts API (BTC, Rung 3) — **CONFIRMED**
- `api.blockchain.info/charts/estimated-transaction-volume-usd` → HTTP 200, daily series
  **2010-08-28 → 2026-06-23** (1,440 sampled points; unsampled/daily also available). This is the
  *Estimated* Transaction Value series, which already **excludes change/return-to-sender outputs**
  (the classic UTXO change-inflation fix) — exactly the change-excluded object Entry 32 wanted.
- **BTC is cleanly covered at Rung 3.** It is the *only* coin with a confirmed ready-made native
  series; blockchain.com is BTC-specific and does not generalize to LTC/BCH/DOGE/XRP/etc.

---

## 2. Per-coin rung assignment (full table: `03_data/phase2_coin_rung_table.csv`)

| Rung | Coins | Material (peak ≥ $1B) | Source |
|---|---|---|---|
| **R1** — DeFiLlama chain DEX (non-degenerate) | 49 | 40 | ETH, BNB, SOL, ADA, TRX, AVAX, TON, NEAR, SUI, APT, STX, HBAR, ALGO, INJ, SEI, CELO, STRK, POL, FLR, GNO, … |
| **R3-BTC** — blockchain.com est. tx value | 1 | 1 | BTC |
| **GAP-R2** — would need Artemis (paid-only) | 81 | **81** | **XRP, DOGE, BCH, DOT, MATIC, LTC, VET, THETA, FIL, IOTA, ZEC, NEO, ATOM, XMR, ETC, DASH, FTM, BSV, XTZ, KAS, XEC, KSM, HNT, TIA, DCR, ENJ, XNO, …** |
| **NaN** — non-material, no free source (expected) | 502 | 0 | long tail of sub-$1B / dead coins |

**The blocker is the GAP-R2 row.** These are payment-/SoV-/app-chain coins whose real economic
throughput is *native settlement value*, not DeFi DEX volume. Their ladder option was Rung 2
(Artemis Settlement Volume) — now paid-only. Rung 3 for non-BTC chains = bounded native `value`
block iteration over a **recent window only** (Entry 32 / this prompt explicitly forbid full
multi-year per-chain iteration) — which **cannot** supply the multi-year monthly history NVT_GL's
trailing-CAGR `g` needs. So on free sources these coins have **no full-history transacted-value
series**. Note also **XMR (Monero) is a hard, not-a-source gap**: RingCT cryptographically hides
transaction amounts, so transacted value is unobservable in principle on any source.

---

## 3. Why this is a STOP (not a proceed)

The prompt's proceed-without-review escape hatch requires that "the DeFiLlama/BTC-fallback
combination covers the panel adequately." It does not: it covers 40 material smart-contract-platform
coins + BTC, but leaves **XRP (the 3rd-largest crypto by all-time peak), DOGE, LTC, BCH, XMR, ZEC,
DASH, ATOM, DOT** and 70+ other material coins uncovered. That is exactly the "coverage ambiguous
for a coin material to the panel (large market cap or long history)" STOP trigger, compounded by
the "Artemis paid-only" trigger. Guessing here — silently NaN-ing XRP/DOGE/LTC or silently dropping
them to Rung 4 (chain fees, a toll proxy already rejected on theory in Entry 30) — is precisely
what the prompt says not to do.

## 4. Options for the human decision (coin tier only — tokens are unblocked)

1. **Proceed with the covered panel; flag the gap (recommended default).** Build NVT_GL for the
   127 tokens (Part A, fully resolved) + 49 Rung-1 coins + BTC. Flag the 81 GAP-R2 material coins
   as **PQ = NaN, documented coverage gap** (consistent with the spec's "flag, don't guess").
   NVT_GL is most defensible where on-chain throughput is actually measurable; pure-payment coins
   without a free throughput series are flagged, not faked. No cost, no scope creep.
2. **Procure Artemis API** (paid; ~$300/mo Pro may still exclude REST — likely Enterprise/custom).
   Unlocks Settlement Volume for the GAP-R2 coins — the theoretically-correct object. Adds cost and
   a round-trip; would meaningfully widen coin coverage.
3. **Authorize a scoped search for free per-chain native series** (out of B1's named scope, hence
   flagged): e.g. XRPL payment volume via XRPL/xrpscan APIs; bitinfocharts/blockchair "sent-in-USD"
   for LTC/BCH/DOGE/DASH. Per-chain, uneven quality, more build time; would partially close the gap
   without paid access. (XMR remains impossible regardless.)

Recommendation: **Option 1 now** (build tokens + Rung-1 coins + BTC, flag GAP-R2), with Option 2/3
as a deliberate follow-up if the coin side needs to be widened for a result. This keeps the session
productive and the gap honestly documented rather than papered over.
