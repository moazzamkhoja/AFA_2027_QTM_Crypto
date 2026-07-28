# Claude Code Session 040 — CRO / INJ / KAVA / SEI ch1 via Cosmos Archive LCD

**Date:** 2026-07-28
**Keys in use:** none — approach is free and keyless
**API keys file:** `04_code/.api_keys.json` (not needed for this session)

**Starting state (post-039):**
- λ: 13,510 asset-months / 463 assets; regression-ready 178 (coins 22, tokens/other 156)
- All four target chains have NVT_GL (pq_usd non-null) but zero ch1 lambda months
- Building ch1 for all four immediately makes them regression-ready → expected 178 → 182
- Output file naming convention: `03_data/phase1/channel1_cosmos_lcd.csv`
  (same schema as `channel1_dot_ksm.csv`: cmc_id, symbol, month_end, staked_native,
  circulating_supply, staking_ratio, source, flag)

---

## Chain registry

| cmc_id | symbol | Cosmos chain | denom | decimals | genesis (approx) | blocks/day |
|--------|--------|--------------|-------|----------|-----------------|------------|
| 3635 | CRO | crypto-org-chain-mainnet-1 | basecro | **8** | 2021-03-25 | ~14,400 (~6s/block) |
| 7226 | INJ | injective-1 | inj | **18** | 2021-11-08 | ~28,800 (~3s/block) |
| 4846 | KAVA | kava_2222-10 | ukava | **6** | 2019-11-15 | ~14,400 (~6s/block) |
| 23149 | SEI | pacific-1 | usei | **6** | 2023-08-15 | ~216,000 (~0.4s/block) |

**CRO decimal warning:** CRO uses 8 decimals (`basecro`), NOT 6. Do NOT divide by 10^6.
**INJ decimal warning:** INJ uses 18 decimals, same as Ethereum ERC-20 native wei.

---

## Task A — Probe: find an archive-capable LCD for each chain

For each chain, test the LCD candidates in the order listed below. Stop at the first one
that passes BOTH the liveness check and the archive depth test.

### Candidate LCD endpoints (try in this order)

```python
CHAIN_CONFIG = {
    "CRO": {
        "cmc_id": 3635,
        "symbol": "CRO",
        "denom": "basecro",
        "decimals": 8,
        "lcd_candidates": [
            "https://rest.crypto.org",
            "https://api-cryptoorgchain-ia.cosmosia.notional.ventures",
            "https://rest.cosmos.directory/cryptoorgchain",
        ],
        "rpc": "https://rpc.crypto.org",
        "genesis_date": "2021-03-25",
        "blocks_per_day": 14400,
    },
    "INJ": {
        "cmc_id": 7226,
        "symbol": "INJ",
        "denom": "inj",
        "decimals": 18,
        "lcd_candidates": [
            "https://sentry.lcd.injective.network",
            "https://injective-api.polkachu.com",
            "https://rest.cosmos.directory/injective",
        ],
        "rpc": "https://sentry.tm.injective.network",
        "genesis_date": "2021-11-08",
        "blocks_per_day": 28800,
    },
    "KAVA": {
        "cmc_id": 4846,
        "symbol": "KAVA",
        "denom": "ukava",
        "decimals": 6,
        "lcd_candidates": [
            "https://api.kava.io",
            "https://kava-api.polkachu.com",
            "https://rest.cosmos.directory/kava",
        ],
        "rpc": "https://rpc.kava.io",
        "genesis_date": "2019-11-15",
        "blocks_per_day": 14400,
    },
    "SEI": {
        "cmc_id": 23149,
        "symbol": "SEI",
        "denom": "usei",
        "decimals": 6,
        "lcd_candidates": [
            "https://rest.sei-apis.com",
            "https://sei-api.polkachu.com",
            "https://rest.cosmos.directory/sei",
        ],
        "rpc": "https://rpc.sei-apis.com",
        "genesis_date": "2023-08-15",
        "blocks_per_day": 216000,
    },
}
```

### Probe script

