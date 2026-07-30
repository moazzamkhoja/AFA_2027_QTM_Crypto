# Session 041 Report — HXRO / SXP / OSMO (2026-07-30)

Last day of the Etherscan Pro subscription. Planned Tasks A (HXRO) + B (SXP)
Etherscan-dependent; C (OSMO) keyless. Outcome: **regression-ready 180 → 182**
(SXP + OSMO in; HXRO moot). Full reasoning in DATA_DECISIONS_LOG Entry 92.

## HXRO (3748) — task moot, 0 quota spent

- Prompt premise wrong twice: (1) checkpoint is NOT empty — streamed checkpoints
  use `rows`/`mblocks` (24 months intact, 2020-09→2022-09), the prompt's
  `monthly`/`last_block` check read a nonexistent schema; (2) even a forced
  rebuild cannot help: panel months are `carried_forward` from 2022-10 onward
  (CMC visibility lost), TVL starts 2023-02, and λ is computed on
  `status='observed'` rows only (assembler line: `panel.status == "observed"`).
- Observed window (→2022-09) ∩ TVL window (2023-02→) = ∅. **Permanent gap**
  under current spec; reopen only if Phase 3 revisits the λ-on-observed rule.

## SXP (4279) — built on Ethereum chainid 1

| Probe | Result |
|---|---|
| getabi | status 1 OK |
| tokensupply | 285,368,788.739 (18 dec) |
| getLogs (latest block) | clean, 0 events (normal) |

- Root cause of the stale `non-EVM` flag: unprefixed Multi-Chain address in
  asset_onchain_identity.csv. Fixed there (`ethereum:` prefix) and in
  universe_lambda_channel_map.csv (Ethereum / reachable / Transfer-log).
- Build: 569,311 transfers, **1,886 getLogs**, contracts screened 10/96,
  **77 λ months** (2019-09-30 → 2026-02-28).
- Guards: B2 no contamination warnings; B4 HODL-6m median 27.0% (< 80%), last 34.0%.
- λ∩TVL overlap: **60 months** (2021-03 → 2026-02) → `complete`.
- BSC fallback not needed.

## OSMO (12220) — built, 2 months (archive floor)

Archive probe (pool @ old height, fake-archive guard on all):

| Endpoint | Verdict |
|---|---|
| lcd.osmosis.zone, polkachu, publicnode, ecostake, stakin, citizenweb3, lavenderfive, stakewolle, validatus, uquad, goldenratio, stake-town, cros-nest, highstakes, quickapi | pruned / dead / 4xx |
| osmosis.api.pocket.network | **FAKE ARCHIVE** (height header ignored — same family as SEI, Entry 91) |
| **osmosis-api.noders.services** | **real archive**, floor h≈58.44M = **2026-04-02** |

- Prompt's 15,000 blocks/day is stale — Osmosis runs ~73,300 blocks/day
  (~1.2 s/block, from epochs-module anchors). The floor is an apparent
  chain-wide post-upgrade state-sync point; no keyless source goes deeper.
- Built via pool @ month-end blocks (binary-search timestamps),
  `channel1_cosmos_osmo.csv`:

| month_end | height | staked (OSMO) | ratio |
|---|---|---|---|
| 2026-04-30 | 60,630,953 | 212,134,602 | 0.2749 |
| 2026-05-31 | 63,027,468 | 203,998,284 | 0.2630 |

- Cross-check vs live pool: **drift 1.77% PASS**. Denom uosmo / 10^6.
- coin_staking_type NaN → `pos`. Both months overlap TVL → `complete`.
- 2021-06 → 2026-03: unreachable without a paid indexer (Numia/Mintscan).

## Permanent gap closures (Task D)

| cmc_id | symbol | chain | Why |
|---|---|---|---|
| 1573 | CASINO | Fantom (250) | not in Etherscan V2 coverage; no free archive |
| 4157 | RUNE | THORChain | non-EVM, non-Cosmos; custom indexer required |
| 10529 | SUN | Tron | ch2 engine not adapted for Tron; TronScan deferred |

## Post-assemble totals

- λ panel: **13,626 asset-months / 467 assets** (+79 / +2)
- ch2 aggregate: 425 tokens / 13,799 rows
- Coverage: 193 complete / 310 partial / 1,436 not_started
- **Regression-ready: 180 → 182** (coins 24 unchanged; tokens/other 156 → 158)
  — regression-ready = `complete` AND λ>0 (excludes 11 pow_only NVT-only coins)

## Etherscan

Subscription lapsed after this session. Remaining Etherscan-dependent work:
none identified.
