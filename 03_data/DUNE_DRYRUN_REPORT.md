# Dune Free-Tier Dry-Run Report — full-panel `small`-engine feasibility + 17-token coverage

**Date:** 2026-06-25
**Session:** 016 (`06_documentation/ai_conversations/session_016_2026-06-25_dune_dryrun.md`)
**Decisions Log:** Entry 37
**Scope:** Diagnostic only. Answers the two caveats left open in `DUNE_PILOT_REPORT.md` §5 for the
**real** token NaN list (not the 3-token sample):
(a) is every NaN token's protocol actually in Dune's normalized spellbook, and
(b) does a **full-history, full-panel** grouped query complete on the free **`small`** engine?
**No panel outputs written.** `pq_tokens.csv` and all Phase 2/2b CSVs are unchanged.

**Code:** `04_code/dune_dryrun_coverage.py`, `dune_dryrun_coverage2.py`, `dune_dryrun_fullpanel.py`
**Raw results:** `03_data/raw/dune_dryrun/`

---

## 0. TL;DR

- **Engine question (b) — settled (A).** The free `small` engine completed **all three** full-history,
  monthly-grouped queries comfortably: lending **2.0 s**, derivatives **1.9 s**, the join-heavy liquid-staking
  query **48.8 s**. No timeouts, no row caps, no errors. **The single risk that the pilot report flagged as
  the one thing that could downgrade to (B) — "small can't finish multi-year scans" — is empirically
  disproven.** A paid plan is **not** needed for the engine.
- **Coverage question (a) — most of the 17 are not on Dune (C).** Only **4 of 17** target tokens are in
  Dune's normalized spell layer: **AAVE** and **STRK** (lending), **LDO** (liquid staking), **GNS**
  (derivatives). STRK is a **net-new** find beyond the 3-token pilot. The other **13** tokens
  (ANC, BZRX, OM, WXT; AVNT, DDX, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR) are **not** in the normalized
  spells — at best a raw decoded ERC-20/vault contract exists, never a pre-priced volume/notional series.
  **A paid plan would not help these** (paid tiers buy bigger engines, not more spellbook coverage); they
  stay flagged-NaN.

**Net recommendation: (A) for the 4 covered tokens — free tier, no upgrade. (C) for the other 13 — not on
Dune at any tier.** There is **no (B) outcome anywhere** — the engine never struggled.

---

## 1. Inputs re-derived live (not trusted from stale copies)

- **NaN token list** re-derived from `03_data/phase2/pq_tokens.csv` (127 unique tokens, 111 all-NaN). The 17
  in-scope tokens confirmed all-NaN: Lending {AAVE, ANC, BZRX, OM, STRK, WXT}, Liquid Staking {LDO},
  Derivatives {AVNT, DDX, GNS, HAKKA, HXRO, KP3R, LINA, MIR, MYX, NMR}.
- **Panel date range** confirmed from `03_data/universe_panel.csv`: **2015-08-31 → 2026-05-31, 130 months**
  (matches the last-checked value).
- **Dune key** present in gitignored `04_code/.api_keys.json` under `"dune"`. Free tier: `small` engine only
  (`medium` rejected, re-confirmed last session).

---

## 2. Step 1 — Coverage check (17 tokens)

**Method.** Two tiers, because catalog text-search alone is misleading. (i) `/v1/datasets/search` tells you
only that a *decoded contract* exists — often just the project's ERC-20 token contract, which has no
transacted-value column. (ii) The decisive test — the thing that made AAVE/LDO/GNS usable in the pilot — is
whether the protocol appears as a `project` value in the **normalized cross-protocol spells**:
`lending.borrow` (pre-priced `amount_usd`) and `perpetual.trades`. A protocol present only as a raw decoded
contract would require hand-rolled reconstruction + a price join — exactly the AAVE-sentinel hazard
(Entry 31) the project has already rejected — so it is **not** counted as cleanly covered.

`SELECT DISTINCT project` returned **25 lending** projects and **28 perp** projects. (The 3 pilot-validated
protocols were not re-searched in the catalog; their coverage was already known.)

### Coverage table

