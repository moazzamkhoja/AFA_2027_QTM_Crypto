# Phase 2c Diagnostic Report — TVL / Fees / Volume / APY Metadata Audit of the 111 NaN Tokens

**Date:** 2026-06-25
**Session:** 017 (`06_documentation/ai_conversations/session_017_2026-06-25_phase2c_diagnostic.md`)
**Decisions Log:** Entry 39
**Scope:** **Diagnostic / feasibility map only. No `pq_tokens.csv` write, no PQ value computed, nothing
purchased.** Answers, per the Entry-38 framing: for each currently-NaN token, *what data exists, and
given that protocol's actual economic model, could any of it plausibly become a transacted-value (PQ)
measure?*

**Code:** `04_code/phase2c_defillama_metadata.py` (Step 2), `phase2c_turnover_cohort.py` +
`phase2c_turnover_refine.py` (Step 3), `phase2c_verdicts.py` (Step 4).
**Data artifacts (diagnostic, not panel):** `03_data/phase2/phase2c_{worklist,metadata,verdicts,
turnover,turnover_scopematched}.csv`. Raw JSON under `03_data/raw/phase2c/`.

---

## 0. TL;DR

- **Worklist re-derived live:** `pq_tokens.csv` = 127 tokens, 16 covered, **111 NaN**; dropping the 7
  Gaming tokens (out of scope, stay NaN by design) leaves **104** tokens audited. Counts match the
  kickoff exactly.
- **Of the 104, only 5 have a defensible free-tier transacted-value path, and 4 of those were already
  known** (the Entry-37 Dune-spell set: **AAVE, STRK, LDO, GNS**). **The single genuinely-new find this
  session is SUN** — its AMM is SunSwap, whose DEX volume sits in DeFiLlama's `dexs` vertical under the
  slugs `sunswap-v1/v2/v3` (the token's stored slug `sun.io` is not in the vertical, which is why the
  original Phase-2 populate missed it). **→ direct volume, no proxy needed.**
- **The TVL→PQ stock-to-flow conversion idea (path 4, the motivation for this whole audit) is NOT
  statistically defensible as a level.** The 25-lending + 28-perp Dune calibration cohort shows turnover
  (PQ/TVL) dispersion of **~1,455× across lending protocols** and **effectively unbounded across perps**
  (per-project medians 0.0000 → 108.8). Even after fixing TVL version-scope mismatches, lending's core
  cluster is still ~10× and perps has no central tendency at all. A borrowed category-average turnover
  rate would be a fabricated number, exactly what spec §0 forbids.
- **TVL×APY (path 3) collapses on data availability:** `yields.llama.fi/pools` is a *current snapshot*,
  so the 28 Farm/Yield/Yield-Aggregator tokens that are mostly **dead/delisted protocols** have no APY
  rate at all (25 of 28). Only 3 still-live ones (CVX, FARM, ZBU) have a current APY — and even those
  have **no free historical APY series**, so a monthly panel would require an indefensible constant-APY
  assumption. Weak at best.
