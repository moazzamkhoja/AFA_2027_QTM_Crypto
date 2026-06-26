# Contract-Level PQ — Solidity Event Taxonomy & Build Feasibility

**Date:** 2026-06-25 (Cowork session, research only — no code run, no data pulled, no decision made)
**Scope:** Background research requested after the Etherscan/contract-flow discussion (`PHASE2_PQ_PILOT_REPORT.md`,
session 012). Question: if PQ = the *paired/settlement asset* moving to/from a protocol's own contract
address(es) — not the protocol's governance token — what does it actually take to build that, per category,
for the 96 "do not build" gap tokens? This file is reference material for review; it does not change any
PQ source decision already logged in `DATA_DECISIONS_LOG.md`.

---

## 0. Bottom line

The corrected framing — track ETH/USDT to/from the *pool* contract, reserve UNI for λ — is exactly right, and
it's precisely what DeFiLlama's and Dune's own protocol adapters already compute under the hood (why Phase 2c's
5 rescues came from Dune spells, not raw Etherscan). Two things make this more than "clean the transfer log,"
but both are tractable and bounded:

1. **Per protocol, you have to know which *event* — not which raw ERC‑20 Transfer — represents genuine PQ.**
   Most categories collapse to a small, recognizable, recurring pattern. There really are only a handful of
   shapes (§1), as suspected.
2. **Per protocol, you have to know how many contract addresses exist and how to enumerate them.** This is a
   solved problem for almost every category — a Factory/Registry contract's creation-event log lists every
   instance — not something requiring bytecode archaeology (§2).

The biggest practical finding: **this doesn't require writing an Etherscan log-decoder from scratch.** Dune
automatically decodes the events of *any* source-verified contract into raw `<contract>_evt_<EventName>` tables
the moment it indexes that contract — no analyst has to have hand-built a "spell" first (§3). That turns the
build from "ABI decoder + `getLogs` pipeline" into "find the verified address, write one SQL query" — much
closer to what session 015/016 already proved out for AAVE/LDO/GNS/STRK than to a from-scratch Etherscan pull.

---

## 1. The category patterns (six core + one watch-item)