| Token | Category | In normalized spell? | Matched table / `project` | Verdict |
|-------|----------|----------------------|---------------------------|---------|
| **AAVE** | Lending | **Yes** | `lending.borrow`, `project='aave'` | **Covered** (pilot) |
| **STRK** | Lending | **Yes** | `lending.borrow`, `project='strike'` (Strike Finance) | **Covered — NET NEW** |
| ANC | Lending | No | only `anchor_ethereum.anchorvault_*` (ETH bridge vault; Anchor was Terra) | not_found |
| BZRX | Lending | No | only `fulcrum_ethereum.itoken_evt_borrow` (raw decoded events, no spell) | not_found |
| OM | Lending | No | only `mantra_polygon.mantra_call_*` (ERC-20 token contract) | not_found |
| WXT | Lending | No | only `wirex_ethereum.polygonvalidiumetrog_*` (Wirex chain infra, not lending) | not_found |
| **LDO** | Liquid Staking | **Yes** | Lido event tables × canonical-WETH `prices.day` | **Covered** (pilot) |
| **GNS** | Derivatives | **Yes** | `dune.gains.result_g_trade_stats_defi_llama` + `perpetual.trades` `project='gains_network'` | **Covered** (pilot) |
| AVNT | Derivatives | No | only `avantis_base.avantis_evt_transfer` (ERC-20 token) | not_found |
| DDX | Derivatives | No | only `derivadex_ethereum.difundtoken_*` / insurance-fund (no trade table) | not_found |
| HAKKA | Derivatives | No | only `hakkafinance_bnb.permittabletoken_*` token; `blackholeswap` is an AMM, not perps | not_found |
| HXRO | Derivatives | No | only `hxro_ethereum.hxrotokencontract_*` (ERC-20 token) | not_found |
| KP3R | Derivatives | No | only `keep3r_network_ethereum.keep3r_*` job tables (not a perps venue) | not_found |
| LINA | Derivatives | No | only `linear_ethereum.lineartoken_*` (ERC-20 token) | not_found |
| MIR | Derivatives | No | only `mirror.xyz` writing-editions NFT noise (wrong Mirror; MIR = Mirror Protocol on **Terra**) | not_found |
| MYX | Derivatives | No | decoded `myx_arbitrum.router_*`/`positionmanager_*` calls exist but **not** in `perpetual.trades` (no normalized notional) | not_found |
| NMR | Derivatives | No | only `numerai_ethereum.numerairebackend_*` (staking backend, no notional) | not_found |

**Full `DISTINCT project` lists (for the record):**
- **lending.borrow (25):** aave, aave_etherfi, aave_horizon, aave_lido, agave, benqi, compound, euler,
  fluxfinance, granary, layer_bank, lodestar, moola, moonwell, morpho, pike, radiant, realt_rmm,
  seamlessprotocol, sonne_finance, spark, **strike**, uwulend, venus, zerolend.
- **perpetual.trades (28):** AVT, FXDX, Minerva Money, Mummy Finance, NEX, OPX Finance, Perpetual, Pika,
  Synthetix, Unidex, basemax_finance, bmx, emdx, **gains_network**, gmx, hubble_exchange, immortalx,
  katanaperps, leverup, meridian, mummy_finance, mux_protocol, nether_fi, perpl, tigris_trade,
  vela_exchange, voodoo_trade, xena.

**Reading of the gap.** This is the report's own predicted finding, confirmed for the real list: Dune's
normalized spells cover the **majors** (Aave, Strike, Compound, Morpho, Spark… ; gmx, Synthetix,
gains_network, mux…) but **not** the long-tail protocols behind these particular NaN tokens. Most of the 17
are small/dead/Terra-era/non-EVM protocols whose only EVM footprint is a token contract.

---

## 3. Step 2 — Full-history, full-panel grouped query per category (`small` engine only)

All queries: **full history (no 30-day window)**, monthly grouping, free `small` engine. Wall-clock and
engine time recorded; explicitly watched for timeout / row cap / Dune error.

| Category | Query | State | Rows | Engine ms | **Wall s** | Notes |
|----------|-------|-------|------|-----------|------------|-------|
| **Lending** | `lending.borrow` GROUP BY project, month, `project IN ('aave','strike')`, full history | COMPLETED | 138 | 402 | **2.0** | aave 78 mo (2020-01→2026-06); strike 60 mo (2021-03→2026-05) |
| **Derivatives** | `dune.gains.result_g_trade_stats_defi_llama` GROUP BY month, full history | COMPLETED | 54 | 232 | **1.9** | GNS 54 mo (2022-01→2026-06), Σ notional **$122.8 B** |
| **Liquid Staking** | Lido submit + withdrawalclaimed × **canonical-WETH** `prices.day`, GROUP BY month, full history | COMPLETED | 102 | 43,085 | **48.8** | Σ stake **$61.1 B**, unstake **$44.0 B** |

**No query timed out, hit a row cap, or returned a Dune error.** `total_row_count == rows_returned` for all
three (no truncation). The heaviest — the Lido two-event join against a full-history daily price series —
took **48.8 s wall / 43.1 s engine** on `small`, comfortably inside limits (and, notably, *faster* than the
pilot's 66 s for the same join over only 30 days — i.e. the 66 s was overhead/variance, not a scan that
grows dangerously with history).

