# Phase 1 λ Scale-Up + Real TVL Panel — Coverage Report

**Project:** AFA 2027 QTM Crypto. **Session:** 019 (2026-06-26). **Model:** Claude Code / Opus 4.8.
**Scope (from the kickoff prompt):** λ scale-up (tokens: widen Channel 1 & Channel 3; coins: a
live PoS-coin source-verification pass) **+** a real, persistent TVL panel for tokens.
**Out of scope (unchanged):** PQ-for-coins, Channel 2 (holding duration), the λ
z-scoring/standardizability/weighting logic.
**Source-of-truth for *why*:** `04_code/DATA_DECISIONS_LOG.md` Entries 21–30, 40, **41 (this session)**.
**New/changed code:** `phase1_channel1_evm_locks_ext.py`, `phase1_channel1_pos_coins.py`,
`phase1_channel3_voting.py` (2 spaces added to the curated map), `phase2_build_tvl_panel.py` (new).

> **Headline.** λ now covers **1,688 observed asset-months across 58 distinct assets**
> (up from 1,374 / 52). The coin side of the locking channel went from **1 asset (ETH only)
> to 3** — Cardano and Tezos now have full, free, on-chain staking-ratio series — and four
> new EVM vote-escrow/staking tokens plus two governance spaces the prior "not on Snapshot"
> gap list actually had were added to the token side. Separately, the diagnostic-only
> `check_tvl()` presence-check is replaced by a **real persistent TVL panel**:
> `03_data/phase2/tvl_panel.csv`, **4,999 monthly asset-months across 99 tokens, 2019-12 →
> 2026-05**. **The TVL panel is a valuation-multiple denominator (NV/TVL), NOT a PQ proxy —
> Entry 30's stock-vs-flow distinction is unchanged by this build.**

---

## 1. λ coverage: before → after

λ is computed on `status='observed'` asset-months only; each channel is z-scored within its
monthly cross-section (≥2 assets with finite values and std>0 required), and λ = the
equal-weighted mean of the available standardized channels (no imputation). **That assembly
logic was not touched** — only the channel *input* files were widened, and
`phase1_assemble_lambda.py` picked them up automatically via its `channel1_*.csv` glob +
`channel3_voting.csv`.

| Metric | Before (session ≤018) | After (session 019) | Δ |
|---|---|---|---|
| λ asset-months (observed) | 1,374 | **1,688** | +314 |
| Distinct assets with any λ | 52 | **58** | +6 |
| — coin | 5 | **7** | +2 (ADA, XTZ) |
| — token | 43 | **47** | +4 (PENDLE, LQTY, ENA, PERP) |
| — other | 4 | 4 | 0 |
| Month range | 2020-08 → 2026-05 | 2020-05 → 2026-05 | earlier start |
| 2-channel asset-months | 253 | **322** | +69 |

**Channel-level distinct-asset coverage (after):**

| Channel | Before | After | New entrants |
|---|---|---|---|
| **Ch1 staking/locking** | 7 | **13** | coins ADA, XTZ; tokens PENDLE, LQTY, 1INCH, RPL |
| — of which coins | 1 (ETH) | **3** | +ADA, +XTZ |
| — of which EVM-escrow tokens | 6 | **10** | +PENDLE, +LQTY, +1INCH, +RPL |
| **Ch3 voting** | 51 | **53** | ENA, PERP |
| **Ch2 holding duration** | 0 | 0 | out of scope (Entry 24) |

Standardizable cross-sections (months a channel had ≥2 assets, so it can z-score): Ch1 in
**73** months, Ch3 in **69** months. The coin-side Channel-1 widening matters specifically
because ETH alone could never be standardized within the coin cross-section; ADA+XTZ+ETH now
co-occur, so coin staking can actually enter λ.

Note: 1INCH and RPL already had a λ via Channel 3 (1inch.eth / rocketpool-dao.eth), so adding
their Channel-1 lock **upgraded them to two-channel** rather than adding a new asset — which is
why Channel-1 gained 6 entrants but the distinct-asset total rose by only the 4 genuinely-new
assets (PENDLE, LQTY, ENA, PERP).

---

## 2. Part A.1 — Token Channel 1 candidates, individually verified

