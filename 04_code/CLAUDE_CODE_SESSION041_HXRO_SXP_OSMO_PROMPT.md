# Claude Code Session 041 — HXRO ch2 extend + SXP probe + OSMO ch1

**Date:** 2026-07-30
**Keys in use:** `04_code/.api_keys.json` → `"etherscan"` (Tasks A + B)
**ETHERSCAN SUBSCRIPTION NOTE:** Today is the last day of the paid Etherscan Pro
subscription. Run Tasks A and B before the subscription lapses. Task C (OSMO) is
free/keyless and can run in any order.

**Starting state (post-040):**
- λ: 13,547 asset-months / 465 assets; regression-ready **180** (coins 24, tokens/other 156)
- 6 tokens have TVL but are not regression-ready: HXRO, SXP, CASINO, OSMO, RUNE, SUN
- Of these, only HXRO has a confirmed Etherscan-reachable EVM address (chainid 1)

---

## Task A — HXRO (3748) ch2 re-run / extend  ← HIGHEST PRIORITY

**Why re-run:** HXRO has 24 ch2 months in `channel2_holding.csv`
(2020-09-30 → 2022-09-30) but its TVL in `tvl_panel.csv` starts 2023-02-28.
Zero overlap → stuck at partial. The checkpoint `03_data/raw/phase1_onchain/holding/3748_HXRO.json`
has `monthly: []` (empty) and `last_block: null`, so a fresh run will rebuild from
genesis and naturally extend through 2026-05-31 — creating 40 months of overlap
with TVL and making HXRO regression-ready.

**Etherscan address:** `0x4bd70556ae3f8a6ec6c4080a0c327b24325438f3` (chainid 1, Ethereum)
**Estimated getLogs:** ~534 (tiny — expect < 30 minutes wall time)

```bash
WORKLIST=3748 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

Expected output: HXRO monthly series 2020-09 → 2026-05 (old + new months).
After build, check checkpoint monthly keys include 2023-02 onward.

```python
import json
ck = json.loads(open("03_data/raw/phase1_onchain/holding/3748_HXRO.json").read())
months = sorted(ck.get("monthly", {}).keys())
print("HXRO months built:", len(months), months[:3], "...", months[-3:])
# Expect >= 2023-02-28 to appear
overlap_months = [m for m in months if m >= "2023-02-28"]
print("Overlap with TVL:", len(overlap_months))
```

**Guards (unchanged):**
- VAL_CAP_MULT = CONTAM_MULT = 100 — do NOT change
- `from == to` self-transfer skip — do NOT remove
- B2: no month exceeds 100× contamination guard
- B4: flag but do not suppress if screened HODL-6m median > 80%

Do NOT run assemble yet — wait until all tasks are done.

---

## Task B — SXP (4279) manual probe

`universe_coverage_status.csv` shows SXP as `evm_chain: non-EVM, etherscan_reachable: no`
but `asset_onchain_identity.csv` lists address `0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9`
with no chain prefix, which is the known Ethereum ERC-20 deployment of SXP (Swipe).
The `non-EVM` flag likely came from the coverage builder not recognising an
unprefixed multi-chain address.

**Probe: confirm if this address is a live EVM ERC-20 on Ethereum (chainid 1)**

```python
import json, requests

key = json.loads(open("04_code/.api_keys.json").read())["etherscan"]
addr = "0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9"

# 1. Contract ABI check (confirms it's a contract on Ethereum)
r_abi = requests.get(
    "https://api.etherscan.io/v2/api",
    params={"chainid": 1, "module": "contract", "action": "getabi",
            "address": addr, "apikey": key},
    timeout=15
)
print("ABI status:", r_abi.json().get("status"), r_abi.json().get("message"))

# 2. Token supply check (confirms ERC-20)
r_supply = requests.get(
    "https://api.etherscan.io/v2/api",
    params={"chainid": 1, "module": "stats", "action": "tokensupply",
            "contractaddress": addr, "apikey": key},
    timeout=15
)
print("Supply:", r_supply.json().get("result", "n/a")[:20])

