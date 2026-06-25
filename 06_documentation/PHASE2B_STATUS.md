# Phase 2b Status — for Cowork discussion

**Date:** 2026-06-25 · **Session:** 014 (Claude Code / Opus 4.8) · **Commit:** eda4df0
**Companion docs:** `DATA_DECISIONS_LOG.md` Entry 35 · `03_data/PHASE2_COVERAGE_REPORT.md` (§1b, §4) ·
`06_documentation/ai_conversations/session_014_2026-06-25_phase2b_coins.md`

This is the decision-facing summary. It does not repeat the full audit trail (above) — it states
what changed, what is now true about coin coverage, and the **calls that are yours to make** before
Phase 3.

---

## 1. What this session set out to do
Phase 2 (session 013) deferred **81 material coins** (peak mcap ≥ $1B) because their only PQ ladder
option, Artemis Settlement Volume, was paid-only. Phase 2b's job: source **native settlement value**
for them from free, keyless, live-verified sources — flag, don't guess; no raw multi-year block
iteration. (PQ = on-chain payment/transfer value in USD, the coin-side analogue of Bitcoin's NVT
denominator; **not** fees, **not** DEX volume, **not** TVL — Entries 30/32.)

**Constraint that shaped everything:** `04_code/.api_keys.json` holds only an Etherscan key. **No
Artemis key was procured, so Rung 2 stayed closed.** Free sources only.

## 2. What changed (the result)
| | Phase 2 | **Now (2b)** |
|---|---|---|
| Coins with a PQ series | 50 | **58** |
| Asset-months with PQ | 2,557 | **3,358** |
| Asset-months with NVT_GL | 1,821 | **2,526** |
| Distinct assets with NVT_GL | 59 (46 coins) | **67 (54 coins)** |

**8 coins newly covered** via bitinfocharts native "Sent in USD":
- **Full history → 2026-06:** DOGE, LTC, BCH, DASH, ETC, BTG
- **Partial / stale:** BSV (ends 2021-08), ZEC (ends 2022-05)

These 8 include 4 of the highest-value gaps (DOGE $62B, BCH $43B, LTC $18B peak) — a real coverage win
on the early-sample coin side, which is exactly where NVT_GL was thinnest.

## 3. The honesty flags you should know about (these are the discussion-worthy bits)
1. **The covered UTXO series are change-INFLATED.** bitinfocharts "Sent in USD" = total on-chain
   *output* value, which for UTXO coins includes change returned to sender. This is the **opposite** of
   BTC's source (blockchain.com Estimated Tx Value, change-*excluded*). Effect: these coins' NVT_GL
   *levels* are pushed down (e.g. LTC median NVT_GL ≈ 5×10⁻⁴). **This is fine for how H2/H3 use NVT_GL —
   a within-month cross-sectional rank — but it means BTC and the 8 new coins are NOT on a comparable
   cardinal scale.** Reinforces the existing "rank, not level" caveat (coverage report §2a).
   - *Exceptions:* **ETC** is account-model (no change, clean). **ZEC** captures only the transparent
     pool — shielded (zk) amounts are cryptographically hidden — so ZEC's PQ is a partial undercount.
2. **BSV and ZEC are stale** (series stop in 2021 / 2022). They add real early-sample months but no
   recent coverage.

## 4. What stayed PQ=NaN — 73 coins, every reason verified live
- **XRP (the single biggest gap, $179B peak):** no free keyless historical XRPL payment-volume series.
  The canonical source (Ripple Data API, data.ripple.com) is **dead/403**; xrpscan exposes account data
  but no volume endpoint; xrplmeta is a token-metadata node; api.xrpldata.com is an NFT API; bithomp
  needs a key. Raw full-history ledger iteration (~21.6k ledgers/day) is the forbidden call-volume wall.
- **XMR:** RingCT hides amounts — unobservable on any source. Permanent.
- **71 others** (DOT, KSM, MATIC, ATOM, VET, THETA, FIL, IOTA, NEO, XTZ, KAS, FTM, …): no free,
  keyless, ready-made historical USD transacted-value series. Cosmos/Kaspa public LCDs give only current
  state; Filfox gives base-fee (a toll); Mintscan/Subscan need keys; blockchair has no free charts API.

## 5. Decisions for you (Cowork)
1. **Is the change-inflation acceptable as-is?** My read: yes for the rank-based H2/H3 use, with the flag
   documented — but if any **coins-only NVT_GL level** ends up in the paper, the 8 UTXO series should be
   sensitivity-checked (or a change-excluded equivalent sought). Your call on whether to note this as a
   limitation now or revisit in Phase 3.
2. **Do you want to spend on a paid key to close the XRP / 71-coin gap?** One key reopens Rung 2 for most
   of them at once:
   - **Artemis** (Settlement Volume — the theoretically-correct object; Pro ~$300/mo may still need
     Enterprise for REST).
   - **Subscan / Mintscan** (would help the Polkadot/Cosmos cluster specifically).
   - **Glassnode / Coin Metrics** (broad coin coverage incl. XRP volume; pricier).
   XMR stays impossible regardless. If "no spend," the panel is final as-is and we just document the gap.
3. **Green-light Phase 3?** Phase 2b is done for what free sources allow. Phase 3 (returns/factors) is the
   next phase and is **not started** — it needs your review per the standing rule.

## 6. Recommendation
Proceed to Phase 3 on the current 67-asset NVT_GL panel, documenting the coin coverage gap and the
change-inflation flag honestly in the methodology/limitations section (spec §6). Treat the paid-key
option as a deliberate, separate decision driven by whether a result actually depends on XRP / the 71
uncovered coins — not bought preemptively. (Same posture as the Channel-2 / coin-age paid-source call,
Entry 28.)
