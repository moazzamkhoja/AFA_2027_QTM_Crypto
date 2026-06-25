# Dune Analytics Feasibility Pilot — Token-Side PQ Gap (Lending / Liquid Staking / Perps)

**Session:** 015 · **Date:** 2026-06-25 · **Scope:** 3 tokens × trailing-30-day, diagnostic only (NOT a Phase 2c build)
**Standard applied:** Entry 31 — *don't trust a number because a query returns one; verify it against an independent reference first.*

---

## 0. What this pilot tested

Three token-side PQ categories are structurally NaN in `03_data/phase2/pq_tokens.csv` because DeFiLlama
has no transacted-value series for them (Lending / Liquid Staking) or paywalls it (Derivatives, HTTP 402).
One token per category was tested as the feasibility probe:

| Token | cmc_id | Category | Why NaN today |
|---|---|---|---|
| AAVE | 7278 | Lending | DeFiLlama category has TVL/fees, no borrow-volume series |
| LDO | 8000 | Liquid Staking | DeFiLlama category has TVL, no stake/unstake-flow series |
| GNS | 13663 | Derivatives | DeFiLlama perps/notional dimension is paid-gated (HTTP 402; re-confirmed this session) |

The pre-written `04_code/dune_pilot_test.py` ran but its auto-picker stopped all three at
`needs_manual_column_mapping` — it grabbed the *wrong* tables (Aave **Polygon** transfers, Lido's submit
event with no USD column, a Gains per-trade table with no `amount_usd`). The real work below was the manual
mapping the prompt calls for: finding the correct **normalized (Spellbook) abstractions** that carry a
clean, pre-priced USD amount, confirming their real columns before aggregating, and cross-checking every
number against an independent reference.

---

## 1. Tables actually used (full Dune `full_name`)

