# Claude Code Session 037 — DOT/KSM ch1 (Subscan era_stat) + CORE ch1 probe/build

**Date:** 2026-07-27
**Keys in use:** `04_code/.api_keys.json` → `"subscan"` (DOT/KSM), `"coredao"` (CORE)

**Starting state (post-036):**
- λ: 13,272 asset-months / 459 assets; regression-ready 177 (coins 21, tokens/other 156)
- DOT (cmc 6636) + KSM (cmc 5034): have NVT_GL; need ch1 → each becomes regression-ready
- CORE (cmc 23254): 40 NVT_GL months; needs ch1 → regression-ready
- Expected post-session: coins 21 → 24 regression-ready (DOT + KSM + CORE if ch1 confirmed)

**BEFORE STARTING:** Pause Windows Update. Sleep/hibernate set to Never.

---

## Task A — DOT ch1 (Subscan era_stat)

### A0: Probe response structure (1 API call)

```python
import json, requests
key = json.loads(open("04_code/.api_keys.json").read())["subscan"]
r = requests.post(
    "https://polkadot.api.subscan.io/api/scan/staking/era_stat",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"row": 2, "page": 0}
)
print(json.dumps(r.json(), indent=2))
```

Print the full response. Identify:
- The field name for total bonded (likely `bonded_total`, `total_bonded`, or similar) — it will be a string in Planck units
- Whether `start_block_num` / `end_block_num` are present (for timestamp calculation)
- Whether any direct timestamp field is present
- Confirm `data.count` gives total era count

Then fetch genesis timestamp:
```python
r0 = requests.post(
    "https://polkadot.api.subscan.io/api/scan/block",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"block_num": 0}
)
print("DOT genesis block:", json.dumps(r0.json()["data"], indent=2))
```
Record `block_timestamp` from the response as `DOT_GENESIS_TS`.

### A1: Paginate all DOT eras

```python
import datetime as dt

DOT_GENESIS_TS = <from_probe>   # Unix timestamp of block 0
DOT_BLOCK_SECS = 6              # Polkadot target block time

all_eras = []
page = 0
while True:
    r = requests.post(
        "https://polkadot.api.subscan.io/api/scan/staking/era_stat",
        headers={"Content-Type": "application/json", "X-API-Key": key},
        json={"row": 100, "page": page},
        timeout=30
    )
    data = r.json()["data"]
    batch = data.get("list", [])
    if not batch:
        break
    all_eras.extend(batch)
    print(f"  page {page}: {len(batch)} eras, running total {len(all_eras)}/{data['count']}")
    if len(all_eras) >= data["count"]:
        break
    page += 1
    time.sleep(0.2)   # polite pacing (free plan: 30 req/s)
print(f"Total DOT eras fetched: {len(all_eras)}")
```

Expected: ~2000–2200 eras (22 pages). Runtime < 30 seconds.

### A2: Map eras to months, convert Planck→DOT

```python
from collections import defaultdict

bonded_field = "<field_name_from_probe>"   # e.g. "bonded_total"
block_field  = "end_block_num"             # or "start_block_num" if end not present

by_ym = defaultdict(lambda: (0, -1))   # ym -> (bonded_planck, era_num)

for e in all_eras:
    era_num    = e["era"]
    end_block  = e[block_field]
    bonded_str = e[bonded_field]
    if not bonded_str or bonded_str in ("0", None):
        continue
    bonded_planck = int(bonded_str)
    ts = DOT_GENESIS_TS + end_block * DOT_BLOCK_SECS
    ym = dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m")
    # Keep last era in each month (highest era_num = most recent snapshot)
    cur_bonded, cur_era = by_ym[ym]
    if era_num > cur_era:
        by_ym[ym] = (bonded_planck, era_num)

# Convert to DOT (1 DOT = 10^10 Planck)
dot_series = {ym: bonded / 1e10 for ym, (bonded, _) in by_ym.items()}

# Drop pre-staking months (NPoS active from ~2020-08)
dot_series = {ym: v for ym, v in dot_series.items() if ym >= "2020-08"}
print(f"DOT months: {min(dot_series)}.." + max(dot_series))
print(f"Latest staked: {dot_series[max(dot_series)]:,.0f} DOT")
```

### A3: Cross-check (DOT)

```python
# Fetch the latest era fresh (bypass any cache)
r_fresh = requests.post(
    "https://polkadot.api.subscan.io/api/scan/staking/era_stat",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"row": 1, "page": 0}   # most recent era
)
latest_era = r_fresh.json()["data"]["list"][0]
latest_fresh = int(latest_era[bonded_field]) / 1e10

latest_ym = max(dot_series)
latest_ours = dot_series[latest_ym]
drift = (latest_ours - latest_fresh) / latest_fresh
print(f"DOT cross-check: ours={latest_ours:,.0f}  fresh={latest_fresh:,.0f}  drift={drift:.2%}")
# ACCEPT if abs(drift) < 5% (Entry-26 standard)
# REJECT if drift > 5% — investigate pagination order / off-by-one
```

---

## Task B — KSM ch1 (same algorithm, different constants)

