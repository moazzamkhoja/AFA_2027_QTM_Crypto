# Session 037 — DOT + KSM + CORE channel-1 (staking) builds

**Date:** 2026-07-27
**Model/interface:** Claude Fable 5 via Claude Code (desktop app, Windows)
**Kickoff:** user pointed to `CLAUDE_CODE_SESSION037_DOT_KSM_CORE_PROMPT.md` ("proceed from there")
**Mode:** autonomous after launch; standing end-of-session commit+push authorization
**Commits:** 7ca6b14 (+ record-keeping hash-fix commit after)

---

## Initial user prompt (verbatim)

> read CLAUDE_CODE_SESSION037_DOT_KSM_CORE_PROMPT.md in C:\AFA_2027_QTM_Crypto\04_code and proceed from there

No mid-session check-ins or decisions requested.

## Structured event log

1. **Subscan plan failed on first probe:** `era_stat` is per-address (400
   "address is a required field"); `/api/scan/daily` `Bonded` category returns
   all zeros with a ~2-month free-plan history window; subscan.io website
   mid-upgrade (charts unreachable). Entry-87 build plan unusable as written.
2. **Pivot designed and validated:** raw-storage-key reads of
   `Staking.ErasTotalStake(ActiveEra)` at month-end blocks (interpolation search
   on `Timestamp.Now`) from public archive RPCs, via a ~200-line websocket
   client (no metadata decode). Discovered both chains' staking had migrated to
   Asset Hub (relay `ActiveEra` = null at head) → AH fallback per month;
   parity AH endpoints verified archive to ≥2022 (block-1 state absent →
   binary-search state anchor added).
3. **DOT built:** 71 months 2020-08..2026-06; relay≤2025-10, AH from 2025-11
   (boundary −0.7%); latest 862.3M; drift vs fresh −2.18% PASS; external anchor
   (Coinbase/StakingRewards ~881.9M, 52.0%) matches fresh to 0.05%.
4. **KSM built:** 76 months 2020-03..2026-06; dropped 2019-11..2020-02 — old
   runtimes only expose `SlotStake` = MIN validator backing, not a total (wrong
   metric); latest 8.38M; drift −2.05% PASS; anchor (~8.5M, 46%) matches.
   2020-07 ratio suppressed (CMC circulating 2.99M < staked — bad point).
5. **CORE probes:** prompt's `staking_summary` path doesn't exist; real API at
   `staking-api.coredao.org` is current-only; CoreScan proxy/balancehistory
   endpoints broken (empty 200s); rpc.coredao.org pruned; **Ankr + dRPC are
   archive**. Contract-balance approach measured and REJECTED (+6.4% vs
   official). Exact definition found and validated to the digit:
   stakedCoreAmount == Σ active validators' `CoreAgent.candidateMap.amount`.
6. **CORE built exact:** 42 months 2023-01..2026-06 via eth_call at month-end
   blocks; active set via `getValidatorOps()` (legacy: `currentValidatorSet(i)`
   walk); legacy stake via `PledgeAgent.agentsMap` word0 ≤2024-10; drift −2.55%
   PASS.
7. **Assemble + coverage:** λ 13,272→13,449 asset-months / 459→462 assets;
   regression-ready 177→178 (coins 21→22: CORE); coverage 189/314/1,436.
   **Prompt premise wrong for DOT/KSM:** they have NO NVT_GL (pq_usd all null)
   → partial (pq_nvtgl their only gap), not regression-ready.
   TRX `pow_only` mislabel identified (explains narrative/file coin-count ±1).
8. **Entry 88**, `SESSION037_DOT_KSM_CORE_REPORT.md`, committed + pushed.

## Data-access notes

- Subscan free API: no network-wide staking history at all (per-address
  era_stat; daily charts plan-gated to ~2 months). A paid plan was NOT needed —
  archive RPC state reads are free and authoritative.
- OnFinality public relay endpoints are full archive (block 1 state readable);
  parity Asset Hub endpoints archive from ~2022 snapshot; Dwellir/IBP/dotters
  DNS-blocked on this network.
- Ankr `rpc.ankr.com/core` and `core.drpc.org` are keyless archive for Core;
  everything CoreScan/official-RPC side is current-only, broken, or pruned.
- Windows Update pause was skipped (short session, no multi-hour unattended run);
  sleep already Never.
