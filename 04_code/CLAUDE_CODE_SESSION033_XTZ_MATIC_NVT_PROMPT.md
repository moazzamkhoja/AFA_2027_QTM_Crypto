# Claude Code Session 033 — XTZ and MATIC NVT_GL (PQ probe and build)

**Date:** 2026-07-25
**No API key required** — all sources in this session are free and keyless.

---

## Context

Five coins have λ but no NVT_GL denominator (pq_nvtgl gap):

| cmc_id | symbol | λ months | why gapped |
|--------|--------|----------|------------|
| 2011 | XTZ | **78** | Phase 2b logged "no free native series" — but TzKT.io was never tried |
| 3890 | MATIC | 50 | Same note; MATIC ends 2024-08 at POL handoff |
| 21585 | SAFE | 10 | Governance token, no native chain — see Task C |
| 11396 | JOE | 6 | DEX governance token, no native chain — see Task C |
| 28324 | DYDX | 1 | dYdX L1 — 1 month too short for regression; skip |

The Phase 2b default note ("Cosmos LCD / api.kaspa.org expose only current state…") was
copy-pasted across all non-bitinfocharts coins. XTZ is Tezos, not Cosmos. TzKT.io is the
official Tezos indexer with a free, keyless, aggregate daily-statistics API going back to
mainnet genesis (2018-06). This session corrects that oversight.

**Entry 31/32 rule:** "Raw multi-year native block iteration forbidden." TzKT's
`/v1/statistics/daily` endpoint returns pre-aggregated daily totals — this is the same
pattern as blockchain.com for BTC and bitinfocharts for UTXO chains. It is NOT raw block
iteration. It is permitted.

---

## Task A — XTZ PQ via TzKT.io (priority)

### A1. Read the existing build infrastructure first

Read these files before writing any code:
- `04_code/phase2b_pq_coins.py` — how pq_coins.csv is structured and updated
- `04_code/phase2_nvt_gl.py` — how pq_coins.csv feeds into NVT_GL (columns needed:
  `cmc_id`, `symbol`, `month_end`, `pq_usd`, `pq_source`, `rung`, `note`)
- `03_data/phase2/pq_coins.csv` — the existing file (XTZ row is a single NaN-marker row)
- `03_data/universe_panel.csv` — for XTZ month-end prices (cmc_id=2011, status='observed')

### A2. Fetch TzKT daily statistics

Endpoint: `https://api.tzkt.io/v1/statistics/daily`
Parameters:
- `limit=10000` (gets full history in one call — Tezos has ~2,100 days since mainnet)
- `sort.asc=date`

Key field: **`totalTransferred`** — total tez transferred per day, in **mutez** (1 XTZ = 1,000,000 mutez).

Convert: `pq_xtz_day = totalTransferred / 1_000_000`

If the endpoint does not return all history in one page, paginate using `offset` parameter.
Cache the raw JSON to `03_data/raw/tzkt/xtz_statistics_daily.json` (gitignored path).

### A3. Cross-check the series

Before building, verify the series is not degenerate:
1. **Start date**: first date should be ~2018-06-30 (Tezos mainnet genesis).
2. **Recent magnitude**: sum the last 30 available days of `totalTransferred` / 1e6 = recent
   monthly XTZ volume. Convert at recent XTZ price. Compare to the DeFiLlama chain DEX
   figure for Tezos (~$16k/30d from `rung_table.csv`). The TzKT native volume should be
   **orders of magnitude larger** than DEX-only (this is the whole point — the
   `mat_ratio=0.000045` in the rung table means DEX captured only 0.0045% of cap, but
   native settlement value is a real number). If the TzKT figure is implausibly small (in
   the thousands USD/month), flag and investigate before building.
3. **No BTC-default contamination** (not applicable here — TzKT is Tezos-specific, not
   a multi-chain chart site that silently substitutes BTC).

### A4. Aggregate to monthly and compute PQ in USD

