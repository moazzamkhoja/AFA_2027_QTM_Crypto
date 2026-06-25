# Session 016 — Dune Free-Tier Full-Panel Dry-Run (the funding-gate test)

**Date:** 2026-06-25
**Agent:** Claude Code / Opus 4.8 (local, normal network access)
**Prompt:** session kickoff (Dune dry-run; continues `DUNE_PILOT_REPORT.md` §5)
**Scope:** Diagnostic only — coverage of the real 17-token NaN list + full-history `small`-engine feasibility.
**Not** a Phase 2c build. **No panel outputs written.**
**Deliverable:** `03_data/DUNE_DRYRUN_REPORT.md` (+ this log, Decisions Log Entry 37, time_log).

## Why this session existed
Session 015's pilot recommended **(A)** (free Dune tier solves the token-side PQ gap) but made it conditional
on one untested risk and two unchecked caveats (`DUNE_PILOT_REPORT.md` §5):
1. Free tier exposes only the **`small`** query engine; a single LDO join already took 66 s on 30 days. Could
   a **full-history, full-panel** scan time out and force a paid `medium`/`large` engine?
2. (a) Is every NaN token's protocol actually in Dune's spellbook? (b) Does a full multi-year grouped query
   complete on `small`? — both for the **real** token list, not the 3-token sample.
Moazzam has university approval to buy a paid plan **if** this dry-run shows the free tier can't cope. This
session produces that decision's actual evidence. (AI must not purchase anything.)

## What I did
1. **Read context first** — Decisions Log Entries 31 (Etherscan rejection — verify before trusting) and 36
   (Dune 3-token pilot), `DUNE_PILOT_REPORT.md` §5, and the pilot scripts
   (`dune_pilot_{test,explore,aggregate,verify}.py`) to reuse the already-validated tables/columns.
2. **Re-derived inputs live** — NaN list from `pq_tokens.csv` (17 in-scope tokens confirmed all-NaN); panel
   range from `universe_panel.csv` (**2015-08 → 2026-05, 130 months**); Dune key present.
3. **Step 1 coverage** (`dune_dryrun_coverage.py`, `dune_dryrun_coverage2.py`):
   - Catalog `/datasets/search` for the 14 unvalidated protocols (hit a **429 rate-limit** after ~14 calls →
     added throttle+retry in coverage2). Found that text-search mostly returns **raw decoded ERC-20/vault
     contracts**, not pre-priced volume series.
   - Decisive test: `SELECT DISTINCT project` from the normalized spells `lending.borrow` (25 projects) and
     `perpetual.trades` (28 projects). This is the real coverage criterion (= what made AAVE/LDO/GNS usable).
4. **Step 2 full-history** (`dune_dryrun_fullpanel.py`): one grouped query per category, **full history**,
   monthly grouping, **`small` only**, with wall-clock/engine-ms/row-count and explicit timeout/cap/error
   watch. Reused the pilot's validated tables and the canonical-WETH price join.
5. **STRK sanity** — its net `amount_usd` came out slightly negative; verified via a `transaction_type`
   breakdown that it's a real protocol ($224.3 M lifetime *borrow* origination), not an empty shell.

## What I found
**Engine (the gated risk) — disproven.** All three full-history grouped queries completed on `small`:
- Lending (`lending.borrow`, aave+strike, full history): **2.0 s wall / 0.4 s engine**, 138 rows.
- Derivatives (Gains DeFiLlama-feed table, full history): **1.9 s / 0.2 s**, 54 rows, Σ $122.8 B notional.
- Liquid staking (Lido two-event join × canonical-WETH price, full history): **48.8 s / 43.1 s**, 102 rows,
  Σ stake $61.1 B / unstake $44.0 B. ← the worst case, still well inside limits.
No timeouts, no row caps, no truncation, no errors. The 66 s pilot figure (30 d) was variance, not a scan
that grows dangerously with history.

**Coverage — most of the 17 are not on Dune (expected).** Only **4 covered** in the normalized spell layer:
AAVE + **STRK** (lending; STRK = `project='strike'`, a **net-new** find beyond the pilot), LDO (staking),
GNS (derivatives). The other **13** (ANC, BZRX, OM, WXT; AVNT, DDX, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR)
appear only as raw token/vault contracts — no normalized notional/volume. MIR's only EVM hits are the
unrelated `mirror.xyz` NFT product (MIR = Mirror **Protocol on Terra**).

## Decision / recommendation
- **(A) for the 4 covered tokens** — free `small` engine handles full-panel full-history scans; **no upgrade
  needed**. The spellbook gap for the other 13 is a **coverage** gap, not an **engine** gap, so a paid plan
  would not help them — **(C)**: they stay flagged-NaN. **No (B) outcome.**
- **Net: do not buy a Dune plan.** Recommend (after human review) a Phase-2c build filling AAVE/STRK/LDO/GNS
  from Dune on the free tier, leaving the other 13 documented NaN. *(Recommendation only — Moazzam decides.)*

## Cost
6 `small` executes (~600 datapoints) + catalog searches (not metered) ≈ <1% of 2,500 free monthly credits.

## Files
- `03_data/DUNE_DRYRUN_REPORT.md` (deliverable)
- `04_code/dune_dryrun_coverage.py`, `dune_dryrun_coverage2.py`, `dune_dryrun_fullpanel.py`
- `03_data/raw/dune_dryrun/*.json`
- Decisions Log **Entry 37**; `time_log.md` updated.

## What NOT done (per scope)
No Phase-2c build; no write to `pq_tokens.csv` or any Phase 2/2b output; no Dune billing action. Stop after
this report pending review.
