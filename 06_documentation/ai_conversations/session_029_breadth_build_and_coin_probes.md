# Session 029 — ch2 breadth build (47 TVL-ready tokens) + TVL slug verdicts + PoS coin probes

**Date:** 2026-07-04
**Agent:** Claude Code (Fable 5)
**Kickoff:** `04_code/CLAUDE_CODE_SESSION029_BREADTH_BUILD_AND_COIN_PROBES_PROMPT.md`
**Log entries:** 76–79. **Report:** `03_data/SESSION029_BREADTH_AND_COIN_PROBE_REPORT.md`

## What was done (chronological)

1. **Task A0 (multi-chain adaptation):** read `phase1_channel2_stream.py` fully; found the
   engine already passes per-token `chainid` through every API call (getLogs, decimals,
   month-blocks, contract screen) — the only mainnet-era constraint was the `CHAIN_ID`
   chain-name lookup in `load_worklist`. Extended it with BSC (56) and Base (8453); no other
   engine change; guard thresholds untouched. Probed getLogs live on 56/137/42161/8453 — all
   answer. All 47 targets present in the channel map with addresses + `etherscan_reachable=yes`
   and observed universe months; zero pre-existing checkpoints.
2. **Task A build:** launched the full 47-token worklist (mainnet smallest-first → BSC →
   Polygon → Base → RAIN/Arbitrum last) at WORKERS=8, RATE=8/s, DAILY_CAP=180000 (20k headroom
   rule). Ran through the session in the background; results in Entry 76.
3. **Task B (30 min):** probed all six orphaned dl_slugs — all six REJECT: DL returns 200
   with protocol metadata but EMPTY tvl/chainTvls/currentChainTvls on every chain. COW
   double-checked against the full /protocols list + parentProtocols (only CoW-named TVL
   series is balancer-cow-amm under parent Balancer — not COW's claim). No panel rebuild.
4. **Task C1 (EVM coins):** Etherscan V2 chainlist fetched — NONE of Flare/Ronin/Kaia/
   Cronos/Chiliz/Lisk are covered (64-chain list). POL probed on Ethereum mainnet:
   `totalStaked()` is validator SELF-stake only (11.7M); the correct aggregate is
   `currentValidatorSetTotalStake()` (3.58B live). Etherscan proxy ignores historical tags
   (Entry-71), so free archive RPCs were probed: publicnode requires a personal token,
   llamarpc/meowrpc/flashbots refuse — **eth.drpc.org serves full mainnet archive eth_call
   keyless**. POL fetched 2020-06→2026-05 (`_s029_pol_fetch.py`).
   RON: official RPC pruned; **ronin.drpc.org is a keyless archive**; contract identities
   verified against axieinfinity/ronin-dpos-contracts; balance route REJECTED (+15.6% over
   candidate-stake sum) in favor of the getter route. KAIA: public-en reverts historically
   but **archive-en.node.kaia.io (official) answers `klay_getStakingInfo` at any block**.
   FLR: P-chain live getter found, then **PChainStakeMirror.totalSupply() on the official
   C-chain archive RPC** (registry-resolved) ties to the P-chain at −0.18%. CRO: staking is
   Cosmos-side (crypto.org LCD live-only) → ATOM-class gap. CHZ: 0x…1000 balance series
   archive-readable but semantics unanchorable keylessly → gate-open w/ manual action.
   LSK: no staking contract locatable → gap.
5. **Task C2 (native):** EGLD **BUILT** (tools.multiversx.com growth-api daily series to
   2020-07, −0.11% vs live economics). STRK **BUILT** (lava archive starknet_call on the
   real staking contract from docs.starknet.io — the kickoff's two addresses were the STRK
   token and the minting curve, both ABI-verified wrong). XRD **BUILT** (Babylon Gateway
   historical `at_ledger_state` — 245–287 validators/page, single page guarded). PEAQ
   **BUILT** (KILT-fork pallet storage `TotalCollatorStake`; Moonbeam's `.Total` is null).
   TON/FLOW/DFI/DASH/WAN/HYPE = documented gaps; CORE = key-gated (Moazzam action logged).
6. **Builders:** `pol_series()` added to `phase1_channel1_pos_coins_evm.py` (MATIC ≤2024-08 /
   POL ≥2024-09 listing handoff, no overlap month); new `phase1_channel1_pos_coins_native.py`
   emits RON/KLAY/FLR/EGLD/STRK/XRD/PEAQ (`channel1_pos_coins_native.csv`, picked up by the
   assembler glob).
7. **Task D:** new reusable `build_coverage_status.py` (replaces the pre-027 inline
   generation; coin_staking_type carried forward as static metadata). Final assemble +
   coverage rebuild + report + log entries + commit/push at session close.

## Session outcome

**λ 7,409 → 9,580 asset-months / 289 → 337 assets (coins 16 → 25); regression-ready
92 → 138 assets (coins 12 → 20 via λ∩NVT_GL, tokens/other 80 → 118 via λ∩TVL).**
Task A: 40/47 ch2 targets built across two quota days (MDX 17.7M and MBOX 21.2M
transfers — the two largest ch2 builds ever), 39 entered λ, B2 clean, 7-token resume
list pending. Task B: all six slugs rejected (no TVL on DL). Task C: 8 coin series /
9 λ assets built, all state reads of chain-own aggregates with Entry-26 cross-checks;
10 gaps/gates documented. Coverage CSV regenerated via new reusable
build_coverage_status.py: 149 complete / 236 partial / 1,554 not_started.
Quota anomaly logged in Entry 76 (no daily-limit rejection at ~292k calls/day).

## Landmines hit / recorded

- Polygon StakeManager `totalStaked()` ≠ total staked (self-stake only; use
  `currentValidatorSetTotalStake()`).
- eth.drpc.org = keyless mainnet (and Ronin) archive; publicnode gates archive behind a
  personal token; blastapi retired its public Starknet endpoint.
- Kaia: only `archive-en.node.kaia.io` serves historical state; the regular public
  endpoint returns "execution reverted" for historical calls (NOT pruned-trie errors).
- peaq's staking pallet is the KILT fork: storage item `TotalCollatorStake`
  (struct{collators, delegators}), not Moonbeam's `Total`.
- Radix Babylon Gateway accepts `at_ledger_state={"timestamp":…}` on /state/validators/list
  — free historical validator stakes; Olympia era unreachable (old gateway retired).
- Starknet staking contract = 0x00ca1702e64c… (docs.starknet.io chain-info); 0x00ca1705e74…
  is the MINTING CURVE and 0x04718f5a… the STRK token.
- Ronin staking contract balance ≠ staked (pending undelegations of revoked candidates,
  +16% at head): use getManyStakingTotals over getValidatorCandidates.
- DeFiLlama /protocol/{slug} can 200 with entirely empty tvl+chainTvls (protocol listed,
  TVL never tracked) — an empty-series REJECT is not an API failure.
