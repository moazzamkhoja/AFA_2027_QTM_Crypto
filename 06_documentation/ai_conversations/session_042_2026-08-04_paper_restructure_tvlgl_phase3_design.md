# Session 042 — 2026-08-04 — Cowork (Fable 5): Paper restructure, TVL*, Phase 3 design

## What happened
1. **Full paper restructure** (continuing Moazzam's rewrite request from session 041.5):
   Theory split into coin framework (QTM -> SoV/MoE -> lambda/(1-lambda), H1a) and token
   framework (no MoE -> governance moat / costly signaling, H1b), common valuation
   conditioning (H2) and quadrant (H3). New Section 3 "Variable Construction" (lambda
   3-channel composite, NVT_GL, NV/TVL). Data section rebuilt: sources -> sample funnel
   -> summary stats.
2. **Introduction restored**: Moazzam rejected the rewritten intro ("starts with a boring
   difference between coins and tokens"). Restored the original progression (motivation /
   DCF critique -> QTM -> SoV+MoE definitions -> lambda extension -> coin channels) from
   commit 5d4c575 with MINOR changes only: token paragraph now states the MoE denominator
   is absent so SoV/MoE is undefined and lambda conveys conviction directly; final
   paragraph gives two metrics per asset type. Abstract restored similarly.
3. **Growth-adjusted TVL** (Moazzam: "otherwise we will miss growth metric completely"):
   built phase2_tvl_gl.py -> nv_tvl_gl_panel.csv. TVL* = same DCF machinery/PARAMS as
   PQ*; TVL0 = trailing-12m mean level. 111 assets/3,125 mo; token regression sample now
   101/2,771 (2021-01..2026-05); combined 125/3,489, $451B = 19.0% of universe at 2026-05.
   Caveat: 44.6% of months hit the g cap (mostly -50% floor). Entry 93.
4. **Data 4.2 funnel**: new Table 1 walking 1,939 -> minus 858 other -> coin track
   633 -> 24 (minus 323 PoW, 24 unverifiable, 256 no staking archive, 6 no PQ overlap)
   and token track 448 -> 101 (minus 299 no TVL, 3 no lambda, 45 short TVL history).
   POL reconciled (coverage file said 'unknown', actually PoS). Summary stats now Table 2.
5. **Bibliography**: fabricated entries dao2024governance + daoreview2025 removed
   (long-standing task #22); bianchi2022 undefined citation fixed.
6. **Phase 3 design** (Moazzam's 3-element plan): (1) H1/H2 FE panel regressions;
   (2) H3 Stars-minus-Avoid vs monthly LTW (2022 JF) factor analogs built from our own
   universe; (3) horse race vs raw NVT, Metcalfe (BitInfoCharts AA build), MVRV
   (checkpoint probe only — Etherscan lapsed), S2F, technicals. Spec:
   04_code/PHASE3_ANALYSIS_SPECIFICATION.md; kickoff:
   04_code/CLAUDE_CODE_PHASE3_KICKOFF_PROMPT.md. Entry 94.

## Ops incident resolved
Git commits kept failing with stale .lock files. Root cause: Cowork sandbox may create/
write but NOT delete files in the mounted folder by default; git cannot remove its own
lock files. Fixed by granting the folder delete permission (mcp allow_cowork_file_delete).
One collateral commit (39f43b1) briefly recorded phase2_tvl_gl.py + nv_tvl_gl_panel.csv
as deleted due to a stale index from the workaround period; amended to 9308322 with both
files verified tracked at HEAD.

## Open items
- Moazzam still unsatisfied with the introduction; deliberately deferred until empirical
  results exist ("no use changing it until we have empirical tests").
- Phase 3 core session (Tasks A-D) ready to launch; Phase 3b horse race after.
- g-cap sensitivity for NV/TVL_GL queued in Phase 3 robustness.

## Commits
687d724 (intro restore), 2b9ac26 (TVL*), 9308322 (funnel), + record-keeping commit.

## Addendum — same Cowork conversation, continued through the full Phase 3/3b/3c cycle

After the Phase 3 design was committed, this conversation continued through: results
review of sessions 043/044/045 (findings review docx + paper-style tables docx);
exploratory token quintile sorts (Entry 97) and size-as-delta test (Entry 108, run
inline); Phase 3b design + kickoff (Entries 98-99, M1-M4 mechanism framework into
paper Section 2.3); DCF misattribution fix + P/F comparator (Entry 107); Phase 3c
kickoff incl. technical battery completion (Entries 109-110); full results written
into the paper after each results report (Entries 106, 115, 116); H3 re-run under
alternative valuation axes (inline, phase3_explore_h3_altval.py — null everywhere);
float-placement fix (placeins); Section 7 Summary of Findings with scorecard table.
Paper stands at 45 pp with 13 tables, all hypotheses + extension + horse race +
mechanisms written up, awaiting Moazzam's pruning review.

## State at close (2026-08-04 evening)
- Paper: complete draft, all results in. NEXT: Moazzam reads and decides table
  pruning (candidates: pooled specs, delta-lambda nulls, Metcalfe + per-sector nulls
  to appendix); intro rework deferred until after pruning.
- Open tasks: bibliography final pass (old task 22, largely done via entry removals);
  push to GitHub (many local commits pending — commit_and_push.bat).
- Data/infra: Etherscan lapsed; delete permission enabled for the folder; git works
  normally from Cowork now.
