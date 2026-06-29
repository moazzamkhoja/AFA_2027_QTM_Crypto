# Session 022 — Etherscan + non-EVM λ-channel recoverability audit (contract-read + on-chain confirm)
**Date:** 2026-06-29
**Agent:** Claude Code / Opus 4.8
**Type:** feasibility / identification pass (NO λ panel modified)

## User's question (evolved over the session)
1. Can a (payable) Etherscan API recover λ Channels 1/2/3 for the 402 token-Bucket-1 rejects? Read the
   smart contracts, find the staking/voting events, confirm on Etherscan.
2. (After pushback that the first answer read 0 contracts) — actually do it: read every contract, find
   the functions, then find the data on Etherscan.
3. Extend to the full token universe (~1,039 expected).
4. Extend to non-EVM chains — each chain has its own transaction repository; assess recoverability.
5. At 66% context, write status + transition + next-session prompt; if finished, write all docs + commit.

## What was done
Built a resumable pipeline (`04_code/universe_lambda_pipeline.py`):
resolve contract (CMC `detail.platforms[]` + identity map) → **read verified contract** (Etherscan-V2
`getsourcecode`, proxy→impl followed, cached `03_data/raw/etherscan_src/`) → classify λ mechanism from ABI
(Ch1 holder-lock events excl. admin/vesting; Ch3 `DelegateVotesChanged`/`VotingPowerChanged`) → **compute
keccak-256 `topic0` and run `getLogs`** to confirm the event actually fires. ABI presence never accepted as
evidence. Deep-read Solidity for HEX/NMR/AST/CORE/ILV/FLOKI to separate genuine from look-alike.

## Key results
- **EVM universe (token+other = 1,306):** 901 reachable & contract-read. **Ch1 confirmed = 6** (HEX, NMR,
  stkAAVE, XAN amount-bearing; AKRO, VSL bare `Locked()`). **Ch3 active confirmed = 34** (UNI, ENS, SUSHI,
  COMP, GTC, KP3R, BTRST, EIGEN, ONDO, STRK, MNT, BLUR, …). **Ch3 needs-paid = 15** + **Ch1 needs-paid = 1**.
  **Ch3 dormant/negligible = 15.** **Ch2 = all 901.**
- **Measured paid-API gate:** free Etherscan `getsourcecode` works on all chains; **`getLogs`/`tokentx` is
  FREE only on Ethereum/Polygon/Arbitrum/Blast and PAID-only on BSC/Base/Avalanche.** This is the real
  trigger for buying Etherscan Pro (16 BSC/Base/Avax candidates + panel-scale Ch2 throughput).
- **Non-EVM (405 off-Etherscan):** 284 no on-chain identity (dead, unrecoverable); 92 on free-indexer chains
  (Solana 59, Tron 8, Cosmos/Osmosis/Kava 7, +tail) → Ch2 recoverable per indexer, Ch1/Ch3 per-project
  low-yield (native staking/gov = gas coin, out of token-scope); 22 EVM-but-not-Etherscan → same method,
  different explorer. Live-verified free repos: Cosmos LCD, Tron TronGrid, Solana RPC, Cardano Koios.

## Corrections this session forced (value of reading vs. asserting)
- Excluded 4 vesting/compliance look-alike "locks" (MVL/WLD/FST/FBTC).
- Excluded 15 dormant-but-declared governance tokens (CORE/SUPER/ILV/FLOKI/PENDLE/…) — infra in bytecode,
  never used; only `getLogs` reveals it.
- Discovered the chain-specific free/paid `getLogs` boundary (would have shipped false "DORMANT" verdicts on
  BSC/Base otherwise).

## Honesty flags
- Many of the 34 Ch3-active tokens (UNI/ENS/SUSHI/COMP) likely already have a Snapshot Ch3 series (Entry 25)
  → on-chain `DelegateVotesChanged` is a cross-check there; net-new only where no Snapshot turnout.
- AKRO/VSL emit amount-less `Locked()` → need contract-balance reads, not the event alone.
- Non-EVM assessment is at chain-capability altitude (live-API-probed), not a per-program read of all 92.

## Artifacts (all committed)
`03_data/phase1/universe_lambda_channel_map.csv` (1,306), `etherscan_lambda_channel_map.csv` (402),
`non_evm_lambda_recoverability.csv` (405); `03_data/ETHERSCAN_LAMBDA_CHANNEL_EMPIRICAL.md`,
`ETHERSCAN_LAMBDA_CHANNEL_FEASIBILITY.md`, `NON_EVM_LAMBDA_CHANNEL_ASSESSMENT.md`;
`04_code/universe_lambda_pipeline.py` + per-event detail CSVs; raw caches under `03_data/raw/`;
Decisions Log Entry 53; status/transition/next-prompt in `06_documentation/SESSION022_STATUS_AND_NEXT_SESSION.md`.

## Status
Identification map complete (EVM + non-EVM). **Nothing built into λ.** Next: dedupe the 34 Ch3 vs Snapshot,
build the 6 Ch1 series, decide the Etherscan-Pro purchase for the 16 paid-chain candidates. No paid tier /
no purchase this session.
