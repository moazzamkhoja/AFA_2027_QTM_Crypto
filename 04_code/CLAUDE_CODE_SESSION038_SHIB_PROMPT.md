# Claude Code Session 038 — SHIB ch2 (EVM DeFi Breadth Batch 3b)

**Date:** 2026-07-27
**Etherscan Pro key:** `04_code/.api_keys.json` under `"etherscan"`

**Starting state (post-037):**
- λ: 13,449 asset-months / 462 assets; regression-ready 178 (coins 22, tokens/other 156)
- channel2_holding.csv: 423 tokens / 13,661 rows
- Engine unchanged: `04_code/phase1_channel2_stream.py`

**BEFORE STARTING:** Pause Windows Update. Sleep/hibernate set to Never.

---

## Task A — Build

```
WORKLIST=5994 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

| cmc_id | symbol | chain (chainid) | contract | est_getLogs | sector |
|--------|--------|-----------------|----------|-------------|--------|
| 5994 | SHIB | Ethereum (1) | 0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE | ~128k | Dexs;Meme |

**Estimate note:** sessions 034–036 ran 3–5× below holder-count estimates due to long
sparse pre-activity blocks. Expect actual getLogs ~25–35k; budget 2–4h not 10h+.
If actual getLogs exceeds 150k, stop and report — do not continue past the daily cap.

**Engine rules (unchanged):**
- VAL_CAP_MULT = CONTAM_MULT = 100 — do NOT change
- `from == to` self-transfer skip — do NOT remove
- B2: no month exceeds 100× contamination guard
- B4: flag but do not suppress if screened HODL-6m median > 80%

---

## Task B — TVL slug check

SHIB is a meme token with **no direct protocol TVL**. Do NOT assign a TVL slug.

The only DeFiLlama slug containing "shib" is `shibaswap` — the ShibaSwap DEX. That
protocol's governance token is **BONE** (cmc_id=11865), not SHIB. Assigning `shibaswap`
to SHIB would double-count the DEX TVL against the wrong token.

Document in the session report: "SHIB excluded from NV/TVL regression — meme token,
no direct protocol TVL. `shibaswap` slug belongs to BONE (cmc_id=11865), not SHIB."

SHIB is λ-only.

---

## Task C — Assemble and rebuild

```
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

Print new λ totals and regression-ready count. Regression-ready is NOT expected to
change (SHIB is λ-only).

---

## DATA_DECISIONS_LOG — Entry 89

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 89 — Session 038: SHIB ch2 built (λ-only; no TVL regression entry)

SHIB (5994/Ethereum): [N] getLogs / [tf] transfers / [scr] screened months.
B2 pass. B4 [pass/flag]. Actual getLogs vs 128k estimate: [ratio]x.

TVL: no protocol TVL for SHIB. `shibaswap` slug in tvl_panel belongs to BONE
(cmc_id=11865, ShibaSwap governance token) — assigning to SHIB would be wrong.
SHIB → λ-only.

Post-assemble: λ [X] asset-months / [N] assets. Regression-ready [178→N]
(no change expected).

EVM DeFi breadth complete (all batches 1–3b done). Next: Session 039 — DOT/KSM PQ
source probe; TRX coin_staking_type fix; WARP identity review.
```

---

## Session report

Write `03_data/SESSION038_SHIB_REPORT.md`:
- getLogs actual vs 128k estimate (note the overestimate ratio)
- transfers, screened months, B2/B4
- TVL decision with BONE/shibaswap disambiguation
- Post-assemble λ and regression-ready totals

---

## Commit

```
git add -A
git commit -m "session 038: SHIB ch2 built (λ-only; no TVL entry)"
git push
```
