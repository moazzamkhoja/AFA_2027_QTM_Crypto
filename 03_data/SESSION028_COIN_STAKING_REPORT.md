# Session 028 — Coin Staking (Channel-1) Expansion + AAVE Channel-2 Recovery

**Date:** 2026-07-04 · **Log entries:** 71–75 · **Kickoff:** `04_code/CLAUDE_CODE_SESSION028_COIN_STAKING_AND_AAVE_FIX_PROMPT.md`

## Headline

Seven PoS coins gained a λ Channel-1 staking series in one session — **BNB, S (Sonic),
GLMR, MOVR, XDC, CELO, AVAX — +358 coin asset-months**, every series passing the
Entry-26 cross-check at ~0% against the chain's own on-chain figure. CELO closes the
Entry-46 gap for $0, AVAX resolves the Entry-42/47 AvaCloud ambiguity (it's keyless-free).
AAVE's 22 spam-nulled Channel-2 months (2024-08→2026-05) were recovered after isolating
the REAL poisoning vector (fake-value self-transfers) — AAVE is now 3-channel through
2026-05 and the panel's 3-channel total rises 332 → 354.

**λ: 7,051 → 7,409 observed asset-months / 282 → 289 assets (coins 9 → 16).
Coin λ∩NVT_GL (regression-ready coins): 5 → 12** (ADA, AVAX, BNB, CELO, ETH, GLMR, GNO,
MOVR, S, SOL, TRX, XDC; 505 overlapping coin asset-months).

## Per-chain outcomes (Task A)

| Chain / coin | cmc_id | Verdict | Months | Method | Cross-check |
|---|---|---|---|---|---|
| BNB (BSC) | 1839 | **BUILT** | 23 (2024-07→2026-05) | StakeHub event replay: Delegated − Undelegated + RewardDistributed (Etherscan Pro, chainid 56) | Replay = live Σ totalPooledBNB over all 53 validators **exactly (+0.000%)** |
| S (Sonic) | 32684 | **BUILT** | 17 (2025-01→2026-05) | SFC event replay: Delegated − Undelegated (chainid 146) | ±0.0000% vs archive totalStake() at 6 blocks across full history |
| GLMR (Moonbeam) | 6836 | **BUILT** | 52 (2022-01→2026-04) | Substrate pallet state read: ParachainStaking.Total at month-end blocks (official archive RPC, keyless) | Chain's own aggregate; decode validated vs Σ getCandidateTotalCounted (1.054 superset ratio) |
| MOVR (Moonriver) | 9285 | **BUILT** | 57 (2021-09→2026-05) | same as GLMR (chainid 1285 RPC) | same (1.015 superset ratio) |
| XDC | 2634 | **BUILT** | 72 (2020-06→2026-05) | Etherscan Pro `balancehistory` of XDCValidator 0x…0088 (native-XDC masternode stake) | 3-way tie-out: Σ getCandidateCap 2.650B ≤ event replay 2.668B ≤ balance 2.701B; replay tracks balance at a CONSTANT +32.625M genesis offset (0.000% co-movement) |
| CELO | 5567 | **BUILT** | 70 (2020-07→2026-05) | Forno archive eth_call `getTotalLockedGold()` — full pre-L2-migration history, keyless | Chain's own getter (state read); Entry-46 reference values reproduced |
| AVAX | 5805 | **BUILT** | 67 (2020-11→2026-05) | metrics.avax.network validatorWeight + delegatorWeight (official, KEYLESS) | −1.6% vs live P-Chain platform.getTotalStake, fully explained by daily-snapshot lag; additive semantics verified against the P-Chain |
| BERA (Berachain) | 24647 | GAP | — | BeaconDeposit logs deposits only; withdrawals are consensus-side (no EVM logs). Cum deposits 382.6M > circulating — not reconstructable from EL | n/a — no free CL archive API found |
| DOT / KSM | 6636/5034 | DEFERRED | — | Subscan era_stat ready per Entry 44; no "subscan" key present | n/a |
| NEAR | 6535 | GAP | — | NearBlocks /v1/stats + /v1/validators current-only; api3 /v1/charts has 2,174 days history but NO staking field; Pikespeak key-gated | n/a |
| ATOM/INJ/SEI/KAVA | — | GAP | — | StakingRewards GraphQL 401 (auth required); Numia 401 (key required); Mintscan contact-sales (Entry 47) | n/a |

New builder: `04_code/phase1_channel1_pos_coins_evm.py` → `03_data/phase1/channel1_pos_coins_evm.csv`
(**358 asset-months / 7 assets**; picked up by the assembler's `channel1_*.csv` glob).
Stage scripts: `_s028_evm.py` (helpers), `_s028_bnb_fetch.py`, `_s028_sonic_fetch.py`,
`_s028_xdc_bera_fetch.py`, `_s028_moonbeam_fetch.py`, `_s028_avax_fetch.py`.
Raw caches: `03_data/raw/phase1_onchain/pos_coins_evm/`.

Latest staking ratios (2026-05): BNB 19.1%, S 42.4%, GLMR 22.4%, MOVR 14.3%, XDC 12.7%,
CELO 13.8%, AVAX 51.3%. FLAGS: early CELO (max 272%) and AVAX (max 1157%, 2020) months
exceed 1 vs CMC circulating because staked supply includes vesting-locked tokens CMC
excludes — kept un-capped and flagged (the SOL/AERO precedent); λ z-scores on relative
rank. XDC includes pending-withdrawal + genesis stake (~1.9% above active caps). S uses
totalStake (incl. deactivated validators' still-locked stake, ~1.2% over active).

## Kickoff-premise corrections (verify-live catches, Entry 71–73)

1. **StakeHub event data order** is `(shares, bnbAmount)` — bnbAmount is the SECOND word
   (kickoff assumed first for Delegated).
2. **StakeHub accounting**: RewardDistributed must be ADDED (rewards compound into pools
   without Delegated events) and MigrateSuccess must NOT be (migration double-emits
   Delegated; adding it → +80% drift). `del − und + rew` matches live to the integer.
3. **BNB window**: pre-2024-07 staking lived on the retired Beacon Chain (BC fusion
   migration ran 2024-04-18→2024-07-14) — kickoff's "Luban ~2023-06" start is not
   reconstructable from BSC logs; documented gap.
4. **Sonic RestakedRewards double-emits Delegated** — the naive 3-event replay drifts
   +0.86% and growing; block-bisection (block 60,010,966: one restake, both events, live
   moved once) proved the fix. Delegated − Undelegated alone is exact.
5. **Etherscan proxy eth_call IGNORES the historical block tag** (verified on Moonbeam:
   round() identical at every tag) — the kickoff's A2d fallback as written is impossible;
   official archive RPCs (which also answer Substrate state queries) are the free
   resolution. Applies everywhere: use Pro endpoints (`balancehistory`,
   `tokensupplyhistory`) or archive RPCs for historical state, never Etherscan eth_call.
6. **CELO balancehistory only covers post-L2-migration blocks** (NOTOK before ~31.06M);
   Forno serves the FULL archive keyless — and the cleaner getter (`getTotalLockedGold`,
   excludes pending withdrawals) rather than the raw balance (+9.2% dirtier).
7. **AVAX kickoff endpoints 404**; the working shape is
   `metrics.avax.network/v2/networks/mainnet/metrics/{validatorWeight,delegatorWeight}`,
   keyless. validatorWeight EXCLUDES delegations (verified vs P-Chain getTotalStake).
8. **The kickoff's AAVE token address was wrong** (`…DDaE8`; the canonical is
   `0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9` per the identity map — caught because
   tokensupply returned 0).

## Task B — AAVE Channel-2 spam-window recovery (Entry 74)

**The real vector (found by bisection, not the kickoff's premise):** address
`0x3d16ee6d…5920` (live AAVE balance 0.0) emits Transfer events with **from == to** on
the genuine AAVE contract carrying fabricated values — max-uint256 (= Entry 66's 1.16e60
reading exactly) down to a fake 10,000,000 in 2024-07 that passes ANY value cap. The
FIFO engines replayed self-transfers as pop-then-append: the pop under-fills (no real
lots), the append credits the full fake value → phantom supply AND phantom aged lots in
the numerator. A denominator-only swap (the kickoff's (b) reading) would have shipped a
numerator still carrying ~9M phantom aged AAVE — the first (cap-only) rebuild showed a
fake HODL jump 17.8%→48.9% at exactly 2025-01 = the 2024-07 spam wave crossing the
6-month age line.

**Fix shipped (Entry 74):** (1) **self-transfer skip** (`from == to` → skip) in all three
engine variants — an accounting identity (a self-transfer never changes a balance; and
replaying one would wrongly refresh a real holder's lot age), not a threshold change;
(2) **`PER_TOKEN_VAL_CAP = {7278: 16_000_000}`** as defense-in-depth (verified live:
totalSupply() == 16,000,000.0 exactly). Global VAL_CAP_MULT / CONTAM_MULT untouched.

**Result:** all 22 nulled months recovered; screened HODL-6m in the recovered window
20.0%–31.3% (inside the 0.5–80% sanity gate, continuous with the pre-window level);
reconstructed on-chain supply 16.0–18.0M across all 67 months (was 1.02e9); pre-spam
months differ from the old rows by ≤ 0.000019 (no-op where no spam existed). AAVE:
67/67 ch2 months, 60 three-channel asset-months. **Panel-wide offline diagnostic
(`_s028_selftransfer_diag.py`): all 210 stored-event tokens unchanged by the fix
(≤1pp, no null flips) — AAVE was uniquely poisoned; no panel-wide recompute needed.**
Old checkpoint preserved (`7278_AAVE.entry66.bak`). NOTE: the kickoff's AAVE address
(`…DDaE8`) was wrong; the identity map's `…DDaE9` is canonical.

## Gap register (Moazzam actions)

| Item | Gate | Action |
|---|---|---|
| DOT/KSM | Subscan free key (signup verification failed at kickoff time) | Retry free signup at pro.subscan.io → put key in `04_code/.api_keys.json` under `"subscan"` → extend `phase1_channel1_pos_coins_bucket2.py` per Entry 44 (era_stat method). ~5-minute action + short build. Do NOT buy Pro. |
| BERA | Consensus-side staking; no public beacon-kit archive API | No action available today; revisit if Berachain ships a public CL API or a validator-history explorer endpoint. |
| NEAR | Historical staking behind Pikespeak (key, pricing undisclosed) | Optional: request Pikespeak pricing; NOT recommended until Cosmos/NEAR PQ side also justifies it. |
| ATOM/INJ/SEI/KAVA | StakingRewards + Numia both 401 key-gated; Mintscan contact-sales | Optional: a StakingRewards key request would cover all Cosmos chains at once if their free tier includes historical `stakedTokens` — unverified without an account; no purchase authorized. |
| BNB pre-2024-07 | Beacon Chain (retired) history | Permanent unless a BC archive dataset surfaces; documented, not blocking (post-fusion window is in λ). |
| HBAR/SUI/ALGO/EOS/ICP/APT | unchanged from Entries 42/45/47 | No new information this session. |

## Remaining 49-coin target list status

Built this session: 7 (BNB, S, GLMR, MOVR, XDC, CELO, AVAX). Previously built: (none of
the 49). Deferred key-gated: DOT/KSM (not on the 49-list: no NVT), NEAR, Cosmos 4.
Structurally gapped (documented): BERA, HBAR, SUI, ALGO, EOS, ICP, APT, TON, and the
PoW/no-staking coins on the list (BTC/LTC/DOGE/BCH/BSV/BTG/ETC/ZEC/DASH/XLM — no staking
mechanism, Channel-1 not applicable; they enter λ only via other channels if ever).

## Quota & sources

Etherscan Pro: ~45k calls today (two full AAVE re-fetches 16,555 + 16,557; BNB/Sonic/
XDC/BERA event fetches ≈ 6k; month-end blocks + balancehistory + cross-checks + spam
forensics ≈ 6k) — well under the 200k/day cap, single day. Keyless sources: official
Moonbeam/Moonriver RPCs (Substrate state), forno.celo.org, metrics.avax.network,
api.avax.network P-Chain, rpc.soniclabs.com (drift diagnosis only). No signups, no
purchases.
