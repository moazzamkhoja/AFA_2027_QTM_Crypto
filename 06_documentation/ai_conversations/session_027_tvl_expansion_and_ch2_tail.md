# Session 027 — TVL expansion + Channel-2 tail completion (2026-07-02 → 2026-07-04)

**Model/interface:** Claude Fable 5 via Claude Code (desktop). Kickoff prompt:
`04_code/CLAUDE_CODE_SESSION027_TVL_EXPANSION_AND_CH2_TAIL_PROMPT.md` (committed alongside).
This structured log is the companion to the verbatim transcript (primary record, AFA rules).

## Initial prompt (summary)
Two tasks in priority order against λ = 6,021 asset-months / 282 assets (session 026 close):
**Task A** — TVL expansion (Entry 68): slug discovery for CRV/YFI/FRAX/GMX (+ RPL direct),
extend the TVL fetch to all λ tokens with slugs, bulk cmcId discovery for the rest, chain-level
TVL where applicable, rebuild `tvl_panel.csv`, plausibility-check the 5 priority tokens.
**Task B** — Channel-2 tail (Entry 69): build ch2 for the 43 λ assets with ch1 OR ch3 but no
ch2 (holder_count ≤ 500k), smallest-first, session-026 streaming engine, 200k/day budget with
20k headroom, B2 integrity scan, re-aggregate + re-assemble, B4 sanity checks. Standing rules:
cmc_id joins only, append-only decisions log (entries 68–70), no new paid subscriptions,
commit+push at session end.

## Timeline / what was done

**2026-07-02 evening (local).** Required reading (Entries 63–67, session-026 report, coverage
map, both builders). Task A executed: DL `/protocols` cmcId lookup → 0 hits for all four
priority tokens AND all 207 no-slug non-coin λ assets (DL cmcId covers only 1,709/7,770;
earlier sessions had harvested every match). Fallback exact symbol+name scan → the
PARENT-protocol finding (CRV/YFI/FRAX/GMX all live under DL parents; parent slug = the
token's whole-protocol claim; verified `/protocol/{parent}` serves aggregated series with
correct launch dates). 23 slugs written to identity (incl. UNI 7083-not-4113 collision
handling); XVS fixed to `venus` after `venus-finance` 400'd; ZORA rejected + reverted.
Builder extended: OTHER_ADDS (RPL/SSV/BLUR/RAIN/MV — the 'other'-class filter gap that had
silently excluded RPL despite its existing slug) and CHAIN_LEVEL
(ARB/OP→'OP Mainnet'/MNT/APE/BLAST via historicalChainTvl; coins excluded — NVT framework;
CYBER/PENGU/GBYTE rejected). Panel rebuilt 4,999→6,620 asset-months / 99→130 tokens, 0
failures; A5 gate passed on all five priority tokens; 331/332 three-channel asset-months have
TVL (gap = SUSHI launch month). User set session to always-allow for autonomous overnight/day
operation; first ch2 launch stopped at user request (~100 calls burned, no checkpoints),
resumed next morning.

**2026-07-03 (local).** Entry 68 logged. Ch2 tail relaunched 14:57 UTC (fresh quota day,
DAILY_CAP=140k in-process so a mid-flight giant cannot pass the 180k stop-rule). Run completed
40/43 tokens at 141,005 getLogs (cap-stop after APE, exactly as designed; zero aborts). B2
scan on the 40: clean (worst on-chain/circ ratio 31× HAKKA, legit Entry-49 band; 0 nulled).
B4: big-token medians 13–48% bounded. XAN median-0 investigated → age artifact (launch
mid-2025; real 74–77% once lots can exceed 6m), coherent with the non-custodial XanV1 lock.
Final 3 (ZRX/COMP/UNI) scheduled via a sleep-until-00:05-UTC background job.

**2026-07-04 (UTC).** ZRX/COMP/UNI built on the fresh quota day (41,871 calls; UNI 8.3M
transfers, the largest of the tail). Aggregate → 260 tokens / 7,823 rows. λ re-assembled:
**6,021 → 7,051 asset-months / 282 assets; n_channels 1/2/3 = 5,331/1,388/332; 2+ share
11.0% → 24.4%.** Entries 69–70 logged; `SESSION027_TVL_AND_CH2_REPORT.md` written; time log +
memory updated; commit + push.

## Key decisions (all logged in DATA_DECISIONS_LOG Entries 68–70)
1. Parent-protocol slugs as the canonical TVL denominator for multi-version protocols.
2. Chain-level TVL (`chain:` prefix) for canonical L2 governance tokens; coins never get TVL.
3. Treasury/Foundation/CEX/bridge slugs kept OUT of the denominator (OP/MNT foundations, ZORA
   bridge, GBYTE third-party DEX, PENGU).
4. Rejection list logged (NEST ambiguous parents, POWER/M0 unconfirmable, CVP re-rejected,
   WLFI no series) so future sessions don't re-try them.
5. Ch2 engine + guard thresholds untouched; the 43-token tail accepted into λ; XAN flagged
   as an age artifact, not excluded; HEX never attempted (Entry 66 permanent deferral).
6. Budget discipline: in-process cap set BELOW the stop-rule so mid-flight overshoot is
   bounded; two quota days used (141,005 + 41,871 = 182,876 getLogs), both with headroom.

## Artifacts
- `03_data/phase1/asset_onchain_identity.csv` (+23 slugs, XVS fix, ZORA revert)
- `04_code/phase2_build_tvl_panel.py` (OTHER_ADDS, CHAIN_LEVEL, fetch_chain)
- `03_data/phase2/tvl_panel.csv` + `tvl_panel_coverage.csv` (6,620 asset-months / 130 tokens)
- `03_data/phase1/channel2_holding.csv` (260 tokens / 7,823 rows)
- `03_data/phase1/lambda_panel.csv` (7,051 asset-months / 282 assets)
- `04_code/DATA_DECISIONS_LOG.md` Entries 68–70
- `03_data/SESSION027_TVL_AND_CH2_REPORT.md`
- 43 new per-token checkpoints under `03_data/raw/phase1_onchain/holding/`
