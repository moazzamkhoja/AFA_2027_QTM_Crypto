# Phase 2 PQ Pilot — Etherscan Transfer-Volume Feasibility

**Date:** 2026-06-24
**Session:** 012 (Claude Code / Opus 4.8), working dir `C:\AFA_2027_QTM_Crypto`
**Scope:** Bounded diagnostic pilot answering one empirical question before Decision 1/2 in
`06_documentation/PHASE2_PQ_DECISION_STATUS.md` (as superseded by `DATA_DECISIONS_LOG.md`
Entry 30) can be finalized. **Not** the Phase 2 build — `phase2_pq.py` / `phase2_nvt_gl.py`
were not built and no full-history/full-panel extraction was attempted.
**Code:** `04_code/phase2_pq_pilot.py` (measurement), `04_code/phase2_pq_pilot_diag.py`
(noise/outlier diagnostic). Cached outputs in `03_data/raw/phase2_pilot/`.

---

## 0. Bottom line

**Cost is not the binding constraint — *validity* is.** Pulling every `Transfer` event of a
**governance token** (UNI, AAVE) over a recent month is cheap and easy on the free key
(~345 calls/token-month, ~5½ min). But the resulting series is **not the protocol's transacted
value**:

- **UNI** token-transfer volume = **$0.79B** for May 2026, while DeFiLlama's reported **Uniswap
  DEX swap volume = $36.75B** — the swap volume is **46.6× larger**, and the daily series
  correlate only **0.30**. The UNI token's own transfers are a small, weakly-related quantity,
  not Uniswap's throughput. (Swaps move the *paired* assets through *pool* contracts; they do
  not move the UNI token.)
- **AAVE** raw token-transfer sum came out **physically impossible** ($8.2×10¹⁹, i.e. ~10¹⁸
  AAVE against a 15.4M-token supply) — **6 transfers** carried non-economic sentinel values, one
  of **10¹⁸ tokens = 65 billion× the entire supply**. After scrubbing those, clean volume =
  **$2.75B**, which is *still* governance-token movement, unrelated to Aave's lending throughput
  (loans are denominated in USDC/ETH/etc., not in AAVE).

**Recommendation: Option (B)** — use **DeFiLlama's reported, sector-appropriate protocol volume**
(DEX/swap, perps notional, borrow/origination) as the working PQ source, with **TVL and fees as
side diagnostics** (per Entry 30), and raw on-chain logs only as an occasional spot-check. See §6.

---

## 1. Setup and a correction

| Token | cmc_id | Contract | Decimals | May-2026 price (panel) | status |
|---|---|---|---|---|---|
| UNI (Uniswap) | **7083** | `0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984` | 18 | $3.01964 | observed |
| AAVE | **7278** | `0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9` | 18 | $82.05048 | observed |

> **Correction logged.** `universe_panel.csv` contains **two** `symbol='UNI'` rows: cmc_id **4113**
> (a dead 2019-era namesake, last `observed` 2020-12, price ~$1.43 — *not* Uniswap) and cmc_id
> **7083** (the real Uniswap UNI, `observed` through 2026-05). The pilot prompt said "UNI
> (Uniswap governance token)"; the correct asset is **7083**. Both pilot tokens were verified
> `status='observed'` for the window before pulling.

**Window:** **May 2026** (2026-05-01 → 2026-05-31 UTC, 31 days) — the most recent complete month
(max `month_end` in the panel is 2026-05-31). Processed **day by day** so each completed day is a
clean measurement and the daily series falls out directly.

**Mechanism:** identical `getLogs` recursive block-range bisection on the 1,000-log/call cap as
`phase1_channel1_evm_locks.py`, with the **counterparty-address filter removed** (no
topic1/topic2) → *all* Transfer events of the token. Day-edge blocks resolved once via
`getblocknobytime` (32 shared calls, cached).

**Dollarization caveat:** the panel is monthly, so there is one price point — the May month-end
price is applied flat across the window. Precise daily-price dollarization is out of pilot scope
(this pilot measures call-cost + magnitude, not a production PQ series).

---

## 2. Measured cost (the headline feasibility numbers)