- **Two NEW landmines found this session** (both materially change the kickoff's assumptions):
  1. **`bridges.llama.fi` is now fully 402-paywalled** — every endpoint shape (`/bridges`,
     `/bridge/{id}`, `/bridgevolume/{chain}`, `/bridgedaystats`). The kickoff assumed it was free. So the
     11 bridge-category tokens have a *valid* transacted-value object (transfer volume) that is simply
     **not free** — distinct from "no object."
  2. **The `nerve` / NVT and `velodrome` / VELO symbol collisions are live traps** that a naive slug
     re-match would have fallen into. Both correctly ruled out on cmcId mismatch (see §2).
- **Net recommendation:** a real Phase-2c build is worth running **only for the 5 viable tokens**
  (AAVE, STRK, LDO, GNS via Dune free tier; SUN via DeFiLlama dexs) — **+1 net-new token (SUN) over what
  Entry 37 already authorized**, at zero subscription cost. The TVL×turnover and TVL×APY ideas should be
  **reported in the paper as explored-and-rejected**, not built. The other ~96 tokens stay documented-NaN.

---

## 1. Worklist (Step 1) — re-derived live, not trusted from a stale count

From `03_data/phase2/pq_tokens.csv` (a token = "covered" if it has ≥1 non-NaN `pq_usd` month):

| | count |
|---|---|
| total unique tokens | 127 |
| covered | 16 |
| NaN | 111 |
| NaN − Gaming(7) = **audited** | **104** |

Live category breakdown of the 111 NaN matches the kickoff exactly (Yield 16, Derivatives 10, Farm 8,
Gaming 7, Dexs 7, Services 7, Bridge 6, Lending 6, Launchpad 6, Chain 6, Yield Aggregator 4, Canonical
Bridge 3, Developer Tools 3, Cross Chain Bridge 2, Token Locker 2, + 17 singleton categories). The 7
Gaming tokens (AXS, ILV, MAGIC, MBOX, PRIME, TLM, YGG) are excluded per Entry 38 and stay NaN.

**NVT collision handled as instructed:** the NaN Dexs token with ticker `NVT` is `nerve-staking`
(cmc_id 5906, Nerve Network) — unrelated to the NVT *metric*. All matching below is keyed by `dl_slug`
/ cmcId, never bare ticker.

---

## 2. Per-token DeFiLlama metadata (Step 2) — what free data actually exists

Endpoint shapes were **live-verified against current behaviour** before the run (not assumed from docs):
`api.llama.fi/protocol/{slug}` (`tvl[]`), `api.llama.fi/summary/fees/{slug}?dataType=dailyFees|dailyRevenue`
(`totalDataChart`), `api.llama.fi/summary/{dexs,derivatives,options}/{slug}`, `yields.llama.fi/pools`.
Free surface only; no Pro API.

**Aggregate presence across the 104:** TVL **83**, Fees **26**, Revenue **24**, direct DEX volume **0**,
current APY snapshot **10**. **Direct volume from the free verticals is empty** for the NaN set:
- **`dexs`** — every one of the 104 returns HTTP 400 ("slug not in the dexs vertical"); verified legitimate
  (a covered slug like `airswap` returns 200). The 7 Dexs-category NaN tokens are genuinely absent from the
  vertical *under their stored slug* — but see the SUN recovery and the two collisions below.
- **`derivatives`** — all 10 Derivatives tokens return **402** (the known paywall, re-confirmed per-token).
- **`bridges.llama.fi`** — **NEW: fully 402-paywalled** across all endpoint shapes. The 11 bridge tokens
  therefore have no free transfer-volume series.
- **`options`** — OPIUM (the one Options token) is absent (400/empty).

### The three Dexs-category resolutions (verified by protocol identity, not string match)

| Token (cmc_id) | Stored slug | Candidate in dexs vertical | cmcId of candidate | Ruling |
|---|---|---|---|---|
| **SUN (10529)** | `sun.io` | `sunswap-v1/v2/v3` (symbol SUN) | v1=1116, v2/v3 null | **MATCH** — SUN.io's AMM is SunSwap; sum the 3 versions. Volume 2020-08→2026-06. → **direct volume** |
| **NVT (5906)** | `nerve-staking` (gecko `nervenetwork`) | `nerve` (Nerve Finance, NRV) | **8755** | **REJECT** — different project (8755 ≠ 5906). Collision trap. |
| **VELO (7127)** | `velo-finance` (gecko `velo`, Stellar payments) | `velodrome-v1/v2/v3` (Optimism AMM) | different VELO (20435) | **REJECT** — different project. The flagged VELO/SXP collision. |

The full 104-row metadata table is `03_data/phase2/phase2c_metadata.csv`; the verdict-annotated version is
`phase2c_verdicts.csv`. The grouped per-token table is in §5 below.

**Fee-inversion (path 2) fired for zero tokens — consistent with the original Phase-2 build (Entry 33).**
26 tokens have a Fees series, but none is a *single, fixed, confidently-citable rate on a notional volume*:
they are L2 sequencer/gas fees (ARB, ZK), bridge per-transfer fees (W, SYN), domain registration (ENS),
restaking/query/curation fees (EIGEN, GRT, API3), lending reserve factors (AAVE/STRK — a % of interest,
not of loan volume), or variable/multi-tier perps fees (GNS, MYX, AVNT). Every one fails the Entry-32 test
("back out volume from fee only when the rate is a confidently known single stable function of notional"),
so the backout is flagged `fee_rate_not_confidently_known` for all and used for none.

---

## 3. Turnover-calibration cohort (Step 3) — is TVL × turnover defensible?

**Method.** Reused the validated Dune pattern (`dune_dryrun_fullpanel.py`) to pull the **full** `DISTINCT
project` lists: `lending.borrow` filtered `transaction_type='borrow' AND amount_usd>0` (25 projects, 921
project-months) and `perpetual.trades` summing `volume_usd` (28 projects, 560 project-months), both full
history, `GROUP BY project, month`, free `small` engine (lending 61 s, perps 7 s). Each Dune `project` was
mapped to a DeFiLlama slug **individually verified by name/cmcId/category** (not string-matched), and that
protocol's TVL history pulled from `api.llama.fi/protocol/{slug}`. `turnover = monthly_PQ / month_end_TVL`.

A first pass matched each project to a single version-slug; because Dune's `project='aave'` aggregates
*all* Aave versions while `aave-v3` is one version, this mismatched scope and inflated dispersion. A
**refinement pass** (`phase2c_turnover_refine.py`) summed TVL across **all** of a protocol's version slugs
(aave-v1+v2+v3+v4, compound-v1+v2+v3, venus-core+isolated+flux, …, verified against the live `/protocols`
list) to separate true dispersion from mapping artifact. Slug-match rate: **lending 21/25, perps 16/28**
(unmatched = dead/Terra-era/non-EVM protocols absent from DeFiLlama, listed in the CSVs).

### Lending — scope-matched (816 protocol-months, 21 projects)

- Pooled median monthly turnover ≈ **0.28** (loan origination ≈ 28% of TVL/month ⇒ ~3.5-month avg loan life).
- **Per-project median turnover spans 0.0008 → 1.24 — a ~1,455× spread.** Trimming the single highest/lowest
  project still leaves **243×**.
- The *core* cluster is tighter but still wide: compound 0.13, agave 0.22, strike 0.27, spark 0.28, granary
  0.35, uwulend 0.37, morpho 0.43, aave 0.64, sonne 0.71, benqi 0.80, radiant 0.81, seamless 0.96, moonwell
  1.24 — roughly **0.13–1.24, ≈10×**. The low tail (venus 0.0008, euler 0.004, layer_bank 0.004, zerolend
  0.014, moola 0.03) is 1–2 orders below and **survived scope-matching** — i.e. venus's tiny turnover is
  *real* (a very-high-TVL pool with modest monthly origination), not an artifact.

### Perpetual — scope-matched (436 protocol-months, 16 projects)

- **Per-project median turnover spans 0.0000 → 108.8 — effectively unbounded; no central tendency.**
  gains_network 0.0000, mummy 0.0004, mux 0.006 … then bmx 2.5, gmx 2.8, synthetix 3.7, hubble 4.7,
  Pika 9.9, Perpetual 23.1, tigris 108.8.
- Part is real (active perp DEXs genuinely run high notional/TVL), part is artifact: **gains_network's
  notional is undercounted in `perpetual.trades`** (its volume lives in the separate DeFiLlama-feed table
  used in Entry 37, hence the ≈0), and tigris matched a $9k-TVL shell slug. Either way, the distribution has
  **no usable centre** — calibrating one perp turnover rate is impossible.

### Verdict on path 4

> **TVL × calibrated turnover is not defensible as a PQ *level*.** Lending dispersion is ~3 orders of
> magnitude overall (~10× even in the core cluster); perps has no central tendency. Borrowing a category
> turnover rate would manufacture a number whose error dwarfs the signal. *At most*, lending's pooled
> median (~0.28) could serve as a coarse **order-of-magnitude rank** proxy (the paper already treats
> NVT_GL as rank-not-level, Entry 33) — but only for pooled-market lenders, never isolated-market ones, and
> never for perps. The honest call: **report this as explored-and-rejected, do not build it.**

---

## 4. Closing recommendation

**Build (Phase 2c, after review) — 5 tokens, free tier, zero subscription:**
- **AAVE, STRK, LDO, GNS** — Dune normalized spells, exactly as Entry 37 authorized (`lending.borrow`
  `transaction_type='borrow'`; Lido events × canonical-WETH `prices.day`; gains DeFiLlama-feed table).
- **SUN** — **NET-NEW** — DeFiLlama `dexs` volume = `sunswap-v1`+`sunswap-v2`+`sunswap-v3`, summed monthly,
  2020-08→2026-06. The one token this audit adds beyond the prior Dune work.

**Weak / conditional — 3 tokens, do not build without an explicit lower bar:**
- **CVX, FARM, ZBU** — TVL present + a *current* yields snapshot, but no free historical APY ⇒ a TVL×APY
  panel needs a constant-APY assumption. Only worth it if a current-rate-held-constant proxy is explicitly
  acceptable; otherwise leave NaN.

**Do not build — 96 tokens, documented NaN:**
- **14 `turnover_undefensible`** (lending ANC/BZRX/OM/WXT, uncoll. TRU, 9 derivatives) — only path is the
  rejected TVL×turnover.
- **25 `no_apy`** — dead/delisted Farm/Yield protocols absent from the yields snapshot.
- **11 `bridge_vol_paywalled`** — transfer volume is the right object but `bridges.llama.fi` is 402. These
  **reopen only if bridges-API access is obtained** (a real lever, unlike the others) — flag, don't pay.
- **2 `symbol_collision`** (NVT, VELO) — kept NaN to avoid attributing another project's volume.
- **44 `no_economic_model`** — Chain / Services / Launchpad / Developer Tools / Token Locker / Domains /
  Payments / CEX / etc.: no capital→flow channel and no transacted-value object to measure.

**Funding:** nothing here justifies a purchase. Dune free tier covers the 4; DeFiLlama free covers SUN. The
two paid levers that *would* extend coverage — DeFiLlama Pro (derivatives + bridges verticals) and a
bridges-API tier — are **flagged for Moazzam's decision, not acted on**, same standing rule as Dune.

**Bottom line for the paper's cross-section:** the token-side PQ panel realistically grows from 16 covered
to **≈21 (16 + AAVE/STRK/LDO/GNS/SUN)**, not to "most of 111." The TVL-as-flow idea, while theoretically
clean (the AK-model framing of Entry 38), founders on **empirical turnover dispersion**, and that negative
result is itself a reportable methodological finding (spec §6).

---

## 5. Per-token feasibility table (104 rows, grouped by category)

Legend — Verdict: `✓dune_spell` / `✓direct_volume` = viable free path; `~tvl_apy` = weak (current-APY only);
`✗turnover_undefensible` / `✗no_apy` / `✗bridge_vol_paywalled` / `✗symbol_collision` / `✗no_economic_model`
= stays NaN. TVL/Fees ranges are YYYY-MM. "DirectVol": `derivs-402`/`402-paywall` = paywalled vertical,
`none` = not in any free vertical. APY(cur) = # live pools in the current yields snapshot.
#### Derivatives (10)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| GNS | gains-network | 2021-12->2026-06 | 2022-07->2026-06 | Y | derivs-402 | 9p | ✓dune_spell |
| AVNT | avantis | 2024-02->2026-06 | 2024-03->2026-06 | Y | derivs-402 | 1p | ✗turnover_undefensible |
| DDX | derivadex | 2021-03->2026-06 | N | N | derivs-402 | N | ✗turnover_undefensible |
| HAKKA | hakka-finance | 2020-10->2026-06 | N | N | derivs-402 | N | ✗turnover_undefensible |
| HXRO | hxro-network | 2023-02->2026-06 | N | N | derivs-402 | N | ✗turnover_undefensible |
| KP3R | keep3r-network | 2021-10->2026-06 | N | N | derivs-402 | N | ✗turnover_undefensible |
| LINA | linear-finance | 2021-12->2026-06 | N | N | derivs-402 | N | ✗turnover_undefensible |
| MIR | mirror | 2021-04->2023-10 | N | N | derivs-402 | N | ✗turnover_undefensible |
| MYX | myx-finance | 2024-03->2026-06 | 2025-03->2026-06 | Y | derivs-402 | N | ✗turnover_undefensible |
| NMR | erasure | 2021-03->2026-06 | N | N | derivs-402 | N | ✗turnover_undefensible |

#### Dexs (7)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| SUN | sun.io | 2021-07->2026-06 | N | N | none | N | ✓direct_volume |
| NVT | nerve-staking | 2021-06->2026-06 | N | N | none | N | ✗symbol_collision |
| VELO | velo-finance | 2024-08->2026-06 | 2024-05->2026-06 | Y | none | N | ✗symbol_collision |
| BAKE | bakeryswap | 2021-07->2026-06 | N | N | none | N | ✗no_economic_model |
| CASINO | defyswap | 2021-12->2026-06 | N | N | none | N | ✗no_economic_model |
| LRC | loopring | 2020-08->2026-06 | N | N | none | 14p | ✗no_economic_model |
| SXP | swipe | 2021-03->2026-06 | N | N | none | N | ✗no_economic_model |

#### Lending (6)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| AAVE | aave-v2 | 2020-12->2026-06 | 2020-12->2026-06 | Y | none | N | ✓dune_spell |
| STRK | strike | 2021-09->2026-06 | 2024-08->2026-06 | Y | none | N | ✓dune_spell |
| ANC | anchor | 2021-04->2023-10 | N | N | none | N | ✗turnover_undefensible |
| BZRX | ooki | 2021-02->2025-06 | N | N | none | N | ✗turnover_undefensible |
| OM | mantra-dao | 2021-06->2026-06 | N | N | none | N | ✗turnover_undefensible |
| WXT | nereus-finance | 2022-02->2026-06 | N | N | none | N | ✗turnover_undefensible |

#### Liquid Staking (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| LDO | lido | 2020-12->2026-06 | 2021-04->2026-06 | Y | none | 1p | ✓dune_spell |

#### Farm (8)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ZBU | zeebu | 2024-12->2026-06 | N | N | none | 2p | ~tvl_apy |
| AURORA | aurora-plus | 2022-09->2026-06 | N | N | none | N | ✗no_apy |
| C98 | coin98 | 2025-04->2026-06 | N | N | none | N | ✗no_apy |
| CHEEL | cheelee | N | N | N | none | N | ✗no_apy |
| LGCT | legacy-network | N | N | N | none | N | ✗no_apy |
| MEME | memecoin | N | N | N | none | N | ✗no_apy |
| ORBS | orbs | 2024-12->2026-06 | N | N | none | N | ✗no_apy |
| VVV | venice | 2026-05->2026-06 | 2025-12->2026-06 | Y | none | N | ✗no_apy |

#### Yield (16)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| CVX | convex-finance | 2021-05->2026-06 | 2021-05->2026-06 | Y | none | 193p | ~tvl_apy |
| ADF | artdefinance | 2024-01->2026-06 | N | N | none | N | ✗no_apy |
| AKRO | akropolis | 2020-08->2026-06 | N | N | none | N | ✗no_apy |
| APE | apecoin | N | N | N | none | N | ✗no_apy |
| BRISE | bitgert | 2022-07->2026-06 | 2024-12->2026-06 | N | none | N | ✗no_apy |
| BTCST | btcst | 2021-12->2026-06 | N | N | none | N | ✗no_apy |
| CORE | cvault-finance | 2021-03->2026-06 | N | N | none | N | ✗no_apy |
| EPIC | ethernity-chain | 2021-06->2026-06 | N | N | none | N | ✗no_apy |
| FLEX | coinflex | 2022-05->2026-06 | N | N | none | N | ✗no_apy |
| HEX | hex | 2019-12->2026-06 | N | N | none | N | ✗no_apy |
| MET | metronome-v1 | 2021-03->2026-06 | N | N | none | N | ✗no_apy |
| MVL | mvl-staking | 2023-10->2026-06 | N | N | none | N | ✗no_apy |
| PEAK | peakdefi | 2021-03->2026-06 | N | N | none | N | ✗no_apy |
| RFOX | rfox | 2022-04->2026-06 | N | N | none | N | ✗no_apy |
| SFI | saffron-finance | 2021-11->2026-06 | N | N | none | N | ✗no_apy |
| TIME | timewarp | 2021-09->2026-06 | N | N | none | N | ✗no_apy |

#### Yield Aggregator (4)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| FARM | harvest-finance | 2020-10->2026-06 | N | N | none | 53p | ~tvl_apy |
| BADGER | badger-dao | 2020-12->2026-06 | 2025-02->2026-06 | Y | none | N | ✗no_apy |
| RGT | rari-capital | 2020-10->2026-06 | N | N | none | N | ✗no_apy |
| YFII | yfii | 2021-04->2026-06 | N | N | none | N | ✗no_apy |

#### Uncollateralized Lending (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| TRU | truefi | 2020-11->2026-06 | N | N | none | N | ✗turnover_undefensible |

#### Bridge (6)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| BICO | hyphen | 2022-03->2026-02 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |
| CELR | cbridge | 2021-11->2026-06 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |
| MERL | merlins-seal | 2024-02->2026-06 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |
| PNT | pnetwork | 2021-09->2024-11 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |
| REN | renvm | 2020-10->2025-06 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |
| W | portal | 2021-09->2026-06 | 2025-05->2026-06 | Y | 402-paywall | N | ✗bridge_vol_paywalled |

#### Canonical Bridge (3)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ACA | acala | N | 2024-12->2026-06 | Y | 402-paywall | N | ✗bridge_vol_paywalled |
| ARB | arbitrum | N | 2021-08->2026-06 | Y | 402-paywall | N | ✗bridge_vol_paywalled |
| STAKE | xdai-stake-bridge | 2020-10->2026-06 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |

#### Cross Chain Bridge (2)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| KEEP | keep-network | 2020-10->2026-06 | N | N | 402-paywall | N | ✗bridge_vol_paywalled |
| SYN | synapse | 2021-08->2026-06 | 2021-08->2026-06 | Y | 402-paywall | 11p | ✗bridge_vol_paywalled |

#### CEX (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| BMX | bitmart | 2023-09->2026-06 | N | N | none | N | ✗no_economic_model |

#### Chain (6)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| BEAM | beam | N | N | N | none | N | ✗no_economic_model |
| TAO | bittensor | N | N | N | none | N | ✗no_economic_model |
| WLD | worldcoin | N | N | N | none | N | ✗no_economic_model |
| ZK | zksync-era | N | 2023-02->2026-06 | Y | none | N | ✗no_economic_model |
| ZKB | zkswap | 2021-02->2026-06 | N | N | none | N | ✗no_economic_model |
| ZKJ | polyhedra-network | N | N | N | none | N | ✗no_economic_model |

#### Charity Fundraising (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| GTC | gitcoin | N | N | N | none | N | ✗no_economic_model |

#### Developer Tools (3)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ATH | aethir | 2025-10->2026-06 | 2024-10->2026-06 | Y | none | N | ✗no_economic_model |
| GRT | the-graph | 2025-07->2026-06 | 2022-12->2026-06 | Y | none | N | ✗no_economic_model |
| WAL | walrus-protocol | N | 2025-03->2026-06 | Y | none | N | ✗no_economic_model |

#### Domains (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ENS | ens | N | 2023-02->2026-06 | Y | none | N | ✗no_economic_model |

#### Indexes (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| MLN | enzyme-finance | 2021-03->2026-06 | 2026-01->2026-06 | Y | none | N | ✗no_economic_model |

#### Launchpad (6)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| AUCTION | bounce-finance | 2023-08->2026-06 | N | N | none | N | ✗no_economic_model |
| BIO | bio-protocol | 2025-10->2026-06 | N | N | none | N | ✗no_economic_model |
| MC | merit-circle | 2021-12->2026-06 | N | N | none | N | ✗no_economic_model |
| MPLX | metaplex | N | 2023-05->2026-06 | Y | none | N | ✗no_economic_model |
| SFUND | seedify | 2022-03->2026-06 | N | N | none | N | ✗no_economic_model |
| WARP | polkastarter | 2021-12->2026-06 | N | N | none | N | ✗no_economic_model |

#### Leveraged Farming (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ALPHA | stella | 2023-06->2026-06 | N | N | none | N | ✗no_economic_model |

#### Liquidity Manager (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ICHI | ichi | 2021-06->2026-06 | N | N | none | 9p | ✗no_economic_model |

#### NFT Marketplace (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| NFTX | nftx | 2021-06->2026-06 | N | N | none | N | ✗no_economic_model |

#### Options (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| OPIUM | opium | 2021-02->2026-06 | N | N | none | N | ✗no_economic_model |

#### Payments (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| AMP | flexa | 2020-11->2026-06 | N | N | none | N | ✗no_economic_model |

#### Prediction Market (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| REP | augur | 2020-03->2026-06 | N | N | none | N | ✗no_economic_model |

#### Reserve Currency (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| OHM | olympus-dao | 2021-03->2026-06 | 2025-02->2026-06 | Y | none | N | ✗no_economic_model |

#### Restaking (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| EIGEN | eigencloud | 2023-06->2026-06 | 2024-09->2026-06 | Y | none | N | ✗no_economic_model |

#### Risk Curators (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| API3 | api3 | 2022-01->2026-06 | 2025-12->2026-06 | Y | none | N | ✗no_economic_model |

#### Services (7)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| ALICE | my-neighbor-alice | N | N | N | none | N | ✗no_economic_model |
| ANT | aragon | N | N | N | none | N | ✗no_economic_model |
| ARKM | arkham | N | N | N | none | N | ✗no_economic_model |
| FORTH | forth-dao | N | N | N | none | N | ✗no_economic_model |
| IQ | iq | 2021-08->2026-06 | N | N | none | 1p | ✗no_economic_model |
| KAITO | kaito | 2025-11->2026-06 | N | N | none | N | ✗no_economic_model |
| SUPER | superfarm | 2021-12->2026-06 | N | N | none | N | ✗no_economic_model |

#### SoFi (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| CYBER | cyberconnect | N | N | N | none | N | ✗no_economic_model |

#### Staking Pool (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| TT | thundercore-staking | 2023-04->2026-06 | N | N | none | N | ✗no_economic_model |

#### Token Locker (2)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| FLOKI | flokifi-locker | 2023-02->2026-06 | N | N | none | N | ✗no_economic_model |
| SWAP | team-finance | 2022-06->2026-06 | N | N | none | N | ✗no_economic_model |

#### Trading App (1)
| Symbol | slug | TVL range | Fees | Rev | DirectVol | APY(cur) | Verdict |
|---|---|---|---|---|---|---|---|
| LAB | lab-terminal | N | 2025-06->2026-06 | N | none | N | ✗no_economic_model |
