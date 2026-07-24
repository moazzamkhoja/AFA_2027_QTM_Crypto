# Remaining Data Collection Plan
**As of: 2026-07-24 (post-session 031)**

---

## Current State

| Panel | Count | Notes |
|---|---|---|
| λ asset-months | 9,638 | 341 assets |
| Regression-ready coins (λ∩NVT_GL) | 20 | PoS coins with both series |
| Regression-ready PoW coins (NVT_GL, λ N/A) | 11 | BTC/ETH/DOGE/LTC/BCH/BSV/BTG/ETC/ZEC/ALPH/rBTC |
| Regression-ready tokens/other (λ∩TVL) | 122 | |
| **Total regression-ready** | **153** | |
| Partial (λ but no denominator, or TVL but no λ) | 232 | |
| Not started | 1,554 | |

SOL is already **complete** (ch1 staking 40 months + NVT_GL 44 months via DeFiLlama chain DEX).

---

## TIER 1 — Next immediate sessions (weeks, not months)

### Session 032: MYX (36410) — last Task-A token
- BSC chain, ~250–300k getLogs (confirmed mega-giant from session 030 abort)
- **Pause Windows Update before running.** Dedicated quota day.
- After completion: tokens regression-ready → 123

### Session 033: XTZ NVT_GL probe + build
- XTZ has **78 months of λ** (the longest partial-coin series) but no PQ/NVT_GL
- Gap-R2 in Phase 2b was logged as "no free keyless series" — but TzKT.io (official Tezos
  indexer) serves free historical on-chain volume via `api.tzkt.io/v1/statistics`
- Probe: fetch monthly XTZ transfer volume from TzKT → multiply by month-end price →
  verify vs any available benchmark → if passes Entry-26 style cross-check, build NVT_GL
- Same session: probe MATIC (50 months λ, no PQ). Polygon transaction volume available via
  bitinfocharts or DeFiLlama chain stats (non-DEX-only needed)
- Also probe JOE (6mo), SAFE (10mo), DYDX (1mo) — lower priority but same session
- If XTZ and MATIC both pass: coins regression-ready → 22

### User actions needed before sessions can proceed
| Action | Unlocks |
|---|---|
| Manual check: read staked total from staking.chiliz.com → compare to 0x…1000 balance (2.38B CHZ) | CHZ ch1 build (~1 coin) |
| Get free API key from scan.coredao.org → add to `.api_keys.json` as `"coredao"` | CORE ch1 build (~1 coin) |
| Free Subscan signup at pro.subscan.io → add key as `"subscan"` | DOT + KSM ch1 (2 top-20 coins) |
| StakingRewards or Numia key inquiry → add key | CRO, INJ, SEI, KAVA ch1 (4 Cosmos coins) |

---

## TIER 2 — Solana ecosystem (new engine required)

### Current status
- SOL (native coin): **complete** ✅
- 59 SPL tokens in universe: **0 λ, 0 TVL, all not_started**
- ch2 (HODL-wave) is **technically feasible** for all 59 via Solana transfer history indexer
  (confirmed in `non_evm_lambda_recoverability.csv`)

### Why it matters (survivorship bias)
Solana has become the dominant chain for DeFi token activity. The 59 Solana tokens include
several major DeFi protocols with trackable TVL in DeFiLlama. Excluding all of them
introduces a chain-level survivorship bias.

### DeFi Solana tokens with TVL potential (~10 targets)

| cmc_id | symbol | sector | DeFiLlama slug (expected) |
|--------|--------|--------|--------------------------|
| 29210 | JUP | DEX Aggregator/Perpetuals | jupiter |
| 11165 | ORCA | DEX/Lending | orca |
| 31278 | DRIFT | Derivatives/Perpetuals | drift |
| 30986 | KMNO | Lending/Liquidity Manager | kamino |
| 11171 | MNGO | Derivatives/DEX | mango-markets |
| 28862 | BSOL | Liquid Staking | blazestake |
| 28853 | JLP | DEX (Jupiter LP) | jupiter (JLP vault) |
| 29082 | SAROS | DEX | saros |
| 36507 | PUMP | Launchpad | pump.fun |
| 22974 | TAO | AI/DePIN | bittensor |

JUP is already "partial" — has ch3_voting from Snapshot but no ch2 or TVL yet.

### Engineering requirement
Solana uses `getSignaturesForAddress` + `getTransaction` (not `getLogs`). A new
`phase1_channel2_solana.py` engine is needed. The Solana public RPC is rate-limited;
Helius (free tier: 100k credits/day) or SolanaFM are the recommended free indexers.
Estimated effort: 1 session to build + test the engine; 1 session to run all 10 tokens.

### Meme/gaming Solana tokens (lower priority)
The remaining ~49 Solana tokens are meme (WIF, BONK, POPCAT, FARTCOIN, etc.) or gaming.
They have no TVL denominator → ch2 builds λ only. They could be included in a
λ-panel-only analysis but cannot enter the NV/TVL regression. Build only if time permits.