Method unchanged from Entry 26: a candidate is accepted only if a **single, identifiable
contract holds the BASE token directly**, so `balanceOf(contract) == locked supply of that
token`, reconstructed from the token's Transfer event logs (Etherscan V2 `getLogs`, the only
historically-correct free-tier method — Entry 21). Each candidate was sanity-checked live with
a current `balanceOf(escrow)` read before acceptance (eth_call latest-state is fine for a
presence check; Entry 21 only forbids *historical* state reads). The reconstructed latest
locked supply matched the independent `balanceOf` to within rounding for all four accepted
mainnet tokens — a strong cross-check that the log reconstruction is correct.

| Token | cmc_id | Contract | Holds | Current lock share | Verdict |
|---|---|---|---|---|---|
| **PENDLE** | 9481 | vePENDLE `0x4f30…0210` | PENDLE | 64.5M / 281.5M = 22.9% | **VERIFIED** — vote-escrow of PENDLE |
| **LQTY** | 7429 | LQTYStaking `0x4f9F…605d` | LQTY | 57.8M / 100M = 57.8% | **VERIFIED** — fee-share stake of LQTY |
| **1INCH** | 8104 | St1inch `0x9A0C…01D7` | 1INCH | 237.1M / 1.5B = 15.8% | **VERIFIED** — governance stake of 1INCH |
| **RPL** | 2943 | RocketVault `0x3bDC…69d6` | RPL | 10.66M / 22.5M = 47.3% | **VERIFIED w/ FLAG** — see below |
| **GMX** | 11857 | StakedGmxTracker `0x908C…9dD4` (Arbitrum) | GMX | 6.16M / 9.6M ≈ 65% | **VERIFIED mechanism; series build DEFERRED** — see below |
| MKR | 1518 | DSChief `0x0a3f…dDC0` | MKR | 432 / 90,225 = 0.5% | **REJECTED** — post-Sky migration the chief holds almost no MKR; the governance lock is fragmented across chief versions and largely abandoned. No single clean meaningful locked-supply contract. |
| BAL | 5728 | — | — | — | **REJECTED** — no clean BAL-only lock (veBAL locks an 80/20 BPT, not BAL; Entry 26). |
| COMP | 5692 | — | — | — | **REJECTED** — governance is in-wallet delegation, no token lock at all (cf. SNX). |
| RUNE | 4157 | — | — | — | **REJECTED** — native THORChain-L1 asset; its identity-map "address" is a placeholder (`thorchain:0x000…000`); bonding happens on the L1, not via an EVM escrow. |
| ANGLE | — | — | — | — | **REJECTED** — not in the universe (no panel rows); cannot contribute to λ. |

**RPL flag:** RocketVault is a shared protocol vault, not a dedicated escrow; its RPL balance
is dominantly node-operator staked collateral plus a small undistributed-inflation/auction
buffer, so the reconstructed series slightly overstates pure node-stake. Kept as a
staking/locking signal with this caveat — the same standard under which xSUSHI/stkAAVE
(reward-staking, not pure vote-escrow) were kept flagged in the original 6.