### B0: Probe KSM genesis timestamp

```python
r0_ksm = requests.post(
    "https://kusama.api.subscan.io/api/scan/block",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"block_num": 0}
)
print("KSM genesis:", json.dumps(r0_ksm.json()["data"], indent=2))
KSM_GENESIS_TS = <from_response>
```

Also verify era count:
```python
r_ksm_probe = requests.post(
    "https://kusama.api.subscan.io/api/scan/staking/era_stat",
    headers={"Content-Type": "application/json", "X-API-Key": key},
    json={"row": 1, "page": 0}
)
total_ksm_eras = r_ksm_probe.json()["data"]["count"]
print(f"KSM total eras: {total_ksm_eras}")   # expect ~8,000–11,000
```

### B1: Paginate all KSM eras

Same loop as DOT but `kusama.api.subscan.io`. Expected ~100 pages.
KSM has more eras (~6-hour era vs DOT's 24-hour era), so allow ~2 minutes.

### B2: Map to months

Same algorithm. Constants:
- **KSM**: `1 KSM = 10^12 Planck`  (NOT 10^10 — KSM never redenominated)
- KSM_BLOCK_SECS = 6
- Drop months before 2019-09 (KSM staking pre-NPoS era unreliable)

```python
ksm_series = {ym: bonded / 1e12 for ...}
```

### B3: Cross-check (KSM)

Same as DOT cross-check but `kusama.api.subscan.io`.

---

## Task C — CORE ch1 probe + conditional build

CORE = Core DAO native coin, cmc_id=23254. Chain launched 2023-01-14.
Key stored as `"coredao"` in `.api_keys.json`.
Entry 78 probe target: `/api/stats/staking_summary` on openapi.coredao.org.

### C0: Probe the staking_summary endpoint

```python
core_key = json.loads(open("04_code/.api_keys.json").read())["coredao"]

# Try both common auth patterns
import requests

# Pattern A: apikey as query param (Etherscan-compatible)
r = requests.get(
    "https://openapi.coredao.org/api/stats/staking_summary",
    params={"apikey": core_key},
    timeout=30
)
print("Pattern A:", r.status_code, r.text[:500])

# Pattern B: X-API-Key header
r2 = requests.get(
    "https://openapi.coredao.org/api/stats/staking_summary",
    headers={"X-API-Key": core_key},
    timeout=30
)
print("Pattern B:", r2.status_code, r2.text[:500])
```

**Read the response carefully:**

- **If the response contains a time-series array** (daily/weekly totals going back to 2023): use it directly — extract staked_CORE per period, bucket to months, convert units to CORE, build `channel1_core.csv`. Go to step C1-timeseries.

- **If the response is current-only** (single snapshot, no history): pivot to block-level reads. Go to step C1-blocklevel.

- **If 401/403 even with key**: try alternate base URL `https://scan.coredao.org/api/stats/staking_summary` with same auth patterns. If all fail, log CORE as "API probe failed — investigate key format" and skip CORE build this session.

### C1-timeseries (if historical series available)

Parse the returned series. Map each data point to a calendar month (last point in month = snapshot). Identify the unit of the staked amount (likely in CORE or in wei). Convert to CORE if needed (1 CORE = 10^18 wei if EVM, or check decimals field in response).

Cross-check: latest month in series vs live `module=stats&action=coinsupply` or similar endpoint.

Output: `03_data/phase1/channel1_core.csv`

Source string: `"openapi.coredao.org:staking_summary"`

### C1-blocklevel (if current-only)

Identify the CORE staking contract — try these in order:

**Step 1 — check if Core (chainid=1116) is on Etherscan Pro V2:**
```python
ev2 = requests.get("https://api.etherscan.io/v2/chainlist",
    params={"apikey": <etherscan_key>}, timeout=20).json()
core_in_v2 = any(str(c.get("chainid")) == "1116" for c in ev2.get("result", []))
print("Core (1116) in Etherscan V2:", core_in_v2)
```

**Step 2 — find the staking/pledge contract on CoreScan:**
Core DAO's Satoshi Plus uses a `PledgeAgent` contract that holds delegated CORE.
Try the CoreScan verified contracts API:
```python
r_src = requests.get(
    "https://openapi.coredao.org/api",
    params={"module": "contract", "action": "getsourcecode",
            "address": "0x0000000000000000000000000000000000001001",
            "apikey": core_key},
    timeout=20
)
print(r_src.status_code, r_src.text[:300])
```
(System contract 0x...1001 is a common address for staking controllers on EVM chains. Try also 0x...1000, 0x...1002.)

If a verified staking/pledge contract is found, get its address. Then:

**Step 3 — block-level balance at month-end blocks:**

For each month-end from 2023-01 to 2026-05:
1. Get an approximate month-end block number:
   - CORE genesis: 2023-01-14. Block time: ~3 seconds.
   - Block at month-end M: `(M_ts - CORE_GENESIS_TS) / 3`
2. Use CoreScan `module=account&action=balance&address=<staking_contract>&tag=<hex_block>&apikey=<key>` if available, OR `eth_getBalance` via JSON-RPC.
3. Convert from wei (divide by 1e18) to get CORE staked.

Cross-check: latest block balance vs live `eth_getBalance` call.

Output: `03_data/phase1/channel1_core.csv`

Source string: `"openapi.coredao.org:PledgeAgent.balance(month-end block)"`

### C2: If CORE cannot be built this session

Log: "CORE (23254) ch1 probe: [describe what endpoint returned]. Block-level approach: [describe outcome]. Deferred to Session 038 for manual staking contract identification."

Do NOT ship a partial or guessed series.

---

## Task D — Assemble and rebuild coverage

```
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

Print new λ totals and regression-ready counts.
- If DOT + KSM built: coins regression-ready 21 → 23
- If CORE also built: coins regression-ready → 24
- Tokens/other should be unchanged.

---

## DATA_DECISIONS_LOG — Entry 87

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 87 — Session 037: DOT + KSM ch1 BUILT via Subscan era_stat; CORE ch1 probe

**DOT (6636):** [N] eras paginated across [P] pages.
Bonded_field = [field_name]. Genesis_ts = [ts].
[N_months] months built ([start]..[end]). Latest staked: [X] DOT.
Cross-check: ours=[X] / fresh=[Y] / drift=[D%] — [PASS/FAIL].
Source: subscan-polkadot:era_stat.bonded_total / 1e10.
DOT enters regression-ready (has NVT_GL): coins [21→22] or [21→23] (with KSM).

**KSM (5034):** [N] eras paginated across [P] pages.
KSM_genesis_ts = [ts]. 1 KSM = 1e12 Planck.
[N_months] months built ([start]..[end]). Latest staked: [X] KSM.
Cross-check: ours=[X] / fresh=[Y] / drift=[D%] — [PASS/FAIL].
Source: subscan-kusama:era_stat.bonded_total / 1e12.
KSM enters regression-ready: coins [22→23].

**CORE (23254):** Probe result: [describe staking_summary response].
[BUILT / DEFERRED / FAILED] — [brief description].
If built: [N_months] months ([start]..[end]). Latest staked: [X] CORE.
Cross-check: [result]. Source: [source string].
If deferred: [reason + next action].

Post-assemble: λ [13,272→X] asset-months / [459→N] assets.
Regression-ready coins: [21→N] (DOT, KSM[, CORE] now complete).
```

---

## Session report

Write `03_data/SESSION037_DOT_KSM_CORE_REPORT.md`:
- Per-asset: eras fetched, months built, bonded field, Planck conversion, drift
- CORE: full probe trace and outcome (built or deferred)
- Post-assemble λ and regression-ready totals
- Next steps

---

## Commit

```
git add -A
git commit -m "session 037: DOT + KSM ch1 built (Subscan era_stat); CORE ch1 [built/deferred]"
git push
```

---

## Technical notes

**DOT Planck:** 1 DOT = 10^10 Planck. Polkadot redenominated in August 2020 (100 old DOT → 1 new DOT). The Planck unit itself did not change. The `bonded_total` from Subscan is expressed in Planck throughout — dividing by 1e10 always gives post-redenomination DOT.

**KSM Planck:** 1 KSM = 10^12 Planck. No redenomination ever occurred on Kusama.

**Subscan pagination order:** eras are returned oldest-first (era 0 at page 0). Paginate forward to collect all history. The final page will have fewer than 100 entries.

**Rate limiting:** Subscan free plan supports 30 requests/second. With `time.sleep(0.2)` between pages, actual rate is ~5 req/s — well within limits. Total wall-clock for DOT (~22 pages) + KSM (~100 pages) should be under 5 minutes.

**Month-end bucketing convention:** all other ch1 files use the last calendar day of the month as `month_end` (e.g., 2024-01-31). Use `calendar.monthrange(yr, mo)[1]` to get the last day and format as `YYYY-MM-DD`. The `staked_native` value for that row is the last-era snapshot within that calendar month.

**Cross-check standard (Entry 26):** drift < 5% = PASS; 5–10% = PASS with flag; > 10% = REJECT (do not ship, investigate).

**schema** (matches all other channel1_*.csv files):
```
cmc_id, symbol, month_end, staked_native, circulating_supply, staking_ratio, source, flag
```
Join `circulating_supply` from `03_data/universe_panel.csv` on `(cmc_id, month_end)` using YYYY-MM matching.
`staking_ratio = staked_native / circulating_supply` (null if circulating_supply missing or zero).

**CORE chain genesis:** Core DAO mainnet launched 2023-01-14. The earliest valid ch1 month is 2023-01. NVT_GL has 40 months for CORE 23254; typical window overlap will be ~29 months (2023-01→2026-05).

**Worklist for Sessions 038+:**
- Session 038: SHIB (5994) ch2, ~128k getLogs est (likely over-estimate), λ-only
- WARP (1166): identity-map review (built-but-empty, Entry 79)
- Cosmos key → CRO, INJ, SEI, KAVA ch1 (+4 coins)
- Blockchair support email → XTZ/MATIC NVT_GL (before paying ~$30/mo)
- Task #22: bibliography sanity-check
