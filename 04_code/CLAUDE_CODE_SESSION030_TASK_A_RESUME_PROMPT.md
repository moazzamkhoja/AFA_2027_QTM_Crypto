# Claude Code Session 030 — Task A Resume: 7 Remaining ch2 Tokens

**Date:** 2026-07-05  
**Estimated getLogs calls:** ~30–45k (well within one quota day)  
**Etherscan Pro key:** in `04_code/.api_keys.json` under `"etherscan"`  

---

## Context

Session 029 built ch2 (HODL-wave) for 40 of 47 non-lambda EVM tokens that already have TVL.
Seven tokens hit the daily quota boundary before completion. Checkpoints are intact — this
session is a zero-loss resume. No methodology changes, no new chains, no new engines.

**Starting state (post-029 assembler):**
- λ: 9,580 asset-months / 337 assets
- regression-ready: 138 (coins 20, tokens 118)
- `03_data/phase1/channel2_holding.csv`: 300 tokens

**After this session completes:** ~307 tokens in channel2_holding.csv; 7 new λ assets;
regression-ready should reach ~145 (all 7 have TVL).

---

## Files to read before starting

- `04_code/phase1_channel2_stream.py` — the multi-chain streaming engine (validated in
  sessions 025–029; multi-chain `--chainid` support added in session 029). **Do not change
  guard thresholds (VAL_CAP_MULT = CONTAM_MULT = 100). Do not remove the `from == to`
  self-transfer skip (added session 028, engine-wide).**
- `03_data/phase1/channel2_holding.csv` — current ch2 panel (check which of the 7 have
  any checkpoint; skip any already complete).
- `03_data/phase2/tvl_panel.csv` — TVL panel (all 7 have TVL; no changes needed here).
- `03_data/phase1/lambda_panel.csv` — current λ panel (post-029).
- `04_code/phase1_assemble_lambda.py` — assembler (run after all 7 are built).

---

## Task — Build the 7 remaining tokens

Build in the order below (smallest est_getlogs_calls first within each chain; RAIN last).
Load checkpoints and skip any token already completed (check channel2_holding.csv).

### BSC (chainid 56)

| cmc_id | symbol | address | DL slug | est_getLogs |
|--------|--------|---------|---------|-------------|
| 8972 | SFUND | `0x477bc8d23c634c154061869478bce96be6045d12` | seedify | ~4k |
| 36410 | MYX | `0xd82544bf0dfe8385ef8fa34d67e6e4940cc63e16` | myx-finance | ~4k |

### Polygon (chainid 137)

| cmc_id | symbol | address | DL slug | est_getLogs |
|--------|--------|---------|---------|-------------|
| 24796 | ADF | `0x6BD10299f4f1d31b3489Dc369eA958712d27c81b` | artdefinance | 1,871 |

### Base (chainid 8453)

| cmc_id | symbol | address | DL slug | est_getLogs |
|--------|--------|---------|---------|-------------|
| 38299 | AVNT | `0x696f9436b67233384889472cd7cd58a6fb5df4f1` | avantis | ~4k |
| 35763 | KAITO | `0x98d0baa52b2d063e780de12f615f963fe8537553` | kaito | ~3k |
| 35509 | VVV | `0xacfe6019ed1a7dc6f7b508c02d1b04ec88cc21bf` | venice | ~1k |

### Arbitrum (chainid 42161) — build last

| cmc_id | symbol | address | DL slug | est_getLogs |
|--------|--------|---------|---------|-------------|
| 38341 | RAIN | `0x25118290e6A5f4139381D072181157035864099d` | rain | 13,637 |

All four chains (BSC, Polygon, Base, Arbitrum) were verified live in session 029 and return
proper log lists via Etherscan Pro V2 (`?chainid=<id>`). No re-verification needed.

---

## Build protocol

1. For each token, invoke `phase1_channel2_stream.py` with the correct `--chainid` and
   `--address`. The script loads its checkpoint automatically.
2. Apply the standard B2/B4 integrity checks on each completed series:
   - **B2:** no month above the 100× contamination threshold.
   - **B4:** screened HODL-6m in [0, 80%]; flag but do not suppress values outside that
     range (document reason).
3. After all 7 are built, run the assembler (`phase1_assemble_lambda.py`) to regenerate
   `lambda_panel.csv`.
4. Run `04_code/build_coverage_status.py` to regenerate `universe_coverage_status.csv`.

---

## DATA_DECISIONS_LOG entry (Entry 80)

After the build and assemble, append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 80 — Session 030: Task-A resume — 7 remaining ch2 tokens BUILT; λ close-out

Resume of session 029's Task A. Tokens built: SFUND (8972/BSC), MYX (36410/BSC),
ADF (24796/Polygon), AVNT (38299/Base), KAITO (35763/Base), VVV (35509/Base),
RAIN (38341/Arbitrum). [Fill in actual getLogs calls, any anomalies, screened HODL-6m
medians, and whether each passed B2/B4.] All 7 have TVL in tvl_panel.csv → all are
regression-ready immediately. Post-assemble λ: [fill]. Regression-ready: [fill].
```

---

## Session report

Write `03_data/SESSION030_TASK_A_RESUME_REPORT.md` covering:
- Per-token outcome table (symbol | cmc_id | chain | getLogs calls | months built |
  screened HODL-6m | B2/B4 pass | notes)
- Any anomalies (hidden giants, empty series, contamination)
- Post-assemble λ totals (asset-months / assets / regression-ready)
- Quota used

---

## Commit

At session end, commit and push all new/modified files:
- `03_data/phase1/channel2_holding.csv`
- `03_data/phase1/lambda_panel.csv`
- `03_data/universe_coverage_status.csv`
- `04_code/DATA_DECISIONS_LOG.md`
- `03_data/SESSION030_TASK_A_RESUME_REPORT.md`
- Any checkpoint files under `03_data/raw/phase1_onchain/`

Commit message: `session 030: ch2 Task-A resume — 7 tokens built (SFUND/MYX/ADF/AVNT/KAITO/VVV/RAIN)`
