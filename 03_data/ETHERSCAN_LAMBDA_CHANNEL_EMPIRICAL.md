# Etherscan λ-Channel Map for the Token Bucket-1 Pool — EMPIRICAL (contracts read + on-chain confirmed)

**Date:** 2026-06-29 (data actually pulled this session — contract source read from Etherscan,
event `topic0`s computed, `getLogs` run to confirm each mechanism fires on-chain)
**Supersedes the speculative parts of** `ETHERSCAN_LAMBDA_CHANNEL_FEASIBILITY.md` (same date), which
reasoned from metadata *before* any contract was read. Where the two disagree, this file wins.
**Primary artifact:** `03_data/phase1/etherscan_lambda_channel_map.csv` (402 rows, per-token verdict).
**Working artifacts:** `04_code/_etherscan_lambda_findings.csv`, `04_code/_etherscan_reach_resolve.csv`,
raw caches `03_data/raw/cmc_detail/` (address resolution) and `03_data/raw/etherscan_src/` (verified source).

---

## 0. What was actually done (not metadata reasoning — real reads)

1. **Resolved a contract address for every one of the 402 tokens** via CMC `data-api … detail.platforms[]`
   (cached) ∪ the project identity map. Result: **301 carry an EVM address Etherscan V2 indexes; 101 are
   non-EVM natives** (Solana/Tron/TON/WAX/NEM/Waves/Qtum/ICON/Cosmos/…) off Etherscan entirely.
2. **Pulled and parsed the verified source/ABI for all 301** (`contract/getsourcecode`, cached). Deep-read
   the Solidity of HEX, NMR, AST, CORE, ILV, FLOKI to separate genuine mechanisms from look-alikes.
3. **For every λ-relevant event in each ABI, computed the exact `topic0` (keccak-256 of the canonical
   signature) and ran `logs/getLogs`** over the full chain history to confirm the event actually fires,
   how many times, and from which block. This is the "find it on Etherscan" step — presence in the ABI
   was *not* accepted as evidence; only emitted logs were.

This process **corrected three different errors** that metadata-only reasoning would have shipped:
- look-alike locks (vesting/compliance) that are not holder conviction (§3);
- governance infrastructure that exists in bytecode but **never fired** (dormant DAOs, §2.2);
- and — most importantly — a **chain-specific free/paid boundary** in the Etherscan API itself (§4).

---

## 1. The headline finding — the bucket is NOT uniformly mechanism-dead

The prior Bucket-1 audit rejected these tokens as *"governance = delegation/Snapshot, no escrow"* and
checked only Snapshot + DeFiLlama staking buckets (396/398 had no Snapshot). Reading the contracts and
hitting Etherscan shows **24 tokens carry on-chain, `getLogs`-retrievable λ data the audit never looked for:**

### Channel 1 — genuine native lock/stake, confirmed firing on Etherscan (4)
| Token | Contract | Mechanism (read from source) | Confirming event | Earliest log |
|-------|----------|------------------------------|------------------|--------------|
| **HEX** | HEX | `stakeStart()` → `_burn(staker, hearts)`, tracked in `_lockedHeartsTotal` | `StakeStart` / `StakeEnd` (stakedHearts) | blk 9,046,425 |
| **NMR** | NumeraireBackend | `stake()` locks NMR in-contract (tournament skin-in-game) | `Staked(staker,…,totalAmountStaked,…)` | 3,905,941 |
| **AKRO** | Akropolis (proxy→impl) | protocol staking lock | stake event | 8,099,298 |
| **stkAAVE** | staked-AAVE safety module | staked AAVE lock/redeem | stake event | 17,300,691 |

→ Channel-1 ratio (locked / total supply) is reconstructable per month-end from these event logs.

### Channel 3 — ACTIVE on-chain delegated voting weight, confirmed firing (20)
`COMP, MET, DDX, FORTH, CVP, RAD, DMG, FLUID, ETHDYDX, BIT, EUL, T, ONDO, BONE, CYBER, PEAK, W, EIGEN,
WLFI, BLAST` — each emits `DelegateVotesChanged` (COMP/OZ-Votes) with real history (COMP back to block
9.69M / 2020). This yields a monthly **delegated-voting-supply** series straight from Etherscan — a
Channel-3 (and arguably a Channel-1-style "supply committed to governance") signal.

### Channel 2 — holding duration (universal, mechanism-free)
Buildable for **all 301** EVM tokens from the `Transfer` log via a coin-age/FIFO engine, regardless of
whether the token has any lock or vote. (This validates the earlier report's core thesis that Ch2 is the
mechanism-independent opening — but the data adds that Ch1/Ch3 are *not* empty, contrary to that report.)

---

## 2. What reading-the-logs ruled OUT (the discipline that matters)

