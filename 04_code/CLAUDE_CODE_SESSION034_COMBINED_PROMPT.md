# Claude Code Session 034 — CHZ ch1 + Blockchair XTZ/MATIC + EVM DeFi Breadth Batch 1

**Date:** 2026-07-25
**Etherscan Pro key:** `04_code/.api_keys.json` under `"etherscan"` (needed for Task D only)
**No key needed:** Tasks A, B, C use public RPC / Blockchair free tier

**Starting state (post-033):**
- λ: 9,648 asset-months / 342 assets; regression-ready 143 (coins 20, tokens/other 123)
- channel2_holding.csv: 307 tokens / 9,867 rows
- No changes to guard thresholds; `from == to` self-transfer skip stays

**BEFORE STARTING:** Sleep/hibernate already set to Never (session 031 fix).
Pause Windows Update (Settings → Windows Update → Pause for 7 days) before Task D.

---

## Task A — CHZ ch1 staking (Chiliz Chain RPC, ~1–2h)

### A1. Context and anchor

CHZ (cmc_id=4066) has 0 lambda months — ch1_staking[pos_possible] gate was the
"semantics anchor" check (Entry 79 / SESSION029 probe). That gate is now OPEN:

**Anchor confirmed 2026-07-25:** staking.chiliz.com shows **2,416,757,292 CHZ**
staked, which matches the balance of the Chiliz Chain staking contract
`0x0000000000000000000000000000000000001000` (2.38B last read, 1.5% drift =
expected growth). This is a native-balance staking contract (same pattern as XDC's
`0x...0088`), NOT an event-replay target. Build via balance reads at month-end blocks.

**Chain:** Chiliz Chain 2.0 (chainid=88888). NOT on Etherscan Pro V2 (confirmed in
Entry 78 — probed live). Use the public Chiliz RPC directly.

### A2. RPC connection

Try in order:
```python
CHILIZ_RPCS = [
    "https://chiliz.drpc.org",         # drpc pattern (same as ronin.drpc.org in prod)
    "https://rpc.ankr.com/chiliz",     # Ankr fallback
    "https://rpc.chiliz.io",           # official fallback
]
```

Test with a simple `eth_blockNumber` call. Use the first that responds.

### A3. Month-end block lookup (binary search)

Etherscan Pro's `getblocknobytime` does NOT cover chainid=88888. Use binary search
via `eth_getBlockByNumber` to find the last block of each month-end (UTC 23:59:59):

```python
import calendar, time, json, requests

def chiliz_rpc(rpc_url, method, params):
    r = requests.post(rpc_url, json={"jsonrpc":"2.0","id":1,"method":method,"params":params},
                      timeout=30)
    return r.json()["result"]

def block_at_ts(rpc_url, target_ts, lo=0, hi=None):
    """Binary search for block closest to target_ts (from below)."""
    if hi is None:
        hi = int(chiliz_rpc(rpc_url, "eth_blockNumber", []), 16)
    while lo < hi - 1:
        mid = (lo + hi) // 2
        b = chiliz_rpc(rpc_url, "eth_getBlockByNumber", [hex(mid), False])
        if b is None:
            hi = mid; continue
        if int(b["timestamp"], 16) <= target_ts:
            lo = mid
        else:
            hi = mid
    return lo

def month_end_blocks(yms, rpc_url, cache_file):
    """yms = ["2023-07","2023-08",...]; returns {ym: block_number}."""
    import os, json
    cache = json.loads(open(cache_file).read()) if os.path.exists(cache_file) else {}
    for ym in yms:
        if ym in cache and cache[ym]:
            continue
        y, m = int(ym[:4]), int(ym[5:7])
        last_day = calendar.monthrange(y, m)[1]
        ts = int(calendar.timegm(
            time.strptime(f"{ym}-{last_day:02d} 23:59:59", "%Y-%m-%d %H:%M:%S")))
        b = block_at_ts(rpc_url, ts)
        # verify the block we found is actually ≤ target_ts
        blk = chiliz_rpc(rpc_url, "eth_getBlockByNumber", [hex(b), False])
        if blk and int(blk["timestamp"], 16) <= ts:
            cache[ym] = b
        else:
            cache[ym] = None
        open(cache_file, "w").write(json.dumps(cache))
        time.sleep(0.15)
    return cache
```

Cache to: `03_data/raw/phase1_onchain/pos_coins_evm/chz_monthend_blocks.json`

### A4. Balance reads