```python
import calendar, json
import pandas as pd

# Load raw
with open("03_data/raw/tzkt/xtz_statistics_daily.json") as f:
    data = json.load(f)

# Daily XTZ volume
rows = []
for r in data:
    date_str = r["date"][:10]   # 'YYYY-MM-DD'
    xtz = r["totalTransferred"] / 1_000_000.0
    rows.append({"date": date_str, "pq_xtz": xtz})
daily = pd.DataFrame(rows)
daily["date"] = pd.to_datetime(daily["date"])

# Month-end bucket
daily["month_end"] = daily["date"].apply(
    lambda d: pd.Timestamp(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
)
monthly_xtz = daily.groupby("month_end")["pq_xtz"].sum().reset_index()
monthly_xtz["month_end"] = monthly_xtz["month_end"].dt.strftime("%Y-%m-%d")

# Join XTZ price from universe_panel
panel = pd.read_csv("03_data/universe_panel.csv")
panel["month_end"] = pd.to_datetime(panel["month_end"]).dt.strftime("%Y-%m-%d")
xtz_price = panel[(panel["cmc_id"] == 2011) & (panel["status"] == "observed")][["month_end","price"]]

merged = monthly_xtz.merge(xtz_price, on="month_end", how="inner")
merged["pq_usd"] = merged["pq_xtz"] * merged["price"]
merged = merged[merged["pq_usd"] > 0]

# Columns for pq_coins.csv
merged["cmc_id"] = 2011
merged["symbol"] = "XTZ"
merged["pq_source"] = "tzkt_total_transferred"
merged["rung"] = "R3-tzkt"
merged["note"] = (
    "Tezos native totalTransferred (aggregate daily XTZ transferred on-chain, "
    "in mutez / 1e6 = XTZ). Source: api.tzkt.io/v1/statistics/daily (official "
    "TzKT indexer, free, keyless, historical). Summed daily->monthly, multiplied "
    "by month-end CMC price. This is native settlement value, not DEX-only volume."
)
```

### A5. Update pq_coins.csv

Remove the existing XTZ NaN-marker row and append the new monthly rows:

```python
pq = pd.read_csv("03_data/phase2/pq_coins.csv")
pq = pq[pq["cmc_id"] != 2011]          # drop old XTZ row(s)
new_xtz = merged[["cmc_id","symbol","month_end","pq_usd","pq_source","rung","note"]]
pq = pd.concat([pq, new_xtz], ignore_index=True)
pq = pq.sort_values(["cmc_id","month_end"], na_position="last")
pq.to_csv("03_data/phase2/pq_coins.csv", index=False)
print(f"XTZ rows added: {len(new_xtz)} months, range {new_xtz['month_end'].min()} → {new_xtz['month_end'].max()}")
print(f"PQ range: ${new_xtz['pq_usd'].min()/1e6:.1f}M – ${new_xtz['pq_usd'].max()/1e6:.1f}M/month")
```

---

## Task B — MATIC PQ probe

MATIC (cmc_id=3890) λ runs 2020-06 → 2024-08 (50 months; ends at POL handoff).

### B1. Try bitinfocharts

The Phase 2b script only tested 13 known tickers. Try `matic` live:

```python
import urllib.request, re

url = "https://bitinfocharts.com/comparison/sentinusd-matic.html"
html = urllib.request.urlopen(
    urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30
).read().decode("utf-8", "ignore")

rows = re.findall(r'new Date\("(\d{4})/(\d{2})/(\d{2})"\),(null|[0-9.eE+-]+)', html)
valid = [(f"{y}/{m}/{d}", float(v)) for y,m,d,v in rows if v != "null"]

# BTC-default guard: fetch BTC reference and assert MATIC differs
btc_url = "https://bitinfocharts.com/comparison/sentinusd-btc.html"
btc_html = urllib.request.urlopen(
    urllib.request.Request(btc_url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30
).read().decode("utf-8", "ignore")
btc_rows = re.findall(r'new Date\("(\d{4})/(\d{2})/(\d{2})"\),(null|[0-9.eE+-]+)', btc_html)
btc_last = float([v for _,_,_,v in btc_rows if v != "null"][-1])

if valid:
    matic_last = valid[-1][1]
    if abs(matic_last - btc_last) < 1e-6:
        print("MATIC series == BTC default → bitinfocharts does not cover MATIC")
    else:
        print(f"MATIC series found: {len(valid)} days, recent ${matic_last/1e6:.1f}M/day")
else:
    print("MATIC: empty or unparseable → bitinfocharts does not cover MATIC")
```

### B2. If bitinfocharts fails: mark still-gapped

If MATIC is not on bitinfocharts, update its NaN-marker row with a more precise note:

```
pq_source: "NaN:polygon_native_volume_no_free_source"
note: "MATIC/Polygon: bitinfocharts does not expose 'sentinusd-matic' (tested live
       2026-07-25 — returns BTC default or empty). Polygon native MATIC transfer value
       requires PolygonScan full-history export (no free API) or Artemis (paid).
       DeFiLlama Polygon chain DEX volume degenerate (not settlement value). λ window
       ends 2024-08 at POL handoff — short window reduces regression value.
       MATIC stays PQ=NaN."
```