| Token | Days | Raw transfers | **getLogs calls** | Max bisection depth | Wall time | Rate |
|---|---|---|---|---|---|---|
| UNI | 31 | 133,350 | **381** | 6 | 345.6 s | 0.91 s/call |
| AAVE | 31 | 116,910 | **309** | 5 | 305.1 s | 0.99 s/call |
| *shared block-edge resolution* | — | — | 32 | — | — | (one-time/window) |

- **~345 getLogs calls per token-month**, **~11 calls/day**, **~0.9 s/call** effective
  (0.22 s pacing + ~0.7 s network round-trip), well under the free key's 5 req/s and 100k/day
  caps. A single token-month is trivial.
- Bisection depth maxed at 5–6 (the 1,000-log cap is hit a handful of times per day for these
  moderately-active tokens — ~2,500–4,300 transfers/day each). No single block exceeded 1,000
  logs (`uncuttable_blocks = 0`), so no within-block undercount.

**This directly refines Entry 24.** Entry 24's "orders of magnitude beyond the free key" finding
was about *full multi-year supply enumeration* (HODL/coin-age). For a *recent bounded window* the
cost is small. The two are not the same regime — see the extrapolation in §5.

---

## 3. Dollarized volume and the outlier problem

| Token | Raw Σtransfer (tokens) | **Raw USD** | Impossible transfers (> circ supply) | Max single transfer | **Clean USD** (outliers removed) |
|---|---|---|---|---|---|
| UNI | 261,099,080 | **$788.4M** | **0** | 5.44M tok (0.86% of supply) | **$788.4M** (= raw) |
| AAVE | 1.0000×10¹⁸ | **$8.2×10¹⁹** ⚠ | **6** | **10¹⁸ tok = 6.5×10¹⁰× supply** | **$2.75B** |

- **UNI is clean**: zero transfers exceed circulating supply; the raw sum is usable as-is.
- **AAVE is corrupted by non-economic events**: 6 of 116,910 transfers carry sentinel-scale
  values (one is exactly 10¹⁸ tokens). They inflate the raw monthly sum by ~10 orders of
  magnitude. Removing transfers larger than the entire circulating supply yields $2.75B — but
  the threshold is *ad hoc*, and this is precisely the wash/internal-churn contamination the
  spec (§6) flags for raw NVT volume, here in an extreme form.
- Transfer-size distributions (tokens): UNI median 162 / p99 31.0k / p99.9 189k; AAVE median
  5.7 / p99 1.35k / p99.9 19.1k. Long right tails in both — raw sums are tail-dominated and
  fragile.

Full per-day series in `03_data/raw/phase2_pilot/pilot_UNI.json` and `pilot_AAVE.json`;
outlier stats in `pilot_noise_diag.json`.

---

## 4. Cross-check vs DeFiLlama (May 2026, same window)

DeFiLlama endpoints verified live & keyless:
`/summary/dexs/uniswap?dataType=dailyVolume`, `/summary/fees/aave?dataType=dailyFees`,
`/protocol/aave` (TVL). Saved in `defillama_may2026.json`.

| Series (May 2026) | Value | vs raw token-transfer |
|---|---|---|
| **Uniswap DEX swap volume** (DeFiLlama) | **$36.75B** | **46.6× larger** than UNI token-transfer ($0.79B) |
| UNI token-transfer ↔ Uniswap DEX daily corr | **0.30** | weakly related |
| **Aave fees** (DeFiLlama) | $52.1M | — |
| **Aave TVL** (avg, DeFiLlama) | $14.33B | (capital stock, not flow) |
| AAVE token-transfer (clean) | $2.75B | a different, unrelated quantity |

**Interpretation.** The pilot prompt anticipated raw-Transfer volume would be a *multiple* of
DeFiLlama's reported volume (routing hops / wrapping inflating it). That intuition holds when you
sum transfers of the *traded* assets through the *pool* contracts. It does **not** hold here,
because we summed the **governance token's own** Transfer events — a different object entirely.
For UNI the raw measure is 47× *smaller* and barely correlated; for AAVE it is both corrupted and
conceptually disconnected from lending throughput. **The correct on-chain swap-volume measure
would require enumerating each protocol's pool `Swap` events (or paired-asset transfers into/out
of every pool) — i.e. re-implementing DeFiLlama's per-protocol adapter layer**, which is far
beyond a free key and out of scope for this paper.

