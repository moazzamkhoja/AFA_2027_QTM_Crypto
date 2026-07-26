# Session 035 — EVM DeFi Breadth Batch 2 (13/13); SNX/LEND/ANKR TVL; KNCL window-clip

**Date:** 2026-07-25 (same day as session 034, same conversation)
**Model/interface:** Claude Fable 5 via Claude Code (desktop app, Windows)
**Kickoff:** user pasted the Batch-2 WORKLIST command from the 034 prompt directly
**Mode:** autonomous after launch; standing end-of-session commit+push authorization
**Commits:** a7aa885 (+ record-keeping commit after)

---

## Initial user prompt (verbatim)

> WORKLIST=3783,2120,5824,1982,1757,2586,2165,5266,2239,28568,9436,2308,2691 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py

One "status?" check-in mid-build; no decisions requested.

## Structured event log

1. **Launched Batch 2 in background** (13 tokens). Flagged the quota caveat (154k gl
   already spent same-day; 034 prompt suggested waiting for reset) — quota did NOT
   bind: full run completed same-day (credit-based, confirming the session-032 read).
2. **Pre-flight while building:** identity map showed ANKR slug present but other-class
   (0 panel rows — the RPL-style filter gap); AAVE holds aave-v2 so aave-v1 free for
   LEND; MKR has NO dl_slug; cmc 2691 "PNT" is Penta, NOT pNetwork (034 prompt note
   wrong).
3. **Build completed: 13/13**, 74,783 getLogs (0.63x of est 119k), 22.9M transfers,
   592 screened months. B2 clean; B4 flag-high only PNT (97.9%, dead token, kept).
   FUN 105 scrMo (longest of the batch), ANKR 85, SNX 73, SLP 58, ELON 56, KNCL 47.
4. **Migration-window checks:** KNCL λ 2017-09..2021-07 vs KNC-9444 λ 2021-07+ →
   single overlap month; MATIC/POL rule applied. MKR λ = ZERO months (never built) →
   no MKR/SKY double-count exposure; nothing assigned to MKR.
5. **TVL implementation:** SNX→`synthetix` parent (children-only in /protocols;
   parent fetchable, 2,545 daily points 2019-08+); LEND→`aave-v1` (73 mo, 4 λ-overlap
   2020-05..2020-08 = the dead-token region); ANKR→OTHER_ADDS (cmcId exact, 67 mo);
   KNCL→kyberswap-classic clipped ≤2021-06 via new CLIP mechanism added to
   `phase2_build_tvl_panel.py` (9 mo). SAI excluded on liability-token circularity
   (CDP stablecoin: NV≈supply, NV/TVL = inverse collateral ratio); EETH excluded (LST
   receipt, Entry-84 rule); FUEL/FUN/ERC20/MLK/SLP/ELON/PNT have no protocol TVL.
6. **Rebuild + assemble:** tvl_panel 163 assets / 8,120 mo; λ 13,191 / 457 assets;
   regression-ready 173→177 (coins 21, tokens/other 156; new: SNX 73, ANKR 66,
   KNCL 9, LEND 4 overlap months); ch2 421 tokens / 13,580 rows; coverage
   188/311/1,440.
7. **Entry 85**, `SESSION035_BATCH2_REPORT.md`, token table, build log force-added;
   committed a7aa885, pushed.

## Data-access notes
- Etherscan Pro V2: 229k getLogs total across the calendar day over two runs, no
  rejection — the account quota is credit-based, not a hard daily getLogs cap.
- DeFiLlama parent slugs (synthetix) fetchable at /protocol/{slug} even when absent
  from /protocols; `maker` parent is NOT (400) — Maker history lives under Sky children.
