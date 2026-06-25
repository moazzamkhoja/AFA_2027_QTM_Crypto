# Session 015 — Dune Analytics Feasibility Pilot (token-side PQ gap)

**Date:** 2026-06-25
**Agent:** Claude Code / Opus 4.8 (local, normal network access)
**Prompt:** `04_code/CLAUDE_CODE_DUNE_PILOT_PROMPT.md`
**Scope:** Bounded diagnostic pilot — 3 tokens × trailing-30-day. **Not** a Phase 2c build.
**Deliverable:** `03_data/DUNE_PILOT_REPORT.md` (+ this log, Decisions Log Entry 36, time_log).

## Why this session existed
Token-side PQ has a structural gap: DeFiLlama has no transacted-value series for Lending / Liquid Staking
and paywalls Derivatives (HTTP 402). Three test tokens — AAVE (Lending), LDO (Liquid Staking), GNS
(Derivatives) — are all `pq_usd` NaN in `pq_tokens.csv`. The Cowork session that wrote `dune_pilot_test.py`
had no network route to `api.dune.com`; this session has normal access and ran it for real, against the
Entry-31 standard (*verify before trusting; raw Etherscan looked plausible but was 46.6× off for UNI and 10¹⁹
off for AAVE*).

## What I did
1. **Read the required context first** — Decisions Log Entries 31 (Etherscan pilot rejection) and 32 (PQ
   waterfall), confirmed AAVE/LDO/GNS are still NaN in `pq_tokens.csv`, and read `dune_pilot_test.py`.
2. **Ran `dune_pilot_test.py`** (via `python`; the `python3` alias here is a Windows Store stub). All three
   stopped at `needs_manual_column_mapping` — the auto-picker grabbed wrong tables: Aave **Polygon**
   `aave_evt_transfer`, Lido `steth_evt_submitted` (no USD), Gains per-trade table (no `amount_usd`).
3. **Manual mapping (`dune_pilot_explore.py`)** — catalog-searched for the correct **normalized (Spellbook)**
   abstractions with pre-priced USD. Found `lending.borrow` (cross-protocol spell, has `amount_usd`),
   `dune.gains.result_g_trade_stats_defi_llama` (Gains' own DeFiLlama-feed table), `prices.day` (price join),
   and the Lido withdrawal-queue table `lido_ethereum.withdrawalqueueerc721_evt_withdrawalclaimed`.
   Pulled schemas from the search payloads (no execute credits) before writing any SQL.
4. **Aggregations (`dune_pilot_aggregate.py`)** — trailing-30-day figures. (Note: `/sql/execute` rejected
   `performance="medium"` as "Invalid performance tier"; free tier only exposes `small`.)
5. **Verification (`dune_pilot_verify.py`)** — caught and fixed the one trap, and pulled external references.

## Numbers (window 2026-05-27 → 2026-06-25)
- **AAVE** — `lending.borrow`, Ethereum v3, `transaction_type='borrow'`: **$4.286 B** origination (25,452
  borrows). Repays/liquidations are negative `amount_usd`, excluded.
- **LDO** — submit (stake) + withdrawalclaimed (unstake), ETH × WETH price: **$1.583 B** flow (stake $938 M +
  unstake $645 M; net +174 k ETH).
- **GNS** — Gains DeFiLlama-feed `daily_volume`, all chains: **$1.178 B** ($39.3 M/day, 84,929 trades).

## The trap I caught (Entry-31 standard in action)
First LDO run used `prices.day` filtered by `symbol='WETH'` and implied a nonsensical **$767/ETH**. Diagnostic
showed `symbol='WETH'` on Ethereum matches **3 distinct contracts**, prices $0.0000008 → $2,112 (avg $795) —
scam tokens sharing the ticker, with `AVG()` dragged down by them. Re-ran filtered to the **canonical WETH
contract** `0xc02a…756cc2` → **$1,768/ETH** (30-day vwap), consistent with DeFiLlama spot **$1,560**. The
contaminated number *looked* fine; only the cross-check exposed it. This is the headline caveat for any
hand-rolled price join at panel scale.

## Cross-checks
- **AAVE**: origination $4.286 B ÷ DeFiLlama Aave-v3 Ethereum borrowed-outstanding $7.215 B = 0.59×/30d
  (≈1.7-month avg loan life) — order-of-magnitude sane. PASS.
- **LDO**: vwap $1,768 vs spot $1,560 — consistent. PASS.
- **GNS**: DeFiLlama per-protocol derivatives endpoint **also 402** (re-confirmed the gap). Corroborated via
  internal consistency (`daily_volume` = component sum to 0.000%), historical $/day range, per-trade sanity.
  An independent raw-table reconstruction (`result_gtrade_all_orders_daily_view`, `position_size_dai`) gave
  ~$44 M (~27× low) — **logged as inconclusive (ambiguous column = margin/DAI-only, not notional), not a
  contradiction**, per the prompt's "don't guess at ambiguous columns" rule.

## Cost
No Dune credit-balance endpoint/header exists (checked headers directly). Precise call count: **14 catalog
searches** (not query-credit-metered) + **9 `/sql/execute` runs** (all `small`; ~130 datapoints total) + 1
rejected `medium` call (0 cost). Only 3 of the 9 executes were strictly necessary. ⇒ on the order of **<100 of
2,500 free monthly credits (<4%)**. Cost is a non-issue at this scale.

## Recommendation
**(A) — free tier is sufficient to prototype all three categories at panel scale**, with one gate. Spell
tables are cross-protocol, so the whole token panel's history is a few `GROUP BY project, block_month` queries,
not one-per-token — credit-cheap even for multi-year backfill. **The one risk** that could downgrade to (B):
free tier only exposes the `small` engine (the LDO join already took 66 s); a multi-year full-panel scan could
hit per-query limits and need the paid `medium`/`large` engine. **Gate before requesting funds:** run a
free-tier panel-scale dry-run over the real token list; only buy a plan if `small` times out — and then for
the engine, not for credits. **Do not start Phase 2c, and do not buy a Dune subscription, before that
dry-run and human review.**

## Files
- New: `03_data/DUNE_PILOT_REPORT.md`; `04_code/dune_pilot_explore.py`, `dune_pilot_aggregate.py`,
  `dune_pilot_verify.py`; raw JSON in `03_data/raw/dune_pilot/`.
- Updated: `04_code/DATA_DECISIONS_LOG.md` (Entry 36), `06_documentation/time_log.md`, this log.
- Unchanged: `pq_tokens.csv` and all Phase 2/2b panel outputs (diagnostic pilot only — no panel writes).