```python
CHZ_STAKING = "0x0000000000000000000000000000000000001000"

def chz_balance_at(rpc_url, block_num):
    """Native CHZ balance of the staking contract at a given block."""
    result = chiliz_rpc(rpc_url, "eth_getBalance",
                        [CHZ_STAKING, hex(block_num)])
    return int(result, 16) / 1e18   # CHZ (18 decimals)
```

Window: `month_ends("2023-07", "2026-05")` — CC2 launched ~2023-Q3; if balance=0
at early months, skip them (staking not yet live). Stop at 2026-05 as usual.

Cache reads to: `03_data/raw/phase1_onchain/pos_coins_evm/chz_balancehistory.json`

### A5. Cross-check

After building the series, verify the most recent month's balance is close to the
anchor:

```python
latest_staked = series[max(series)]
anchor = 2_416_757_292
drift = (latest_staked - anchor) / anchor
print(f"CHZ cross-check: latest series {latest_staked:,.0f} vs anchor {anchor:,.0f} "
      f"-> drift {drift:+.2%}")
# Accept if drift < 5% (anchor was read on 2026-07-25; some growth since last month-end)
if abs(drift) > 0.05:
    raise RuntimeError("CHZ balance vs anchor drift >5%; verify contract address before shipping")
```

### A6. Emit to channel1 CSV

Write to `03_data/phase1/channel1_chz.csv` with columns:
`cmc_id, symbol, month_end, staked_native, circulating_supply, staking_ratio, source, flag`

Join circulating_supply from `universe_panel.csv` on `(cmc_id=4066, month_end)`.

```python
source = ("chiliz-chain-pubRPC eth_getBalance(0x...1000) at month-end blocks "
          "(native CHZ balance of the CC2 staking contract; anchor 2,416,757,292 "
          "CHZ confirmed 2026-07-25 vs staking.chiliz.com)")
flag   = ("native-balance series; CC2 launched ~2023-Q3; pre-launch months = NaN; "
          "balance includes any queued-but-not-yet-withdrawn undelegations if any")
```

Run `python 04_code/phase1_assemble_lambda.py` after writing.

---

## Task B — Blockchair XTZ and MATIC probe (keyless, ~30 min)

Session 033 tried TzKT, TzStats, TzPro, CoinMetrics, bitinfocharts, Messari,
CryptoCompare for XTZ — but did NOT try Blockchair. Blockchair covers both Tezos
and Polygon and has a `?a=sum(field)` aggregation API. Free tier: ~30 req/day.
The one-time pull needs ~96 monthly points for XTZ and ~48 for MATIC — doable
over a few minutes with 1s sleep between calls.

**No Blockchair key required for free tier.** If a key exists in `.api_keys.json`
under `"blockchair"`, use `?key=<key>` parameter; otherwise proceed keyless.

### B1. XTZ — Tezos native transfer volume

Blockchair's Tezos model uses `calls` (internal operations) and `operations`.
The field for value transferred is `amount` (in mutez = 1e-6 XTZ).

Probe one month first to confirm the endpoint shape:

```python
import requests, time

def blockchair_get(url, params=None):
    r = requests.get(url, params=params, timeout=30,
                     headers={"User-Agent": "academic-research/1.0"})
    return r.json()

# Probe: Tezos - try multiple entity types to find native transfer value
for entity in ["calls", "operations", "transactions"]:
    url = f"https://api.blockchair.com/tezos/{entity}"
    r = blockchair_get(url, {"a": "sum(amount)", "q": "time(2024-01)",
                              "limit": 1})
    print(f"tezos/{entity}: status={r.get('context',{}).get('code','?')} "
          f"data={r.get('data')}")
    time.sleep(1)
```

Pick the entity type that returns a non-zero `sum(amount)`. Then build monthly series:

```python
rows = []
for ym in month_list("2018-06", "2026-05"):   # XTZ mainnet genesis 2018-06
    y, m = ym[:4], ym[5:]
    r = blockchair_get(f"https://api.blockchair.com/tezos/{ENTITY}",
                       {"a": f"sum(amount)", "q": f"time({ym})"})
    val_mutez = r["data"][0].get("sum(amount)", 0)
    rows.append({"month_end": month_end_str(ym), "pq_xtz": val_mutez / 1e6})
    time.sleep(1.2)   # free tier rate limit
```

**BTC-default guard:** after fetching, compare a 2024-01 XTZ value to the Bitcoin
equivalent call. If XTZ `sum(amount)` matches BTC to 6 decimal places: abort.

### B2. MATIC — Polygon native transfer volume

Polygon is EVM. Native MATIC transferred is in the `value` field (Wei = 1e18).