---

## TIER 2 — HYPE ecosystem

### HYPE coin (cmc 32196)
- **NVT_GL**: 6 valid months (DeFiLlama Hyperliquid chain DEX) — series is short but live
- **λ**: NONE — `api.hyperliquid.xyz/validatorSummaries` returns current state only; no
  historical endpoint found (documented Entry 78 as live-only gap)
- **Status**: partial (NVT_GL but no λ). Will remain a gap unless Hyperliquid ships a
  validator-history API or a third-party archives it.
- **Action**: monitor Hyperliquid docs for a `/validators/history` endpoint. If one appears,
  ch1 staking build is straightforward (same architecture as XRD/FLR).

### HyperEVM tokens (KHYPE, WHYPE)
- Both on HyperEVM (EVM-compatible L1, chainid TBD)
- **KHYPE (39072)**: Liquid Staking/Restaking — ch1 and ch2 both buildable via per-contract
  events (same method as Etherscan Pro V2 with `?chainid=<hyperevm_id>`)
- **WHYPE (35881)**: Wrapped HYPE — ch2 buildable
- **TVL**: KHYPE = Hyperliquid liquid staking TVL (DeFiLlama likely tracks as `khype` or
  `hyperliquid-lsd`); WHYPE = wrapped asset, TVL under Hyperliquid
- **Blocker**: need to confirm Etherscan Pro V2 covers HyperEVM chainid; need DeFiLlama slug
- **Effort**: 1 short session if Etherscan Pro covers the chain; otherwise needs direct RPC

---

## TIER 3 — EVM DeFi breadth expansion (survivorship bias fix, ~3 sessions)

116 DeFi-sector EVM tokens (DEX/Lending/Yield/Bridge — dead and alive) are ch2-buildable
via existing Etherscan Pro infrastructure. ~74 of them are expected to have historical TVL
in DeFiLlama (even for dead/bankrupt protocols like Celsius, Multichain, old Aave v1).

Including dead protocols is important: they populate the low-TVL, low-λ region of the
regression and prevent the sample from being skewed toward survivors.

- **getLogs estimate**: ~503k calls ≈ 3 sessions
- **Work**: ch2 Transfer-event replay + DeFiLlama slug search for all 116
- **Expected new regression-ready tokens**: ~74
- **After completion**: regression-ready total → ~227

Notable dead/bankrupt DeFi targets: LEND (old Aave v1, 133k holders), CEL (Celsius, 30k),
SNX (Synthetix, 88k), SAI (old MakerDAO, 177k), MULTI (Multichain collapse, 4k),
stETH/rETH/cbETH/eETH (LSTs — TVL under parent: Lido/Rocket Pool/Coinbase/EtherFi).

---

## TIER 4 — Structural gaps (document and move on)

These have been individually verified in session 029 Entry 78. No free path today.

| Asset(s) | Gap reason |
|----------|-----------|
| BERA | Consensus-layer staking; no public beacon archive API |
| TON | Elector balance current-only; no historical keyless endpoint |
| FLOW | Cadence execution is spork-bound; no historical staking API |
| DFI | Chain sunset; on-chain stats current-only |
| DASH | Masternode count history APIs all dead (stats.masternode.me DNS-dead) |
| NEAR | Historical staking behind Pikespeak (key + undisclosed pricing) |
| ALGO | No historical participation series anywhere — full tx replay required |
| HBAR, SUI | Free sources current-only; historical aggregation not available keyless |
| EOS, ICP, APT | No historical staking source found |
| WAN | wanscan.org HTML-only; no staking API |
| LSK | Lisk migrated to OP-stack L2; no staking/locking contract found |

---

## Summary: What this adds to the regression sample

| Work item | Sessions | New regression-ready |
|-----------|----------|---------------------|
| MYX (session 032) | 1 | +1 token → 123 tokens |
| XTZ + MATIC NVT_GL | 1 | +2 coins → 22 coins |
| CHZ staking (user anchor check first) | 1 | +1 coin → 23 |
| CORE staking (user gets API key first) | 1 | +1 coin → 24 |
| DOT + KSM (user Subscan signup first) | 1 | +2 coins → 26 |
| CRO + INJ + SEI + KAVA (Cosmos key) | 1 | +4 coins → 30 |
| Solana DeFi tokens (~10) | 2 | +~8 tokens → ~131 |
| HYPE ecosystem (KHYPE/WHYPE) | 1 | +~2 tokens → ~133 |
| EVM DeFi breadth (~116 tokens) | 3 | +~74 tokens → ~207 |
| **Total if all completed** | **~12 sessions** | **~207 tokens + 30 coins = ~237** |

**Current: 153. Realistic near-term target (Tier 1 + user actions): ~165. Full build: ~237.**
