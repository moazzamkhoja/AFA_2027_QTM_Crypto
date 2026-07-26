# Claude Code Session 036 — EVM DeFi Breadth Batch 3a: stETH + MEME

**Date:** 2026-07-25
**Etherscan Pro key:** `04_code/.api_keys.json` under `"etherscan"`

**Starting state (post-035):**
- λ: 13,191 asset-months / 457 assets; regression-ready 177 (coins 21, tokens/other 156)
- channel2_holding.csv: 421 tokens / 13,580 rows
- Engine unchanged: `04_code/phase1_channel2_stream.py`

**BEFORE STARTING:** Pause Windows Update. Sleep/hibernate already set to Never.

---

## Task A — Build

```
WORKLIST=8085,28301 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

| cmc_id | symbol | chain (chainid) | est_getLogs | sector |
|--------|--------|-----------------|-------------|--------|
| 8085 | stETH | Ethereum (1) | ~49k | Liquid Staking;Restaking |
| 28301 | MEME | Ethereum (1) | ~61k | Dexs;Farm;NFT;Meme |

Total estimate: ~110k getLogs, well under the 185k daily cap.
Expected runtime: 4–8h.

**Engine rules (unchanged):**
- VAL_CAP_MULT = CONTAM_MULT = 100 — do NOT change
- `from == to` self-transfer skip — do NOT remove
- B2: no month exceeds 100x contamination guard
- B4: flag but do not suppress if screened HODL-6m median > 80%

---

## Task B — TVL slug check

### stETH (8085)
stETH IS the Lido liquid staking receipt token. Its market cap ≈ the ETH staked in
Lido by construction — **NV/TVL is circular** (same rule as wstETH, weETH, cbETH,
rETH excluded in session 034). Do NOT assign a TVL slug.

Document in the session report: "stETH excluded from NV/TVL regression (LST receipt
circularity — NV≈TVL by construction, Entry 84 rule). λ months retained for the
conviction-only analysis."

The correct Lido TVL slug (`lido`) is already referenced by other tokens if applicable.
Do not create a stETH → lido mapping.

### MEME (28301)
Check DeFiLlama: `https://api.llama.fi/protocols` — search for `MEME` by symbol and
by any known contract address. Expect no match (no dedicated protocol TVL for a
meme/farm token). If a match is found, verify it is not a coincidental symbol clash
before accepting.

---

## Task C — Assemble and rebuild

```
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

Print new λ totals and regression-ready count. Regression-ready is NOT expected to
change (both tokens are λ-only adds due to TVL circularity/no-match).

---

## DATA_DECISIONS_LOG — Entry 86

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 86 — Session 036: stETH + MEME ch2 built (λ-only; no TVL regression entry)

stETH (8085/Ethereum): [N] getLogs / [tf] transfers / [scr] screened months.
B2 pass. B4 [pass/flag]. TVL excluded: LST receipt circularity (NV≈Lido TVL by
construction, Entry 84 rule). λ months retained for conviction-only panel.

MEME (28301/Ethereum): [N] getLogs / [tf] transfers / [scr] screened months.
B2 pass. B4 [pass/flag]. TVL: no DeFiLlama protocol match confirmed.

Post-assemble: λ [X] asset-months / [N] assets. Regression-ready [177→N] (no change
expected).

Remaining EVM breadth: Session 037 — SHIB (5994), ~128k getLogs, λ-only.
```

---

## Session report

Write `03_data/SESSION036_BATCH3A_REPORT.md`:
- Per-token: getLogs actual, transfers, screened months, B2/B4, TVL decision
- Post-assemble λ and regression-ready totals
- Note: regression-ready unchanged; next count movement requires user actions
  (Subscan key → DOT/KSM, CORE key, Cosmos key)

---

## Commit

```
git add -A
git commit -m "session 036: stETH + MEME ch2 built (λ-only; no TVL entry)"
git push
```
