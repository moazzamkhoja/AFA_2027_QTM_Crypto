# Claude Code Session 032 — MYX ch2 build

**Date:** 2026-07-24 (overnight run)
**Etherscan Pro key:** `04_code/.api_keys.json` under `"etherscan"`

---

## Context

MYX (36410) is the last remaining token from the session 029 Task-A list. It was aborted in
session 030 at batch 81/128 (tf=15.4M, ~10h from finishing) due to user departure. It was
NOT started in session 031 (reserved for a dedicated day). No checkpoint exists — clean start.

**Starting state (post-031):**
- λ: 9,638 asset-months / 341 assets; regression-ready 142 (coins 20, tokens/other 122)
  *(Note: coverage_status.csv may show 153 complete — coin count includes PoW coins tagged
  complete; functionally 20 PoS coins with λ∩NVT_GL)*
- `03_data/phase1/channel2_holding.csv`: 306 tokens / 9,857 rows
- Engine: `04_code/phase1_channel2_stream.py` — DO NOT change guard thresholds
  (VAL_CAP_MULT = CONTAM_MULT = 100) or the `from == to` self-transfer skip.

**BEFORE STARTING:** Pause Windows Update (Settings → Windows Update → Pause for 7 days).
Sleep/hibernate is already set to Never from the session 031 powercfg fix.

---

## Task — Build MYX

```
WORKLIST=36410 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

| cmc_id | symbol | chain | chainid | address | DL slug |
|--------|--------|-------|---------|---------|---------|
| 36410 | MYX | BSC | 56 | `0xd82544bf0dfe8385ef8fa34d67e6e4940cc63e16` | myx-finance |

**Budget: ~250–300k getLogs calls / ~12–15h wall-clock.**

### Expected behavior during the run

- Session 030 observed tf=15.4M by batch 81/128; expect >20M total (MBOX-record class).
- **Expect a MULTI-HOUR SILENT stretch after batch ~61** (BSC blocks ≥49M = the Aug-2025
  MYX launch region; the engine binary-splits densely there and prints only every 5 batches).
  This is NOT a hang. Verify liveness via CPU accrual or active network connections.
  Do not kill it unless CPU is idle AND no established connections for several minutes.
- The API has shown no hard daily-cap rejection at these volumes (Entry 76/80: evidently
  credit-based). Run until completion.

---

## After MYX completes

### 1. B2 / B4 integrity checks
- B2: confirm no month exceeds the 100× contamination threshold.
- B4: confirm screened HODL-6m median is in [0, 80%]. Flag but do not suppress if outside.

### 2. Assemble
```
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

### 3. DATA_DECISIONS_LOG — Entry 82

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 82 — Session 032: MYX (36410/BSC) ch2 BUILT; Task-A fully closed

MYX ch2 (HODL-wave): [getLogs actual] getLogs / [months built]/[observed window],
[screened months]. screened HODL-6m median [X]% / last [Y]%. B2: [max multiplier].
B4: [PASS/FLAG]. tf=[N]. Expect BSC mega-giant pattern (>20M transfers).
MYX has TVL (myx-finance, 27 months) → regression-ready on completion.
Post-assemble: λ [X] asset-months / [N] assets. Regression-ready: [N].
Session 029 Task A fully closed (all 47 targets resolved: 41 built, 5 non-EVM skipped,
1 WARP deferred for identity review).
```

### 4. Session report

Write `03_data/SESSION032_MYX_REPORT.md`:
- Token outcome table (same format as session 031 report)
- Anomalies (esp. if tf > 21.2M MBOX record)
- Post-assemble λ totals
- Quota used

### 5. Commit + push

```
git add -A
git commit -m "session 032: MYX ch2 built — Task-A fully closed"
git push
```