# 3. Quick getLogs probe (most recent 2000 blocks)
import web3  # or use eth_getLogs via etherscan if web3 unavailable
r_logs = requests.get(
    "https://api.etherscan.io/v2/api",
    params={"chainid": 1, "module": "logs", "action": "getLogs",
            "address": addr, "fromBlock": "latest", "toBlock": "latest",
            "topic0": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "apikey": key},
    timeout=15
)
print("getLogs probe:", r_logs.json().get("status"), len(r_logs.json().get("result", [])), "events")
```

**Decision logic:**
- If ABI + supply both return OK AND getLogs probe returns without error:
  **Run SXP ch2** — update `asset_onchain_identity.csv` to add prefix
  `ethereum:0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9` and set evm_chainid=1,
  then `WORKLIST=4279 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py`
- If address not found or ABI status "NOTOK":
  **Document as permanent gap** — SXP's ERC-20 may have been migrated/deprecated.
  Move to BSC probe below.

**BSC fallback probe (if Ethereum fails):**
```python
# SXP BSC address (known Binance-chain deployment)
bsc_addr = "0x47BEAd2563dCBf3bF2c9407fEa4dC236fAbA485A"
r_bsc = requests.get(
    "https://api.etherscan.io/v2/api",
    params={"chainid": 56, "module": "contract", "action": "getabi",
            "address": bsc_addr, "apikey": key},
    timeout=15
)
print("BSC ABI:", r_bsc.json().get("status"), r_bsc.json().get("message"))
```
If BSC address is live, run ch2 on chainid 56 instead.

**If both fail:** close SXP as a permanent gap in Entry 92.

---

## Task C — OSMO (12220) ch1 via Cosmos Archive LCD

OSMO is the native staking + governance token of Osmosis (Cosmos SDK chain).
It has 60 TVL months (2021-06-28 → 2026-05-31) and 0 lambda months.
Building ch1 = bonded OSMO via `cosmos/staking/v1beta1/pool` at month-end blocks,
exactly the same approach as CRO and KAVA in session 040.

| Field | Value |
|-------|-------|
| cmc_id | 12220 |
| symbol | OSMO |
| Cosmos chain | osmosis-1 |
| denom | uosmo |
| decimals | **6** (1 OSMO = 10^6 uosmo) |
| Genesis | ~2021-06-18 |
| blocks/day | ~15,000 (~5.75 s/block) |

**LCD candidates (probe in order):**
1. `https://osmosis-api.polkachu.com` — Polkachu (known archive provider)
2. `https://lcd.osmosis.zone` — official Osmosis LCD
3. `https://rest.cosmos.directory/osmosis` — cosmos.directory aggregator

**CometBFT RPC** (for block timestamp lookups): `https://rpc.osmosis.zone`

### C1 — Archive probe (same as session 040 Task A)

```python
import requests, time

lcd_candidates = [
    "https://osmosis-api.polkachu.com",
    "https://lcd.osmosis.zone",
    "https://rest.cosmos.directory/osmosis",
]

BLOCKS_PER_DAY = 15000

for lcd in lcd_candidates:
    # Liveness
    try:
        r = requests.get(f"{lcd}/cosmos/staking/v1beta1/pool", timeout=20)
        if not r.ok:
            print(f"{lcd}: pool {r.status_code} — skip"); continue
        live_bonded = r.json()["pool"]["bonded_tokens"]
        print(f"{lcd} LIVE — bonded={live_bonded[:20]}...")
    except Exception as e:
        print(f"{lcd} UNREACHABLE: {e}"); continue

    # Latest block
    try:
        rb = requests.get(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/latest", timeout=20)
        latest = int(rb.json()["block"]["header"]["height"])
        print(f"  latest height={latest}")
    except Exception as e:
        print(f"  cannot read latest: {e}"); continue

    # Archive depth test (~365 days ago)
    old_height = max(1, latest - BLOCKS_PER_DAY * 365)
    ra = requests.get(
        f"{lcd}/cosmos/staking/v1beta1/pool",
        headers={"x-cosmos-block-height": str(old_height)},
        timeout=20
    )
    if ra.ok:
        bonded_old = ra.json()["pool"]["bonded_tokens"]
        # Fake-archive guard: if bonded_old == live_bonded digit-for-digit, header is ignored
        if bonded_old == live_bonded:
            print(f"  FAKE ARCHIVE (header ignored) — skip")
        else:
            print(f"  ARCHIVE CONFIRMED @ {old_height}: bonded={bonded_old[:20]}...")
            print(f"  --> USE {lcd}")
            break
    else:
        print(f"  archive FAIL @ {old_height}: {ra.status_code} {ra.text[:60]}")
    time.sleep(0.5)
```

### C2 — Build series (only if archive confirmed)

Use the same binary-search + pool-query pattern from session 040.
Month range: observed months in `universe_panel.csv` for cmc_id=12220 that are
at or after 2021-06-18 (Osmosis genesis).