### 2.1 Look-alike "lock" events that are NOT conviction (4) — excluded by reading source
`MVL` (`addTokenLock`, founder/vesting), `WLD` (`inflationUnlockTime`, emission schedule), `FST`, `FBTC`
— admin/vesting/compliance locks, not voluntary holder conviction. Keyword-matching the ABI would have
counted these; reading who-can-call-it excludes them. Also `AST`: `lockBalance()`→`BalanceLocked` is a
*genuine* voluntary lock in source, but `getLogs` returns **0** — the feature was deployed and never used.

### 2.2 Governance infrastructure present but DORMANT/negligible (9, on free chains) — excluded by getLogs
`CORE, SUPER, ILV, FLOKI, APEX, BEAM` (≤2 lifetime `DelegateChanged`, `DelegateVotesChanged` never fired)
and `ALI, CPOOL, BARD` (zero delegation ever). These copied the COMP/OZ-Votes boilerplate but the
delegated-voting channel is effectively empty → not usable. Only the on-chain log count, not the ABI,
reveals this.

---

## 3. THE PAID-API ANSWER (chain-specific, measured live — not assumed)

The free Etherscan V2 key behaves differently **per chain**, confirmed by probing `getLogs` on a real
bucket token on each chain:

| Etherscan API call | Ethereum | Polygon | Arbitrum | Blast | **BSC** | **Base** | **Avalanche** |
|--------------------|:--------:|:-------:|:--------:|:-----:|:-------:|:--------:|:-------------:|
| `getsourcecode` (read contract) | ✅ free | ✅ free | ✅ free | ✅ free | ✅ free | ✅ free | ✅ free |
| `getLogs` / `tokentx` (event history) | ✅ free | ✅ free | ✅ free | ✅ free | ❌ **PAID** | ❌ **PAID** | ❌ **PAID** |

BSC/Base/Avalanche return literally: *"Free API access is not supported for this chain. Please upgrade
your api plan for full chain coverage."* So:

- **Where a paid Etherscan plan is genuinely required:** event-history (`getLogs`) on **BSC, Base,
  Avalanche** — i.e. the **41 bucket tokens on those chains**, of which **8 have ERC20Votes infra in
  their ABI whose activity cannot be confirmed without paying**: `ALT, AWE, BAKE, CHEEL, EDG, MDX, PONKE,
  ZORA`. For these, the paid plan would resolve active-vs-dormant and (if active) unlock the Channel-3
  series. Channel 2 (Transfer-log holding duration) on these 41 also needs the paid plan.
- **Where paid adds nothing:** the **260 tokens on Ethereum/Polygon/Arbitrum/Blast** — all event history
  is already free; the 24 confirmed-active channels above were all built on the free key.