**GMX deferral (honest gap, not a silent drop):** the StakedGmxTracker cleanly holds ~65% of
GMX supply directly — the mechanism *passes* the Entry-26 standard (live-verified). But the
`getLogs` reconstruction over Arbitrum's full history is impractically slow on the free tier:
Arbitrum mines millions of blocks/month, so each month-end window exceeds Etherscan's
result-window cap and recurses into a deep split tree (>60 s/month observed; 44 months would
far exceed this session's budget). Deferred to a follow-up using a transfer-pagination method
(`account/tokentx`) instead of block-range `getLogs`. The verdict (VERIFIED) stands; only the
series is pending. (Code: the GMX row is left in `phase1_channel1_evm_locks_ext.py`, commented,
with this rationale inline.)

Output: `03_data/phase1/channel1_evm_locks_ext.csv` (214 asset-months, 4 assets).

---

## 3. Part A.2 — Token Channel 3 (voting) widening

**Path 1 — DeFiLlama `governanceID` / `snapshot_space` cross-check (no new spaces).** All 29
auto-matched token Snapshot spaces (and the 3 coin ones) in `asset_onchain_identity.csv` are
already subsumed by the curated 56-space map — zero net-new spaces from this field.

**Path 2 — the Entry-25 "not on Snapshot / on-chain governance only" gap list
(MKR, LQTY, PENDLE, RUNE, PERP, WLD, ONDO, ENA).** Probed Snapshot live (direct `id_in`
lookups + the `ranking(search:)` query) rather than guessing space ids. Result: **two of the
eight actually do have official, active, token-weighted Snapshot spaces that Entry 25 missed**,
now verified and added to the curated map:

| Token | cmc_id | Space | Verification |
|---|---|---|---|
| **ENA** (Ethena) | 30171 | `ethenagovernance.eth` | erc20-balance-of on canonical ENA `0x57e1…6061` (+sENA); power/voter ≈ 10⁵–10⁶ ⇒ token-weighted ✓; 5 months of `vw_turnout` |
| **PERP** (Perpetual Protocol) | 6950 | `vote-perp.eth` | erc20-balance-of on canonical PERP `0xbC39…3447` (+sPERP/vePERP); token-weighted ✓; 20 months of `vw_turnout` |

The other six yield no defensible new coverage: ONDO/WLD return only spam or impostor spaces
(`bondone.eth`, `0xworldcoin.eth`, …); PENDLE's top result is `sdpendle.eth` (StakeDAO's
third-party Pendle locker, not Pendle's own governance) — and PENDLE is now covered via
Channel 1 anyway; RUNE is non-EVM L1; MKR (DSChief, no Governor `VoteCast`) and LQTY (no
on-chain governor in v1) have no standard EVM Governor to reconstruct from. The prompt's
on-chain `VoteCast` reconstruction was therefore not pursued for these — none exposes a
verifiable clean Governor contract, and guessing a log signature would violate the project's
no-guess rule.

Output: `03_data/phase1/channel3_voting.csv` (now 57 spaces / 53 assets with `vw_turnout`).

---

## 4. Part A.3 — Live PoS-coin source audit (coin Channel 1)

An Entry-21-style **live** free-access audit was run over the highest-cap PoS/staking coins in
the 633-coin roster (candidate list derived from `classification_table.csv` consensus tags —
173 coins carry a pos/dpos/staking tag — cross-referenced with the reference set
SOL/ADA/DOT/ATOM/AVAX/NEAR/ALGO/TRX/XTZ/EOS/ICP/KSM/CELO/KAVA/HBAR/INJ/SEI/SUI/APT). Only two
chains publish a genuinely **free, keyless, historical** bonded/staked-supply series:

| Chain | cmc_id | Source (free, keyless) | Series | Result |
|---|---|---|---|---|
| **ADA** | 2010 | Koios `api.koios.rest /epoch_info` | `active_stake` per epoch (lovelace /1e6) | **BUILT** — 70 months, 2020-08→2026-05, ratio 49%→74% (latest 60%). Shelley staking begins epoch 210 (2020-08); pre-Shelley emitted NaN, never 0. |
| **XTZ** | 2011 | TzKT `api.tzkt.io /cycles` | `totalBakingPower` per cycle (mutez /1e6) | **BUILT w/ FLAG** — 95 months, 2018-07→2026-05, ratio 35%→93% (latest 40%). FLAG: the 2024 "Paris" protocol redefined baking power, so post-2024 levels aren't strictly comparable to the delegation-era level (analogous to ETH's post-Shapella caveat). |

**Documented gaps (live-verified this session — no free historical staked-supply series):**

| Chain(s) | Reason (verified live) |
|---|---|
| ATOM, INJ, SEI, KAVA, CELO (Cosmos SDK) | `/cosmos/staking/v1beta1/pool` returns only **current** `bonded_tokens`, no history (confirms Entry 24 / Phase 2b). |
| SOL | public RPC `getEpochInfo`/`getVoteAccounts` are current-state only; historical staked supply needs a keyed indexer (Solana Beach / validators.app) — not free/keyless. |
| HBAR | Hedera Mirror `/network/stake` returns current reward params only. |
| ICP | ic-api governance metric endpoints now 404 (API moved); no verified free historical neuron-staking series located. |
| DOT, KSM | Subscan requires an API key; public RPC is current-state only. |
| AVAX, NEAR, ALGO, TRX, EOS, SUI, APT | no verified free, keyless, historical staked-supply series found; not built (no-guess / no-interpolate rule). |

**No value was guessed or interpolated** — only months with a real epoch/cycle observation are
emitted. Output: `03_data/phase1/channel1_pos_coins.csv` (165 asset-months, 2 assets).

---

## 5. Part B — Real TVL panel (tokens)

`phase2_build_tvl_panel.py` (new) reuses Phase 2c's fetch/cache/retry shape, fetches
`api.llama.fi/protocol/{slug}` for **every** dl_slug-matched token (127, re-derived live —
not just the Phase-2c NaN-PQ subset), and persists the **full series at monthly grain** (last
observation per calendar month, matching `universe_panel.csv`'s calendar-month-end
convention). Raw per-token JSON cached under `03_data/raw/phase2/tvl/`; `time.sleep(0.2)`
between calls; idempotent.

