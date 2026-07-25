# SESSION 034 — Combined Report (2026-07-25)

## Task A — CHZ ch1 staking: BUILT ✅
- **Source:** Chiliz Chain 2.0 public RPC (`chiliz.drpc.org`), `eth_getBalance` on the
  native staking contract `0x0000000000000000000000000000000000001000` at month-end
  blocks (binary-search block lookup, cached).
- **Window:** 2023-07 → 2026-05, **35 months**, all with non-zero staked balance.
- **Cross-check:** latest month (2026-05) 2,391,774,380 CHZ vs staking.chiliz.com anchor
  2,416,757,292 CHZ → **drift −1.03%** (gate: <5%). PASS.
- **Staking ratio range:** 2.35% → 26.61%. Real ~4x step-up in 2024-06
  (262M → 1.11B CHZ staked), consistent with Chiliz staking-program expansion.
- Output: `03_data/phase1/channel1_chz.csv`. CHZ already had 21 non-NaN PQ months →
  **CHZ is the 21st regression-ready coin**.

## Task B — Blockchair XTZ/MATIC probe: FAILED (keyless unusable) ❌
- `tezos/calls`, `tezos/operations`, `tezos/transactions`, `polygon/transactions`
  (with `?a=sum(...)`) → all **HTTP 404** — no aggregation tables exposed for these chains.
- After ~4 anonymous requests, the IP was **blacklisted (HTTP 430)** on every endpoint
  including `/stats`: "Your IP address is temporary blacklisted due to exceeding usage
  of API resources. Please apply for an API key."
- **Decision needed (Moazzam):** a paid Blockchair key (~$30/month) might unblock this,
  BUT the 404s (returned before the blacklist fully kicked in) suggest Tezos/Polygon
  aggregation may not exist at any tier. Recommend confirming with Blockchair support
  (info@blockchair.com) that `sum(amount)`/`sum(value)` aggregation works for
  tezos/polygon **before** paying. Not subscribed. XTZ and MATIC stay PQ=NaN.

## Task C — EVM DeFi Breadth Batch 1: 101/102 BUILT ✅
- MSOL (11461) was already complete from a prior session → engine skipped it.
- **154,049 getLogs** (est. ~147k — first batch estimate to land on target),
  **47.56M transfers**, **2,916 screened λ months**.
- **B2:** clean across all 101 tokens (no 100x contamination flags).
- **B4 flagged-high** (screened HODL-6m median >80%, kept per rule): META, TROY, SMT,
  YOU, BOX(3475), WHITE, HOT, BOX(2945), STRONG.
- Biggest builds: STRONG 6.66M tf / 20.0k gl; WSTETH 4.02M tf / 11.9k gl; XAI 2.62M tf.
- Survivorship targets: **CEL** (Celsius) 54 scrMo, **FTT** (FTX) 81 scrMo — HODL median
  34.7% → 82.5% last (the dead-exchange holding pattern), MULTI already built.

## Task C2 — DeFiLlama TVL matching
Raw symbol matching was ~40% wrong (Litentry→"lighter-bridge", 2017-Jupiter→Solana
"jupiter-lend", Wrapped Solana→"solana-farm"...). Re-matched with cmcId authority +
name corroboration + individual verification of every accept:
- **24 token-class slugs** written to `asset_onchain_identity.csv`
- **4 other-class adds** (phase2 OTHER_ADDS): MULTI/multichain (dead — 49 mo of
  historical TVL), ORC/orbit-bridge (hacked — 46 mo), MUBI, FF
- **2 chain-level adds** (Entry-68 pattern): METIS/chain:Metis (54 mo), XAI/chain:Xai (28 mo)
- **LST receipt tokens excluded on circularity** (NV≈TVL by construction): wstETH, weETH,
  cbETH, rETH, sfrxETH, mETH, ETHx, swETH, rswETH, ezETH, rsETH, WBETH, tETH, LBTC,
  MSOL, aEthWETH, bUSD0
- **CEL and FTT have no DeFiLlama entries** (CeFi books never TVL-tracked)
- `tvl_panel.csv` rebuilt: **159 assets / 7,889 asset-months**

