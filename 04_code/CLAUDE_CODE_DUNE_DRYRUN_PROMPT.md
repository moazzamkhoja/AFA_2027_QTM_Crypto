# Claude Code Pilot Prompt — Dune Free-Tier Panel-Scale Dry-Run

Paste the prompt below as the first message in a new Claude Code session opened with
working directory `C:\AFA_2027_QTM_Crypto` (the repo root). This is the explicit gate
Entry 36 / `DUNE_PILOT_REPORT.md` §5 requires **before** any university funds are
requested for a paid Dune plan. It is still a diagnostic dry-run, not a Phase 2c build.

---

```
You're working in the AFA 2027 QTM Crypto research repo. Before doing anything else,
read in full:

1. 04_code/DATA_DECISIONS_LOG.md Entry 31 (Etherscan pilot rejection — verify before
   trusting a number) and Entry 36 (Dune 3-token feasibility pilot — AAVE/LDO/GNS all
   passed on the free tier, but only as single tokens over 30 days).
2. 03_data/DUNE_PILOT_REPORT.md, especially §5: the one open risk is that the free tier
   only exposes the `small` query engine (a single LDO join already took 66s), and two
   coverage caveats were flagged but NOT yet checked: (a) whether every NaN token's
   protocol actually exists in Dune's spellbook (majors like Aave/Lido/Gains are
   confirmed; long-tail protocols may not be), and (b) whether a full multi-year,
   full-panel grouped query completes on `small` without hitting time/row limits. This
   session answers both, for the REAL token list, not the 3-token sample.
3. 03_data/phase2/pq_tokens.csv — confirm the current full NaN lists (re-derive live,
   don't trust a stale copy):
   - Lending (6): AAVE, ANC, BZRX, OM, STRK, WXT
   - Liquid Staking (1): LDO
   - Derivatives (10): AVNT, DDX, GNS, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR
4. 03_data/universe_panel.csv — confirm the panel's full date range (was 2015-08 to
   2026-05, 130 months, as of last check — re-verify).
5. 04_code/dune_pilot_{test,explore,aggregate,verify}.py and 03_data/raw/dune_pilot/ —
   the working code and raw query results from the 3-token pilot. Reuse the same
   tables/columns already validated there (`lending.borrow`, the Lido event tables +
   canonical-WETH-contract price join, `dune.gains.result_g_trade_stats_defi_llama`)
   rather than re-discovering them.

The free-tier Dune key is in gitignored `04_code/.api_keys.json` under "dune" (2,500
free credits/month, resets monthly; ~100 were used by the 3-token pilot).

## Funding context (read before deciding what to recommend)

Moazzam has university approval for a paid Dune plan **if** this dry-run shows the free
tier can't handle full-panel scans. This removes the prior hard "do not upgrade" gate —
you may recommend a paid plan if the evidence supports it. It does NOT mean you (or any
AI agent) should attempt to purchase or subscribe. If a paid plan is the right call,
say so clearly in the report and stop — Moazzam will do the actual checkout himself in
Dune's billing UI. Do not enter payment details, do not create or modify any billing
subscription, under any circumstance.

## What to do

**Step 1 — Coverage check (catalog search only, cheap, not query-credit-metered).**
For each of the 17 tokens above, confirm whether its protocol is actually findable in
Dune's spellbook/decoded catalog (`/v1/datasets/search`). For the 3 already-validated
protocols (Aave→AAVE, Lido→LDO, Gains→GNS) you already know the answer from the pilot —
don't re-spend calls confirming those. For the other 14 (ANC, BZRX, OM, STRK, WXT;
AVNT, DDX, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR), search and report found/not-found,
with the matched `full_name` if found. Do not guess — if a search returns nothing
relevant after 2-3 reasonable query phrasings, mark it `not_found` and move on; do not
force a match.

**Step 2 — Full-history, full-panel grouped query per category, `small` engine only.**
For whichever tokens in each category ARE covered (per Step 1):
- **Lending:** one `lending.borrow` query, `GROUP BY project, block_month`, filtered to
  the covered lending protocols, full history (no 30-day window this time — the spec's
  actual panel needs the whole series). Record wall-clock time and row count returned.
- **Liquid Staking (LDO only):** the same stake+unstake event tables from the pilot,
  full history, monthly grouping, with the price join on the **canonical WETH contract**
  (never `symbol='WETH'` — Entry 36's trap). Record wall-clock time.
- **Derivatives:** GNS via `dune.gains.result_g_trade_stats_defi_llama`, full history,
  monthly grouping. For any other derivatives tokens found covered in Step 1, the
  equivalent per-protocol table if one exists.
Note explicitly whether any query times out, hits a row cap, or returns a Dune error —
that is the actual data point this dry-run exists to produce. If a query is slow but
completes, record the exact seconds.

**Step 3 — Report results, including coverage gaps.** Most of the 17 tokens will likely
turn out NOT to be in Dune's spellbook (long-tail protocols, per the report's own
caveat) — that is a useful, expected finding, not a failure of this dry-run. Report it
plainly per token: covered+fast, covered+slow/timed-out, or not_found.

## What NOT to do

- Do not build a panel-scale extraction pipeline (`phase2c_pq_tokens.py` or similar).
- Do not write to `pq_tokens.csv` or any Phase 2/2b output — diagnostic only.
- Do not purchase, subscribe to, or modify any Dune billing plan.
- Do not guess at column semantics or force a coverage match that isn't real — same
  standard as Entry 31/36.

## Deliverable

Write `03_data/DUNE_DRYRUN_REPORT.md`: the Step 1 coverage table (17 tokens, found/not
found, matched table if found), the Step 2 timing/row-count results per category, and a
clear recommendation per category — (A) free `small` engine handles the full panel, no
upgrade needed, (B) free tier finds the tables but `small` can't finish full-history
scans, recommend the paid plan **for the engine, not credits** (Moazzam must purchase it
himself), or (C) most tokens in this category aren't on Dune at all regardless of
engine tier — note this means even a paid plan wouldn't help those specific tokens; they
stay flagged-NaN. Log this session as
`06_documentation/ai_conversations/session_016_<date>_dune_dryrun.md`, continue
`04_code/DATA_DECISIONS_LOG.md` from **Entry 37**, and update `06_documentation/time_log.md`.
Commit and push to github.com/moazzamkhoja/AFA_2027_QTM_Crypto (main) at session end.
Stop after the report — do not start a Phase 2c build until this is reviewed.
```