```python
import requests, json, time
from datetime import datetime, timezone

def probe_chain(sym, cfg, timeout=20):
    """Try each LCD candidate. Return (lcd_url, latest_height) for first archive-capable node."""
    for lcd in cfg["lcd_candidates"]:
        # Step 1: liveness check — current pool
        try:
            r = requests.get(f"{lcd}/cosmos/staking/v1beta1/pool", timeout=timeout)
            if not r.ok:
                print(f"  {lcd} pool: {r.status_code} — skip")
                continue
            live_bonded = r.json()["pool"]["bonded_tokens"]
            print(f"  {lcd} LIVE — bonded={live_bonded[:20]}...")
        except Exception as e:
            print(f"  {lcd} UNREACHABLE: {e}")
            continue

        # Step 2: get latest block height
        try:
            rb = requests.get(
                f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=timeout
            )
            latest_height = int(rb.json()["block"]["header"]["height"])
            print(f"  {lcd} latest height={latest_height}")
        except Exception as e:
            print(f"  {lcd} cannot read latest block: {e}")
            continue

        # Step 3: archive depth test — probe block ~365 days ago
        old_height = max(1, latest_height - cfg["blocks_per_day"] * 365)
        try:
            ra = requests.get(
                f"{lcd}/cosmos/staking/v1beta1/pool",
                headers={"x-cosmos-block-height": str(old_height)},
                timeout=timeout,
            )
            if ra.ok:
                bonded_old = ra.json()["pool"]["bonded_tokens"]
                print(f"  {lcd} ARCHIVE OK @ height {old_height}: bonded={bonded_old[:20]}...")
                return lcd, latest_height
            else:
                print(f"  {lcd} archive probe FAILED @ {old_height}: {ra.status_code} {ra.text[:80]}")
        except Exception as e:
            print(f"  {lcd} archive probe error: {e}")
        time.sleep(0.5)

    return None, None  # no archive node found

for sym, cfg in CHAIN_CONFIG.items():
    print(f"\n=== {sym} ===")
    lcd, height = probe_chain(sym, cfg)
    if lcd:
        print(f"  --> USE: {lcd} (latest height {height})")
    else:
        print(f"  --> NO ARCHIVE NODE FOUND for {sym}")
```

**If no archive node found for a chain:** document in Entry 91 and skip that chain.
The remaining chains with archive nodes proceed to Task B.

---

## Task B — Binary search for month-end blocks

For each chain with a confirmed archive LCD, find the block height at the last moment
of each month-end date within the observed window (from `universe_panel.csv`).

```python
import pandas as pd
from datetime import datetime, timezone, timedelta
import calendar

def parse_block_time(lcd, height, timeout=15):
    """Return UTC datetime for block at given height."""
    r = requests.get(
        f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/{height}",
        timeout=timeout
    )
    t_str = r.json()["block"]["header"]["time"]
    # RFC3339 with nanoseconds: "2021-03-31T23:45:12.345678901Z"
    # Truncate nanoseconds to microseconds for fromisoformat compatibility
    t_str = t_str[:26].rstrip('Z') + '+00:00'
    return datetime.fromisoformat(t_str)

def find_month_end_block(lcd, year, month, lo, hi, timeout=15):
    """
    Binary search for the last block at or before the last second of month-end.
    lo, hi: known block heights bracketing the target.
    Returns (block_height, block_time_utc).
    """
    # Target: last second of the last day of the month
    last_day = calendar.monthrange(year, month)[1]
    target = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    while hi - lo > 1:
        mid = (lo + hi) // 2
        t = parse_block_time(lcd, mid, timeout)
        if t <= target:
            lo = mid
        else:
            hi = mid
        time.sleep(0.05)  # be gentle

    # Verify lo is at or before target, hi is after
    t_lo = parse_block_time(lcd, lo, timeout)
    return lo, t_lo

# Build month list for each chain
def get_observed_months(cmc_id):
    """Month-ends where universe_panel has an observed row for this asset."""
    panel = pd.read_csv("03_data/universe_panel.csv")
    rows = panel[(panel["cmc_id"] == cmc_id) & (panel["status"] == "observed")]
    months = sorted(rows["month_end"].str[:7].unique())
    return months  # list of "YYYY-MM" strings
```

**Efficiency:** binary search takes ~17 iterations per month-end (2^17 = 131,072 blocks).
At 0.05s per call, ~1 second per month. For 60 months → ~60s per chain. Acceptable.

Use the `latest_height` from Task A as the upper bound. Use `1` as the lower bound
(or the known genesis block if faster). If the genesis block postdates the first
observed month, skip months before genesis.

---

## Task C — Build the ch1 series

For each chain × each observed month:

```python
def build_chain_series(sym, cfg, lcd, latest_height):
    """Build staking series for one chain. Return list of row dicts."""
    cmc_id = cfg["cmc_id"]
    decimals = cfg["decimals"]
    denom = cfg["denom"]

    # Load circulating supply from universe panel
    panel = pd.read_csv("03_data/universe_panel.csv")
    panel_cid = panel[
        (panel["cmc_id"] == cmc_id) & panel["cmc_supply_circ"].notna()
    ][["month_end", "cmc_supply_circ"]].set_index("month_end")

    months = get_observed_months(cmc_id)
    from datetime import date
    import calendar

    rows = []
    lo = 1
    for ym in months:
        year, mon = int(ym[:4]), int(ym[5:7])
        # Skip months before chain genesis
        genesis = datetime.fromisoformat(cfg["genesis_date"]).replace(tzinfo=timezone.utc)
        last_day = calendar.monthrange(year, mon)[1]
        month_end_dt = datetime(year, mon, last_day, 23, 59, 59, tzinfo=timezone.utc)
        if month_end_dt < genesis:
            continue

        # Find month-end block via binary search
        block_h, block_t = find_month_end_block(lcd, year, mon, lo, latest_height)
        lo = block_h  # monotonic: next month's lo >= this month's block

        # Query pool at that block
        r = requests.get(
            f"{lcd}/cosmos/staking/v1beta1/pool",
            headers={"x-cosmos-block-height": str(block_h)},
            timeout=20,
        )
        if not r.ok:
            print(f"  {sym} {ym}: pool query failed at height {block_h}: {r.status_code}")
            continue

        bonded_raw = int(r.json()["pool"]["bonded_tokens"])
        staked_native = bonded_raw / (10 ** decimals)

        # Circulating supply from panel
        month_end_str = f"{year}-{mon:02d}-{last_day:02d}"
        if month_end_str not in panel_cid.index:
            print(f"  {sym} {ym}: no circulating supply in panel — skip")
            continue
        circ = float(panel_cid.loc[month_end_str, "cmc_supply_circ"])
        staking_ratio = staked_native / circ if circ > 0 else None

        rows.append({
            "cmc_id": cmc_id,
            "symbol": sym,
            "month_end": month_end_str,
            "staked_native": round(staked_native, 4),
            "circulating_supply": round(circ, 4),
            "staking_ratio": round(staking_ratio, 6) if staking_ratio else None,
            "source": f"cosmos_lcd_pool@{block_h}",
            "flag": f"{denom} / 10^{decimals}; block_time={block_t.isoformat()[:19]}Z",
        })
        print(f"  {sym} {ym}: height={block_h}, staked={staked_native:,.0f}, ratio={staking_ratio:.4f}")

    return rows
```

Collect all rows from all chains that passed the archive probe. Write to output:

```python
import csv
from pathlib import Path

all_rows = []
for sym, cfg in CHAIN_CONFIG.items():
    # only process chains where probe succeeded
    if sym not in archive_confirmed:
        continue
    lcd, latest_height = archive_confirmed[sym]
    chain_rows = build_chain_series(sym, cfg, lcd, latest_height)
    all_rows.extend(chain_rows)
    print(f"\n{sym}: {len(chain_rows)} months built")

if all_rows:
    out_path = Path("03_data/phase1/channel1_cosmos_lcd.csv")
    df_out = pd.DataFrame(all_rows)
    df_out.to_csv(out_path, index=False)
    print(f"\nWrote {len(df_out)} rows to {out_path}")
    print(df_out.groupby("symbol")[["month_end", "staking_ratio"]].agg(
        {"month_end": ["count", "min", "max"], "staking_ratio": "mean"}
    ))
```

---

## Task D — Cross-check (Entry-26 standard)

For each chain built, compare the latest month's `staked_native` against the live
current pool endpoint (no height header — returns the present-day value):

```python
for sym, cfg in CHAIN_CONFIG.items():
    if sym not in archive_confirmed:
        continue
    lcd = archive_confirmed[sym][0]
    decimals = cfg["decimals"]

    # Live pool (current)
    r_live = requests.get(f"{lcd}/cosmos/staking/v1beta1/pool", timeout=15)
    live_bonded = int(r_live.json()["pool"]["bonded_tokens"]) / (10 ** decimals)

    # Our latest built month
    df_sym = df_out[df_out["symbol"] == sym]
    last_row = df_sym.sort_values("month_end").iloc[-1]
    built_val = last_row["staked_native"]

    # Drift: built is month-end of last panel month (may be 1–3 months ago)
    # so some drift is expected from staking in/out since then.
    # A <5% drift PASS confirms we're reading the right chain + denom.
    # For chains where staking has shifted significantly, note it but don't hard-fail.
    drift_pct = abs(built_val - live_bonded) / live_bonded * 100
    status = "PASS" if drift_pct < 5 else "WARN (staking shifted since last panel month)"
    print(f"{sym}: built_latest={built_val:,.0f}  live={live_bonded:,.0f}  drift={drift_pct:.2f}%  {status}")
```

If drift > 20% for any chain, investigate — likely a wrong denom or decimal error.
A drift of 5–15% is acceptable given that live values are 1–3 months after our last panel month.

---

## Task E — Coverage label fix

