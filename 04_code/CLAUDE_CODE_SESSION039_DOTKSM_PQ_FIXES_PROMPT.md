# Claude Code Session 039 — DOT/KSM PQ probe + TRX fix + WARP review

**Date:** 2026-07-28
**Keys in use:** `04_code/.api_keys.json` → `"subscan"`, `"etherscan"`

**Starting state (post-038):**
- λ: 13,510 asset-months / 463 assets; regression-ready 178 (coins 22, tokens/other 156)
- DOT (6636) + KSM (5034): ch1 BUILT (session 037), but pq_usd ALL NULL in
  nvt_gl_panel.csv — not yet regression-ready. Finding a PQ source for either
  would add 1–2 coins immediately.
- TRX (1958): mislabeled `pow_only` in coverage logic; DPoS, has 78 ch1 months.
- WARP (1166): ch2 built-but-empty (Entry 79 identity mismatch).

---

## Task A — DOT/KSM PQ source probe

DOT and KSM need annualized on-chain transfer volume in USD (pq_usd) to compute
NVT_GL. The goal here is to find a free source with multi-year history. Run probes
in order and stop at the first that returns usable data.

### A1: Subscan daily stats — "transfer" category (same key as ch1)

The session-037 pivot notes the `/api/scan/daily` endpoint returned
`history_window_exceeded` for the "Bonded" category (staking). The "transfer"
category may have a different (longer) history window. Probe it:

```python
import json, requests

key = json.loads(open("04_code/.api_keys.json").read())["subscan"]

# DOT probe — last 90 days of transfer data to check depth
r = requests.post(
    "https://polkadot.api.subscan.io/api/scan/daily",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"start": "2020-08-01", "end": "2026-06-30",
          "format": "month", "category": "transfer"}
)
print("DOT transfer status:", r.status_code)
d = r.json()
print(json.dumps(d, indent=2)[:1000])
```

Also try categories `"extrinsic"`, `"transaction"`, `"fee"`.

**If historical monthly transfer data returns (multi-year):** proceed to A2.
**If `history_window_exceeded`:** try A3.

### A2: Build DOT + KSM PQ series from Subscan daily stats

If Subscan returns usable monthly transfer amounts:

- Field to use: whichever of `transfer_amount`, `amount`, `volume_usd`, or
  similar contains native-token transfer volume (inspect the response keys).
- Convert to USD using `universe_panel.csv` price column for that month-end.
- Sum or take the month-end value as appropriate.
- Run for both `polkadot.api.subscan.io` and `kusama.api.subscan.io`.
- Output: append rows to `03_data/phase2/pq_coins.csv` and rebuild
  `03_data/phase2/nvt_gl_panel.csv` via `python 04_code/phase2_nvt_gl.py`.
- Cross-check: the resulting NVT_GL ratio for DOT/KSM should be broadly
  consistent with other L1 coins (typical range 10–200).

### A3: Polkadot archive RPC — enumerate transfer extrinsics (BLOCKED by Entry 31/32)

Raw multi-year block iteration is **FORBIDDEN** (Entry 31/32 rule). Do NOT attempt
to scan blocks one-by-one for transfer extrinsics. If Subscan daily stats fail,
move to A4.

### A4: Blockchair Polkadot/Kusama aggregation probe

Blockchair supports DOT and KSM natively (not EVM). Try the chain-level stats
and daily aggregation endpoints:

```python
# Current stats (free, keyless)
r_stats = requests.get("https://api.blockchair.com/polkadot/stats", timeout=20)
print("Blockchair DOT stats:", r_stats.status_code, r_stats.text[:500])

# Daily aggregated transfer volume (the same endpoint that failed for XTZ/MATIC
# in session 034 — but Polkadot may be implemented differently)
r_agg = requests.get(
    "https://api.blockchair.com/polkadot/calls",
    params={"a": "date(time),sum(value)", "q": "type(transfer)"},
    timeout=30
)
print("Blockchair DOT aggregation:", r_agg.status_code, r_agg.text[:500])
```

**If aggregation returns multi-year daily/monthly data:** parse it, convert to USD,
append to pq_coins.csv, rebuild NVT_GL panel.

**If 404 or blocked:** note it, log CORE result in Entry 90 as "DOT/KSM PQ
no free source found — candidates exhausted, Blockchair paid tier or
Subscan Pro required", and continue to Task B.

