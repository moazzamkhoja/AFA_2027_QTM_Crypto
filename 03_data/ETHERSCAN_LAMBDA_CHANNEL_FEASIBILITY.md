# Etherscan as a λ-Channel Source for the Token Bucket-1 Reject Pool — Meta-Data Feasibility

**Date:** 2026-06-29 (research / meta-data analysis only — no data pulled, no panel written, no
decision logged in `DATA_DECISIONS_LOG.md`)
**Scope:** the 402 rows of `03_data/phase1/token_bucket1_full_audit.csv` — the tokens rejected
(or flagged) during the session-021 Bucket-1 exhaustive re-audit. Question posed by the user:
*can a **paid** Etherscan API recover any of the three λ channels (Ch.1 staking/lock, Ch.2 holding
duration, Ch.3 voting) for these tokens?* This file is reference material for review; it changes
no source decision already in `DATA_DECISIONS_LOG.md` (Entries 21–26 govern λ sourcing).

---

## 0. Bottom line

**A paid Etherscan API does NOT recover Channel 1 or Channel 3 for this bucket, and it is not a
near-miss.** These tokens were rejected on **mechanism** grounds, not **access** grounds, and a
block explorer — at any price tier — improves *access* (speed, historical state, completeness),
not the existence of an on-chain mechanism to read. If a token has no single-contract base-token
vote-escrow, there is no contract for a paid `balancehistory` call to point at; if it never voted
on-chain and has no Snapshot space, there is no `VoteCast` log to replay.

**The one real opening is Channel 2 (holding duration).** It is the *only* λ channel that is
**mechanism-independent**: every EVM ERC-20 with a contract address has a complete `Transfer`-event
history, and coin-age / dormancy / HODL-wave can be computed from that history alone — whether or
not the token ever had staking, escrow, or governance. This is exactly the channel `DATA_DECISIONS_LOG.md`
**Entry 24** left unbuilt and named *"the highest-value addition"* pending a paid source. For this
bucket specifically, Channel 2 is the single intervention that would convert the largest share of
these tokens from **zero-channel (λ = NaN today)** to **one-channel (λ-eligible)** — and a paid
Etherscan key is a defensible, possibly the *only*, way to source it for long-tail dead microcaps
that Glassnode/CoinMetrics don't cover.

So the honest framing for the spend decision: **buy Etherscan Pro for Channel 2 if at all, not for
Channels 1/3.** The 1/3 rejections survive the upgrade unchanged.

---

## 1. Why "paid Etherscan" doesn't touch the rejection reasons (Ch.1 & Ch.3)

The rejections in `token_bucket1_full_audit.csv` are almost entirely *mechanism* verdicts. Tallying
the 402 rows by the mechanism archetype encoded in the `reason` field:

| Count | Mechanism archetype | Can paid Etherscan create the missing channel? |
|------:|---------------------|------------------------------------------------|
| 110 | DEX/exchange token; governance = delegation / Snapshot / farming | **No** — no base-token escrow exists to read |
| 86 | utility / infra / governance token; no DeFiLlama staking bucket, no lock | **No** — nothing to read |
| 31 | **non-EVM native L1/L2 coin** (NEM, Waves, Qtum, ICON, Skycoin, GXChain, Carbon…) | **No** — not on Etherscan *at all* (EVM-only explorer) |
| 27 | lending/CDP token; governance = delegation / Snapshot | **No** — nothing to read |
| 23 | gaming/NFT token; rewards/farming, not vote-escrow | **No** — not a base-token lock |
| 19 | REJECT-no-data: a DL "staking" figure existed but **no single contract reproduces it** | **No** — already disproven by top-holder check; paid access re-confirms the same negative |
| 19 | meme token; no mechanism | **No** |
| 18 | derivatives/perps token; no escrow | **No** |
| 13 | governance-only; in-wallet delegation/Snapshot (ANT, CTR, COMP-style) | **Marginal** — only if on-chain Governor/lock events exist (rare here) |
| 10 | stablecoin / rebase (excluded asset class) | **No** — excluded by design, not by data |
| ~40 | "other": wrapped/composite LSTs (xBTC/LST family), bridge/interop tokens (ZRO, BICO, STAKE, BFC, RIVER), **staking-lives-on-another-chain** (AXS→Ronin, SUN→Tron, ORN→TON, TLM→WAX, C98→TomoChain, HXRO→Solana), multi-contract restaking (EigenLayer, Illuvium) | **No / wrong explorer** — see §1.2 |

**Read the table as: the dominant blocker is "no single-contract base-token lock," which is a fact
about the protocol, not about Etherscan's tier.** Paid access cannot manufacture a vote-escrow
contract for a token whose governance is in-wallet delegation or off-chain Snapshot.