CRO (3635) and KAVA (4846) are currently labeled `pos_possible` in
`03_data/universe_coverage_status.csv`. Now that we have confirmed archive staking
data, update them to `pos`.

First check current labels for all four:

```python
cov = pd.read_csv("03_data/universe_coverage_status.csv")
print(cov[cov["cmc_id"].isin([3635, 7226, 4846, 23149])][
    ["cmc_id", "symbol", "coin_staking_type", "coverage_status"]
])
```

For any that show `pos_possible` and for which we successfully built ch1, update:

```python
# Edit universe_coverage_status.csv directly:
# for each chain we built, set coin_staking_type = "pos" (it IS a PoS chain)
for cid in [cid for cid in [3635, 7226, 4846, 23149] if cid in built_cids]:
    cov.loc[cov["cmc_id"] == cid, "coin_staking_type"] = "pos"
cov.to_csv("03_data/universe_coverage_status.csv", index=False)
```

Do NOT change the `coverage_status` column manually — it will be recomputed in Task F.

---

## Task F — Assemble + rebuild coverage

```bash
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

Expected outcomes:
- λ panel: +N asset-months (where N = total months built across all 4 chains)
- Each built chain: coverage_status `partial` → `complete` (has ch1 + NVT_GL pq_usd)
- Regression-ready: 178 → **182** (if all 4 chains built; fewer if some archive probes fail)

Print the new regression-ready breakdown:
```python
cov = pd.read_csv("03_data/universe_coverage_status.csv")
print("Regression-ready:", (cov["coverage_status"] == "complete").sum())
print(cov[cov["cmc_id"].isin([3635, 7226, 4846, 23149])][
    ["cmc_id", "symbol", "coverage_status", "lambda_months"]
])
```

---

## DATA_DECISIONS_LOG — Entry 91

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 91 — Session 040: CRO/INJ/KAVA/SEI ch1 via Cosmos Archive LCD

**Approach:** free, keyless Cosmos SDK LCD `cosmos/staking/v1beta1/pool` with
`x-cosmos-block-height` header at month-end blocks found via binary search on
`cosmos/base/tendermint/v1beta1/blocks/{height}`.

**Archive probe results:**
- CRO: [archive node URL] — PASS / FAIL
- INJ: [archive node URL] — PASS / FAIL
- KAVA: [archive node URL] — PASS / FAIL
- SEI: [archive node URL] — PASS / FAIL

**Decimal notes:**
- CRO: basecro, 10^8 (NOT 10^6 like standard Cosmos chains)
- INJ: inj, 10^18 (EVM-compatible native denom)
- KAVA: ukava, 10^6
- SEI: usei, 10^6

**Cross-check results (latest month vs live pool):**
- CRO drift: [X]% — [PASS/WARN]
- INJ drift: [X]% — [PASS/WARN]
- KAVA drift: [X]% — [PASS/WARN]
- SEI drift: [X]% — [PASS/WARN]

**Coverage label fixes:** coin_staking_type pos_possible → pos for
[list chains updated].

**Post-assemble:** λ [X] asset-months / [N] assets.
Regression-ready [178 → N] (coins [22 → N], tokens/other 156 unchanged).

Output: 03_data/phase1/channel1_cosmos_lcd.csv
```

---

## Session report

Write `03_data/SESSION040_COSMOS_LCD_REPORT.md`:
- Archive probe table: each chain, endpoint tried, liveness result, archive result
- Months built per chain + date range
- Cross-check table: built vs live, drift %
- Coverage label changes
- Post-assemble λ and regression-ready totals
- Any chains that failed archive probe (with reason)

---

## Commit

```bash
git add -A
git commit -m "session 040: CRO/INJ/KAVA/SEI ch1 via Cosmos archive LCD; regression-ready 178→N"
git push
```

---

## Failure-mode guidance

| Failure | Diagnosis | Action |
|---------|-----------|--------|
| All LCD candidates return 404/503 | Chain may have migrated endpoints | Check official chain docs; try `https://chains.cosmos.directory` registry for updated URLs |
| Archive probe returns "height X was not found" | Node is pruned (non-archive) | Move to next candidate |
| Archive probe returns "request failed" with state mismatch | Migration / chain upgrade at that height | Try a slightly different height (±5,000 blocks) |
| `bonded_tokens` field missing in pool response | Different Cosmos SDK version | Check for `not_bonded_tokens` + `bonded_tokens` in response structure; some chains nest differently |
| Decimal mismatch (staking ratio > 1.0) | Wrong decimals used | Re-check chain denom registry; CRO=8, INJ=18, others=6 |
| SEI binary search timeout (216k blocks/day) | Large height range | Narrow lo/hi bracket by estimating from known timestamps before searching |
