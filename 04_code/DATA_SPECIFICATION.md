# Data and Variable Construction — Specification for the Empirical Pipeline

**Audience:** this document is written for a coding agent (Claude Code) building the
empirical pipeline for this paper, with no prior context on the project. It should be
self-contained.

**Status:** specification only. No hypothesis testing, no Section 3 prose, until the
phases below are complete and reviewed.

---

## 0. Operating Principle: Improvise, Don't Guess Silently

This spec describes the *ideal* data. Real crypto data will not match it everywhere —
some chains lack staking data for parts of the sample, some DAOs vote off-chain, some
tokens have no clean transaction-volume series, etc.

**Rule:** when ideal data is unavailable, do not silently drop the asset-month or
silently substitute a proxy and move on. Instead:

1. Implement the best defensible proxy you can construct from available sources.
2. Log it in `04_code/DATA_DECISIONS_LOG.md` (template provided alongside this file):
   what was wanted, what was used instead, why, and what the limitation is.
3. Flag it clearly in the coverage report (Section 7) rather than burying it.
4. Do not proceed to build derived variables (λ, NVT_GL, factor models) on top of a
   judgment call large enough to change the paper's conclusions without flagging it for
   review first.

The goal of this pipeline's first pass is as much to find out **what data actually
exists** as it is to compute the variables below. Treat Phase 0 (Section 7) as a
feasibility audit, not just a build step.

---

## 1. Why These Variables Exist (Theoretical Context)

The paper applies the Quantity Theory of Money to crypto assets: market cap (MC) is
decomposed into a Medium-of-Exchange (MoE) component and a Store-of-Value (SoV)
residual, via a variable λ = the share of supply that is locked/staked. The key
results (see `05_paper/main.tex`):

- **SoV/MoE ratio = λ/(1−λ)** — directly observable, no velocity estimation needed.
- **λ_t = H(b_t + θ_{t+1})** — λ is a publicly observable signal of the holder base's
  aggregate private conviction about the asset's future growth trajectory θ_{t+1},
  where b_t is a current benefit from locking (seigniorage for coins, fee/yield share
  or zero for governance tokens).
- **Hypothesis 1a/1b:** assets with higher λ/(1−λ) earn higher subsequent returns,
  cross-sectionally, for both coins and governance tokens.
- **Growth-Levelized NVT (NVT_GL) = MC / PQ\*** — traditional NVT (Network Value to
  Transactions) but with the denominator replaced by PQ\*, a forward-looking, levelized
  (PMT/annuity-style) present value of projected transaction throughput. NVT_GL is a
  *conditioning* variable, not an independent return predictor: H2 says the λ effect is
  concentrated among low-NVT_GL assets (the market hasn't yet priced in the conviction
  signal).
- **Hypothesis 3 (Quadrant Portfolio):** long high-λ/low-NVT_GL assets ("Star"), short
  low-λ/high-NVT_GL assets ("Avoid").

Every variable below exists to test one of these hypotheses. If a proxy can't support
the hypothesis it was meant to test, say so explicitly — don't ship a number that looks
plausible but can't bear the theoretical weight placed on it.

---

## 2. Asset Universe Construction

### 2.1 Inclusion rule (avoid both penny-token noise and survivorship bias)

Do **not** use a fixed nominal-dollar market-cap floor (e.g., "$50M"). Crypto's total
market cap grew by orders of magnitude from 2015 to 2026, so a fixed dollar threshold
that excludes noise in 2024 would have excluded almost everything in 2016, and a
threshold calibrated to 2016 would admit hundreds of microcaps by 2024.

**Use a relative, point-in-time rank/percentile screen instead:**

- At each month-end, rank all tracked crypto assets by market cap.
- An asset becomes *eligible* for the panel the first month it appears in the top N
  (default **N = 250** — adjust if Claude Code's coverage audit suggests this is too
  wide or too narrow; report the count of qualifying assets per month either way).
- **Once eligible, an asset stays in the panel for every subsequent month through the
  end of the sample**, even if it later falls out of the top N, gets delisted from
  exchanges, or its protocol fails entirely (price → 0). Record its last observed price
  and treat the failure as a return realization, not a missing observation.