Do NOT try PolygonScan raw block iteration — forbidden by Entry 31/32.

---

## Task C — JOE and SAFE classification review (no build needed)

### JOE (cmc_id=11396)
Classification_table says: `asset_class=coin, classification_basis="consensus tags: ['staking']"`.
JOE is the Trader Joe DEX governance token on Avalanche/Arbitrum — not a native gas coin for
any chain. Its λ (6 months) comes from a vote-escrow staking mechanism (veJOE).

**Finding**: There is no valid PQ (chain settlement value) for JOE — it is not a chain's
native coin. It also has no TVL in the DeFiLlama panel. This token is stuck regardless of
classification. Document in the DATA_DECISIONS_LOG that JOE's `pq_nvtgl` gap is permanent
(governance token misclassified as coin; no applicable NVT denominator; no TVL path either).
Do not attempt a PQ probe.

### SAFE (cmc_id=21585)
Same situation: Safe governance token, not a chain native. `classification_basis="consensus tags: ['staking']"`. No valid PQ path and no TVL. Document same conclusion.

### DYDX (cmc_id=28324)
dYdX is the native token of the dYdX Chain (a Cosmos L1) — legitimately a coin. However
it has only 1 month of λ (far too short for regression). Note it and skip for now; revisit
if λ extends via a Cosmos key.

---

## Task D — Rebuild NVT_GL panel

After updating pq_coins.csv (Task A + any B update):

```
python 04_code/phase2_nvt_gl.py
python 04_code/build_coverage_status.py
```

Verify XTZ appears in `nvt_gl_panel.csv` with non-null `nvt_gl` rows for the months where
both λ and NVT_GL overlap (should be the full 78-month λ window since TzKT goes back to
2018-06).

Print the overlap count:
```python
nvt = pd.read_csv("03_data/phase2/nvt_gl_panel.csv")
lam = pd.read_csv("03_data/phase1/lambda_panel.csv")
xtz_nvt = nvt[(nvt["cmc_id"]==2011) & nvt["nvt_gl"].notna()]
xtz_lam = lam[lam["cmc_id"]==2011]
print(f"XTZ NVT_GL months: {len(xtz_nvt)}")
print(f"XTZ λ months: {len(xtz_lam)}")
overlap = set(xtz_nvt["month_end"]) & set(xtz_lam["month_end"])
print(f"XTZ regression-ready overlap: {len(overlap)} months")
```

---

## DATA_DECISIONS_LOG — Entry 83

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 83 — Session 033: XTZ NVT_GL BUILT via TzKT.io; MATIC still gapped; JOE/SAFE closed

XTZ (2011): Phase 2b's GAP-R2 note was incorrect — Cosmos LCD is not the XTZ indexer.
TzKT.io (official Tezos indexer) serves free, keyless aggregate daily statistics via
/v1/statistics/daily including `totalTransferred` (native settlement value in mutez).
[N] months of PQ built ([date_range]); PQ range $[X]M–$[Y]M/month; regression-ready
overlap with λ: [N] months. pq_source = "tzkt_total_transferred", rung = "R3-tzkt".

MATIC (3890): bitinfocharts does not cover 'matic' ticker (BTC-default guard triggered /
empty). Polygon native transfer value has no free keyless source. λ window ends 2024-08
at POL handoff. MATIC stays PQ=NaN; note updated with precise reason.

JOE (11396) and SAFE (21585): Permanently closed. Classified as coin via staking tag but
are DEX/service governance tokens with no native chain. No valid PQ denominator exists
(not a chain gas coin); also no TVL path. Gap is architectural, not a data-sourcing problem.
DYDX (28324): 1-month λ too short for regression; skip until λ extends via Cosmos key.

Post-rebuild: coins regression-ready (λ∩NVT_GL): [20→N].
```

---

## Session report

Write `03_data/SESSION033_XTZ_MATIC_NVT_REPORT.md`:
- XTZ: months fetched, date range, PQ USD range, cross-check passed/failed, regression overlap
- MATIC: bitinfocharts probe result, final verdict
- JOE/SAFE/DYDX: classification notes
- Post-rebuild NVT_GL counts and regression-ready total

---

## Commit

```
git add -A
git commit -m "session 033: XTZ NVT_GL built via TzKT; MATIC/JOE/SAFE gaps closed"
git push
```