| # | Category | Contract shape | **PQ event** (genuine transacted value) | **Excluded** (capital-stock / non-PQ) | Discovery mechanism |
|---|---|---|---|---|---|
| 1 | **DEX / AMM** (Uniswap V2/V3, Sushi, Curve, Balancer forks) | Multi-contract: one pool per pair × fee tier | `Swap` — V2: `Swap(sender, amount0In, amount1In, amount0Out, amount1Out, to)`; V3: `Swap(sender, recipient, amount0, amount1, sqrtPriceX96, liquidity, tick)` | `Mint` / `Burn` — liquidity add/remove (capital stock, not flow) | Factory's `PairCreated` (V2) / `PoolCreated` (V3) event log — one log per pool ever deployed |
| 2 | **Lending** (Aave V2/V3, Compound V2/V3) | Aave: one shared Pool proxy across all reserves. Compound: one cToken contract per listed asset (small, fixed count) | Aave: `Supply`, `Borrow`, `Repay`, `Withdraw`. Compound: `Mint`(=deposit→cToken), `Redeem`, `Borrow`, `RepayBorrow` | Compound's own `Mint` means "deposit," **not** an AMM-style LP mint — same word, different category, must not conflate | Small enough to enumerate directly from protocol docs/Etherscan; factory pattern not critical |
| 3 | **Derivatives / Perps** (GMX V2, Synthetix-style) | Few core singleton contracts (Vault, Router/PositionManager) | `IncreasePosition` / `DecreasePosition`, keyed on **`sizeDeltaUsd`** (notional, leverage-adjusted) | Raw collateral-token Transfer into the vault = margin only, **understates** true notional by the leverage multiple | No factory enumeration needed, but every protocol has bespoke event names/decimals (GMX uses 30-decimal USD fixed-point) — each is its own mini-spec |
| 4 | **Bridges — lock & mint** (Wormhole Token Bridge-style) | Escrow/lock contract per asset per chain | The lock/burn transfer-initiated event (Wormhole: `transferTokens()` → Core Contract's message event) | None structurally — every unit locked is, by definition, a transfer in progress | Small, fixed, documented escrow address set |
| 4b | **Bridges — liquidity-pool** (Across, Hop, Stargate) | SpokePool/Pool contracts, sometimes one per chain | `FundsDeposited` (v2) / `V3FundsDeposited` (v3) on the source SpokePool, matched to `FilledRelay`/`FilledV3Relay` on destination | Relayer/LP capital deposited to *back* relays — same liquidity-provision conflation problem as AMM Mint/Burn | Documented Hub/Spoke addresses, no factory enumeration needed |
| 5 | **Liquid staking** (Lido-style) | Singleton contract | `Submitted` (ETH staked in) + withdrawal-queue claim event (ETH out) | Ordinary stETH ERC‑20 transfers between wallets — secondary-market trading of the receipt token, not new staking flow | Trivial — one contract |
| 6 | **Yield vaults / farm aggregators** (Yearn, Convex, generic) | Multi-contract if many strategies, but standardizing | **If ERC‑4626-compliant:** generic `Deposit(sender, owner, assets, shares)` / `Withdraw(sender, receiver, owner, assets, shares)` works across *any* compliant vault with one decoding rule | Legacy pre‑4626 Yearn V1/V2, Convex use custom non-standard events — must check per-protocol; also note `Deposit`/`Withdraw` here is gross capital flow, closer to a TVL-flow than a "transacted value" in the swap/loan sense — a definitional question for the paper, separate from extraction | Registry contract where one exists (Yearn has one); otherwise enumerate from docs |
| 7 (watch) | **Stablecoin / CDP issuance** (MakerDAO-style) | Vault-per-position pattern | `Frob`/vault-specific debt mint/burn events | — | Not deeply researched this round — flag only if a gap token turns out to be CDP-style |

**Why this is bounded, not 96 bespoke investigations:** every one of the 96 gap tokens' protocols is, structurally,
a fork or variant of one of rows 1–6. The "read the Solidity" step is really "identify which of ~7 known shapes
this protocol is," then apply that shape's known event pattern — not starting from zero each time.

---

## 2. Contract discovery / aggregation ("all addresses running a certain type of code")

- **Factory/Registry event log — the standard mechanism, not a workaround.** Query `getLogs` once on the
  Factory's creation event (`PairCreated`/`PoolCreated`/`MarketCreated`-style) and you get every instance address
  ever deployed. This is literally how DeFiLlama and Dune enumerate pools themselves — no bytecode inspection
  needed. [Uniswap V2 Factory](https://docs.uniswap.org/contracts/v2/reference/smart-contracts/factory),
  [`PairCreated` source](https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Factory.sol).
- **EIP‑1167 minimal-proxy clones** (common in vault/farm forks): a fixed, recognizable 45-byte runtime bytecode
  pattern with only the implementation address swapped in. Etherscan and Dune already auto-detect and label these
  ("Similar Match"/clone display) — finding "every clone of vault X" is a known bytecode-prefix grep, not a
  research problem. [EIP‑1167 spec](https://eips.ethereum.org/EIPS/eip-1167).
- **Etherscan Similar Contract Search** (`etherscan.io/find-similar-contracts`): given one verified contract,
  surfaces other deployed contracts with matching/near-matching bytecode — useful for finding unverified forks of
  known protocol code. Etherscan's own caveat: differing constructor arguments can mean similar bytecode behaves
  differently, so it's a heuristic, not a guarantee. [Tool](https://etherscan.io/find-similar-contracts),
  [explainer](https://info.etherscan.com/what-is-similar-match-bytecode/).
- **Net:** none of this requires hand-reading raw bytecode for the 96 tokens. The practical path is almost always
  "find the protocol's Factory/Registry address from its docs or Etherscan label → pull its creation-event log."

---

## 3. The real shortcut: Dune auto-decodes verified contracts, no hand-built spell required

Worth separating two layers of Dune that the project has only used the top one of so far:

- **Spellbook** (curated, analyst-built SQL views — `lending.borrow`, `dex.trades`, etc.) is what Phase 2c used
  for AAVE/LDO/GNS/STRK/SUN. This is the layer that was *missing* for 13 of the 17 dry-run tokens (session 016).
- **Underneath Spellbook, Dune automatically decodes the events and function calls of *any* contract that is
  source-verified** on its chain's explorer into raw `<project_or_contract>_evt_<EventName>` tables — this
  happens automatically on indexing, with zero analyst curation. [Dune Spellbook repo](https://github.com/duneanalytics/spellbook)
  describes this decode-then-curate structure directly.

This means the real blocker for many of the 96 gap tokens isn't "nobody wrote a spell" (true, but not the
question) — it's whether (a) the relevant contract(s) are source-verified at all, and (b) Dune has indexed that
chain. If both hold, the per-event table already exists today, queryable with one SQL query — turning "build an
Etherscan ABI decoder" into "find the verified address, write one query." Same tool, same workflow already proven
on AAVE/LDO/GNS in sessions 015–016, not a new build process.

---

## 4. Applying this to the remaining gap-token shape (Phase 2c's own categories)

| Gap category | Fit for this method | Why |
|---|---|---|
| **Bridges** (DeFiLlama vertical paywalled) | Good — *if* lock-and-mint | No LP conflation; check per-bridge whether it's lock-and-mint (good fit) or liquidity-pool style (same Mint/Burn-style conflation as AMMs) before assuming |
| **Derivatives** (DeFiLlama vertical paywalled) | Workable but bespoke | Must read the specific notional field per protocol (no universal "Swap"-style shortcut); collateral-only tracking systematically undercounts |
| **Lending gaps beyond AAVE** | Good | Same Supply/Borrow/Repay/Withdraw pattern, small fixed contract count — easiest of the remaining categories if the contract is verified and Dune-indexed |
| **Farm/Yield** (mostly dead, Phase 2c) | N/A | The technical method doesn't revive a dead contract — not worth building where there's no activity left to capture |
| **DEX/AMM-adjacent / symbol-collision** | Best fit of all | Factory-discovery + `Swap`-event decoding is the most mature, lowest-risk pattern — it's literally DeFiLlama's own method |

---

## 5. Recommended scoping process

1. Re-tag each of the 96 gap tokens by which row of §1 its protocol matches (DEX, Lending, Derivatives, Bridge
   lock-vs-pool, Staking, Vault, CDP/other).
2. Per token, a 2-minute Etherscan check: is there a verified contract, and is it Factory-style (many pools) or
   singleton-style (one/few contracts)? This alone rules out the "unenumerable many-pool" failure mode early.
3. For survivors, check Dune for an already-auto-decoded event table on that contract *before* writing anything
   — a meaningful fraction may already be queryable with no new build.
4. Only write a bespoke per-protocol query/decode step for what's left, prioritized by cleanest event semantics
   first (Bridges, Lending) over messiest (Derivatives notional fields, legacy non‑4626 vaults).

No purchase implied anywhere in this process — steps 1–4 run on the free Dune tier already in use, or
Etherscan's free tier for one-off address lookups.

---

## Sources

- [Uniswap V3 Pool events](https://docs.uniswap.org/contracts/v3/reference/core/interfaces/pool/IUniswapV3PoolEvents) / [V2 Factory](https://docs.uniswap.org/contracts/v2/reference/smart-contracts/factory) / [`UniswapV2Factory.sol`](https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Factory.sol)
- [Aave V3 Pool contract docs](https://aave.com/docs/aave-v3/smart-contracts/pool)
- [Compound V2 cToken docs](https://docs.compound.finance/v2/ctokens/)
- [ERC‑4626 spec](https://eips.ethereum.org/EIPS/eip-4626)
- [Wormhole Token Bridge contracts](https://wormhole.com/docs/products/token-bridge/guides/token-bridge-contracts/)
- [Across Protocol tracking events](https://docs.across.to/reference/tracking-events) / [`HubPool.sol`](https://github.com/across-protocol/contracts/blob/master/contracts/HubPool.sol)
- [GMX V2 contracts docs](https://docs.gmx.io/docs/api/contracts-v2/)
- [Lido contracts docs](https://docs.lido.fi/contracts/lido/)
- [EIP‑1167 minimal proxy spec](https://eips.ethereum.org/EIPS/eip-1167)
- [Etherscan Similar Contract Search](https://etherscan.io/find-similar-contracts) / [explainer](https://info.etherscan.com/what-is-similar-match-bytecode/)
- [Dune Spellbook repo](https://github.com/duneanalytics/spellbook)

**Next step:** human review tomorrow morning, then decide whether to run step 1–2 of §5 (categorize + Etherscan
verified/Factory check) as a bounded Claude Code diagnostic pass before committing to any per-protocol build.