- This must be computed from **historical, point-in-time** rankings (e.g., "what was
  the top 250 by market cap in March 2018"), not a single ranking taken from today's
  data. Ranking by today's market cap and backfilling is the single most common way to
  silently reintroduce survivorship bias — every dead project that doesn't exist in
  today's CoinGecko/CoinMarketCap "current" listings would be invisibly excluded. Use
  CoinGecko's historical snapshot endpoints / Artemis's historical coverage / archived
  CoinMarketCap rankings, which include delisted assets, not the current top-N list.

### 2.2 Sample period

**Start: August 2015** (the month after Ethereum's mainnet launch, July 30, 2015 — the
practical start of the smart-contract "token economy"). **End: most recently completed
month** at time of data pull. Monthly frequency (the hypotheses in `main.tex` are
written in terms of "month t").

Expect the 2015–2019 portion of the panel to be thin and coin-dominated (BTC, ETH, a
handful of early ICO-era ERC-20 tokens, many of which later failed — include the
failures; that is exactly the survivorship-bias case Section 2.1 exists to handle).
Most governance-token-style assets (UNI, COMP, AAVE, CRV, etc.) don't exist before
2020. **Report coverage by year** so we can see, concretely, where H1b/H2/H3 (which
need governance/voting data) become testable versus where only H1a (coins) has enough
density. Do not extend any individual asset's own series further back than August 2015
even if the asset itself is older (e.g., BTC launched 2009) — common start date is for
clean comparability across the panel, but **also produce a separate, supplementary
note in the coverage report on how much earlier history exists for pre-2015 native
coins** (BTC chiefly), in case a coins-only robustness subsample is useful later in
Section 5.

### 2.3 Coin vs. governance-token classification (functional, not architectural)

Per `main.tex` Section 2.1: the cut is whether locking the asset earns a security- or
seigniorage-related benefit (b_t > 0 → **coin**, Hypothesis 1a bucket) or not (b_t = 0,
governance-only → **token**, Hypothesis 1b bucket). This is independent of L1 vs. L2.

Build a classification table with the supporting evidence for each asset, not just a
silent label:
- Does the asset have a staking/validation mechanism that distributes
  protocol-level rewards (new issuance, fee share, or both) for securing the network or
  a comparable function? → coin.
- Does locking/staking only grant governance rights or a fee/yield share *unrelated to
  network security* (e.g., a DeFi protocol's fee-sharing vote-escrow token)? → token.
- **Flag ambiguous or mixed cases explicitly** (e.g., assets that started as one and
  added the other mechanism later — note the date of the change) rather than forcing a
  single static label across the whole sample. A worked example to watch for: Ethereum
  was proof-of-work (no staking, b_t effectively undefined as a coin-staking benefit)
  until the Beacon Chain deposit contract opened in **December 2020** and the Merge to
  proof-of-stake completed in **September 2022**. ETH's b_t > 0 staking regime
  realistically only starts at one of those dates, not in 2015. Verify exact dates with
  live sources — don't rely on this document's dates without checking, since this is
  describing the kind of issue to look for, not asserting these are final.

### 2.4 Candidate list and market-cap data sources

Build the candidate universe and historical market-cap rankings from:
- **CoinGecko** (historical market data API, broad coverage including many delisted
  coins)
- **DeFiLlama** (protocol-level data: TVL, fees, revenue — most useful for governance
  tokens' PQ proxy, see Section 4)
- **Artemis Analytics** (app.artemisanalytics.xyz) (cross-chain on-chain fundamentals
  aggregator — check current API access/terms)

Cross-check coverage between at least two sources where feasible; note discrepancies
rather than picking one arbitrarily.

### 2.5 Per-asset transactional, staking, and voting data sources

Once the universe and classification are set, pull asset-specific series from the
appropriate **chain explorer for that asset's native chain** — there is no single
source:
- Ethereum L1 and most ERC-20 governance tokens: **Etherscan**
- Solana: Solscan / Solana Beach
- Avalanche C-Chain: Snowtrace
- L2s (Arbitrum, Optimism, Base, etc.): Arbiscan / Optimistic Etherscan / Basescan
- Others: identify the canonical explorer per chain; don't assume Etherscan covers
  non-EVM or even all EVM chains.

For **voting/governance records**, note that many major DAOs vote **off-chain**
(gasless signaling) via **Snapshot**, with only execution on-chain — a pure
block-explorer read will miss the actual vote. Check **Snapshot's API**, **Tally**,
**Boardroom**, and **DeepDAO** for governance-participation data in addition to
on-chain governance contracts (e.g., Governor Bravo-style contracts, readable via
Etherscan/RPC) for protocols that vote fully on-chain.

---

## 3. Variable 1: λ — The Locking/Conviction Index

λ_t is constructed as an index over three channels, used wherever each is observable
for a given asset-month. Per the project's decision: **standardize (z-score) each
available channel within its monthly cross-section, then take the equal-weighted
average of whichever channels are available** for that asset-month. Do not impute a
missing channel with a cross-sectional mean or zero — average only over the channels
that actually exist for that asset-month, and record how many channels contributed.

### 3.1 Channel 1 — Staking/locking ratio
`staked_or_locked_supply / total_or_circulating_supply` at month-end. For coins:
validator/staking totals (chain-specific staking dashboards, beaconcha.in-style
explorers for ETH, equivalents for other PoS chains). For vote-escrow tokens: locked
supply (e.g., veCRV, veBAL) via protocol dashboards or DeFiLlama.

### 3.2 Channel 2 — Holding duration
The hardest channel to source cleanly. Proxy via on-chain holding-period analysis —
e.g., share of supply unmoved for some threshold window, or average coin-age of moved
supply ("HODL wave"-style metrics). If a clean off-the-shelf metric isn't available for
a given chain, document the computation actually used (e.g., computed directly from
transfer histories) and its limitations.

### 3.3 Channel 3 — Voting engagement
`unique addresses (or token-weight) voting / eligible voting supply`, aggregated to a
monthly participation rate. Source per Section 2.5 (Snapshot/Tally/Boardroom for
off-chain, on-chain governance contracts otherwise). Expect this channel to be
essentially unavailable before ~2020 and absent entirely for pure-coin assets with no
governance mechanism — that's expected, not a bug.

### 3.4 Output
For every asset-month: λ_t, plus the count and identity of which of the three channels
contributed to it. This channel-availability breakdown is itself a useful diagnostic —
report it in the coverage audit.

---

## 4. Variable 2: Growth-Levelized NVT (NVT_GL)

Per Appendix A of `main.tex`:

```
NVT_GL = MC / PQ*

PQ* = [ Σ(s=1..n) PQ_0(1+g)^s / (1+r_e)^s  +  PQ_0(1+g)^n(1+g_inf) / ((r_e − g_inf)(1+r_e)^n) ]
      / annuity_factor(r_e, n)
```

where g = trailing k-year CAGR of PQ, r_e = CAPM-estimated required return, g_inf =
terminal growth rate, and the annuity factor converts the present value to a levelized
annual equivalent (Excel PMT analogy).

### 4.1 Inputs needed, per asset-month

- **MC** — market cap (same source as Section 2.4).
- **PQ** — nominal economic throughput.
  - For coins: on-chain transaction (transfer) volume. **Flag and, where possible,
    use an "adjusted" volume series that nets out known double-counting (exchange
    internal transfers, self-churn)** rather than raw transfer volume — raw on-chain
    volume is a well-known weak point of traditional NVT. If an adjusted series isn't
    available for a given chain, use raw volume and flag it.
  - For governance tokens: protocol throughput — DEX volume, total fees, or active-user
    counts (DeFiLlama fees/revenue data, Artemis, or comparable). Use a consistent
    definition across tokens where possible; document where it had to vary.
- **g** — trailing CAGR of PQ. Default window k = 3 years; flag if fewer than k years
  of history exist (common for younger assets) and document the shorter window used.
- **r_e** — CAPM-style required return: asset-specific beta against a crypto market
  index (e.g., a cap-weighted total-market index, or BTC as a simple alternative)
  plus a risk-free rate. (Note: this is a *discount-rate* input to PQ\*, distinct from
  the portfolio-level risk adjustment in Section 5 — don't conflate the two uses of
  "CAPM" in the pipeline's code or naming.)
- **g_inf** — terminal growth rate. This is a modeling assumption, not something to
  estimate from data. Use a single defensible macro-anchored default (e.g., a constant
  in the 2–4% range) and flag it as a parameter to be sensitivity-tested later
  (Section 5, Robustness, of the paper) rather than something to tune per-asset.
- **n** — projection horizon for the annuity factor. Default n = 10 years; also a
  robustness parameter, not estimated.

### 4.2 Output
NVT_GL per asset-month, plus the underlying g, r_e, and PQ series used, so the
construction is auditable and the g_inf/n/k assumptions can be varied later without
rebuilding from scratch.

---

## 5. Returns, Controls, and Factor Models

### 5.1 Asset returns
Monthly forward returns r_{j,t+1} per asset from price/MC data, plus standard controls:
size (market cap), momentum (trailing return), and market beta.

### 5.2 Factor Model A — Liu-Tsyvinski-Wu-style 3-factor model
The paper's literature review cites Liu, Tsyvinski, and Wu (2022, *Journal of
Finance*), "Common Risk Factors in Cryptocurrency," as the closest published
crypto-specific factor model (market, size, momentum). First check whether the authors
publish a factor-return data file (some asset-pricing papers maintain a public data
appendix); if so, use it directly and cite the source. If not, reconstruct the three
factors following their published methodology over this paper's own asset universe,
and document any deviation from their exact construction.

### 5.3 Factor Model B — CAPM beta + custom size/momentum controls
Build a standard single-factor CAPM beta (against a crypto market index) plus
separately constructed size and momentum sorts directly from this paper's asset
universe, as an independent, more transparent alternative specification.

**Per project decision: build and report both A and B as robustness checks against
each other** — not a single choice between them.

---

## 6. Known Data Landmines (Illustrative, Not Exhaustive)

These are the kinds of issues Phase 0/1 should surface — flag them in the decisions
log and coverage report, don't quietly work around them:

- **ETH's PoW→PoS transition** (Section 2.3): no staking-based λ channel exists for
  ETH before the Beacon Chain deposit contract / the Merge. Verify exact dates live.
- **Wash trading / exchange-internal transfers** inflating raw on-chain transaction
  volume (PQ for coins) — a known critique of traditional NVT.
- **Off-chain governance voting** (Snapshot) invisible to pure block-explorer reads.
- **Survivorship bias from "current top-N" lists** — see Section 2.1; must use
  point-in-time historical rankings.
- **Rebrands/migrations** (e.g., a token migrating to a new contract or a new chain) —
  decide and document whether to treat as a continuous series or an exit-plus-new-entry.
- **Inconsistent PQ definitions across protocols** for governance tokens (DEX volume vs.
  fees vs. active users aren't the same thing) — document whichever is used per asset.

---

## 7. Deliverables and Phasing

Work in phases; produce a written coverage/feasibility report at the end of each phase
before starting the next, so scope can be adjusted with real numbers in hand rather
than assumptions.

- **Phase 0 — Universe.** Candidate list, point-in-time market-cap panel, entry/exit
  dates, classification table (coin vs. token, with evidence), coverage by year/month.
- **Phase 1 — λ channels.** Staking/locking, holding duration, voting engagement, per
  asset-month, with channel-availability counts.
- **Phase 2 — NVT_GL inputs.** MC, PQ, g, r_e inputs, g_inf/n parameters, NVT_GL.
- **Phase 3 — Returns and factors.** Asset returns; Factor Model A and B.
- **Phase 4 — Assembly.** Master panel (asset × month, all variables), a data
  dictionary, the final coverage/quality report, and the decisions log.

Each phase's output should be reproducible (scripts, not one-off manual pulls) and
land in `03_data/` (processed data) and `04_code/` (pipeline code), with this
specification and the decisions log as the source of truth for *why* each choice was
made.

---

## 8. Decisions Log

Maintain `04_code/DATA_DECISIONS_LOG.md` (template provided) for every deviation from
this spec — proxy substitutions, classification judgment calls, threshold choices that
turned out to need adjusting, sources that didn't pan out. This feeds two things: the
actual Section 3 prose once the dust settles, and the AFA-required documentation of the
AI-assisted research process in `06_documentation/`.