```python
# Probe one month
r = blockchair_get("https://api.blockchair.com/polygon/transactions",
                   {"a": "sum(value)", "q": "time(2024-01)", "limit": 1})
print(f"polygon/transactions sum(value): {r.get('data')}")
```

If that works, build series for `month_list("2020-06", "2024-08")` (MATIC λ window).

### B3. If both work: update pq_coins.csv and rebuild NVT_GL

Remove existing NaN-marker rows for XTZ (cmc_id=2011) and/or MATIC (cmc_id=3890),
append new monthly rows, sort, save. Then:

```
python 04_code/phase2_nvt_gl.py
python 04_code/build_coverage_status.py
```

Print regression-ready overlap counts for XTZ and MATIC.

### B4. If Blockchair rate-limits or requires paid key

Document in the session report exactly what was tried and what error was returned.
If the only blocker is a paid key (~$30/month), flag it clearly in the report so
Moazzam can decide: "Blockchair key needed for XTZ and/or MATIC — $30/month plan
covers both in a one-time pull."

Do NOT subscribe without explicit approval.

---

## Task C — EVM DeFi Breadth Batch 1 (102 tokens, ~147k getLogs, ~3–8h)

These are DeFi-sector EVM tokens (DEX, Lending, Liquid Staking, Yield, Bridge,
Derivatives, etc.) in the not_started universe, sorted by estimated getLogs
ascending (smallest first). All are buildable via the existing Etherscan Pro V2
multi-chain engine. No engine changes.

### C1. Run the build

```
WORKLIST=11461,33981,1888,2593,38417,5830,23177,3367,3418,17050,1882,2576,7672,35818,1768,39125,2503,29974,3325,3855,19843,2363,5007,12387,1660,29335,6833,4862,24760,2726,2277,2110,5798,5326,3083,37574,29035,18037,6748,38482,2559,1500,2826,19650,2296,2202,3053,33038,2772,8161,9308,2223,25147,39720,7224,16876,3928,33824,38408,8420,9444,28412,7501,5429,3296,3475,34104,15060,8075,1503,9674,12573,29242,33652,9640,29520,26997,34143,5617,2430,23711,28695,10407,2015,2700,2945,27566,4195,6511,1984,11289,12409,27565,8083,11156,29676,36458,16116,28933,2424,21535,1758 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```

**Notable tokens (survivorship bias targets):**
- CEL (2700, ~2.4k gl) — Celsius, DEAD, Yield Aggregator — include historical TVL check
- MULTI (17050, ~337 gl) — Multichain, DEAD, Bridge — include historical TVL check
- FTT (4195, ~2.5k gl) — FTX Token, DEAD — Exchange Token/Derivatives
- LEND (2239 — in Batch 2) — old Aave v1, MIGRATED — Lending, historical TVL on DeFiLlama
- SAI (2308 — in Batch 2) — old MakerDAO single-collateral, DEAD — CDP

**Engine rules (unchanged):**
- VAL_CAP_MULT = CONTAM_MULT = 100 — do NOT change
- `from == to` self-transfer skip — do NOT remove
- B2: no month exceeds 100x contamination guard
- B4: screened HODL-6m in [0, 80%]; flag but do not suppress if outside

**Expected behavior:**
- Most tokens have est_gl < 2k → very fast (seconds each)
- Tokens with est_gl 3k–5k → a few minutes each
- Total wall-clock ~3–8h depending on rate-limit behavior
- No long silences expected (these are small Ethereum mainnet tokens)

### C2. DeFiLlama TVL slug lookup (after build completes)

For every token successfully built in Batch 1, check DeFiLlama for a protocol slug.
This step determines which ch2 builds become regression-ready (λ∩TVL).

```python
import requests, json, time
from pathlib import Path

# Fetch full protocol list
protos = requests.get("https://api.llama.fi/protocols", timeout=60).json()

# For each built token, try symbol match then address match
built_ids = [...]   # list of cmc_ids that were just built
id_map = {...}      # cmc_id -> {symbol, address, chainid}

matches = []
for cmc_id in built_ids:
    sym = id_map[cmc_id]["symbol"].lower()
    addr = id_map[cmc_id].get("address","").lower()
    candidates = [p for p in protos
                  if p.get("symbol","").lower() == sym
                  or addr in str(p.get("address","")).lower()]
    if candidates:
        # pick the one with most TVL history
        best = max(candidates, key=lambda p: p.get("tvl", 0))
        matches.append({"cmc_id": cmc_id, "dl_slug": best["slug"],
                        "dl_name": best["name"], "tvl": best.get("tvl",0)})
        print(f"  MATCH: cmc_id={cmc_id} {sym} -> {best['slug']} (TVL ${best.get('tvl',0)/1e6:.1f}M)")
    else:
        print(f"  NO MATCH: cmc_id={cmc_id} {sym}")

print(f"\n{len(matches)}/{len(built_ids)} tokens matched on DeFiLlama")
```

