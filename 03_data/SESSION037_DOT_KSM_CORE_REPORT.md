# Session 037 Report — DOT + KSM + CORE channel-1 builds

**Date:** 2026-07-27
**Prompt:** `04_code/CLAUDE_CODE_SESSION037_DOT_KSM_CORE_PROMPT.md`
**Scripts:** `session037_build_dot_ksm.py`, `session037_build_core.py`, probes `session037_probe_*.py`

## Method pivot (important)

The planned Subscan `era_stat` endpoint is **per-address** (returns
`400 address is a required field`) — Subscan exposes no network-wide bonded
history on this plan. The `/api/scan/daily` chart category `Bonded` exists but
returns all-zero values and the free key has a ~2-month `history_window_exceeded`
limit. The subscan.io website itself was mid-upgrade ("some URLs may be
temporarily inaccessible"), so its chart endpoint could not be inspected.

**Pivot:** read `Staking.ErasTotalStake(activeEra)` directly from public
**archive RPC nodes** at month-end blocks (raw storage keys via twox128/twox64,
no metadata decoding; month-end block found by interpolation search on
`Timestamp.Now`). Both networks migrated staking to their Asset Hub (AHM):
relay staking storage is cleared post-migration, so months where the relay
returns nothing are read from the Asset Hub at the same timestamp.
Endpoints: OnFinality public (relays), Parity `*-asset-hub-rpc.polkadot.io`
(Asset Hubs; archive verified back to ≥2022).

## DOT (cmc 6636) — BUILT, PASS

- 71 months, 2020-08-31 .. 2026-06-30 (`channel1_dot_ksm.csv`)
- Relay through 2025-10, Asset Hub from 2025-11 (AHM boundary smooth: 831.5M → 825.9M, −0.7%)
- 1 DOT = 1e10 Planck; genesis ts 1590507378 (2020-05-26, block 1)
- Latest (2026-06-30): **862,345,368 DOT** staked; ratio 2026-05: 0.519
- Cross-check: fresh head query 881,519,184 DOT → drift **−2.18% PASS**
  (difference = July staking growth). External anchor: Coinbase/StakingRewards
  report ~881.9M DOT staked, 52.0% ratio (2026-07) — matches fresh to 0.05%.
- Ratio range (joined months): 0.478–0.790

## KSM (cmc 5034) — BUILT, PASS

- 76 months, 2020-03-31 .. 2026-06-30 (`channel1_dot_ksm.csv`)
- Relay through 2025-09, Asset Hub from 2025-10; 1 KSM = 1e12 Planck
- **Dropped 2019-11..2020-02** (4 months): pre-runtime-1050 storage exposes only
  `SlotStake` = *minimum* validator backing (11k KSM ≠ network total) — wrong
  metric, and pre-universe-coverage anyway (KSM universe starts 2020-07).
- Latest (2026-06-30): **8,384,479 KSM**; cross-check fresh 8,559,862 → drift
  **−2.05% PASS**. External anchor: Coinbase ~8.5M KSM staked, 46.0% — matches.
- `staking_ratio` suppressed for 2020-07 (CMC circulating 2.99M < staked 5.98M,
  clearly a bad CMC supply point; jumps to 8.47M the next month). Note: CMC
  holds KSM circulating frozen at 8.47M for 2020-2024, so KSM ratios 0.77-0.93
  in 2022-24 carry a stale denominator (universe panel is the supply authority;
  not overridden here).

## CORE (cmc 23254) — BUILT (exact method), PASS

Probe trace:
1. `openapi.coredao.org/api/stats/staking_summary` does not exist (404 past auth;
   query-param `apikey` auth works, `X-API-Key` header rejected).
2. Real staking API found at `staking-api.coredao.org` (no auth):
   `/staking/summary/overall` → current snapshot only (round param ignored) —
   **no historical series exists on any Core API**.
3. `openapi.coredao.org` proxy + `balancehistory` endpoints return empty 200s;
   `rpc.coredao.org` is pruned. **Ankr `rpc.ankr.com/core` and dRPC
   `core.drpc.org` are archive** → block-level build possible.
4. Naive staking-contract balance reads REJECTED: PledgeAgent+CoreAgent balances
   = 335.9M vs official 315.8M staked (+6.4%, includes reward/queue buffer).
5. **Exact definition validated to the digit at head**: official
   `stakedCoreAmount` == Σ over ACTIVE validators (`ValidatorSet.getValidatorOps()`)
   of `CoreAgent.candidateMap(op).amount` (315,775,339 CORE matched exactly,
   per-validator numbers matched exactly).

Build (`session037_build_core.py`): 42 months, 2023-01-31 .. 2026-06-30.
- Active set: `getValidatorOps()`, legacy fallback = walk of public array
  `currentValidatorSet(i)` (getValidatorOps reverts pre-hardfork).
- Stake: CoreAgent.candidateMap.amount from 2024-11 (post-StakeHub upgrade);
  legacy `PledgeAgent.agentsMap(op)` word0 through 2024-10 (word0/word2 differ
  <2% throughout; upgrade boundary continuous — the Oct→Nov 2024 dip mirrors the
  in-legacy Sep→Oct decline).
- Latest (2026-06-30): **307,727,006 CORE**; fresh API 315,775,339 → drift
  **−2.55% PASS**. Ratio range 0.114–0.81 (early CMC circulating tiny).
- CORE-only: BTC and hashpower dual-staking legs excluded.
- Output: `channel1_core.csv`, 42 rows (40 with ratio).

## Post-assemble

| metric | pre-037 | post-037 |
|---|---|---|
| λ asset-months / assets | 13,272 / 459 | **13,449 / 462** |
| regression-ready | 177 (coins 21, tokens/other 156) | **178 (coins 22, tokens/other 156)** |
| coverage (complete/partial/not_started) | 188/313/1,438 | **189/314/1,436** |
| channel2_holding | 423 / 13,661 | unchanged |

- **CORE enters regression-ready** (had 27 NVT_GL months; same-month overlap confirmed).
- **DOT/KSM do NOT** — the session-prompt premise "have NVT_GL" was wrong:
  `nvt_gl_panel.csv` has their rows but `pq_usd` is all null (no PQ source).
  They move not_started → **partial**; their only remaining gap is `pq_nvtgl`
  (ch1 gate now closed).
- Bookkeeping: narrative "coins 21" vs file pos-coin count 20 pre-session =
  **TRX mislabeled `pow_only`** (DPoS, has 78 λ months) — flagged in Entry 88.

## Next steps

- Session 038: SHIB (5994) ch2 (~128k gl est — treat as ~5x over-estimate), λ-only
- DOT/KSM PQ source hunt (would add 2 regression-ready coins)
- Cosmos key → CRO/INJ/SEI/KAVA ch1; Blockchair support email re XTZ/MATIC
- WARP (1166) identity review; TRX coin_staking_type fix; bibliography check