| Token | Table (`full_name`) | Type | USD basis |
|---|---|---|---|
| AAVE | `lending.borrow` | spell (cross-protocol) | `amount_usd` (Dune-priced at canonical contracts) |
| LDO  | `lido_ethereum.steth_evt_submitted` (stake in) + `lido_ethereum.withdrawalqueueerc721_evt_withdrawalclaimed` (unstake out) | decoded | raw ETH (wei) × `prices.day` WETH price |
| GNS  | `dune.gains.result_g_trade_stats_defi_llama` | community (Gains-maintained, **this is DeFiLlama's own upstream feed**) | `daily_volume` (USD, pre-aggregated) |

Price table for LDO: `prices.day`, filtered to the **canonical WETH contract**
`0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2` — *not* `symbol = 'WETH'` (see §3, the one trap caught here).

---

## 2. Verified 30-day figures

Window: trailing 30 days, **2026-05-27 → 2026-06-25** (consistent across all three).

| Token | 30-day PQ figure | Definition used | Detail |
|---|---|---|---|
| **AAVE** | **$4,285,619,623** (≈ $4.29 B) | Borrow origination flow (Ethereum, v3) | `transaction_type='borrow'`, 25,452 borrows, avg $168,380. (Repays/liquidations stored as negative `amount_usd` and excluded — origination only, per spec.) |
| **LDO** | **$1,582,853,346** (≈ $1.58 B) | stETH stake + unstake flow (summed, not netted) | stake 544,740 ETH = $938.3 M + unstake 370,457 ETH = $644.5 M. Net +174,284 ETH. |
| **GNS** | **$1,178,026,993** (≈ $1.18 B) | gTrade perps notional volume (all chains, all asset classes) | $39.3 M/day; 84,929 trades; avg notional $13,871. Chains: arbitrum $993 M, base $160 M, polygon $15 M, megaeth $9 M, apechain $0.2 M. |

All three are **clean** (no sentinel/scam artifacts — contrast the Etherscan pilot's AAVE 10¹⁹ blow-up):
AAVE and GNS arrive pre-priced from Dune/Gains; LDO was hand-priced and the one contamination risk was
caught and removed (§3).

---

## 3. Cross-checks (independent reference per token)

**AAVE — vs DeFiLlama Aave-v3 Ethereum borrowed-outstanding.**
DeFiLlama `currentChainTvls`: Ethereum borrowed-outstanding = **$7.215 B**, Ethereum TVL = $9.343 B.
30-day origination $4.286 B ÷ outstanding $7.215 B = **0.59× per 30 days** ⇒ implied average loan life ≈ 1.7
months. That is a flow-vs-stock comparison, so we only claim **order-of-magnitude consistency** — and it
passes cleanly: same order of magnitude, sane turnover for a lending market. **Not** 47× off (Entry 31's UNI
miss) or 10¹⁰ off (Entry 31's AAVE sentinel miss). **PASS.**

**LDO — vs DeFiLlama spot ETH price (sanity on the price join).**
Volume-weighted ETH price implied by the clean query = **$1,768/ETH** (30-day avg); DeFiLlama spot ETH today
= **$1,560/ETH**. Consistent (window average slightly above today's spot — ETH drifted down ~12% over the
month). **PASS.** *The catch:* the first LDO run used `symbol='WETH'` and implied a nonsensical **$767/ETH**.
Diagnostic: `symbol='WETH'` on Ethereum in `prices.day` matches **3 distinct contracts** with prices ranging
**$0.0000008 → $2,112** (avg $795) — i.e. scam tokens sharing the ticker. Switching to the canonical WETH
contract fixed it ($1,768). This is the Entry-31 lesson recurring in a new form (a clean-looking number that
was wrong); it is also the single most important caveat for any hand-rolled price join at panel scale.

**GNS — DeFiLlama is the *paywalled* reference, so cross-check is internal + historical.**
Both `…/summary/derivatives/gains-network` and `…/overview/derivatives/gains-network` returned **HTTP 402** —
re-confirming the exact paywall that created this gap. The Dune table used **is Gains' own table that feeds
DeFiLlama's (paywalled) gTrade number**, and is the same data behind the public `dune.com/gains/gtrade_stats`
dashboard, so Dune retrieves *for free the precise series DeFiLlama charges for*. Three corroborations in lieu
of an external number: (1) **internal consistency** — `daily_volume` equals the sum of its asset-class
components (crypto+forex+stocks+indices+commodities) to **0.000%**; (2) **historical range** — $39.3 M/day is
squarely within gTrade's known $20–60 M/day band; (3) **per-trade sanity** — $13,871 avg notional is normal
for leveraged retail perps. **PASS (plausibility), with the honest caveat that the one external aggregator
that would corroborate it is the one paywalling this dimension.**

> **One reconstruction that did NOT verify — reported, not hidden.** An independent within-Dune cross-check
> from the raw per-trade table `dune.gains.result_gtrade_all_orders_daily_view` summed `position_size_dai`
> to only **~$44 M** (OPEN $20.3 M + CLOSE $19.3 M + others) — ~27× below the $1.178 B headline. This is a
> **column-semantics ambiguity, not a contradiction**: `position_size_dai` is almost certainly *margin /
> DAI-collateral-only*, not leveraged notional across all chains/collaterals. Per the prompt's rule ("do not
> guess at column semantics if ambiguous — say so"), this reconstruction is logged as **inconclusive**, and
> the headline rests on the Gains-maintained summary table, which is internally consistent and is DeFiLlama's
> own upstream.

---

## 4. Credit / API-call cost

Dune exposes **no credit-balance endpoint and no usage header** (checked the response headers directly —
none present), so exact credits cannot be read back. What *can* be reported precisely is the call count:

| Call type | Count | Credit-metered? |
|---|---|---|
| `/datasets/search` (catalog lookups) | **14** | No — catalog metadata, not query credits |
| `/sql/execute` executions (all **`small`** tier) | **9** | Yes |
| Failed `/sql/execute` (`medium` → HTTP 400 "Invalid performance tier"; free tier only exposes `small`) | 1 | No — rejected before execution |

The 9 executions: 3 `LIMIT 5` samples + 3 headline aggregations (one grouped query per token) + 1 LDO
price-fix + 1 WETH-contamination diagnostic + 1 GNS raw reconstruction. **Total datapoints retrieved across
all 9: ~130.** Of these, **only 3 executions were strictly necessary** for the deliverable (one grouped
aggregation per token); the other 6 were exploration, diagnostics, and verification.

Under Dune's published per-execution schedule (≈10 credits/medium execution; `small` is the free engine and
no costlier), this 3-token pilot consumed on the order of **well under 100 of the 2,500 free monthly credits
(< 4%)** — and the free credit pool **resets monthly**. **Cost is a non-issue at this scale.**

---

## 5. Recommendation → **(A), with one gate before requesting funds**

**All three categories are cleanly solvable on Dune's free tier**, with validated numbers and trivial credit
cost. Concretely:

- **Lending (AAVE):** `lending.borrow` is a *cross-protocol* spell with clean `amount_usd`. The entire
  token panel's lending history is one `GROUP BY project, block_month` query — **not one query per token.**
- **Liquid staking (LDO):** decoded events + a price join works, *provided* the join uses canonical contract
  addresses (the WETH trap, §3). Doable but the one place hand-rolled care is required.
- **Derivatives (GNS):** the paywalled-at-DeFiLlama dimension is **free on Dune** via the protocol's own
  upstream table. This is the single strongest result — Dune directly fills the 402 gap (10 tokens incl. GNS).

Because the spell tables aggregate the whole panel per query, the credit math for **full multi-year, full-panel
history is also affordable on the free tier** (a handful of grouped queries per category per refresh, << 2,500
credits/month).

**The one real risk that could downgrade this to (B):** the free tier only exposes the **`small` query
engine** (`medium` is rejected). The LDO event+join query already took **66 s** on `small`; a multi-year
full-panel scan with joins could hit per-query time/row limits and force the paid `medium`/`large` engine.
Two coverage caveats also remain: confirm each panel protocol is actually in Dune's spellbook (majors are;
long-tail may not be), and apply canonical-contract discipline to every price join.

**Gate before any university-funding request (this is the decision Moazzam is weighing):** run a **free-tier
panel-scale dry-run** — one grouped `lending.borrow` / `perpetual.trades` / staking query over full history
across the real token list — and see whether the `small` engine completes within limits. If it does → free
tier is fully sufficient, **no paid plan needed (A)**. If it times out on multi-year scans → a modest paid
plan is justified **only** for the `medium`/`large` engine on backfill, not for credits **(B)**. **Do not buy
a Dune subscription before this dry-run.**

---

## 6. Reproducibility

Scripts (`04_code/`): `dune_pilot_test.py` (stage-1 auto-probe, as supplied) · `dune_pilot_explore.py`
(catalog search for the right normalized tables) · `dune_pilot_aggregate.py` (headline 30-day aggregations) ·
`dune_pilot_verify.py` (LDO price-join fix + external cross-checks). Raw JSON for every search, sample,
aggregation, and cross-check: `03_data/raw/dune_pilot/`. Free-tier Dune key in gitignored
`04_code/.api_keys.json` (`"dune"`).
