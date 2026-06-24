# Phase 2 Coverage Report — NVT_GL (PQ, g, r_e, PQ*, NVT_GL)

**Date:** 2026-06-24
**Session:** 013 (Claude Code / Opus 4.8), working dir `C:\AFA_2027_QTM_Crypto`
**Scope:** builds the Growth-Levelized NVT (NVT_GL = MC / PQ\*) per asset-month, on the resolved
PQ definition (Entries 30–32). Resumes Part B of `CLAUDE_CODE_PHASE2_KICKOFF_PROMPT.md`.
**Status:** **token PQ (Part A) + covered-coin PQ (Part B Rungs 1/3) + full NVT_GL machinery
COMPLETE.** 81 material coins deferred to **Phase 2b** (Artemis paid-only — human decision,
session 013). Do not start Phase 3 without review.

---

## 0. Headline

| Quantity | Value |
|---|---|
| Observed asset-months in panel | 67,303 |
| Asset-months with monthly PQ (transacted value) | **2,557** (65 assets) |
| Asset-months with a computed **NVT_GL** | **1,821** (59 assets: 46 coins, 13 tokens) |
| NVT_GL month range | 2016-08 → 2026-05 |
| Assets with PQ: tokens / coins | 16 / 50 |

NVT_GL requires MC (always present) **and** PQ history deep enough for both a trailing CAGR `g`
and a trailing beta — so the 65-asset PQ set narrows to 59 with a full NVT_GL. Coverage by year
rises from 1 asset (BTC, 2016) to 53 assets (2026), exactly the coin-dominated-early → broad-late
shape spec §2.2 anticipated.

| Year | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NVT_GL asset-months | 5 | 12 | 12 | 14 | 24 | 41 | 143 | 325 | 480 | 524 | 241 |
| distinct assets | 1 | 1 | 1 | 2 | 2 | 6 | 18 | 37 | 44 | 51 | 53 |

---

## 1. PQ — the resolved definition (Entries 30–32)

PQ = **transacted value** (the dollar flow that actually moved through the contract/chain),
**not** fees (a toll, Entry 30) and **not** TVL (capital stock). Routed by sector. Raw gov-token
Transfer logs were piloted and rejected (Entry 31, wrong object). Source per asset below.

### 1a. Tokens (Part A) — DeFiLlama sector-routed reported volume

| PQ source | # tokens | Notes |
|---|---|---|
| `defillama_dexs` (DEX swap volume) | 11 | SUSHI, OSMO, RUNE, MDX, EPS, ORN, SOLO, LIGHT, PENDLE, HFT, … |
| `defillama_aggregators` (routed volume) | 4 | 1INCH, COW, ZRX, AST — **flagged**: aggregator volume may double-count underlying DEX volume |
| `defillama_options` (notional) | 1 | HEGIC |
| **NaN — derivatives volume paywalled (HTTP 402)** | 10 | GNS, MYX, HXRO, DDX, LINA, MIR, KP3R, NMR, HAKKA, AVNT — **landmine:** DeFiLlama gated the perps/derivatives volume dimension behind a paid key this session (verified 402 at both `/overview/derivatives` and `/summary/derivatives/{slug}`); open-interest is free but is a stock, not a flow, so not valid PQ |
| NaN — no transacted-value object | 93 | Yield/Farm/Lending/Gaming/Services/Bridge/Chain/etc.: these have no swap/notional flow; their throughput would be borrow-origination/active-users, which DeFiLlama exposes no free *volume* series for → flagged NaN (fees/TVL kept as diagnostics) |
| NaN — slug absent / ambiguous | 8 | SUN(sunswap split by version), VELO/SXP (symbol collisions), LRC, BAKE, NVT, … — left NaN rather than risk wrong-asset attribution |

**16 of 127 slugged tokens get a volume PQ.** This is expected: most governance tokens are not
DEXs/perps and have no transacted-value object. **Fee→volume backout (Entry 32) fired for 0
protocols** — no token protocol-month met the strict "documented single, stable, notional-
proportional rate" test without circularity (the candidates are multi-tier DEX fees, variable
perps fees, or lending reserve factors, all explicitly excluded by the rule). Per spec §0, those
are flagged NaN, never filled with the raw fee.

### 1b. Coins (Part B) — Entry 32 ladder (see `phase2_coin_rung_table.csv`, B1 report)

| Rung / status | # coins | # material (peak ≥ $1B) | Source |
|---|---|---|---|
| **R1** DeFiLlama chain DEX volume | 49 | 40 | ETH, BNB, SOL, ADA, TRX, AVAX, TON, NEAR, SUI, APT, STX, HBAR, ALGO, INJ, SEI, POL, … |
| **R3-BTC** blockchain.com est. tx value | 1 | 1 | BTC (change-excluded, 2010→present) |
| **GAP-R2** Artemis paid-only → **Phase 2b** | 81 | 81 | XRP, DOGE, LTC, BCH, XMR, ZEC, DASH, ATOM, DOT, MATIC, … (flagged PQ=NaN) |
| NaN non-material (expected) | 502 | 0 | long tail of sub-$1B / dead coins |