### 1.1 The handful Etherscan *already* handled on the free tier
The tokens in this universe that *do* have a clean single-contract lock (the 5 session-021 BUILDs,
and the LOW-tier vote-escrow names) were captured by the **existing free `getLogs` event-replay
method** documented in Entry 21/23/26 — Transfer logs into a known escrow contract, cumulative-summed
to each month-end block. Paid Pro would only swap that for a more convenient `tokenbalancehistory`
balance-at-block read; it adds **convenience, not coverage**, and only where an escrow already exists.

### 1.2 Two sub-classes that look rescuable but aren't (via Etherscan)
- **Staking-on-another-chain** (AXS→Ronin, SUN→Tron, ORN→TON/DeDust, TLM→WAX, C98→TomoChain,
  HXRO→Solana, BRISE→own chain): the lock is real but lives off the EVM/Etherscan surface. Etherscan
  V2's one key spans ~60 **EVM** chains, but **not** Solana, Tron, WAX, TON, or Ronin. These need
  each chain's own explorer/indexer, not a paid Etherscan tier.
- **Wrapped/composite LSTs** (the BTC/ETH-LST family: tBTC, LBTC, SolvBTC, syrupUSDC, stkAAVE, BETH,
  WFTM, SOL-as-wrapped, …): excluded because the "lock" is of a *different* underlying asset, not the
  token itself — a definitional exclusion the audit made deliberately, unaffected by data access.

### 1.3 Channel 3 specifically: dead on arrival for this bucket regardless of source
Of the 398 bucket tokens matched in `_stage1_triage.csv`, **396 have `has_snapshot = False`.** Snapshot
(off-chain, gasless) is the canonical Channel-3 store (Entry 25) and is *invisible to any block
explorer* — so even setting Etherscan aside, the off-chain path is empty. The only Etherscan-reachable
Channel-3 data would be **on-chain `VoteCast` logs** from a real Governor (OZ/Bravo/Alpha) or
DSChief-style lock events — but the bucket's governance archetypes are overwhelmingly
"delegation/Snapshot/in-wallet," i.e. *no* on-chain Governor. The few genuine on-chain-governance
relics here (e.g. Aragon ANT's voting app, Maker's DSChief) are already reachable on the **free**
`getLogs` tier. Net new Channel-3 coverage from a paid tier: **≈ zero.**

---

## 2. Why Channel 2 is the real (and only) opening — and what Etherscan actually gives you

Channel 2 (holding duration) does **not** ask "does this token have a lock/vote?" — it asks "how long
has supply sat unmoved?" That is computable for **any** token with a transfer history, from the
`Transfer` event log alone. This is precisely the channel Entry 24 deferred:

> *"computing coin-age requires the FULL transfer/UTXO history … the entire Transfer-log set of every
> token … No free API serves ready HODL-wave series … If a paid source or a full-history indexer is
> later obtained, Channel 2 is the highest-value addition."*

A paid Etherscan key **is** that full-history indexer for EVM tokens. Mapping the build to endpoints:

| Step | Etherscan endpoint | Tier | Note |
|------|--------------------|------|------|
| Enumerate every transfer of the token, genesis→now | `account/tokentx` *or* `logs/getLogs` on Transfer `topic0 = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` | works on **free**, but rate/volume-capped | paginate by block window (10k records/window cap); paid tier raises the 5 calls/s · 100k/day ceiling — the binding constraint at panel scale |
| Reconstruct per-address balance lots with acquisition timestamps | *(your code — FIFO lot engine)* | — | Etherscan supplies raw inputs, not the metric |
| Month-end block boundaries | `block/getblocknobytime` | free | already used in Channel 1 |
| Coin-age / dormancy / % supply unmoved > N months, per month-end | *(your code)* | — | the actual Ch.2 value |
| (optional) total supply at block, for normalization | `stats/tokensupplyhistory` | **Pro only** | else use CMC circulating from Phase 0 |
| (optional) label/strip exchange & contract wallets | `account` address tags / known-address | partial | see caveat below |

**What the paid tier actually buys here is throughput, not a magic endpoint.** Pulling the complete
Transfer history of ~150–200 EVM tokens, windowed by block, blows past the free 100k-calls/day cap;
Pro tiers (higher calls/s and daily quota) are what make a panel-scale Channel-2 pull finish in
reasonable wall-clock. The Pro-exclusive *historical-state* endpoints (`tokenbalancehistory`,
`balancehistory`) are the wrong tool for this bucket — they shine when you have an escrow contract to
read, which §1 established these tokens don't.

