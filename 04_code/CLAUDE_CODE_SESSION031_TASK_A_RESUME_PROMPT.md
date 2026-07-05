# Claude Code Session 031 — Task A Resume: 6 Remaining ch2 Tokens (small-first; MYX gets its own day)

**Planned date:** Monday 2026-07-13 (user back from a week away)
**Etherscan Pro key:** in `04_code/.api_keys.json` under `"etherscan"`
**Predecessor:** session 030 (Entry 80, `03_data/SESSION030_TASK_A_RESUME_REPORT.md`) — SFUND built; MYX aborted mid-build with NO checkpoint; 5 tokens untouched.

---

## Context

Session 030 built SFUND (28,553 getLogs — 7x its estimate) and had to kill MYX at user
departure after ~120k calls (batch 81/128, tf=15.4M, ~10h from finishing). The streamed
engine keeps no partial checkpoint, so MYX restarts from scratch.

**Starting state (post-030, commit pushed 2026-07-05):**
- λ: 9,603 asset-months / 338 assets; regression-ready 139 (coins 20, tokens/other 119)
- `03_data/phase1/channel2_holding.csv`: 301 tokens / 9,817 rows
- Engine unchanged: `04_code/phase1_channel2_stream.py` (do NOT touch VAL_CAP_MULT =
  CONTAM_MULT = 100; keep the `from == to` self-transfer skip)

**LESSON FROM 029/030 (Entry 80): holder-count estimates undershoot BSC 7–30x.
Build small chains FIRST, BSC LAST, and give MYX a dedicated quota day.**

---

## Day 1 — the 5 small tokens (~25–30k est, treat as lower bound)

```
WORKLIST=24796,35509,35763,38299,38341 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

| order | cmc_id | symbol | chain (chainid) | address | DL slug | est_getLogs |
|-------|--------|--------|-----------------|---------|---------|-------------|
| 1 | 24796 | ADF | Polygon (137) | `0x6BD10299f4f1d31b3489Dc369eA958712d27c81b` | artdefinance | 1,871 |
| 2 | 35509 | VVV | Base (8453) | `0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf` | venice | ~1k |
| 3 | 35763 | KAITO | Base (8453) | `0x98d0baa52b2d063e780de12f615f963fe8537553` | kaito | ~3k |
| 4 | 38299 | AVNT | Base (8453) | `0x696f9436b67233384889472cd7cd58a6fb5df4f1` | avantis | ~4k |
| 5 | 38341 | RAIN | Arbitrum (42161) | `0x25118290e6A5f4139381D072181157035864099d` | rain | 13,637 |

The engine auto-skips any token whose checkpoint already exists. All 5 have TVL in
`03_data/phase2/tvl_panel.csv` → regression-ready on completion.

## Day 2 (or whenever day-1 quota allows) — MYX alone

```
WORKLIST=36410 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

- MYX (36410) BSC `0xd82544bf0dfe8385ef8fa34d67e6e4940cc63e16`, DL slug myx-finance.
- **Budget ~250–300k calls and ~12–15h wall-clock.** Session 030 observed tf=15.4M by
  batch 81/128; expect >20M total (MBOX-record class).
- Expect a MULTI-HOUR SILENT stretch after batch ~61 (blocks ≥49M = the Aug-2025 launch
  region; the engine prints every 5 batches and binary-splits densely there). Verify
  liveness via CPU accrual / established connections, not log freshness.
- Start it EARLY in the day. Do not kill it unless truly hung (no CPU accrual AND no
  established connections over several minutes).

---

## Build protocol (unchanged)

1. B2: no month above the 100x contamination guard. B4: screened HODL-6m in [0, 80%];
   flag but don't suppress (document).
2. After all builds: `python 04_code/phase1_assemble_lambda.py`, then
   `python 04_code/build_coverage_status.py`.
3. Append Entry 81 to `04_code/DATA_DECISIONS_LOG.md` (per-token gl/months/medians/B2-B4,
   post-assemble λ and regression-ready).
4. Write `03_data/SESSION031_TASK_A_RESUME_REPORT.md` (same table format as the 030 report).
5. Commit + push at session end:
   `session 031: ch2 Task-A close-out — <N> tokens built (<symbols>)`

**After this completes:** ch2 panel ~307 tokens; regression-ready ~145; session 029's
Entry-79 open items (b)–(g) — DOT/KSM key, CHZ anchor, CORE key, WARP review, non-TVL
breadth, MATIC NVT probe — are then the queue.
