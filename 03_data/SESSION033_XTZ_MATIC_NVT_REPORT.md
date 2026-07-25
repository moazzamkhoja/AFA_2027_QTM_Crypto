# Session 033 Report — XTZ and MATIC NVT_GL probes (2026-07-25)

**Outcome: both probes NEGATIVE. No PQ built. The kickoff prompt's Task A premise was factually wrong.**
All source checks were performed live this session; every claim below is verifiable from the probe list.

## XTZ (cmc_id 2011, 78 λ months) — NOT built; stays PQ=NaN

The prompt directed fetching `totalTransferred` from `https://api.tzkt.io/v1/statistics/daily`.
**That field does not exist.** Live response fields: date, level, timestamp, totalSupply,
circulatingSupply, totalBootstrapped, totalCommitments, totalActivated, totalCreated, totalBurned,
totalBanished, totalFrozen, totalRollupBonds, totalSmartRollupBonds, totalLost, totalOwnStaked,
totalOwnDelegated, totalExternalStaked, totalExternalDelegated, totalBakingPower, totalVotingPower,
totalBakers, totalStakers, totalDelegators — supply/staking only, no transfer volume.

Exhaustive follow-up sweep (all free/keyless candidates, all NEGATIVE):

| Source | Result |
|---|---|
| TzKT full swagger (287 paths) | No historical volume/sum endpoint anywhere |
| back.tzkt.io/v1/home (UA+Referer required) | Current-day volume + 30-day price chart only — no history |
| TzStats api.tzstats.com | DEAD — connection refused (HTTP 000) |
| TzPro api.tzpro.io | Unreachable (HTTP 000); key-gated by policy anyway |
| CoinMetrics community API | xtz Tx metrics limited to TxCnt/TxTfrCnt; TxTfrValUSD → 403 pro-gated |
| CoinMetrics GitHub csv/xtz.csv | Same community column set — no transfer value |
| bitinfocharts sentinusd-xtz | EMPTY page (no series; not the BTC default) |
| Messari legacy keyless API | 404 — dead |
| CryptoCompare blockchain histo | 401 — API key required |

Raw TzKT operation iteration (~3.7M txs/month) is forbidden by Entry 31/32. **Conclusion: XTZ
native settlement value has no free keyless historical source.** Marker row refined to
`pq_source = NaN:xtz_no_free_native_series_s033`. XTZ remains the largest single pq_nvtgl gap;
only a paid source (Artemis, CoinMetrics Pro, or a TzPro key) can close it.

## MATIC (cmc_id 3890, 50 λ months) — NOT built; stays PQ=NaN

bitinfocharts `sentinusd-matic` probe: returns 5,852 days starting **2010/07/17** with last value
identical to the BTC reference — the **BTC-default guard triggered** (Polygon launched 2020).
bitinfocharts does not cover MATIC. CoinMetrics community rejects value metrics for `matic`.
No other free keyless Polygon native-transfer-value source; PolygonScan full-history export has no
free API; Artemis is paid. λ window ends 2024-08 at the POL handoff. Marker row refined to
`pq_source = NaN:polygon_native_volume_no_free_source`. Entry-79(g)'s "candidate 21st
regression-ready coin" is closed negative.

## JOE / SAFE / DYDX classification review

- **JOE (11396, 6 λ months): permanently closed.** `coin` via `consensus tags: ['staking']`, but it
  is Trader Joe's DEX governance token (λ from veJOE vote-escrow), not a chain-native coin. No
  settlement value exists in principle; verified 0 rows in tvl_panel.csv, so no TVL path either.
- **SAFE (21585, 10 λ months): permanently closed.** Same structure — Safe{Wallet} governance
  token, staking-tag misclassification, 0 TVL rows.
- **DYDX (28324, 1 λ month, 2024-03): skip.** Legitimately a coin (dYdX Chain, Cosmos L1) but one
  λ month is too short for regression. Revisit only if λ extends via a Cosmos/Mintscan key.

Neither JOE nor SAFE has (or needs) a pq_coins.csv row; the closure is documented in
DATA_DECISIONS_LOG Entry 83.

## Post-rebuild verification (no changes expected, none observed)

`phase2_nvt_gl.py` and `build_coverage_status.py` re-run clean after the marker edits:

- pq_coins.csv: 3,275 rows (unchanged; 2 marker notes edited)
- NVT_GL panel: 2,526 asset-months / 67 assets (54 coins, 13 tokens)
- **Coins regression-ready (λ∩NVT_GL): 20 assets / 645 months — unchanged**
- Coverage: 154 complete / 231 partial / 1,554 not_started — unchanged
- Regression-ready total stays **143**

## Open items carried to session 034

Entry-79 (b)–(e): DOT/KSM Subscan key, CHZ manual anchor (gate-open), CORE key, WARP identity
review, non-TVL breadth ch2 (~500 >3k-holder tokens). Items (f)/(g) — the MATIC NVT_GL probe —
are now closed by this session.
