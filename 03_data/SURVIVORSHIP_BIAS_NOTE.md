# Survivorship-Bias Note — the 284 no-on-chain-identity listings
**Date:** 2026-06-29 (session 023) · **Log entry:** DATA_DECISIONS_LOG Entry 56 · **Status:** paper-ready

This note is written to be pulled directly into `05_paper/` (data/methodology + limitations). It documents
the 284 universe assets with no recoverable on-chain identity as an **acknowledged survivorship-bias
limitation**, not a pending data gap.

## Numbers (re-derived live and reconciled to the penny)

Source: `03_data/phase1/non_evm_lambda_recoverability.csv` (405 rows) and
`03_data/phase1/universe_lambda_channel_map.csv` (1,306 token+other assets).

```
1,306 token+other universe = 901 Etherscan-reachable + 405 off-Etherscan
  405 off-Etherscan        = 284 NO-IDENTITY (dead)
                           +  92 non-EVM-indexed (Solana/Tron/Cosmos/… — Ch2 recoverable per chain)
                           +  22 EVM-non-Etherscan (KAIA/HyperEVM/… — same method, other explorer)
                           +   7 obscure
Reconciliation: the 405 off-Etherscan == exactly the 405 rows with etherscan_reachable != yes
                (overlap 405/405, 0 outside the universe map, 0 duplicate cmc_ids).
```

**Criteria for "dead" (NO-IDENTITY):** no contract address resolvable via CoinMarketCap
`detail.platforms[]` plus the project identity map, **and** no chain or explorer (EVM or non-EVM) on which
any λ channel (staking, holding-duration, or voting) can be queried — verified across sessions 021–022.

**Cohort character:** 83% are asset_class **"other"** (non-DeFi / non-governance); 89% (252/284) are
pre-2020 listings — 191 carry a CoinMarketCap id below 2000 (the earliest 2013–2017 cohort) — with a small
(~32-asset) tail of newer non-standard-chain assets (BRC-20/ordinals, the Bitcoin-Cash-ABC fork, etc.)
whose identity our pipeline cannot resolve.

## Paper-ready paragraph (citable, ~5 sentences)

> Our λ universe of 1,306 non-native ("token"/"other") assets includes 284 that were active CoinMarketCap
> listings — overwhelmingly from 2014–2018 — for which no on-chain identity is recoverable today: there is
> no resolvable contract address and no chain or block explorer (EVM or non-EVM) on which any locking,
> holding-duration, or governance series can be queried, after checks against both Etherscan-class and
> non-EVM indexers. These assets have since been delisted, abandoned, or rug-pulled, and their absence is a
> genuine source of **survivorship bias** rather than a discretionary methodological exclusion; we name it
> explicitly here rather than absorbing it silently into the broader "no available data" category. The bias
> is unlikely to be mean-zero with respect to λ: the dead cohort is disproportionately low-conviction,
> non-governance, non-staking "other" assets (83% are so classified), exactly the kind of asset that would
> sit at the bottom of the λ (monetary-conviction) distribution even had it survived — so excluding it
> **truncates the low-λ tail and leaves the surviving panel conditionally higher-λ**. The direction of the
> resulting bias in any λ–return relationship is therefore predictable: estimates are conditioned on assets
> that lived long enough to retain a queryable on-chain footprint, which a reader should treat as a lower
> bound on the dispersion of λ in the full historical cross-section rather than as a neutral sample.

## Why no further recovery is planned

The 284 fail at the *identity* step, not the *access* step — there is no contract and no chain on which to
run any query, on free **or** paid sources. This is distinct from the paywalled-but-identifiable cases
(e.g. the 16 BSC/Base/Avax tokens that need an Etherscan-Pro plan, or the 92 non-EVM-indexed assets that
need per-chain indexers): those are *recoverable with effort/spend*; the 284 are not. If a paid multi-chain
identity resolver is ever adopted, re-run the identity-resolution step before treating any of the 284 as
recoverable.