**Materiality threshold (R1 split):** a chain qualifies for Rung 1 iff **30-day chain DEX volume
÷ latest market cap ≥ 0.01** (≥1% monthly DEX turnover ≈ 12%+ annualized). Calibration: BTC
9×10⁻⁶ (degenerate, correct), ETH 0.143 / SOL 1.04 / BNB 0.27 (material). The big payment/SoV
coins fall decisively below and are NOT forced onto chain-DEX volume. Full rationale in
`PHASE2_COIN_PQ_VERIFICATION_B1.md`. **Rung 4 (chain fees) was NOT auto-applied** to any coin —
it is a flagged toll proxy of last resort requiring explicit approval, deferred to Phase 2b.

---

## 2. NVT_GL machinery (spec §4.1, `phase2_nvt_gl.py`)

For each asset-month with PQ:
- **PQ0** (annual throughput) = trailing-12-month sum of monthly PQ.
- **g** = trailing 3-year CAGR of PQ0 (`(PQ0_t / PQ0_{t-3y})^{1/3} − 1`); **≥1y fallback flagged**
  in `g_window_years` (3y: 794 rows, 2y: 475, 1y: 552). Capped to [−50%, +200%].
- **beta** = trailing-36m (min 12) covariance of asset return vs **BTC** (the spec's simple market
  proxy; the cap-weighted index is numerically unusable — penny-token return blowups give inf).
  Monthly returns winsorized to [−90%, +300%].
- **r_e** = rf + beta·MRP, floored at 0.05. **rf = 4%**, **MRP = 30%** — both *documented
  robustness parameters*, **not** the realized BTC premium (~114%/yr, far too high for a forward
  required return). beta is emitted so any rf/MRP can be re-applied without rebuild (spec §4.2).
- **g_inf = 3%**, **n = 10 yr** — robustness parameters (spec §4.1).
- **PQ\*** = levelized-annuity present value of projected throughput (spec §4.1 formula);
  **NVT_GL = MC / PQ\***.

Output `03_data/phase2/nvt_gl_panel.csv` carries MC, monthly PQ, PQ0, g, g_window_years, g_capped,
beta, r_e, PQ\*, NVT_GL, pq_source, asset_class, sector — so g_inf/n/rf/MRP/k are all re-varyable.

### 2a. Sanity & the one caveat that matters
- No pathologies: 0 infinite NVT_GL, 0 non-positive PQ\*, 0 negative NVT_GL across 1,821 rows.
- Levelization behaves correctly: high projected growth → large PQ\* → **low** NVT_GL (asset looks
  "cheap" on forward throughput; e.g. SOL g=2.0 → NVT_GL 1.9×10⁻⁵), declining growth → higher
  NVT_GL (SUSHI g=−0.5 → 0.22).
- **CAVEAT (flagged for review):** the g-cap binds on **43.4%** of NVT_GL rows, and because PQ\*
  scales with (1+g)^n (n=10), NVT_GL spans many orders of magnitude driven largely by `g`.
  Trailing-3y CAGR is inherently explosive/volatile in crypto. **NVT_GL is therefore reliable as a
  cross-sectional *rank/conditioning* variable (which is exactly how H2/H3 use it — median splits),
  not as a cardinal level.** g_cap and n are the first knobs to sensitivity-test. This is a
  property of the spec'd formula + the data, surfaced here rather than worked around.

### 2b. Side diagnostics (Entry 30/31) — `phase2_pq_diagnostics.csv`
Volume/TVL turnover (monthly PQ ÷ month-end TVL; protocol TVL for tokens, chain TVL for coins):
2,534 asset-months, **median turnover 1.15×**, p90 7.5× — a protocol/chain restatement of M·V=PQ
with TVL standing in for M. TVL retained as the capital-stock control. (Monthly fee series not
pulled to bound calls; slug-level fee 30d totals cached in `_fees_overview.json`.)

---

## 3. Source landmines hit this session
1. **DeFiLlama derivatives/perps volume is now paid-gated (HTTP 402)** — removes free perps notional
   for 10 derivatives tokens (→ NaN). Open-interest is free but is a stock, not transacted value.
2. **Artemis REST API is paid-only** (Lite = Terminal/Sheets only) — closes Rung 2, the 81-coin gap.
3. **Aggregator volume double-counts** underlying DEX volume (1INCH/COW/ZRX/AST) — flagged, kept.
4. **Cap-weighted crypto index unusable** for beta (penny-token return → inf); BTC used as market.
5. **Parent/child DeFiLlama slugs** (SunSwap split v1/v2/v3; Velodrome) + symbol collisions
   (VELO, SXP) — left NaN rather than risk mis-attribution.

## 4. Open items → Phase 2b / Phase 3
- **Phase 2b:** source transacted-value PQ for the 81 GAP-R2 coins (XRP via XRPL APIs; LTC/BCH/
  DOGE/DASH via bitinfocharts/blockchair "sent-in-USD"; Artemis-paid option). See
  `06_documentation/CLAUDE_CODE_PHASE2B_KICKOFF_PROMPT.md`. XMR is a permanent gap (RingCT hides
  amounts). Until then those coins carry PQ=NaN in the panel.
- **Sensitivity (deferred, spec §5):** vary g_cap, n, g_inf, rf, MRP; emitted intermediates make
  this a re-compute, not a rebuild.
- **Do not start Phase 3 without review.**
