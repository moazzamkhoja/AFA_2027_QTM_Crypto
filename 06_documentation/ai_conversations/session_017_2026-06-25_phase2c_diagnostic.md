# Session 017 — Phase 2c Diagnostic: TVL/Fees/Volume/APY Metadata Audit (111 NaN tokens)

**Date:** 2026-06-25
**Agent:** Claude Code / Opus 4.8 (local, normal network access)
**Prompt:** `04_code/CLAUDE_CODE_PHASE2C_DIAGNOSTIC_PROMPT.md` (drafted in the Entry-38 Cowork session)
**Scope:** **Diagnostic / feasibility map only.** For each currently-NaN, non-Gaming token: what free
DeFiLlama data exists, and could any of it plausibly become a transacted-value PQ given the protocol's
economic model? **No `pq_tokens.csv` write, no PQ value computed, nothing purchased.**
**Deliverable:** `03_data/PHASE2C_DIAGNOSTIC_REPORT.md` (+ this log, Decisions Log Entry 39, time_log).

## Why this session existed
The Entry-38 Cowork discussion challenged the Dune dry-run's 4-of-17 coverage as too thin and asked whether
TVL (a stock) could be converted into a PQ flow via a calibrated "turnover" rate (the AK-model framing,
Y=A·K ⇒ PQ=A·TVL). This session is the live, local audit that decision required: walk the full 111-token
NaN universe (not just the 17 Dune-scoped tokens), check what DeFiLlama actually has per token, and test
whether TVL×turnover is statistically defensible against a real comparable-protocol cohort — before any
build is authorized.

## What I did
1. **Read context first** — DATA_DECISIONS_LOG Entries 30 (TVL is capital stock, not PQ), 31 (Etherscan
   rejection — verify before trusting), 32 (fee→volume inversion rule), 36/37 (Dune pilot + dry-run; the
   4 covered tokens AAVE/STRK/LDO/GNS), 38 (this session's framing); `DUNE_DRYRUN_REPORT.md` §2 (the 25
   lending + 28 perp `DISTINCT project` cohorts); `pq_tokens.csv`; `dune_dryrun_fullpanel.py`.
2. **Step 1 — re-derived the worklist live** (`phase2c_defillama_metadata.py` preamble): 127 tokens, 16
   covered, **111 NaN**, − 7 Gaming = **104 audited**. Category counts matched the kickoff exactly. NVT
   collision noted (slug `nerve-staking`, key by slug not ticker).
3. **Verified every endpoint shape live before relying on it** (not from docs): `protocol/{slug}` tvl[],
   `summary/fees/{slug}?dataType=dailyFees|dailyRevenue`, `summary/{dexs,derivatives,options}/{slug}`,
   `yields.llama.fi/pools`, `bridges.llama.fi/*`.
