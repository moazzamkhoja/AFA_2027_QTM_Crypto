# Session 027 — TVL expansion + Channel-2 tail completion build report

**Date:** 2026-07-03/04 · **Decisions Log:** Entries 68–70 · Parallel to `SESSION026_TAIL_BUILD_REPORT.md`.

Starting point (session 026 close, Entry 67): **λ 6,021 asset-months / 282 assets** (n_channels
1/2/3 = 5,356 / 333 / 332); **TVL panel 4,999 asset-months / 99 tokens** — the five 3-channel
assets CRV/YFI/FRAX/GMX/RPL had full λ but **no TVL denominator**, so they could not enter the
NV/TVL regression. Two tasks, in priority order: (A) TVL expansion, (B) the Channel-2 tail for
the 43 λ tokens with ch1 OR ch3 but no ch2.

**Session result: λ 6,021 → 7,051 asset-months (+1,030) / 282 assets; 2+ channel share
11.0% → 24.4%; TVL panel 4,999 → 6,620 asset-months / 99 → 130 tokens; NV/TVL computable for
all nine 3-channel assets.**

---

## Task A — TVL expansion (Entry 68)

### A1 — Slug discovery: the PARENT-protocol finding

DeFiLlama's `/protocols` cmcId lookup found **zero** of the four missing priority tokens (and
zero of the 207 no-slug non-coin λ assets) — DL's `cmcId` field covers only 1,709 of 7,770
protocols, and every cmcId-matchable asset was already harvested in earlier sessions. Fallback:
exact symbol+name matching (the session-019 LOOSE_ADDS precedent), each hit verified
individually (name + category + live TVL + series launch date).

The decisive pattern: all four live under DL **parent protocols** with per-version children
(e.g. curve-dex / curve-llamalend / crvusd under `curve-finance`). Since the token governs the
WHOLE family, the parent slug is the correct denominator; `/protocol/{parent}` verified to
serve the aggregated series with correct launch dates:

| token | slug | series | last TVL |
|-------|------|--------|---------:|
| CRV  | curve-finance | 2020-02 → 2026-05 (76 mo) | $1.61B (peak $23.1B Jan-22) |
| YFI  | yearn         | 2020-02 → 2026-05 (76 mo) | $253M (peak $5.9B) |
| FRAX | frax-finance  | 2020-12 → 2026-05 (66 mo) | $336M |
| GMX  | gmx           | 2021-09 → 2026-05 (57 mo) | $194M |
| RPL  | rocket-pool (existing slug, was excluded by the token-class filter) | 2021-10 → 2026-05 (56 mo) | $1.10B |

**19 more name-verified slugs** (same bar): AERO→aerodrome, ALCX→alchemix, BAL→balancer,
BLUR→blur, BNT→bancor, BONE→shibaswap, CAKE→pancakeswap, COMP→compound-finance, ENA→ethena,
EUL→euler, FLUID→fluid, LQTY→liquity, ONDO→ondo-finance, STG→stargate-finance,
T→threshold-network, UNI (cmc **7083 only** — 4113 "UNI COIN" is a symbol collision)→uniswap,
VVS→vvs-finance, XVS→venus (parent slug; "venus-finance" 400s), plus RPL above. All written to
`asset_onchain_identity.csv` by cmc_id join, `dl_matched=True`.

### A2/A3 — Builder extensions (`phase2_build_tvl_panel.py`)

1. **OTHER_ADDS** — the original `asset_class=='token'` filter silently excluded 'other'-class
   λ assets. Five reviewed adds: RPL/rocket-pool, SSV/ssv-network, BLUR/blur, RAIN/rain,
   MV/gensokishi.
2. **CHAIN_LEVEL** — canonical L2 governance tokens whose DL protocol entry is a
   Foundation/treasury or an empty parent now get CHAIN DeFi TVL via
   `/v2/historicalChainTvl/{chain}`, recorded as `dl_slug='chain:{name}'` so downstream can
   include/exclude them explicitly: ARB→Arbitrum, OP→**'OP Mainnet'** (DL renamed; 'Optimism'
   is a dead $0 alias), MNT→Mantle, APE→ApeChain, BLAST→Blast. **Coins deliberately excluded**
   (they use NVT, not NV/TVL, per the framework).

