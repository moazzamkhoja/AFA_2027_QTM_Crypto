# Session 020 — Bucket 2 + Bucket 3 Coverage Addendum

**Project:** AFA 2027 QTM Crypto. **Session:** 020 (2026-06-26). **Model:** Claude Code / Opus 4.8.
**Scope (from `CLAUDE_CODE_LAMBDA_BUCKET2_BUCKET3_RECOVERY_PROMPT.md`):** build every Bucket-2
(non-EVM coin staking) and Bucket-3 (EVM token lock) series that verifies **live, response-body**,
and upgrade Entry 42's docs-level findings to response-body-verified ones. No PQ, no Channel 2, no
λ-assembly-logic change. **No paid tier used, no purchase made.** Source-of-truth for *why*:
`04_code/DATA_DECISIONS_LOG.md` Entries 43–49 (this session).

> **Headline.** λ now covers **1,880 observed asset-months across 62 distinct assets**
> (up from 1,688 / 58). Coin staking went **3 → 5** (added **TRX, SOL**, both built **keyless** —
> no signup needed, correcting Entry 42's "free with signup"). Token locks went **10 → 13**
> (added **GMX** — the Entry-41 deferral — plus **AERO, CAKE**, all via a validated Dune
> curated-transfers reconstruction that cross-checks to live `balanceOf` at <0.1%). Every other
> Bucket-2 chain was checked live and is recorded below as a response-body-verified rejection,
> engineering gap, access gate, or open gap — **not** a silent drop.

| λ metric | session 019 (before) | session 020 (after) | Δ |
|---|---|---|---|
| observed asset-months | 1,688 | **1,880** | +192 |
| distinct assets | 58 | **62** | +4 (TRX, SOL, AERO, CAKE) |
| — coin | 7 | **9** | +2 (TRX, SOL) |
| — token | 47 | **49** | +2 (AERO, CAKE); GMX upgraded 1→2-channel |
| — other | 4 | 4 | 0 |
| 2-channel asset-months | 322 | **354** | +32 (GMX's voting+lock months) |
| Ch1 standardizable months | 73 | **78** | +5 |

---

## Part A — Bucket 2 (non-EVM coin staking)

| Chain | cmc | Tier | Verdict | Response-body evidence (live, this session) |
|---|---|---|---|---|
| **TRX** | 1958 | 1 | **BUILT (keyless)** | TronScan `apilist.tronscanapi.com/api/freezeresource?start_day=&end_day=` returns full **daily** history with **NO API key** — `total_freeze_weight` = total frozen TRX. 78 months (2019-12→2026-06), ratio 26%→56% (latest 49%). **Corrects Entry 42**: no free signup needed, the read endpoint answers unauthenticated. |
| **SOL** | 5426 | 1 | **BUILT (keyless)** | validators.app `/api/v1/epochs/mainnet.json?per=200&page=N` returns `total_active_stake` (lamports) **WITHOUT a token** for every epoch it recorded — which begins ~epoch 414 (~2023-01); earlier epochs are `null` on the free/keyless tier (data vintage, not a paywall — the null pattern is time-based). 40 months (2023-02→2026-06), ratio ~74%. **FLAG:** a few early months show ratio>1 (active stake includes tokens CMC counts as non-circulating) — kept un-capped & flagged. |
| **DOT, KSM** | 6636, 5034 | 2 | **NOT built — Entry-42 correction** | Subscan `polkadot.api.subscan.io/api/scan/staking/era_stat` returns **HTTP 403** "API strictly requires an API key. Unauthenticated access is disabled." A **free** Subscan plan exists and is self-serve (pro.subscan.io), but the key requires interactive email signup that could not be completed in this non-interactive session. So Entry 42's docs-level "free, untagged `[PRO]` ⇒ free-tier" could **not** be response-body confirmed — the endpoint is unreachable without *any* key. Build script ready to extend once a free key is in `.api_keys.json`. **No Pro purchase.** |
| **HBAR** | 4642 | 3 | **Documented gap (scoped)** | Mirror Node `/api/v1/network/stake` returns only the **current** aggregate (`stake_total` = 14.6B HBAR) and takes no timestamp. A historical series needs per-account `staked_node_id` summation over 15-min balance snapshots across millions of accounts — intractable keyless (confirms Entry 42's engineering framing; not built). |
| **SUI** | 20947 | 3 | **Documented gap (scoped)** | `suix_getLatestSuiSystemState` works keyless and gives current total stake (sum `stakingPoolSuiBalance` across 129 validators = 7.23B SUI), but RPC exposes **only current** system state — historical per-epoch totals require reading every validator pool's `exchange_rates` table object-by-object across all epochs (engineering, keyless-intractable). Not built. |
| **CELO** | 5567 | 4 | **Documented gap (reclassification confirmed, build FAILED cross-check)** | Reclassification half **confirmed**: Celo is on Etherscan V2 (chainid 42220, existing key), and LockedGold `0x6cC0…349E` is still live (balanceOf 85.65M; `getTotalLockedGold()` 82.43M CELO). BUT the free getLogs reconstruction does **not** reproduce that total — GoldToken Transfer in/out → 2.0M (native locking emits no ERC-20 Transfer); LockedGold's own `GoldLocked/Unlocked/Relocked` events → 25.8M (the ~57M shortfall is locked CELO carried over as **state** in the 2025-03 L2 migration, with no re-emitted lock event on the indexed chain). Fails the Entry-26 cross-check → **not shipped**; the only clean number is historical `getTotalLockedGold()` (archive/PRO). |
| **ATOM/INJ/SEI/KAVA** | 3794/7226/23149/4846 | 5 | **Open gap (access checked)** | Mintscan/Cosmostation API = contact-sales, pricing undisclosed (not self-serve). Bitquery Developer tier is a **trial only** (10K points, first month, then upgrade/contact) — not a sustained free tier; per-appchain historical bonded-total coverage + points cost unconfirmed. No self-serve free path. **No purchase.** |
| **AVAX** | 5805 | 5 | **Open gap (access checked)** | AvaCloud Metrics API has a historical "Staking Information" feature, but the pricing/free-read gate could not be confirmed from the public pricing pages (ambiguous, as Entry 42 found). Needs a direct API-key signup-flow check. **No purchase.** |
| **NEAR** | 6535 | 5 | **Open gap (access checked)** | Pikespeak (key-gated, pricing undisclosed) / NearBlocks (current `/v1/stats` only; historical-staking endpoint + pricing unconfirmed). No self-serve free historical path confirmed. **No purchase.** |
| **EOS, ICP, APT** | 1765/8916/21794 | 6 | **Open gap (no source)** | No free, keyless, historical staked/neuron-stake/delegation series located this session (APT's free Indexer GraphQL `current_delegated_staking_pool_balances` is current-state-only). Left as documented gaps. |
| **ALGO** | 4030 | excl. | **Structural gap (Entry 42)** | Confirmed not a money problem — no vendor has a precomputed online-stake series; requires full chain replay. Not pursued. |

**Built Bucket-2 output:** `03_data/phase1/channel1_pos_coins_bucket2.csv` (TRX + SOL, 118 asset-months,
2 assets). No value guessed or interpolated; ratio denominator = panel circulating supply (cmc_id+month).

---

## Part B — Bucket 3 (EVM token locks)

**Candidate pool.** From `classification_table.csv`, `asset_class='token'` rows not already recovered
by any channel in the live-recomputed coverage set (61 cmc_ids), not one of the 5 final rejects
(MKR/BAL/COMP/RUNE/ANGLE), carrying a governance/staking tag or a `defillama_categories` value →
**290 candidates** (`03_data/phase1/_bucket3_candidates.csv`). The Entry-26 single-clean-escrow
standard is the real filter: the overwhelming majority are DEXes / lending / RWA / memes / L1-L2
chains whose "governance" is in-wallet delegation, MasterChef-style farming, or off-chain Snapshot
voting — none custodies a meaningful share of the **base** token in a single contract. The same
small-clean-set outcome as Entry 26/41.

**Dune method correction.** The kickoff's named table `balances_<chain>.daily_updates` **does not
exist** on the Dune free tier (verified live: query FAILED, "does not exist or is private"). The
correct free curated tables are **`tokens_<chain>.transfers`** (cumulate in−out of the escrow) and
`tokens_<chain>.balances` (historical snapshots). BSC's schema is **`tokens_bnb`**, not `tokens_bsc`.
Etherscan V2's free key does **not** cover Base/BSC ("upgrade your api plan"), so those escrows were
verified via keyless public RPC `balanceOf` and built entirely through Dune.

| Token | cmc | Chain | Escrow (holds BASE token) | Verdict | Cross-check (recon final vs live balanceOf) |
|---|---|---|---|---|---|
| **GMX** | 11857 | Arbitrum | StakedGmxTracker `0x908C…9dD4` | **BUILT** (was Entry-41 deferral; built first as the method confidence-check) | 6,162,450 vs 6,160,000 — **PASS (0.04%)**. 44 λ months, ratio 57%→84%. |
| **AERO** | 29270 | Base | veAERO VotingEscrow `0xeBf4…e6B4` | **BUILT** (vote-escrow of AERO, 50.3% of total supply) | 968,405,575 vs 968,403,885 — **PASS (0.00%)**. 26 λ months. **FLAG:** ratio>1 vs circulating (CMC excludes veAERO-locked AERO); ~50% vs total. |
| **CAKE** | 7186 | BNB | veCAKE `0x5692…1bAB` | **BUILT w/ FLAG** (clean ve-lock; veCAKE adoption fell post-2024 → small ~1.5% share) | 5,896,692 vs 5,896,692 — **PASS (0.00%)**. 31 λ months. |
| **AXS** | 6783 | (Ronin) | — | **REJECT** | AXS staking lives on the **Ronin** appchain — not indexed by any free EVM tool (no Etherscan-V2 free coverage, no Dune curated schema). Legacy Ethereum staking contract abandoned. No clean reconstructable single-escrow. |
| **VELO** | 7127 | Optimism | veVELO (v2) | **DEFER** | v1→v2 migration split: the in-universe cmc 7127 maps to the **v1** token `0x9560e827…`; the live veVELO locks the **v2** token `0x3c8B6502…` (a different contract). Joining a v1 cmc_id to a v2-token lock is exactly the cmcId/symbol collision the project forbids — deferred pending an identity-map resolution. |
| ~287 others | — | — | — | **No clean single-escrow lock** | DEX/lending/RWA/meme/chain tokens; governance via delegation/farming/Snapshot, not base-token custody. Many already carry a Channel-3 voting value. Not a Channel-1 lock. |

**Built Bucket-3 output:** `03_data/phase1/channel1_evm_locks_bucket3.csv` (GMX + AERO + CAKE,
101 asset-months, 3 assets), via `phase1_channel1_evm_locks_bucket3.py` (Dune `tokens_<chain>.transfers`
cumulative method, free-tier; CAKE uses a `block_time` floor for partition pruning to stay inside the
2-min free-tier limit).

---

## What is still NOT covered (for the next session's accurate starting picture)

- **Bucket 2:** DOT/KSM need a free Subscan key (self-serve, but interactive email signup not completable
  headless); CELO needs archive/PRO historical `getTotalLockedGold()`; HBAR/SUI need real aggregation
  engineering; ATOM/INJ/SEI/KAVA/AVAX/NEAR have only contact-sales/trial/ambiguous gates (Moazzam's
  purchase call, none made); EOS/ICP/APT/ALGO have no free historical source.
- **Bucket 3:** VELO deferred on v1/v2 identity ambiguity; the ~287 non-clean-escrow candidates are not
  Channel-1 locks by construction.
- **Unchanged out-of-scope:** coin PQ, Channel 2 (holding duration), λ assembly logic.

**Every join is on `cmc_id`, never symbol. Every built series cross-checks to a live on-chain
`balanceOf`/aggregate. No staking ratio was guessed or interpolated. No paid tier was used; no purchase
of any kind was made.**
