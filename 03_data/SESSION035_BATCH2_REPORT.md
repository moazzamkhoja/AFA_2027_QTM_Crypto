# SESSION 035 — EVM DeFi Breadth Batch 2 (2026-07-25)

Launched same-day after session 034 by direct user command (the 034-planned WORKLIST).
Etherscan Pro quota did not bind despite 154k getLogs earlier the same day (credit-based).

## Build: 13/13 ✅
74,783 getLogs (est ~119k → 0.63x), 22.9M transfers, 592 screened λ months. B2 clean.

| symbol | cmc_id | getLogs | transfers | scr months | B4 | TVL |
|---|---|---|---|---|---|---|
| ANKR | 3783 | 3,129 | 1,038,372 | 85 | pass | Y (ankr, 66 overlap mo) |
| FUEL | 2120 | 444 | 106,285 | 33 | pass | N |
| SLP | 5824 | 7,131 | 2,393,756 | 58 | pass | N |
| KNCL | 1982 | 4,568 | 1,488,085 | 47 | pass | Y (kyberswap-classic ≤2021-06, 9 mo) |
| FUN | 1757 | 3,511 | 1,166,549 | 105 | pass | N |
| SNX | 2586 | 7,877 | 2,592,989 | 73 | pass | Y (synthetix parent, 73 overlap mo) |
| ERC20 | 2165 | 918 | 147,250 | 46 | pass | N |
| MLK | 5266 | 26,197 | 7,094,910 | 15 | pass | N |
| LEND | 2239 | 2,054 | 622,011 | 33 | pass | Y (aave-v1, 4 overlap mo — died 2020-08) |
| EETH | 28568 | 3,417 | 1,109,069 | 11 | pass | N (LST receipt — circularity rule) |
| ELON | 9436 | 5,107 | 1,685,185 | 56 | pass | N |
| SAI | 2308 | 9,368 | 3,129,097 | 25 | pass | N (stablecoin liability — circularity rule) |
| PNT | 2691 | 1,062 | 271,594 | 5 | flag-high 97.9% | N (Penta, dead — NOT pNetwork; 034 note wrong) |

## TVL decisions (Entry 85)
- **SNX → `synthetix`** (parent slug; children-only in /protocols, Entry-68 CRV/GMX precedent)
- **LEND → `aave-v1`** (AAVE keeps aave-v2; clean protocol-era split)
- **ANKR → OTHER_ADDS** (other-class filter gap, same as RPL)
- **KNCL → `kyberswap-classic` window-clipped ≤2021-06** via new CLIP mechanism
  (KNC-9444 λ starts 2021-07; MATIC/POL no-double-count rule)
- **MKR**: no DL parent (`maker` 400s; history lives in SKY's sky-lending), and MKR has
  zero λ months — nothing assigned, no double-count exposure
- **SAI**: excluded — CDP-stablecoin NV≈supply, NV/TVL = inverse collateral ratio
  (liability-token circularity, same family as LST rule)

## Post-assemble
| metric | after 034 | after 035 |
|---|---|---|
| λ asset-months / assets | 12,599 / 444 | **13,191 / 457** |
| regression-ready | 173 | **177** (coins 21, tokens/other 156) |
| tvl_panel | 159 / 7,889 mo | **163 / 8,120 mo** |
| channel2_holding | 408 / 12,955 | **421 / 13,580** |
| coverage | 184/302/1,453 | **188/311/1,440** |

## Next
- **036:** stETH (8085) + MEME (28301), ~110k gl
- **037:** SHIB (5994), ~128k gl
- Open: DOT/KSM Subscan key, CORE key, WARP review, non-TVL breadth (~500 tokens),
  Blockchair paid-key decision (XTZ/MATIC)
