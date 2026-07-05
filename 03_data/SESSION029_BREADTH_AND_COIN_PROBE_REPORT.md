# SESSION 029 — ch2 breadth build + TVL slug verdicts + PoS coin probes

**Date:** 2026-07-04 (UTC quota day shared with the tail of session 028's day — budget tracked below)
**Inputs:** Etherscan Pro V2 (existing key), keyless sources only. No signups, no purchases.
**Log entries:** 76 (Task A), 77 (Task B), 78 (Task C), 79 (close-out).

---

## TASK A — Channel-2 breadth build: 47 non-λ tokens with TVL (Entry 76)

**40 of 47 BUILT (36 on day 1 + 4 on day 2); 39 entered λ as NEW assets (+1,849
asset-months, all single-channel ch2); 38 of them are regression-ready immediately
(λ∩TVL same-month). 7 pending on the resume list; 5 skipped non-EVM by construction.**

### A0 multi-chain adaptation
- `phase1_channel2_stream.py` was already per-token multi-chain (every API call passes the
  token's chainid); the only constraint was the `CHAIN_ID` chain-name lookup used by
  `load_worklist`. Extended with BSC (56) and Base (8453). No other engine change; guard
  thresholds untouched (VAL_CAP_MULT = CONTAM_MULT = 100).
- getLogs coverage probed live (one recent-window call each): **BSC 56 ✓** (head 108.06M),
  **Polygon 137 ✓** (head 89.65M), **Arbitrum 42161 ✓** (head 480.38M), **Base 8453 ✓**
  (head 48.20M). All four return proper log lists.
- All 47 targets have addresses + `etherscan_reachable=yes` in `universe_lambda_channel_map.csv`
  (chain column carries the per-token chain); universe panel has observed months for all 47.
- Skipped by construction (non-EVM): SXP, RUNE, OSMO, SUN, CASINO. HEX not attempted
  (permanent deferral, Entry 66).

### Build results

**Day 1 (36 tokens, 186,942 getLogs, cap-stopped cleanly before EPS):** all 35 mainnet
targets + MDX. **Day 2 (4 tokens, 281,671 getLogs, cap-stopped before SFUND):** EPS,
BAKE, BTCST, MBOX. `channel2_holding.csv` 260 → 300 tokens / 9,794 rows.

Hidden giants (the ORBS lesson at record scale — holder_count does not predict transfer
volume): **MDX 17.67M transfers / 135.8k getLogs** (largest ch2 build in the project) and
**MBOX 21.2M transfers / 171.9k getLogs**, plus BAKE 9.0M, EPS 2.9M, FLOKI 1.67M,
ATH 1.34M, AMP 1.17M.

- **WARP (cmc 1166) built but EMPTY** — its observed universe window (2016→2018-02)
  entirely predates the mapped contract's first Transfer (every month "pre-history"):
  an identity-map mismatch between the old dead cmc-1166 listing and the later 0x83e6f1E4…
  contract. Flagged for identity review; NOT forced into λ.
- **B2 integrity scan (all 40): CLEAN** — 0 months above the 100× contamination threshold;
  worst AURORA 49.5× (legit Entry-49 heavy-lock band). Guard thresholds untouched.
- **B4 sanity:** screened HODL-6m medians economically bounded; BMX 96.2% / MVL 84.5% are
  the documented illiquid-inactivity band; EPIC 0% is a XAN-class age artifact.
- **QUOTA ANOMALY (logged honestly):** MBOX blew through the in-process cap mid-flight
  (the cap only checks at token boundaries — the session-027 landmine at 172k/token
  scale), and the API returned **no daily-limit rejection at ~292k calls** on the
  2026-07-05 UTC day: the assumed 200k/day hard cap did not bind (plan evidently
  credit-based or higher). We stopped anyway per the documented budget rule.
- **Pending resume list (zero-loss from checkpoints, ~30–45k est calls, one clean quota
  day):** SFUND (8972), MYX (36410), ADF (24796, Polygon), AVNT (38299) / KAITO (35763) /
  VVV (35509) (Base), RAIN (38341, Arbitrum — largest, build last).
- Skipped non-EVM by construction: SXP, RUNE, OSMO, SUN, CASINO. HEX not attempted.

---

## TASK B — Orphaned dl_slug TVL verdicts (Entry 77)

**All six REJECTED — DeFiLlama tracks NO TVL data for any of them.** Each
`/protocol/{slug}` answers 200 with protocol metadata but an EMPTY `tvl` array, EMPTY
`chainTvls` sub-series on every chain, and empty `currentChainTvls`:

| cmc_id | symbol | dl_slug | verdict | reason |
|--------|--------|---------|---------|--------|
| 19269 | COW | cowswap | REJECT | DL categorizes CoWSwap as "DEX Aggregator" with `tvl: null` — batch-auction settlement holds no persistent liquidity. The only CoW-named TVL series on DL (`balancer-cow-amm`, $391k) belongs to parent **Balancer** (symbol BAL) — not the COW token's protocol claim. |
| 1896 | ZRX | 0x-aggregator | REJECT | aggregator; `chainTvls[Ethereum]` empty |
| 9421 | FORTH | forth-dao | REJECT | governance only; series empty |
| 13855 | ENS | ens | REJECT | naming service; series empty |
| 10052 | GTC | gitcoin | REJECT | grants platform; series empty |
| 23054 | CHEEL | cheelee | REJECT | `chainTvls[BSC]` empty — DL lists the protocol but records no TVL |

No tvl_panel rebuild needed; no identity-map change. This *confirms* Entry 68's
"genuinely-no-TVL" classification for all six — the kickoff's hope that COW "should have
genuine TVL" is answered: CoW Protocol's design (intent settlement) has no TVL to track,
and DL agrees. **Do not re-probe these six.**

---

## TASK C — PoS coin probes and builds (Entry 78)

### BUILT (8 series / 9 λ assets — every one a state read of the chain's own figure)

| asset | months w/ ratio | staking ratio (min→max, latest) | latest staked |
|-------|-----------------|--------------------------------|---------------|
| MATIC (3890) | 50 (2020-06→2024-08) | 10.7%→41.3%, 34.7% at handoff | 3.47B |
| POL (28321) | 21 (2024-09→2026-05) | 31.5%→47.1%, 33.7% | 3.59B |
| RON (14101) | 39 (2023-03→2026-05) | 9.5%→66.3%, 17.4% | 134.7M (genuine 2026 unstaking wave, live-confirmed 105.8M in July) |
| KLAY (4256) | 43 (2021-03→2024-09, full observed window) | 32.1%→61.9%, 61.9% | 2.36B |
| FLR (7950) | 32 (2023-10→2026-05) | 6.7%→17.1%, 17.1% | 14.79B |
| EGLD (6892) | 68 (2020-09→2026-05, full observed window) | 39.6%→67.2%, 48.3% | 14.50M |
| STRK (22691) | 19 (2024-11→2026-05) | 3.6%→22.7%, 21.8% | 1.39B |
| XRD (11948) | 32 (2023-10→2026-05) | 32.2%→46.1%, 34.2% | 4.60B |
| PEAQ (14588) | 18 (2024-12→2026-05) | 74.3%→259.1% (early >1 = genesis/vesting stake, SOL/AERO flag), 74.3% | 1.62B |

Builders: `pol_series()` added to `phase1_channel1_pos_coins_evm.py` (now 429 asset-months /
9 assets); NEW `phase1_channel1_pos_coins_native.py` → `channel1_pos_coins_native.csv`
(251 asset-months / 7 assets), picked up by the assembler's channel1_*.csv glob.
Task-C λ delta: **7,409 → 7,731 asset-months (+322) / 289 → 298 assets (+9; coins 16 → 25)**.
Coin regression-ready (λ∩NVT_GL): **12 → 20 assets / 505 → 645 coin-months** (new: EGLD,
FLR, KLAY, PEAQ, POL, RON, STRK, XRD; MATIC has no NVT_GL so it adds λ only).

Session-028 fix applied in passing: the XDC cross-check compared the STATIC event-cache
replay to the LIVE balance — a net −10M outflow on 2026-07-04 moved the apparent offset
32.6M→22.6M within hours of session 028 and tripped the gate. Both sides are now pinned at
the cache's scan-head block (balancehistory at `scan_to`), making the +32,625,000
genesis-offset identity time-invariant. Offset at scan_to: 32,625,000 exactly — gate green.

Summary of sources (all keyless, all response-body verified live this session):

| coin | cmc_id | source | metric | window |
|------|--------|--------|--------|--------|
| POL + MATIC | 28321 / 3890 | eth.drpc.org (keyless mainnet ARCHIVE eth_call — publicnode/llamarpc/flashbots all refuse archive) | StakeManager `currentValidatorSetTotalStake()` (NOT `totalStaked()` = self-stake only, 11.7M vs 3.58B) | 2020-06→2026-05, MATIC rows ≤2024-08, POL rows ≥2024-09 (listing handoff, no overlap) |
| RON | 14101 | ronin.drpc.org (keyless archive; official RPC pruned) | sum(Staking.getManyStakingTotals(ValidatorSet.getValidatorCandidates)) — contract identities verified vs axieinfinity/ronin-dpos-contracts deployments | 2023-04→2026-05 |
| KAIA/KLAY | 4256 | archive-en.node.kaia.io (official archive) | `klay_getStakingInfo` councilStakingAmounts (+CL when present) — the node's own consensus snapshot | 2021-03→2024-09 (KLAY observed window) |
| FLR | 7950 | flare-api.flare.network (official archive) | `PChainStakeMirror.totalSupply()` (address from FlareContractRegistry) | ~2023-07→2026-05 |
| EGLD | 6892 | tools.multiversx.com/growth-api (official) | daily totalStaked, month-end sample | 2020-08→2026-05 |
| STRK | 22691 | rpc.starknet.lava.build (keyless archive starknet_call) | staking contract `get_total_stake()` (docs.starknet.io address; kickoff's addr was the STRK token; 0x00ca1705… is the minting curve) | 2024-11→2026-05 |
| XRD | 11948 | mainnet.radixdlt.com Babylon Gateway (official; HISTORICAL `at_ledger_state` timestamps) | sum(stake_vault.balance) over all validators | 2023-10→2026-05 (Olympia era = gap) |
| PEAQ | 14588 | peaq.api.onfinality.io/public (keyless archive) | pallet `ParachainStaking.TotalCollatorStake` (KILT-fork storage name; Moonbeam's `.Total` is null on peaq) | 2024-11→2026-05 |

### Cross-checks (Entry-26)

- **POL:** drpc vs Etherscan proxy eth_call at head **+0.00000%** (independent providers);
  StakeManager token balance / stake = 1.028–1.075 every month (constant-shape superset =
  unclaimed rewards); getter semantics anchored live (3.58B ≈ official dashboard).
- **RON:** contract native balance / candidate-stake sum = 1.006–1.18 (superset = pending
  undelegations incl. revoked candidates; the METRIC is the per-candidate sum, not the
  balance — the +16% head gap is exactly why the balance route was rejected).
- **KAIA:** councilStakingAmounts == CnStaking contract native balances (spot-checked 8/43,
  max deviation **0.0000%**); the getter IS what the node uses for GC weighting.
- **FLR:** C-chain mirror vs P-chain `platform.getTotalStake` live: **−0.18%** (mirroring
  granularity).
- **EGLD:** chart head vs live `/economics` staked: **−0.11%** (daily snapshot timing).
- **STRK:** state read of the official staking contract (docs.starknet.io address);
  get_total_stake vs get_current_total_staking_power internally consistent at head.
- **XRD:** official gateway state read; single-page validator list guarded (fetch raises if
  the response ever paginates).
- **PEAQ:** chain's own pallet aggregate (GLMR/MOVR state-read standard); archive verified
  at block 1.0M / mid / head.

### GAPS / GATES (documented, per coin — "flag, don't guess")

| coin | verdict | gate / Moazzam action |
|------|---------|----------------------|
| CRO (3635) | GAP (Cosmos gate) | Staking lives on the Crypto.org Cosmos chain, not Cronos EVM (chainid 25 live but no staking surface). LCD `rest.mainnet.crypto.org/cosmos/staking/v1beta1/pool` answers LIVE (bonded 14.3B) but historical-height queries fail (`x-cosmos-block-height` → 500, state pruned). Same gate as ATOM/INJ/SEI/KAVA — solved by the same Cosmos key sourcing already on Moazzam's list. |
| CHZ (4066) | GATE-OPEN (one manual anchor needed) | rpc.chiliz.com IS its own keyless archive; system contract 0x…1000 (Parlia-fork validator set, 24KB unverified bytecode) holds 2.38B CHZ (243M @5M → 1.20B @15M → 2.38B head — plausible total-staked trajectory). No aggregate getter; event topics unmatched vs known staking signatures. **Action: read the total-staked figure off staking.chiliz.com (or Chiliz support docs) at a known time and compare to the 0x…1000 balance; if it ties, the build is a ~30-line balance fetch** (XDC pattern, archive confirmed). |
| LSK (1214) | GAP | Lisk migrated to an OP-stack L2 (chainid 1135, live RPC, Blockscout). No staking/locking contract locatable: docs.lisk.com staking pages 404/redirect, Blockscout search returns only third-party "staking"-named contracts. If Lisk ships governance locking, revisit. |
| TON (11419) | GAP | tonapi.io answers live (Elector balance 1.29B TON) but the Elector balance is a SUPERSET (stakes + credits + bonuses), and no keyless HISTORICAL account-state endpoint exists (toncenter v3 has no statistics route; tonapi has no history). |
| FLOW (4558) | GAP | Access API live but historical Cadence execution is spork-bound; flowdiver 429s/findlabs DNS-dead. No free staking history. |
| DFI (5804) | GAP | ocean.defichain.com/stats is current-only (timestamp param ignored); chain effectively sunset. Live: 16,656 masternodes. |
| DASH (131) | GAP | Masternode collateral (1000 DASH × count) needs a COUNT HISTORY: stats.masternode.me dead (DNS), chainz masternodecount query unsupported ("?"), insight has no MN route, dashcentral.org/api/v1/public is current-only (2,062 MNs). |
| WAN (2606) | GAP | wanscan.org serves HTML only; no staking API found. |
| HYPE (32196) | GAP (live-only) | api.hyperliquid.xyz `{"type":"validatorSummaries"}` answers with per-validator `stake` (33 validators, ~438M HYPE incl. foundation) but no history endpoint. |
| CORE (23254) | GATE-OPEN (key) | openapi.coredao.org exists but every route returns 401 "apikey is illegal". **Action: check whether scan.coredao.org offers a free self-serve API key; if yes, drop it in `.api_keys.json` under `"coredao"` and probe `/api/stats/staking_summary` for history.** No signup attempted (session rule). |

### Deferred per kickoff (not probed): DOT/KSM, NEAR, ATOM/INJ/SEI/KAVA, BERA, HBAR/SUI/ALGO/EOS/ICP/APT.

---

## TASK D — close-out (Entry 79)

| metric | pre-029 | post-029 |
|--------|---------|----------|
| λ asset-months | 7,409 | **9,580** (+2,171) |
| λ assets | 289 | **337** (+48 = 39 tokens + 9 coins) |
| λ coins | 16 | **25** |
| n_channels 1 / 2 / 3 | 5,689 / 1,366 / 354 | 7,860 / 1,366 / 354 |
| 2+ channel share | 23.2% | 18.0% (compositional — all new months single-channel) |
| regression-ready coins (λ∩NVT_GL) | 12 / 505 mo | **20 / 645 mo** |
| regression-ready tokens+other (λ∩TVL) | 80 / ~2,800 mo | **118 / 4,194 mo** |
| **TOTAL regression-ready assets** | **92** (kickoff said 90 — stale coverage file) | **138** |
| coverage CSV | stale (pre-027) | regenerated: 149 complete / 236 partial / 1,554 not_started |

`universe_coverage_status.csv` is now produced by the reusable
`04_code/build_coverage_status.py` (same-month-overlap "complete" semantics;
coin_staking_type carried forward as static metadata). Re-run it after any assemble.

### Gap register (all open items with the exact gate + action)

1. **Task-A resume list** — 7 tokens (SFUND/MYX/ADF/AVNT/KAITO/VVV/RAIN): run
   `WORKLIST=8972,36410,24796,38299,35763,35509,38341 phase1_channel2_stream.py` on a
   fresh quota day (~30–45k calls). Checkpoints make this zero-loss.
2. **DOT/KSM** — unchanged Entry-44/72 gate: free Subscan signup at pro.subscan.io →
   `.api_keys.json` under `"subscan"` → Entry-44 era_stat build.
3. **CHZ** — read total-staked off staking.chiliz.com manually, compare to the 0x…1000
   balance (2.38B CHZ now); if it ties, ~30-line archive balance fetch ships it.
4. **CORE** — check scan.coredao.org for a free self-serve API key → `.api_keys.json`
   under `"coredao"` → probe openapi.coredao.org `/api/stats/staking_summary`.
5. **WARP (cmc 1166)** — identity-map mismatch (observed window predates the mapped
   contract); review the correct contract/listing pairing before any rebuild.
6. **MATIC NVT_GL** — MATIC now has λ but no PQ series; a bitinfocharts/native probe
   would make it the 21st regression-ready coin.
7. **NEAR / ATOM-INJ-SEI-KAVA / BERA / TON / FLOW / DFI / DASH / WAN / HYPE / LSK /
   CRO** — gates/gaps re-verified this session (Entry 78 table); no free path today.
