# Session 028 — Coin Staking (ch1) Expansion + AAVE ch2 Fix

**Date:** 2026-07-04 · **Model:** Claude Fable 5 (Claude Code desktop) · **Kickoff:**
`04_code/CLAUDE_CODE_SESSION028_COIN_STAKING_AND_AAVE_FIX_PROMPT.md` · **Log entries:** 71–75

## What was asked

Two tasks: (A) expand coin Channel-1 staking for the 49 NVT-ready/λ-absent coins —
first the EVM chains on the Etherscan Pro key (BNB/GLMR/MOVR/S/BERA/XDC), then CELO
balance-history, then AVAX/NEAR/Cosmos alternative-source probes; DOT/KSM deferred
(Subscan signup blocked). (B) recover AAVE's 22 spam-nulled ch2 months.

## How it ran (decisions and turning points)

1. **Chain coverage check first**: all 9 target chainids live on Etherscan V2 with the
   Pro key. pycryptodome for keccak topics; new `_s028_evm.py` helper module.
2. **BNB**: fetched StakeHub ABI → corrected the kickoff's event-data order
   (`shares, bnbAmount`). Full event fetch (106k logs, 6 event types). Reconciliation
   table: `del−und+rew` = live Σ totalPooledBNB over 53 StakeCredit contracts **to the
   integer** (25,717,017 BNB); adding MigrateSuccess → +80% (migration double-emits
   Delegated). Series starts 2024-07 (BC-fusion completed 2024-07-14; earlier stake
   lived on the retired Beacon Chain — documented gap).
3. **Moonbeam/Moonriver**: precompile emits no logs, no aggregate getter; **discovered
   Etherscan proxy eth_call ignores historical tags** (round() constant at every tag) —
   kickoff's fallback impossible as written. Resolution: official RPCs are full archives
   AND answer Substrate state queries → read `ParachainStaking.Total` (twox128 storage
   key, xxhash) at each month-end block. Decode validated via the eth_call
   Σ getCandidateTotalCounted superset relation (1.054 / 1.015).
4. **Sonic**: full SFC event fetch (246k logs). Naive replay drifted +0.86% and growing;
   **block-bisection to a single block (60,010,966) proved restakeRewards emits BOTH
   Delegated and RestakedRewards** for the same amount. `del−und` alone = archive
   totalStake() at ±0.0000% at six blocks across the whole history.
5. **XDC**: XDCValidator holds native XDC. Three-way tie-out: Σ getCandidateCap (2.650B)
   ≤ event replay (2.668B; +18M resigned-pending) ≤ contract balance (2.701B; +32.625M
   CONSTANT genesis/eventless offset, stable at every probed block from 40M). Series =
   Pro `balancehistory` at month-ends (72 mo), flagged for the pending/genesis components.
6. **BERA**: deposits-only replay = 382.6M BERA > circulating — withdrawals are
   consensus-side, invisible in EL logs; no free CL archive API (routescan/berascan/hub
   probed). Documented gap.
7. **CELO**: Pro `balancehistory` works on 42220 but ONLY post-L2-migration (block
   ≥ ~31.06M). **forno.celo.org serves the FULL archive keyless** — historical
   `getTotalLockedGold()` (the exact number Entry 46 wanted) at every month-end back to
   2020-07. 70 months, closes the Entry-46 gap for $0.
8. **AVAX**: kickoff endpoints 404; the working shape is
   `metrics.avax.network/v2/networks/mainnet/metrics/{metric}` — **keyless**, daily to
   genesis. Semantics anchored to the chain: P-Chain platform.getTotalStake ≈
   validatorWeight+delegatorWeight (additive), not validatorWeight alone. 67 months.
   Resolves the Entry-42/47 AvaCloud ambiguity: free, no account at all.
9. **NEAR/Cosmos**: NearBlocks charts = 2,174 days of history but no staking field
   (stats/validators current-only); StakingRewards GraphQL 401; Numia 401. Gaps stand.
10. **AAVE ch2 — two-stage detective work**: kickoff's (b) denominator-swap reading
    rejected on mechanics (phantom lots also poison the NUMERATOR — they age at
    EOA-class addresses). First rebuild with the Entry-70 per-token totalSupply cap
    (16,000,000, verified live; the kickoff's token address `…DDaE8` was wrong — the
    identity map's `…DDaE9` is canonical) recovered the months but left a fake HODL
    jump at 2025-01 and supply still climbing to 62M. Forensics on the sharpest jump
    month (2024-07) found the REAL vector: **fake-value SELF-transfers** from a
    0.0-balance address (incl. max-uint256 = Entry 66's 1.16e60, and a fake 10M that
    passes any cap) — the FIFO pop-then-append mints the shortfall as phantom supply.
    Fix: **self-transfer skip** (accounting identity) in all three engine variants +
    the cap as defense-in-depth; second full rebuild → supply 16.0–18.0M all months,
    recovered HODL 20.0–31.3%, pre-spam months ≤1.9e-5 from old. **Offline diagnostic
    over all 210 stored-event checkpoints: zero other tokens affected.** Old checkpoint
    kept as `7278_AAVE.entry66.bak`.

## Outcome

- New builder `phase1_channel1_pos_coins_evm.py` → 358 asset-months / 7 coins
  (BNB 23, S 17, GLMR 52, MOVR 57, XDC 72, CELO 70, AVAX 67), all Entry-26-passing.
- λ: 7,051 → 7,409 asset-months / 282 → 289 assets (coins 9 → 16).
- Regression-ready coins (λ∩NVT_GL): 5 → 12; 505 overlapping coin asset-months.
- AAVE ch2: all 22 nulled months recovered; 67/67 ch2 months; AAVE 3-channel through
  2026-05; panel 3-channel asset-months 332 → 354 (+22 = exactly the recovered window);
  2+ channel share 23.2% (compositional dip from 24.4%: +358 single-channel coin months).
- Entries 71–75; report `03_data/SESSION028_COIN_STAKING_REPORT.md`; gap register with
  exact Moazzam actions (Subscan free key being the actionable one).

## Session hygiene

Single Etherscan Pro quota day, ~45k calls total incl. two full AAVE re-fetches
(16,555 + 16,557) — well under 200k. No signups, no purchases. Keyless sources used: Moonbeam/Moonriver official RPCs,
forno.celo.org, metrics.avax.network, api.avax.network (P-Chain), rpc.soniclabs.com.
Commit+push at session end.