For each match, fetch TVL history and append to `03_data/phase2/tvl_panel.csv`
using the same schema as existing TVL rows. DeFiLlama historical TVL endpoint:
`https://api.llama.fi/protocol/{slug}` → `tvl` array with `{date, totalLiquidityUSD}`.

**Dead protocol note:** DeFiLlama archives historical TVL even for dead/bankrupt
protocols (CEL, MULTI, LEND, SAI). Fetch their history exactly like live protocols.
This is the survivorship bias defense — the low-TVL, low-λ region of the regression.

---

## Task D — Assemble and rebuild

```
python 04_code/phase1_assemble_lambda.py
python 04_code/build_coverage_status.py
```

Print:
- New λ asset-months and asset count
- New regression-ready count (tokens with both ch2 and TVL)
- How many of the 102 Batch 1 tokens found TVL slugs

---

## DATA_DECISIONS_LOG — Entry 84

Append to `04_code/DATA_DECISIONS_LOG.md`:

```
### Entry 84 — Session 034: CHZ ch1 BUILT; Blockchair XTZ/MATIC [probe result];
  EVM DeFi Breadth Batch 1 (102 tokens)

CHZ (4066): ch1 staking built via Chiliz Chain 2.0 public RPC (eth_getBalance on
0x...1000 staking contract at month-end blocks; anchor drift [X]% vs 2,416,757,292
CHZ confirmed 2026-07-25). Window: [start]..2026-05 ([N] months). Staking ratio range
[X%]..[Y%]. pq_source suffix: chiliz-chain-pubRPC.

Blockchair XTZ: [BUILT via blockchair/tezos/{entity} sum(amount) mutez / 1e6 | 
FAILED: <reason>]. [If built]: [N] months, PQ range $[X]M..[Y]M/month. Coins
regression-ready [20→21].

Blockchair MATIC: [BUILT | FAILED: <reason>]. [If built]: [N] months.

EVM DeFi Breadth Batch 1: [N] of 102 tokens built (B2/B4 pass/flag per token below
or in session report). [M] tokens matched DeFiLlama TVL slugs. [K] new
regression-ready tokens (λ∩TVL). Dead protocol builds: CEL, MULTI, [others].

Post-assemble: λ [X] asset-months / [N] assets. Regression-ready [143→N].
Remaining EVM DeFi breadth batches:
  Batch 2 (session 035): 13 tokens, ~119k getLogs — WORKLIST provided in 034 prompt
  Batch 3 (session 036): stETH + MEME, ~110k getLogs
  Batch 4 (session 037): SHIB alone, ~128k getLogs
```

---

## Session report

Write `03_data/SESSION034_COMBINED_REPORT.md`:
- CHZ: months built, staking ratio range, cross-check result
- Blockchair XTZ: probe result (pass/fail, months if pass, PQ range)
- Blockchair MATIC: probe result
- EVM Batch 1: token-level table (symbol, cmc_id, getLogs actual, months built,
  B2/B4 status, TVL slug found Y/N)
- Post-assemble λ and regression-ready totals

---

## Commit

```
git add -A
git commit -m "session 034: CHZ ch1 built; Blockchair XTZ/MATIC probe; EVM DeFi batch 1 (102 tokens)"
git push
```

---

## Reference: remaining EVM DeFi batches (for follow-on sessions)

**Session 035 — Batch 2 (13 tokens, ~119k getLogs, run immediately after quota resets):**
```
WORKLIST=3783,2120,5824,1982,1757,2586,2165,5266,2239,28568,9436,2308,2691 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```
Notable: SNX (Synthetix, 7k gl), LEND (old Aave v1, 10.7k gl), SAI (old MakerDAO, 14.1k gl),
EETH (EtherFi, 12.8k gl), PNT (pNetwork bridge, 14.3k gl)

**Session 036 — Batch 3a (2 tokens, ~110k getLogs):**
```
WORKLIST=8085,28301 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```
stETH (49k gl) — Lido's core staked ETH token, massive TVL; MEME (61k gl)

**Session 037 — Batch 3b (1 token, ~128k getLogs):**
```
WORKLIST=5994 PYTHONUTF8=1 python 04_code/phase1_channel2_stream.py
```
SHIB (Shiba Inu, 128k gl) — largest meme/DeFi-hybrid build; no protocol TVL expected