**Data-semantics cross-checks (so the timings rest on real numbers, per Entry 31/36):**
- **Lending.** Summed across all transaction types, `strike` netted **−$0.02 B** (repays/liquidations carry
  negative `amount_usd`). Verified the protocol is genuinely live, not an empty shell: filtered to
  `transaction_type='borrow'`, **Strike Finance = $224.3 M lifetime borrow origination** (3,746 borrows;
  repay −$228.6 M, liquidation −$11.0 M). AAVE net stays positive at **$7.90 B**. → a real Phase-2c build
  filters `transaction_type='borrow'` (or `amount_usd>0`), exactly the pilot's convention. STRK is small but
  real.
- **Liquid staking.** Months span 2018-01→2026-06, but real Lido stake data begins ~Dec 2020; the earlier
  months come from the price-side `LEFT JOIN` (null stake/claim) and are harmless — a Phase-2c build drives
  off the submit table or filters to ≥ first Lido month. Price join used the **canonical WETH contract**
  `0xc02a…756cc2`, never `symbol='WETH'` (the Entry-36 scam-token trap).
- **Derivatives.** GNS lifetime notional **$122.8 B** over 54 months ($2.3 B/mo avg) is consistent with the
  pilot's $1.18 B/30d recent run-rate and gTrade's known volume band.

---

## 4. Recommendation (per category)

**(A) Lending — free `small`, no upgrade.** `lending.borrow` is one cross-protocol `GROUP BY project, month`
query for the *entire* lending panel's full history, **2.0 s** on `small`. Covered NaN tokens: **AAVE, STRK**.
The other four (ANC, BZRX, OM, WXT) fall under (C).

**(A) Liquid Staking — free `small`, no upgrade.** The join-heavy LDO query — the worst case for `small` —
finished full-history in **48.8 s**. Covered: **LDO** (the only liquid-staking NaN token). Requires
canonical-contract price-join discipline, but no engine upgrade.

**(A) Derivatives — free `small`, no upgrade (for the one covered token).** GNS via the Gains DeFiLlama-feed
table, full history **1.9 s** — and this is the dimension DeFiLlama **paywalls at 402**, retrieved free on
Dune. Covered: **GNS**. The other nine derivatives tokens fall under (C).

**(C) The 13 uncovered tokens — not on Dune at any tier.** ANC, BZRX, OM, WXT, AVNT, DDX, HAKKA, HXRO, KP3R,
LINA, MIR, MYX, NMR are absent from Dune's normalized spells. **A paid plan would not recover them** — paid
tiers buy a bigger query engine, not additional spellbook coverage. They remain **flagged-NaN** with the
existing documented reasons (no transacted-value object / wrong-chain / dead protocol), unchanged by this
dry-run. (In principle a few — MYX's decoded router, Fulcrum's `itoken_evt_borrow` — could be hand-
reconstructed from raw decoded events, but that is the rejected AAVE-sentinel path and out of scope.)

### Net call on the funding question
**No paid Dune plan is needed.** The pilot report made (A) conditional on this dry-run showing `small`
survives full-history scans; it does, decisively (worst case 48.8 s). The remaining coverage gap is a
**spellbook** gap, not an **engine** gap, so spending money would not close it. Recommend: **stay on the
free tier; proceed (after human review) to a Phase-2c build that fills AAVE, STRK, LDO, GNS from Dune and
leaves the other 13 as documented NaN.** *(Decision for Moazzam — do not purchase anything on this basis;
this is a recommendation, not an action.)*

---

## 5. Credit cost

Catalog `/datasets/search` calls are **not** query-credit-metered. `/sql/execute` this session: 2 coverage
`DISTINCT project` (engine 2.7 s + 0.7 s) + 3 full-history (0.4 s + 0.2 s + 43.1 s engine) + 1 STRK
verification (0.3 s) = **6 small executes, ~600 datapoints total**, well under 1% of the 2,500 free monthly
credits. Combined with the pilot's ~100, the free monthly pool is barely touched.

---

## 6. Reproducibility

```
python 04_code/dune_dryrun_coverage.py     # Step 1: catalog text-search (free), 17 tokens
python 04_code/dune_dryrun_coverage2.py    # Step 1: decisive DISTINCT-project spell coverage + throttled re-search
python 04_code/dune_dryrun_fullpanel.py    # Step 2: full-history grouped queries, small engine, with timings
```
Raw JSON in `03_data/raw/dune_dryrun/` (`coverage_search.json`, `coverage2_spell_projects.json`,
`full_lending_fullhist.json`, `full_gns_fullhist.json`, `full_ldo_fullhist.json`, `fullpanel_calls.json`).
Key in gitignored `04_code/.api_keys.json` under `"dune"`.

**Do not start a Phase-2c build until this report is reviewed.**