4. **Step 2 — per-token metadata for all 104** (`phase2c_defillama_metadata.py`): TVL/Fees/Revenue/direct-
   volume/APY presence + date ranges. Then **investigated the 7 Dexs-category tokens for slug mismatches**
   (the kickoff's "check direct volume FIRST" instruction), verifying protocol identity by cmcId.
5. **Step 3 — turnover-calibration cohort** (`phase2c_turnover_cohort.py` + `phase2c_turnover_refine.py`):
   pulled the full `lending.borrow` (25 proj, borrow-filtered) and `perpetual.trades` (28 proj) cohorts
   from Dune; mapped each to a DeFiLlama slug **individually verified by name/cmcId** (not string-matched);
   computed turnover = PQ/TVL per protocol-month; ran a refinement pass summing TVL across all version
   slugs (aave-v1+v2+v3+v4, …) to separate true dispersion from version-scope artifact.
6. **Step 4 — per-token verdicts** (`phase2c_verdicts.py`) + wrote the report, this log, Entry 39, time_log.

## What I found
**Only 5 of 104 tokens have a defensible free-tier transacted-value path — and 4 were already known.**
- **AAVE, STRK, LDO, GNS** — the Entry-37 Dune-spell set (unchanged).
- **SUN — the one genuinely-new find.** Its AMM is SunSwap; DeFiLlama's `dexs` vertical carries it under
  `sunswap-v1/v2/v3` (the stored slug `sun.io` is not in the vertical → why Phase 2 missed it). Direct
  volume 2020-08→2026-06, no proxy needed. Verified by identity (sun.io cmcId 10529; the AMM is SUN's).

**Two symbol-collision traps correctly avoided** (cmcId mismatch, exactly the NVT-collision hazard):
- `dexs 'nerve'` = Nerve Finance (NRV, cmcId **8755**) ≠ NVT/Nerve Network (cmcId **5906**).
- `dexs 'velodrome-*'` = a different VELO (Optimism) ≠ velo-finance (cmcId 7127, Stellar payments).

**The TVL→PQ turnover idea is NOT defensible as a level** (the session's central result):
- **Lending** (816 protocol-months, 21 projects, scope-matched): pooled median turnover ≈ 0.28/month, but
  per-project medians span **0.0008 → 1.24 (~1,455×)**; core cluster still ~10×; the low tail (venus
  0.0008) survived scope-matching, so it's real dispersion, not artifact.
- **Perpetual** (436 protocol-months, 16 projects): per-project medians **0.0000 → 108.8 — no central
  tendency** (partly real high perp turnover, partly artifact — gains undercounted in `perpetual.trades`,
  tigris matched a $9k-TVL shell). Calibrating one perp rate is impossible.

**TVL×APY (path 3) collapses on availability:** `yields.llama.fi/pools` is a *current* snapshot, so 25 of
the 28 Farm/Yield tokens (dead/delisted) have no APY at all; only CVX/FARM/ZBU have a current rate, and
none has a free historical APY series → weak (constant-APY assumption required).

**Fee-inversion fired for zero tokens** — 26 have a Fees series but none is a single fixed volume-linked
rate (L2 gas, bridge per-transfer, lending reserve factors, variable perps), consistent with Entry 33.

**Two NEW landmines (both change kickoff assumptions):**
1. **`bridges.llama.fi` is fully 402-paywalled** (all endpoint shapes) — the kickoff assumed it was free.
   The 11 bridge tokens have a *valid* object (transfer volume) that's simply not free.
2. The nerve/NVT and velodrome/VELO collisions are live traps (handled above).

## Verdict tally (104 tokens)
| verdict | n |
|---|---|
| ✓ Dune spell (AAVE, STRK, LDO, GNS) | 4 |
| ✓ direct volume (SUN) | 1 |
| ~ weak TVL×APY (CVX, FARM, ZBU) | 3 |
| ✗ turnover undefensible | 14 |
| ✗ no APY (dead farm/yield) | 25 |
| ✗ bridge volume paywalled | 11 |
| ✗ symbol collision (NVT, VELO) | 2 |
| ✗ no economic model | 44 |

## Recommendation handed back
Build (after review) only the **5 viable tokens** — AAVE/STRK/LDO/GNS (Dune free) + SUN (DeFiLlama dexs),
zero subscription. **+1 net-new token (SUN) over Entry 37.** Report TVL×turnover and TVL×APY in the paper
as **explored-and-rejected** (the turnover-dispersion negative result is itself a §6 methodological
finding). Leave ~96 tokens documented-NaN. Two paid levers (DeFiLlama Pro for derivatives+bridges; a
bridges-API tier) flagged for Moazzam's decision, **not acted on**.

## Files
- Report: `03_data/PHASE2C_DIAGNOSTIC_REPORT.md`
- Code: `04_code/phase2c_{defillama_metadata,turnover_cohort,turnover_refine,verdicts}.py`
- Data (diagnostic): `03_data/phase2/phase2c_{worklist,metadata,verdicts,turnover,turnover_scopematched}.csv`
- Raw JSON: `03_data/raw/phase2c/`
- Decisions Log: Entry 39

**No panel outputs written. Do not start the Phase 2c build before this report is reviewed.**