---

## 5. Extrapolation (real numbers)

At the measured **~345 getLogs calls/token-month** and **~0.9 s/call**, against the free key's
**100,000 calls/day** cap:

| Target | getLogs calls | Runtime @0.9 s/call | Days @100k/day cap |
|---|---|---|---|
| 1 token, full history (UNI ~68 mo) | ~23,500 | ~5.9 h | 0.2 d |
| 1 recent month × 127 DeFi-slug tokens | ~43,800 | ~11 h | 0.4 d |
| **Full history × 127 DeFi-slug tokens** (avg ~40 mo) | **~1.75M** | **~438 h** | **~17.5 d** |
| Full history × 241 slugged assets (avg ~40 mo) | ~3.33M | ~832 h | ~33 d |

(The 127/241 slug counts are from Entry 22 / the decision memo: only 241/1,939 observed assets
carry a DeFiLlama slug; 127 of those are tokens.)

**Reading:**
- A **single flagship's full history** or a **single recent month across the DeFi-token panel** is
  comfortably feasible on the free key (hours, ≤½ a day's budget).
- **Full multi-year history across the panel is not** a routine/repeatable build: ~1.75–3.3M
  calls is **2½–4½ weeks** of continuous running even at the daily cap, before any
  re-runs, and the early-sample coverage still wouldn't improve (pre-launch months don't exist).

But the cost table is almost beside the point given §3–4: even where it is cheap, the
**governance-token Transfer log is the wrong quantity**.

---

## 6. Recommendation

**Option (B): DeFiLlama's reported volume as the working PQ source.**

1. **PQ = sector-appropriate reported volume** from DeFiLlama, routed by the `sector` field
   (Entry 16 / Entry 30): DEX/swap volume for AMMs, perps notional for derivatives,
   borrow/origination flow for lending. DeFiLlama already computes these from the correct
   per-protocol pool events.
2. **TVL and fees → side diagnostic columns** (capital-stock control; cost-of-intermediation /
   take-rate), plus the Volume/TVL turnover diagnostic — exactly as Entry 30 specified.
3. **Raw Etherscan Transfer logs → occasional spot-check only**, not the primary source. They are
   cheap for a recent window but (a) measure the gov-token's movements rather than protocol
   throughput, (b) require ad-hoc outlier scrubbing (AAVE), and (c) don't scale to full-panel
   history on the free key.
4. **Carry into the paper's methodology/limitations (spec §6):** reported aggregator volume is
   itself subject to the classic NVT wash-trading caveat; note that an independent raw-log
   reconstruction was piloted and found to measure a different quantity, so the aggregator series
   is adopted deliberately, not for convenience alone.

**Not (A)** (raw Etherscan volume at panel scale): ruled out on both validity (governance-token
transfers ≠ throughput; AAVE corruption) and cost (full-panel history ≈ weeks).
**Not pure (C)** (small flagship raw subset as primary): a flagship raw build is feasible but
would still measure the wrong object; keep it only as a *spot-check* of DeFiLlama, not a source.

> **Coin-side PQ (ETH/BTC native transfers) was *not* in this pilot** and faces a harder wall
> (archive state, not Transfer logs — Entries 21/24). DeFiLlama chain-level data remains the
> coin-side fallback; this pilot speaks only to ERC-20 tokens.

---

## 7. Reproducibility

- `04_code/phase2_pq_pilot.py` — day-by-day measured pull, per-token call budget, checkpointed.
- `04_code/phase2_pq_pilot_diag.py` — outlier/percentile diagnostic.
- `03_data/raw/phase2_pilot/` — `eth_day_blocks.json`, `pilot_UNI.json`, `pilot_AAVE.json`,
  `pilot_noise_diag.json`, `defillama_may2026.json` (cached numbers only; no large raw-log dumps).
- API key read from gitignored `04_code/.api_keys.json` (not committed).

**Next step:** human review of this recommendation, then resume the Phase 2 build on the
DeFiLlama-volume basis (do **not** build `phase2_pq.py` before that review).