This *refines* the earlier report's claim ("buy paid only for Channel 2"): the real paid-plan value is
**(a) any channel on BSC/Base/Avalanche, and (b) Channel-2 throughput at panel scale on the free chains**
(the free tier's 100k-calls/day cap, not a per-chain block, is what binds for full Transfer-history pulls).

---

## 4. Final comprehensive tally (402 tokens)

```
non-EVM, off Etherscan entirely .......................... 101
EVM-reachable, contract READ & ABI-classified ............ 301
   ├─ on getLogs-FREE chains (ETH 255 / Polygon 1 / Arb 3 / Blast 1) ... 260
   └─ on getLogs-PAID chains (BSC 33 / Base 6 / Avax 2) ................. 41

CHANNEL 1  genuine lock/stake, getLogs-CONFIRMED ........... 4   HEX, NMR, AKRO, stkAAVE
CHANNEL 3  ACTIVE delegated voting, getLogs-CONFIRMED ...... 20  (list §1)
CHANNEL 3  ERC20Votes infra, confirm needs PAID plan ...... 8   ALT,AWE,BAKE,CHEEL,EDG,MDX,PONKE,ZORA
CHANNEL 3  ERC20Votes infra but DORMANT/negligible ........ 9   CORE,SUPER,ILV,FLOKI,APEX,BEAM,ALI,CPOOL,BARD
CHANNEL 2  holding duration buildable ..................... all 301 (free for 260, PAID for 41)
look-alike locks excluded (vesting/compliance/unused) ..... 5   MVL,WLD,FST,FBTC,AST
```

**Net:** on the **free** key alone, the bucket yields **4 new Channel-1 series + 20 new Channel-3 series**
(24 tokens that were previously λ = NaN), all confirmed by on-chain logs. A **paid** plan would add up to
**8 more** Channel-3 candidates (BSC/Base/Avax) pending active-vs-dormant resolution, plus panel-scale
Channel-2 across the board. The remaining tokens are genuinely without an on-chain conviction mechanism
(dormant governance, vesting-only locks, or non-EVM).

---

## 4b. EXTENSION TO THE FULL TOKEN UNIVERSE (token + other = 1,306 assets)

The same pipeline (resolve → read contract → classify → `getLogs`-confirm) was then run over the
**entire token-class + "other"-class universe** (1,306 assets; the 633 native coins are out of scope —
handled by native-chain staking, not Etherscan). Artifact: `03_data/phase1/universe_lambda_channel_map.csv`
(1,306 rows). Caches reused; only new assets hit the API.

```
token+other universe ................................ 1306
  EVM-reachable, contract READ & ABI-classified ..... 901
     ├─ on getLogs-FREE chains (ETH/Polygon/Arb/Blast) 793
     └─ on getLogs-PAID chains (BSC/Base/Avax/…) ...... 108
  non-EVM / no contract on file ..................... 405

CHANNEL 1 genuine lock/stake, getLogs-CONFIRMED ..... 6   HEX, NMR, AKRO, stkAAVE, XAN, VSL
CHANNEL 3 ACTIVE on-chain voting, getLogs-CONFIRMED . 34  (list below)
CHANNEL 3 ERC20Votes infra, needs PAID plan ........ 15  ALT,AWE,BAKE,BNX,CHEEL,EDG,ESPORTS,FORM,
                                                         LINEA,MCT,MDX,OP,PONKE,TKO,ZORA
CHANNEL 1 lock infra, needs PAID plan .............. 1   TNC
CHANNEL 3 infra present but DORMANT/negligible ..... 15  ALI,APEX,BARD,BEAM,BOBA,CORE,CPOOL,FLOKI,
                                                         ICHI,ILV,MC,MOC,PENDLE,RACA,SUPER
```

**Channel-3 ACTIVE (34):** BIT, BLAST, BLUR, BONE, BTRST, COMP, CVP, CYBER, DDX, DMG, EIGEN, ENS,
ETHDYDX, EUL, FLUID, FORTH, GTC, HFT, KP3R, MET, MNT, ONDO, PEAK, RAD, RAIN, RGT, STRK, SUSHI, T, TOMI,
UNI, UXLINK, W, WLFI — each emitting `DelegateVotesChanged` with real on-chain history.

**New beyond the bucket-1 set:** +2 Channel-1 (`XAN`/Anoma `Locked(address,uint256)`; `VSL`/vSlice —
but VSL fires a bare `Locked()` with no amount, mechanism-only) and **+14 Channel-3 active** — `UNI, ENS,
SUSHI, GTC, KP3R, BTRST, RGT, HFT, STRK, MNT, BLUR, RAIN, TOMI, UXLINK` (the major on-chain DAOs, expected).

**Overlap caveat:** several of the 34 active Channel-3 tokens (UNI, ENS, SUSHI, COMP, …) almost certainly
already have a Channel-3 series in the λ panel via the **Snapshot** path (Entry 25). The on-chain
`DelegateVotesChanged` series is therefore a *complementary/cross-check* source for those, and net-new λ
coverage only for the ones with no existing Snapshot turnout. Deduping against the panel is a follow-up,
not done here.

**Event-quality nuance (Channel 1):** `HEX`, `NMR`, `stkAAVE`, `XAN` emit amount-bearing stake/lock events
(directly usable for the locked-supply series). `AKRO` and `VSL` emit a bare `Locked()` with no amount —
the lock mechanism is real but the series needs contract-balance reads, not the event alone. Flagged so the
6 are not treated as uniformly build-ready.

---

## 5. Method notes / caveats (flag-don't-bury, spec §0)

- **Proxy contracts:** where `getsourcecode` returned a proxy, the implementation ABI was pulled and read
  (e.g. AKRO, W, EIGEN, FLUID) so classification reflects logic, not the proxy shell.
- **Signature variants:** a few tokens (ILV) emit voting events under a signature not matching their
  verified ABI (verified-source vs deployed-bytecode drift); for those the standard `DelegateVotesChanged`
  series is unavailable and they are conservatively classed dormant/negligible, not active.
- **`getLogs` 1000-row window:** counts shown are confirmation-of-firing (capped at 1000), not final
  series; a production pull windows by block range.
- **Channel-3 semantics:** `DelegateVotesChanged` measures *delegated* voting weight (engagement via
  delegation), the canonical on-chain analogue of the spec's voter-turnout channel for protocols that
  vote on-chain rather than on Snapshot.
- **No λ panel was modified.** This is a feasibility/identification pass; building the series for the 24
  confirmed tokens (and deciding the BSC/Base/Avax paid question) is the next, separate step — seeds a
  `DATA_DECISIONS_LOG.md` entry when undertaken.