---

## Task B — TRX coin_staking_type fix

TRX (cmc_id=1958) is classified `pow_only` in `universe_coverage_status.csv` but
TRON uses DPoS (Delegated Proof of Stake) and has 78 ch1 staking months already built.
This mislabel makes the coin count in coverage reports inaccurate.

Find where `coin_staking_type` is set. It is likely either:
1. A column in `03_data/universe_panel.csv` (or a static metadata file)
2. Computed inline in `04_code/build_coverage_status.py`

```python
import subprocess
result = subprocess.run(
    ["grep", "-rn", "pow_only\|coin_staking_type\|1958", "04_code/", "--include=*.py"],
    capture_output=True, text=True
)
print(result.stdout)
```

Once found, change TRX's entry from `pow_only` to `pos` (DPoS is a PoS variant).
Re-run `python 04_code/build_coverage_status.py` and confirm:
- TRX moves from the PoW bucket to PoS
- Regression-ready coin count is consistent with 22 (TRX already has both ch1
  and NVT_GL, so fixing the label may shift it from "partial" to "complete")

**Important:** do NOT change any logic that affects whether TRX's ch1 data is
used in the lambda panel — that data is already correctly included. This is a
metadata label fix only.

---

## Task C — WARP identity review

WARP (cmc_id=1166) has a ch2 checkpoint but all months are "pre-history" (zero
transfers in every observed month) because the stored contract address
(`0x83e6f1E41cdd28eAcEB20Cb649155049Fac3D5Aa` or similar) postdates the CMC
listing's active window (2016..2018-02).

Check:
```python
import json
from pathlib import Path

# Find the WARP checkpoint
ck_files = list(Path("03_data/raw/phase1_ch2").glob("1166_*.json"))
print("WARP checkpoints:", ck_files)
if ck_files:
    ck = json.loads(ck_files[0].read_text())
    print("address:", ck.get("address"))
    print("chainid:", ck.get("chainid"))
    print("n_transfers:", ck.get("n_transfers"))
    print("months with data:", [m for m, v in ck.get("monthly", {}).items() if v.get("screened_hodl_6m") is not None])
```

Then look up cmc_id=1166 on CoinMarketCap (via web or the universe panel) to
confirm what "WARP" actually is:
- If the listing refers to a pre-2018 dead project that never deployed an
  ERC-20 token, close as **permanent identity mismatch** — no usable data possible.
- If the listing refers to a live project with a different contract address,
  update the identity mapping and rebuild.

In either case: document the decision in Entry 90 and update coverage status
to `not_started` (if dead/mismatch) or trigger a rebuild (if remapped).

---

## DATA_DECISIONS_LOG — Entry 90

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 90 — Session 039: DOT/KSM PQ probe; TRX label fix; WARP review

**DOT/KSM PQ probe:**
Subscan /api/scan/daily category=transfer: [result — returned/history_exceeded/error].
Blockchair polkadot/calls aggregation: [result — returned/404/blocked].
Decision: [BUILT: append to pq_coins + rebuild NVT_GL → coins +2 regression-ready]
          [or: no free PQ source found; Subscan Pro or Blockchair paid required]

**TRX (1958) coin_staking_type fix:**
Label was pow_only; corrected to pos (DPoS, has ch1 78 months).
Source of label: [file/line]. build_coverage_status.py re-run.
TRX coverage status: [partial→complete if NVT_GL present, else unchanged].

**WARP (1166) identity review:**
Contract [address]. Observed window [dates]. Transfer count [N].
Decision: [permanent identity mismatch, closed as not_started]
          [or: remapped to [new address], rebuild triggered].

Post-assemble: λ [X] / [N] assets. Regression-ready [178→N].
```

---

## Session report

Write `03_data/SESSION039_DOTKSM_PQ_FIXES_REPORT.md`:
- DOT/KSM probe: exact endpoints tried, response content (first 200 chars), verdict
- TRX fix: where the label lived, what changed, new coverage counts
- WARP: checkpoint address, transfer count, identity verdict
- Post-assemble totals

---

## Commit

```
git add -A
git commit -m "session 039: DOT/KSM PQ probe; TRX staking-type fix; WARP identity review"
git push
```