### 2.1 The addressable population is bigger than the 88 with an address "on file"
`_stage1_triage.csv` shows only **88/398** bucket tokens carry a contract address, of which **80** are
on an EVM chain and **22** are `Ethereum` exactly. **But the 310 `has_addr = False` rows are a project-
data gap, not a true absence:** a large share are well-known Ethereum ERC-20s whose contracts resolve
trivially from CMC `data-api … detail.platforms[]` (the enrichment Entry 22 already flagged as a
to-do) — REP/Augur, MKR (legacy), MLN/Enzyme, ANT/Aragon, NMR/Numeraire, AST/AirSwap, OMG, LEND
(legacy Aave), AGIX, POLY/Polymath, RLC/iExec, KNCL, SNX (legacy), and dozens more. Resolving
addresses first plausibly lifts the Channel-2-addressable count from ~80 toward **~150–200**.

### 2.2 Caveats that keep Channel 2 honest (flag, don't bury — spec §0)
- **Etherscan gives raw logs, not a HODL metric.** You build the coin-age engine; there is real but
  *bounded* compute (these are low-volume dead microcaps — few transfers each, the easy end of the
  problem, unlike BTC/ETH).
- **"Holding duration" needs address-class filtering to be a clean conviction proxy.** Exchange,
  custodial, contract, and LP wallets sitting unmoved are *not* holder conviction. Etherscan's address
  labels are incomplete for 2017-era tokens, so the filter is itself a judgment call to document.
- **It's a proxy, not the spec's ideal.** §3.2 already frames Ch.2 as a proxy; the limitation is to be
  recorded, per §0, not hidden.
- **Non-EVM and another-chain stakers (§1.2) stay out** — Channel 2 via Etherscan only reaches the EVM
  ERC-20 subset.

---

## 3. Recommendation (no spend implied by this analysis)

1. **Do not buy Etherscan Pro to chase Channels 1 or 3 for this bucket.** Those rejections are
   mechanism facts; a paid tier re-confirms the same negatives. The few real locks/votes here are
   already reachable on the free `getLogs` tier.
2. **The defensible reason to buy is Channel 2** — and it is a *panel-wide* upgrade, not bucket-1-only:
   Channel 2 is currently NaN for **every** asset (Entry 24). Building it benefits the whole panel, but
   *this bucket benefits most*, because Ch.2 would be its **only** channel — converting zero-channel
   (λ = NaN) tokens into one-channel λ-eligible ones.
3. **Sequence before any purchase** (all free): (a) resolve EVM contract addresses for the bucket from
   CMC `platforms[]` (Entry-22 enrichment) to size the true Channel-2-addressable count; (b) prototype
   the FIFO coin-age engine on **one** token's full Transfer log on the *free* tier to validate the
   metric and measure call volume; (c) extrapolate the call budget to ~150–200 tokens × full history to
   decide whether the free 100k/day ceiling actually binds — *that* number, not a guess, justifies the
   tier.
4. If built, it seeds a `DATA_DECISIONS_LOG.md` entry **superseding the open question in Entry 24**
   (paid-source-for-Ch.2) and the Entry-21 note that "a paid Etherscan-Pro tier would broaden Channel 1"
   — with the correction recorded here that, *for this bucket*, the broadening is Channel **2**, not 1.

---

## 4. One-paragraph answer to the question asked

Can a paid Etherscan API find Channel 1/2/3 for the Bucket-1 reject pool? **For 1 and 3: no — these
tokens were rejected because the on-chain mechanism (single-contract base-token escrow; on-chain
governance) doesn't exist, and a richer API tier reads contracts faster but cannot invent them; 31 of
them aren't even on an EVM chain Etherscan indexes, and 396/398 have no Snapshot space.** **For 2: yes,
and it's the only place a block explorer helps** — holding-duration is computable from the `Transfer`
log of any EVM ERC-20 regardless of mechanism, it's the exact gap Entry 24 flagged as highest-value,
and it would give these otherwise-zero-channel tokens their first λ channel. The paid tier's value
there is throughput to pull full transfer histories at panel scale, not its historical-state endpoints
(which need an escrow contract these tokens lack).

---

## Sources / cross-references (internal)
- `03_data/phase1/token_bucket1_full_audit.csv` (402 rows; mechanism archetypes tallied in §1)
- `03_data/phase1/_stage1_triage.csv` (`has_addr` 88/398 true, 80 EVM/22 Ethereum; `has_snapshot` 2/398 true)
- `04_code/DATA_DECISIONS_LOG.md` Entry 21 (source audit; free `eth_call` silently latest-only; getLogs is the historical path), Entry 22 (DeFiLlama/CMC as address-book; CMC `platforms[]` enrichment to-do), Entry 23 (ETH beacon-deposit `getLogs` event-replay — the Ch.1 technique), **Entry 24 (Ch.2 unbuilt, "highest-value addition")**, Entry 25 (Ch.3 = Snapshot GraphQL, off-chain → explorer-invisible), Entry 26 (single-escrow top-holder confirmation standard)
- `03_data/CONTRACT_EVENT_TAXONOMY_RESEARCH.md` (companion: event taxonomy for *PQ* flows, a separate variable from λ)
