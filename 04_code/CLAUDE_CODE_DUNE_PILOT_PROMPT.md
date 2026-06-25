# Claude Code Pilot Prompt — Dune Analytics Feasibility Pilot (Lending/Staking/Perps)

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). This is a bounded **diagnostic
pilot**, not a Phase 2c build — it tests whether Dune's decoded tables can supply the
token-side PQ categories DeFiLlama has no volume dimension for, before any university
funds are requested for a paid Dune subscription.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Phase 1 and Phase 2 (coins) are
complete; token-side PQ has a structural gap (see below). Before doing anything else, read
in full:

1. 04_code/DATA_DECISIONS_LOG.md Entry 31 — the Etherscan Transfer-log pilot. It looked
   plausible but was the WRONG QUANTITY: UNI raw transfer volume was 46.6x smaller than
   actual Uniswap DEX volume (corr 0.30), and AAVE's raw transfer sum was corrupted by
   sentinel-value transfers (off by ~10 orders of magnitude before cleaning). The standard
   this pilot must meet: don't trust a number just because a query returns one — verify it
   against a real reference before reporting it as usable.
2. 04_code/DATA_DECISIONS_LOG.md Entry 32 — the PQ source waterfall this gap sits inside
   (DeFiLlama volume primary; fee-backout only for confidently-known flat fee rates; else
   PQ flagged missing).
3. 03_data/phase2/pq_tokens.csv — confirm AAVE (category "Lending"), LDO (category "Liquid
   Staking"), and GNS (category "Derivatives") are all still `pq_usd` NaN, each because
   DeFiLlama has no transacted-value series for that category (Lending/Liquid Staking) or
   has paywalled it (Derivatives — HTTP 402 on the perps dimension, affecting 10 tokens
   including GNS). These three are the test cases: one per category.
4. 04_code/dune_pilot_test.py — already written, NOT yet run. It searches Dune's dataset
   catalog for the real decoded tables behind AAVE borrow events, Lido stake/unstake
   events, and GNS trade events, samples 5 raw rows to confirm actual column names (does
   NOT assume Spellbook naming guesses are correct), and attempts a trailing-30-day SUM
   only if an obvious USD-amount + timestamp column pair exists.

A free-tier Dune API key is already in gitignored `04_code/.api_keys.json` under "dune"
(2,500 free credits). The Cowork session that wrote the script has no network route to
api.dune.com (sandbox egress is allowlisted to dev-infra domains only) — that's the only
reason this wasn't already run. You have normal network access; run it for real.

## What to do

1. Run `python3 04_code/dune_pilot_test.py`. Read its console output and the raw JSON it
   writes to `03_data/raw/dune_pilot/`.
2. For any token where the script stopped at "needs_manual_column_mapping" (no obvious
   USD-amount/timestamp pair), look at the real sample columns it printed and write the
   correct aggregation SQL yourself — e.g. raw token-unit amounts may need a join to a
   price table, or the right table may be a normalized abstraction (`lending.borrow`,
   `dex.trades`, or similar cross-protocol table) rather than the raw per-pool event table.
   Use Dune's `/v1/datasets/search` endpoint again with different query phrasing if the
   first candidate table was wrong.
3. For each of the three tokens, get a trailing-30-day (or most recent complete month,
   whichever is cleaner) USD volume figure:
   - AAVE: borrow/loan-origination volume (NOT TVL, NOT repayments-net — origination flow)
   - LDO: stETH stake + unstake flow (submit + withdrawal events, summed as volume not net)
   - GNS: gTrade perps trading/notional volume
4. **Cross-check each number against an independent reference** before trusting it — the
   whole point, per Entry 31's standard. Options: Dune's own public dashboards
   (`dune.com/gains/gtrade_stats` for GNS; Lido's official stats page; Aave's own analytics
   page or DeFiLlama's AAVE TVL/fees as a sanity bound), or order-of-magnitude plausibility
   against the token's market cap / TVL. State the comparison explicitly — ratio, and
   whether it's in a sane range (unlike the Etherscan pilot's 46.6x miss).
5. **Note the credit cost.** Record how many Dune credits/API calls this 3-token pilot
   used, out of the 2,500 free. This is the actual feasibility data point for the
   university-funding decision Moazzam is weighing — be precise, not approximate.

## What NOT to do

Do not build a panel-scale Dune extraction pipeline (`phase2c_pq_tokens.py` or similar) and
do not attempt to backfill multi-year history. This is a 3-token, ~30-day feasibility check
only. Do not guess at column semantics if a table's columns are ambiguous — say so in the
report rather than reporting an unverified number.

## Deliverable

Write `03_data/DUNE_PILOT_REPORT.md`: the three tables actually used (with full Dune
`full_name`), the verified 30-day volume figure for each (or "could not verify" with the
reason), the cross-check comparison for each, total credits/calls consumed, and a clear
recommendation — (A) Dune's free tier is sufficient to prototype all three categories at
panel scale, (B) free tier works for discovery/spot-checks but a paid plan is needed for
full-panel history, or (C) Dune does not cleanly solve one or more of these categories
(say which, and why). Log this session as
`06_documentation/ai_conversations/session_015_2026-06-25_dune_pilot.md`, continue
`04_code/DATA_DECISIONS_LOG.md` from Entry 33, and update `06_documentation/time_log.md`.
Commit and push to github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end. Stop
after the report — do not start a Phase 2c build until this is reviewed.
```