| Metric | Value |
|---|---|
| Tokens fetched (core, dl_slug-matched) | 127 |
| Tokens with a non-empty TVL series | **97** |
| Asset-months (core) | 4,895 |
| **+ verified looser-match additions** | **AXL, PERP** → **99 tokens / 4,999 asset-months** |
| Month range | 2019-12 → 2026-05 |
| Fetch failures | 0 |
| Empty series (slug matched but protocol reports no TVL) | 30 |

**Output:** `03_data/phase2/tvl_panel.csv` (`cmc_id, symbol, dl_slug, month_end, ym, tvl_usd`)
+ `03_data/phase2/tvl_panel_coverage.csv` (per-token status/range diagnostic).

**The 30 empty series are expected, not failures:** the slug maps to a protocol that legitimately
reports no protocol-level TVL — DEX/aggregators (`0x-aggregator`, `jupiter-aggregator`,
`cowswap`), DAOs/governance tokens (`aragon`, `ens`, `gitcoin`, `apecoin`, `forth-dao`),
gaming/NFT (`axie-infinity`, `my-neighbor-alice`, `yield-guild-games`), and chains
(`arbitrum`, `bittensor`, `zksync-era`, `acala`). These are tokens for which NV/TVL is simply
undefined, not data we failed to fetch.

**Optional slug-widening (stretch goal — low yield, as the prompt anticipated):** of the 321
unmatched in-universe tokens, an exact (normalized) symbol-**and**-name match against
DeFiLlama's protocol list produced only 9 candidates. Verified individually: **AXL** (Axelar,
$135M TVL, DeFiLlama `cmcId` null — a clean miss of the cmcId-keyed join) and **PERP**
(Perpetual Protocol, $0.4M TVL; DeFiLlama's `cmcId` is *stale* (1301), but the slug is
unambiguously PERP — the same asset whose `vote-perp.eth` space was verified in §3) were added.
The other 7 were rejected: **CVP, POLS** (cmcId mismatch + trivial TVL → collision risk, the
VELO/velodrome landmine from Entry 39) and **METIS, HONEY, PUMP, PYTH, WLFI** (zero protocol
TVL → nothing to add). Net stretch-goal yield: +2 tokens. Stopped there per the prompt's
"stop if low-yield" instruction.

**Semantics (reaffirmed):** this panel is the **denominator of a valuation multiple (NV/TVL)**,
a stock. It is **not** a PQ (transacted-value flow) substitute and is **not** a λ channel.
Entry 30's stock-vs-flow rejection of TVL-as-PQ is unchanged.

**Known inherited caveat (not introduced here):** the panel uses the identity map's
one-slug-per-`cmcId` choice (`phase1_build_identity_map.py` keeps the highest-TVL protocol
entry per cmcId). For multi-version protocols this captures only the mapped version's TVL
(e.g. AAVE maps to `aave-v2`, not v1+v2+v3 combined). Fixing that is an identity-map decision,
out of scope this session; flagged for whoever builds the NV/TVL ratio.

---

## 6. What is still NOT covered (so the next session starts from an accurate picture)

- **Coin PQ** — still 58/633 with real data. Explicitly deferred to a separate, later,
  authorized session (no PQ-for-coins work was done here). Flagged leads noticed in passing:
  none that change the Phase-2c conclusion (Entry 39) that token-side PQ realistically tops out
  near ~21 on free sources.
- **Channel 2 (holding duration / coin-age)** — still 0 assets, still a documented gap (Entry
  24). Untouched.
- **GMX Channel-1 series** — mechanism verified, series build deferred for Arbitrum-`getLogs`
  performance (§2). The one accepted candidate left unbuilt this session.
- **Coin staking beyond ADA/XTZ** — the other ~17 reference PoS chains have no free, keyless,
  historical staked-supply series (§4). Recovering them needs either a keyed indexer
  (Subscan/Solana Beach/validators.app — a purchase decision for Moazzam) or per-chain native
  block iteration (expensive), neither attempted under the free-tier rule.
- **TVL for the 30 empty-series tokens** — undefined by construction (no protocol TVL), and the
  321 unmatched tokens beyond AXL/PERP (low-yield, stopped).

**No paid tier of any service was used. No purchase action of any kind was taken. Every join is
on `cmc_id`, never symbol. No staking ratio, Snapshot space, or slug match was guessed — each
was verified live or logged as a gap.**