**Rejected (logged so they are not re-tried):** ZORA (parent 400s; bridge-custody ≠ protocol
TVL; identity slug reverted), GBYTE (oswap-amm is a third-party DEX on Obyte), PENGU (not
Abstract's fee token), CYBER (chain TVL ~$0), NEST (two conflicting DL parents), POWER/M0
(identity unconfirmable), CVP (019 rejection re-affirmed), WLFI (no TVL series); MNT/OP
Foundation slugs NOT fetched as protocol TVL. Genuinely-no-TVL protocols left NaN: ENS, GTC,
COW, FORTH, ZRX, CHEEL (+ apecoin/cyberconnect protocol entries).

### A4/A5 — Rebuild + plausibility

**Panel: 4,999 → 6,620 asset-months / 99 → 130 distinct tokens** (2018-09 → 2026-05), 0 fetch
failures. A5 gate on the five priority tokens: PASS (56–76 months each, no post-launch
near-zeros, USD magnitudes sane). **λ assets with TVL 49 → 80** (of 282); λ asset-months with
same-month TVL 2,103 of 7,051 (pre-tail-λ basis: 2,103/6,021); **3-channel asset-months with
TVL: 331 of 332** — the one gap is SUSHI 2020-08, its launch month, before DL's sushiswap
series begins (genuine early-launch per the A5 rule).

---

## Task B — Channel-2 tail: ALL 43 tokens completed (Entry 69)

Targets: every λ asset with ch1 OR ch3_voting but no ch2 and holder_count ≤ 500k (from
`universe_coverage_status.csv`), built smallest-first with the validated session-026 streaming
engine (`phase1_channel2_stream.py`, **no code changes, guard thresholds untouched**). HEX not
attempted (permanent deferral, Entry 66).

**All 43 completed, zero network aborts: 60,100,476 Transfer events replayed; ch2 panel
217 → 260 tokens / 5,663 → 7,823 rows.** Hidden giants (holder_count under-predicts transfer
volume — the ORBS lesson) absorbed in bounded memory: UNI 8.3M transfers, APE 5.9M, BNT 5.7M,
GNS 3.5M (Polygon), ENA/PENDLE 3.3M each.

### Per-token results (screened HODL-6m = >6m-old supply held by non-contract addrs / on-chain supply)

| token | cmc | transfers | scr months | median (last) % | | token | cmc | transfers | scr months | median (last) % |
|-------|----:|----------:|---------:|--------------|-|-------|----:|----------:|---------:|--------------|
| NFTX | 8191 | 85,703 | 42 | 48.4 (80.4) | | CAKE | 7186 | 290,552 | 39 | 24.6 (41.1) |
| HAKKA | 6622 | 126,153 | 9 | 8.4 (10.7) | | GNS | 13663 | 3,509,446 | 38 | 45.4 (55.7) |
| IQ | 2930 | 273,514 | 63 | 4.8 (58.0) | | LINA | 7102 | 255,328 | 50 | 20.0 (35.9) |
| BZRX | 5810 | 222,729 | 26 | 2.7 (37.5) | | API3 | 7737 | 818,267 | 52 | 14.0 (16.1) |
| COW | 19269 | 683,876 | 11 | 9.3 (12.3) | | MNT | 27075 | 603,455 | 35 | 9.4 (5.8) |
| MC | 13523 | 298,199 | 24 | 1.6 (14.1) | | BADGER | 7859 | 849,986 | 58 | 35.0 (35.3) |
| SSV | 12999 | 281,934 | 46 | 49.0 (36.7) | | BNT | 1727 | 5,747,417 | 108 | 36.1 (44.0) |
| OHM | 9067 | 551,377 | 7 | 10.4 (10.5) | | STG | 18934 | 1,109,808 | 40 | 8.0 (33.1) |
| KP3R | 7535 | 528,842 | 47 | 38.5 (52.8) | | BAL | 5728 | 2,064,156 | 65 | 19.6 (27.1) |
| ORBS | 3835 | 396,103 | 85 | 26.4 (35.9) | | REN | 2539 | 1,257,662 | 82 | 42.5 (57.5) |
| RGT | 7486 | 210,798 | 25 | 20.9 (21.8) | | ARB | 11841 | 615,316 | 39 | 22.1 (24.8) |
| SYN | 12147 | 590,778 | 39 | 43.4 (39.1) | | LDO | 8000 | 1,856,680 | 51 | 32.0 (30.7) |
| PNT | 5794 | 121,025 | 43 | 25.0 (53.9) | | ENS | 13855 | 1,537,815 | 55 | 13.4 (22.1) |
| STRK | 8911 | 113,753 | 50 | 45.4 (67.2) | | PENDLE | 9481 | 3,262,676 | 36 | 25.5 (18.7) |
| XAN | 38481 | 191,782 | 9 | 0.0 (75.8)* | | GTC | 10052 | 782,945 | 35 | 24.0 (25.0) |
| LQTY | 7429 | 727,531 | 40 | 7.1 (17.6) | | ENA | 30171 | 3,291,994 | 26 | 32.7 (43.5) |
| ALCX | 8613 | 835,568 | 60 | 41.2 (43.0) | | LRC | 1934 | 1,586,784 | 85 | 44.0 (38.8) |
| PERP | 6950 | 563,707 | 56 | 10.4 (11.2) | | GRT | 6719 | 2,810,548 | 66 | 37.2 (40.7) |
| HFT | 22461 | 264,271 | 39 | 5.6 (20.9) | | APE | 18876 | 5,927,482 | 51 | 47.9 (26.8) |
| TRU | 7725 | 333,479 | 50 | 36.3 (38.2) | | ZRX | 1896 | 2,741,212 | 106 | 51.3 (54.9) |
| FARM | 6859 | 698,297 | 58 | 5.4 (7.5) | | COMP | 5692 | 2,738,163 | 71 | 40.7 (32.9) |
| | | | | | | UNI | 7083 | 8,343,365 | 68 | 50.9 (51.8) |

\* XAN's 0.0 median is an AGE artifact, not degeneracy: the token launched mid-2025, so no lot
*could* be >6m old before 2026-03; from 2026-03 the screened series is a real 74–77%, coherent
with its non-custodial XanV1 lock (locked tokens age in place in holders' wallets, Entry 58).

### B2 integrity scan
Reconstructed on-chain supply vs circulating across all 43: **0 months above the 100×
contamination threshold** (worst = HAKKA 31×, inside the legitimate Entry-49 heavy-lock band);
0 months nulled. The two-layer guard (VAL_CAP_MULT / CONTAM_MULT = 100, Entry 66) was not
modified.

### B4 sanity (>50k-holder tokens)
Medians all economically bounded: ENS 13.4% · BAL 19.6% · ARB 22.1% · GTC 24.0% · PENDLE 25.5%
· LDO 32.0% · ENA 32.7% · GRT 37.2% · COMP 40.7% · REN 42.5% · LRC 44.0% · APE 47.9% · UNI
50.9% · ZRX 51.3%. None degenerate.

### λ result (Entry 69)
**λ 6,021 → 7,051 observed asset-months (+1,030); assets unchanged at 282** — all 43 were
already λ members; this session is DEPTH (the +1,030 months are where ch2 extends beyond each
token's ch1/ch3 window). n_channels 1/2/3 = **5,331 / 1,388 / 332** (was 5,356 / 333 / 332):
2-channel asset-months **+1,055**. **2+ channel share 11.0% → 24.4%.** 3-channel unchanged at
332 across 9 assets (none of the 43 had BOTH ch1 and ch3, by construction of the priority
list). ch2_holding is standardizable in 114 monthly cross-sections, the widest of any channel.

---

## Budget / method compliance
- **Etherscan Pro getLogs: 182,876 total across two compliant quota days** — day 1 (2026-07-03
  UTC) 141,005, engine cap-stopped cleanly after APE at the in-process DAILY_CAP=140k (set
  below the 180k stop-rule so a mid-flight giant cannot overshoot; 59k day-headroom remained);
  day 2 (2026-07-04 UTC) 41,871 for ZRX/COMP/UNI after the 00:00 UTC reset. Per-token
  checkpoints made the cap-stop a zero-loss resume.
- DeFiLlama free/keyless (~35 new protocol + 5 chain fetches, cached per slug). No additional
  paid subscriptions.
- cmc_id joins only; screened HODL denominator = on-chain supply (not CMC circulating);
  assembler z-score/equal-weight logic untouched (channel inputs only); guard thresholds
  unchanged; PYTHONUTF8=1.

## Next-session priorities (Entry 70)
(a) coin staking ch1 (AVAX/BNB/NEAR/INJ/SUI/APT…) — non-EVM, separate research effort;
(b) the ~500 >3k-holder non-λ breadth tokens (single-channel ch2 adds);
(c) AAVE's spam-excluded 2024-08→2026-05 ch2 window via a per-token totalSupply value cap
(Entry 66 refinement, still open);
(d) PQ/NVT_GL expansion (deferred);
(e) the ~140 λ assets with neither TVL nor a defensible DL protocol stay TVL-NaN — do not
loosen the name-match bar.