Output: **`03_data/phase1/channel1_cosmos_osmo.csv`** (separate file so it doesn't
overwrite session 040's `channel1_cosmos_lcd.csv`).

Columns: `cmc_id, symbol, month_end, staked_native, circulating_supply, staking_ratio, source, flag`

```python
# circulating_supply: from universe_panel.csv cmc_supply_circ column
# staked_native: bonded_tokens / 1e6
# source: f"cosmos_lcd_pool@{block_height}"
# flag: f"uosmo / 10^6; block_time={block_t_utc}"
```

### C3 — Cross-check

Compare latest built month `staked_native` vs live pool value.
Drift < 5% → PASS. 5-20% acceptable with note (staking changes since last panel month).
> 20% → investigate decimals.

### C4 — Coverage label

Update `coin_staking_type` for OSMO (12220) from NaN → `pos`
(Osmosis uses standard Cosmos SDK staking / delegation).

---

## Task D — Close remaining TVL gaps (no data builds needed)

For each of the remaining 3 tokens with TVL but no viable build path, document
their permanent-gap status in Entry 92:

| cmc_id | symbol | chain | Why gap |
|--------|--------|-------|---------|
| 1573 | CASINO | Fantom (250) | `etherscan_reachable: no` — Fantom not in Etherscan Pro V2 coverage; no free archive alternative identified |
| 4157 | RUNE | THORChain | Non-EVM, non-Cosmos; native THORChain chain requires custom indexer |
| 10529 | SUN | Tron | Non-EVM; TronScan API available but ch2 engine not adapted for Tron |

These stay partial. No action required beyond documenting in Entry 92.

---

## Task E — Assemble + rebuild coverage

Run after ALL builds above are complete:

```bash
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

Expected outcomes (minimum scenario = HXRO only):
- HXRO: partial → **complete** (ch2 months now overlap TVL; regression-ready +1 → 181)

Expected outcomes (maximum scenario = HXRO + SXP + OSMO all succeed):
- Regression-ready: 180 → up to **183**

Print final counts:

```python
import pandas as pd
cov = pd.read_csv("03_data/universe_coverage_status.csv")
print("Regression-ready:", (cov["coverage_status"] == "complete").sum())
targets = [3748, 4279, 12220, 1573, 4157, 10529]
print(cov[cov["cmc_id"].isin(targets)][
    ["cmc_id", "symbol", "coverage_status", "lambda_months", "tvl_months"]
].to_string())
```

---

## DATA_DECISIONS_LOG — Entry 92

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 92 — Session 041: HXRO ch2 extend; SXP probe; OSMO ch1; gap closures

**HXRO (3748) ch2 extend:**
Checkpoint was empty (monthly: []); ch2 re-run rebuilt from genesis through 2026-05.
Old coverage: 2020-09 → 2022-09 (no TVL overlap). New coverage: [first] → 2026-05.
Overlap with TVL (2023-02 → 2026-05): [N] months. B2 [pass]. B4 [pass/flag].
Actual getLogs: [N] (est 534).

**SXP (4279) probe:**
Ethereum address 0x8ce9137d39326ad0cd6491fb5cc0cba0e089b6a9:
  [ABI probe result + getLogs probe result]
Decision: [built on chainid 1 / built on BSC chainid 56 / permanent gap — reason]

**OSMO (12220) ch1:**
Archive LCD: [node URL] — PASS / FAIL
[N] months built, range [start] → 2026-05. Drift: [X]% [PASS/WARN].
Denom: uosmo / 10^6. coin_staking_type updated: NaN → pos.
[or: NO ARCHIVE NODE — permanent gap]

**Permanent gap closures:**
CASINO (1573): Fantom chainid 250 — not in Etherscan V2 coverage, no free alternative.
RUNE (4157): THORChain — non-EVM, non-Cosmos; custom indexer required.
SUN (10529): Tron — ch2 engine not adapted for Tron; TronScan API deferred.

**Post-assemble:** λ [X] / [N] assets. Regression-ready [180 → N].

Note: Etherscan Pro subscription lapsed after this session.
Remaining Etherscan-dependent work: none identified.
```

---

## Session report

Write `03_data/SESSION041_HXRO_SXP_OSMO_REPORT.md`:
- HXRO: getLogs count, month range extended, TVL overlap months, B2/B4
- SXP: probe result (ABI status, getLogs status, decision)
- OSMO: archive probe table, months built, cross-check drift
- Gap closures table
- Post-assemble totals

---

## Commit

```bash
git add -A
git commit -m "session 041: HXRO ch2 extended; SXP probe; OSMO ch1; gap closures; regression-ready 180→N"
git push
```