## Task D — Post-assemble totals
| metric | before (033) | after (034) |
|---|---|---|
| λ asset-months | 9,648 | **12,599** |
| λ assets | 342 | **444** |
| regression-ready | 143 | **173** (coins 21, tokens/other 152) |
| channel2_holding.csv | 307 tok / 9,867 rows | **408 tok / 12,955 rows** |
| tvl_panel.csv | ~6.7k mo | **7,889 mo / 159 assets** |
| coverage | 149/236/1554 | **184 complete / 302 partial / 1,453 not_started** |

Batch-1 tokens with λ∩TVL overlap (new regression-ready): **29** (790 overlapped months).

## Next sessions
- **035 — Batch 2:** 13 tokens (~119k gl): SNX, LEND, SAI, EETH, PNT, old-KNC 1982…
  (WORKLIST in 034 prompt). Note: old-KNC ↔ kyberswap window-split vs KNC 9444 to review.
- **036 — Batch 3a:** stETH + MEME (~110k gl)
- **037 — Batch 3b:** SHIB (~128k gl)
- DOT/KSM on Subscan key; CORE on key; WARP identity review; non-TVL breadth ch2 (~500 tokens).

## Token-level table (101 built)
| symbol | cmc_id | getLogs | transfers | scr months | B2 | B4 | HODL med/last | TVL slug |
|---|---|---|---|---|---|---|---|---|
| bUSD0 | 33981 | 1,039 | 288,913 | 9 | pass | pass | 5.9%/5.9% | - |
| IFT | 1888 | 198 | 30,119 | 15 | pass | pass | 52.2%/92.7% | - |
| DRG | 2593 | 160 | 23,511 | 18 | pass | pass | 32.8%/33.5% | - |
| RIVER | 38417 | 513 | 91,950 | 6 | pass | pass | 0.0%/0.0% | river-omni-cdp |
| NXM | 5830 | 460 | 118,725 | 30 | pass | pass | 40.0%/46.7% | - |
| SFRXETH | 23177 | 543 | 153,350 | 10 | pass | pass | 35.6%/47.8% | - |
| CRD | 3367 | 294 | 54,921 | 4 | pass | pass | 9.4%/2.0% | - |
| META | 3418 | 311 | 13,126 | 87 | pass | flag-high | 91.1%/91.1% | - |
| MULTI | 17050 | 304 | 60,295 | 12 | pass | pass | 7.0%/7.7% | multichain |
| CAT | 1882 | 119 | 28,461 | 12 | pass | pass | 6.4%/75.8% | - |
| TEN | 2576 | 282 | 51,201 | 54 | pass | pass | 79.5%/91.9% | - |
| UNFI | 7672 | 263 | 61,320 | 45 | pass | pass | 49.4%/9.6% | - |
| SOSO | 35818 | 1,301 | 363,859 | 9 | pass | pass | 0.5%/0.5% | sosovalue-indexes |
| ADX | 1768 | 560 | 180,121 | 64 | pass | pass | 17.4%/36.2% | - |
| LIT | 39125 | 691 | 143,947 | 6 | pass | pass | 0.0%/0.0% | lighter-bridge |
| DMT | 2503 | 174 | 29,500 | 32 | pass | pass | 78.6%/56.1% | - |
| RSWETH | 29974 | 1,173 | 346,322 | 11 | pass | pass | 41.2%/54.3% | - |
| ROX | 3325 | 178 | 24,486 | 20 | pass | pass | 69.6%/82.7% | - |
| LOCUS | 3855 | 423 | 105,674 | 41 | pass | pass | 79.9%/84.4% | - |
| APEX | 19843 | 757 | 211,511 | 9 | pass | pass | 51.4%/52.5% | apex-pro |
| ZAP | 2363 | 242 | 68,553 | 11 | pass | pass | 42.5%/45.1% | - |
| TROY | 5007 | 226 | 20,531 | 53 | pass | flag-high | 87.7%/30.3% | - |
| RBN | 12387 | 862 | 257,795 | 30 | pass | pass | 9.7%/8.4% | ribbon |
| TKN | 1660 | 344 | 112,365 | 48 | pass | pass | 74.2%/66.4% | - |
| PIXEL | 29335 | 375 | 73,738 | 28 | pass | pass | 5.1%/3.6% | - |
| LIT | 6833 | 312 | 69,575 | 48 | pass | pass | 28.7%/5.3% | - |
| DAD | 4862 | 249 | 34,288 | 40 | pass | pass | 65.8%/46.0% | - |
| WBETH | 24760 | 497 | 116,275 | 23 | pass | pass | 18.6%/89.4% | - |
| GEN | 2726 | 298 | 94,914 | 6 | pass | pass | 43.7%/44.9% | - |
| SMT | 2277 | 214 | 29,988 | 37 | pass | flag-high | 100.0%/100.0% | - |
| DOV | 2110 | 305 | 73,665 | 41 | pass | pass | 56.5%/50.4% | - |
| RING | 5798 | 734 | 216,241 | 30 | pass | pass | 12.6%/23.0% | - |
| ORC | 5326 | 356 | 91,546 | 36 | pass | pass | 51.3%/45.4% | orbit-bridge |
| LINA | 3083 | 216 | 53,175 | 18 | pass | pass | 73.9%/93.8% | - |
| TETH | 37574 | 997 | 259,957 | 5 | pass | pass | 3.9%/3.9% | - |
| METH | 29035 | 665 | 170,478 | 11 | pass | pass | 12.5%/14.1% | - |
| MAV | 18037 | 466 | 114,273 | 34 | pass | pass | 3.0%/17.6% | maverick-v1 |
| CFG | 6748 | 1,051 | 275,392 | 15 | pass | pass | 0.0%/46.1% | centrifuge-protocol |
| FF | 38482 | 1,353 | 361,148 | 9 | pass | pass | 0.0%/0.3% | falcon-finance |
| AUTO | 2559 | 232 | 52,425 | 31 | pass | pass | 38.2%/73.1% | - |
| WINGS | 1500 | 478 | 153,383 | 45 | pass | pass | 39.7%/46.7% | - |
| ZIP | 2826 | 186 | 35,485 | 28 | pass | pass | 35.1%/35.7% | - |
| VOLT | 19650 | 490 | 121,182 | 22 | pass | pass | 48.8%/54.7% | - |
| OST | 2296 | 510 | 147,047 | 42 | pass | pass | 44.3%/44.3% | - |
| PRL | 2202 | 263 | 72,495 | 10 | pass | pass | 25.1%/46.7% | - |
| YOU | 3053 | 238 | 57,296 | 16 | pass | flag-high | 94.3%/99.3% | - |
| SKY | 33038 | 3,175 | 996,285 | 13 | pass | pass | 0.3%/3.5% | sky-lending |
| DGTX | 2772 | 264 | 44,823 | 6 | pass | pass | 0.0%/32.3% | - |
| SPI | 8161 | 595 | 168,006 | 11 | pass | pass | 26.6%/46.6% | - |
| PYR | 9308 | 960 | 299,812 | 53 | pass | pass | 29.0%/17.0% | - |
| VEE | 2223 | 797 | 261,517 | 71 | pass | pass | 63.6%/60.9% | - |
| SWETH | 25147 | 2,549 | 814,882 | 11 | pass | pass | 12.2%/16.3% | - |
| EDGE | 39720 | 2,057 | 581,563 | 3 | pass | pass | 0.0%/0.0% | edgex-bridge |
| DODO | 7224 | 1,369 | 465,519 | 63 | pass | pass | 17.9%/34.1% | dodo-amm |
| ALI | 16876 | 954 | 299,290 | 40 | pass | pass | 8.4%/15.4% | - |
| IDEX | 3928 | 586 | 159,564 | 64 | pass | pass | 70.1%/41.6% | idex-v1 |
| SYRUP | 33824 | 1,917 | 574,251 | 14 | pass | pass | 11.4%/23.6% | maple |
| BARD | 38408 | 1,803 | 501,084 | 9 | pass | pass | 0.0%/1.4% | lombard-lbtc |
| DAO | 8420 | 2,000 | 649,613 | 48 | pass | pass | 4.9%/11.1% | - |
| KNC | 9444 | 1,403 | 452,019 | 59 | pass | pass | 24.1%/22.6% | kyberswap-classic |
| MUBI | 28412 | 1,526 | 445,657 | 13 | pass | pass | 6.3%/26.9% | multibit-protocol |
| WOO | 7501 | 2,395 | 798,802 | 62 | pass | pass | 16.1%/20.7% | woofi-swap |
| DEP | 5429 | 945 | 322,914 | 48 | pass | pass | 45.6%/23.6% | - |
| MIN | 3296 | 220 | 28,613 | 15 | pass | pass | 77.8%/80.7% | - |
| BOX | 3475 | 220 | 28,248 | 22 | pass | flag-high | 85.1%/95.4% | - |
| MORPHO | 34104 | 2,619 | 814,919 | 18 | pass | pass | 9.0%/20.0% | morpho-blue |
| RETH | 15060 | 2,745 | 868,428 | 17 | pass | pass | 20.2%/21.6% | - |
| RLY | 8075 | 1,409 | 431,472 | 37 | pass | pass | 14.4%/30.3% | - |
| JUP | 1503 | 358 | 95,120 | 14 | pass | pass | 25.3%/38.5% | - |
| WILD | 9674 | 1,624 | 526,364 | 54 | pass | pass | 9.8%/18.8% | - |
| CPOOL | 12573 | 2,295 | 748,913 | 18 | pass | pass | 29.4%/31.1% | clearpool-lending |
| RSETH | 29242 | 1,361 | 415,042 | 11 | pass | pass | 2.7%/2.5% | - |
| LBTC | 33652 | 1,869 | 547,656 | 10 | pass | pass | 2.1%/3.1% | - |
| METIS | 9640 | 1,979 | 641,646 | 54 | pass | pass | 11.5%/10.7% | - |
| EZETH | 29520 | 2,473 | 778,082 | 12 | pass | pass | 14.8%/25.4% | - |
| ZRO | 26997 | 2,113 | 655,100 | 24 | pass | pass | 22.5%/34.9% | layerzero-v2 |
| WHITE | 34143 | 1,593 | 477,196 | 16 | pass | flag-high | 90.4%/97.7% | - |
| UMA | 5617 | 2,545 | 806,941 | 69 | pass | pass | 21.0%/22.0% | - |
| HOT | 2430 | 268 | 64,098 | 36 | pass | flag-high | 83.7%/93.9% | - |
| PRIME | 23711 | 2,758 | 883,569 | 31 | pass | pass | 15.4%/12.2% | - |
| weETH | 28695 | 4,313 | 1,386,191 | 12 | pass | pass | 1.7%/4.2% | - |
| BabyDoge | 10407 | 783 | 250,321 | 48 | pass | pass | 78.1%/78.3% | babydogeswap |
| ATM | 2015 | 261 | 61,645 | 13 | pass | pass | 7.8%/12.7% | - |
| CEL | 2700 | 3,237 | 1,096,985 | 54 | pass | pass | 55.1%/31.1% | - |
| BOX | 2945 | 480 | 100,577 | 16 | pass | flag-high | 96.0%/96.4% | - |
| ETHX | 27566 | 661 | 178,293 | 11 | pass | pass | 13.1%/15.2% | - |
| FTT | 4195 | 2,075 | 689,112 | 81 | pass | pass | 34.7%/82.5% | - |
| STRONG | 6511 | 20,037 | 6,663,109 | 18 | pass | flag-high | 95.6%/94.4% | - |
| SUB | 1984 | 324 | 61,591 | 17 | pass | pass | 71.5%/85.5% | - |
| SPELL | 11289 | 2,911 | 945,921 | 54 | pass | pass | 15.4%/21.8% | abracadabra-spell |
| WSTETH | 12409 | 11,901 | 4,015,810 | 11 | pass | pass | 12.2%/15.3% | - |
| ARKM | 27565 | 1,961 | 589,187 | 28 | pass | pass | 13.5%/14.3% | - |
| LON | 8083 | 1,569 | 505,756 | 65 | pass | pass | 14.9%/15.5% | tokenlon-amm |
| ETHDYDX | 11156 | 2,687 | 880,118 | 49 | pass | pass | 15.5%/14.1% | dydx-v3 |
| AEVO | 29676 | 2,109 | 633,035 | 27 | pass | pass | 16.7%/29.4% | aevo-perps |
| AETHWETH | 36458 | 4,169 | 1,366,558 | 8 | pass | pass | 29.6%/48.5% | - |
| SOL | 16116 | 3,257 | 1,098,234 | 10 | pass | pass | 15.5%/17.8% | - |
| XAI | 28933 | 8,711 | 2,619,661 | 29 | pass | pass | 17.0%/38.8% | - |
| AGIX | 2424 | 2,487 | 814,797 | 39 | pass | pass | 55.8%/41.2% | - |
| cbETH | 21535 | 2,701 | 886,222 | 17 | pass | pass | 59.5%/68.9% | - |
| PAY | 1758 | 1,769 | 551,739 | 52 | pass | pass | 38.5%/72.0% | - |