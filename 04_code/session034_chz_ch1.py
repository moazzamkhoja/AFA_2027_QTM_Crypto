# Session 034 Task A: CHZ ch1 staking via Chiliz Chain 2.0 public RPC.
# Native CHZ balance of the CC2 staking contract 0x...1000 at month-end blocks
# (XDC 0x...0088 pattern). Anchor 2,416,757,292 CHZ vs staking.chiliz.com 2026-07-25.
import calendar, time, json, os, sys
import requests
import pandas as pd

ROOT = r"C:\AFA_2027_QTM_Crypto"
RAWDIR = os.path.join(ROOT, "03_data", "raw", "phase1_onchain", "pos_coins_evm")
BLOCK_CACHE = os.path.join(RAWDIR, "chz_monthend_blocks.json")
BAL_CACHE = os.path.join(RAWDIR, "chz_balancehistory.json")
OUT_CSV = os.path.join(ROOT, "03_data", "phase1", "channel1_chz.csv")

CHILIZ_RPCS = [
    "https://chiliz.drpc.org",
    "https://rpc.ankr.com/chiliz",
    "https://rpc.chiliz.io",
]
CHZ_STAKING = "0x0000000000000000000000000000000000001000"
ANCHOR = 2_416_757_292

def rpc_call(rpc_url, method, params):
    r = requests.post(rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": method,
                                     "params": params}, timeout=30)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"{rpc_url} {method}: {j['error']}")
    return j["result"]

def pick_rpc():
    for u in CHILIZ_RPCS:
        try:
            bn = int(rpc_call(u, "eth_blockNumber", []), 16)
            print(f"RPC OK: {u} head={bn}")
            return u, bn
        except Exception as e:
            print(f"RPC FAIL: {u}: {e}")
    raise RuntimeError("no Chiliz RPC responded")

def block_at_ts(rpc_url, target_ts, hi):
    lo = 0
    while lo < hi - 1:
        mid = (lo + hi) // 2
        b = rpc_call(rpc_url, "eth_getBlockByNumber", [hex(mid), False])
        if b is None:
            hi = mid
            continue
        if int(b["timestamp"], 16) <= target_ts:
            lo = mid
        else:
            hi = mid
    return lo

def month_list(start, end):
    ys, ms = int(start[:4]), int(start[5:7])
    ye, me = int(end[:4]), int(end[5:7])
    out = []
    y, m = ys, ms
    while (y, m) <= (ye, me):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out

def main():
    rpc, head = pick_rpc()
    yms = month_list("2023-07", "2026-05")

    cache = json.loads(open(BLOCK_CACHE).read()) if os.path.exists(BLOCK_CACHE) else {}
    # genesis timestamp sanity: find earliest block time
    b1 = rpc_call(rpc, "eth_getBlockByNumber", ["0x1", False])
    genesis_ts = int(b1["timestamp"], 16) if b1 else None
    print(f"block 1 timestamp: {genesis_ts} ({time.strftime('%Y-%m-%d', time.gmtime(genesis_ts)) if genesis_ts else '?'})")

    for ym in yms:
        if ym in cache and cache[ym] is not None:
            continue
        y, m = int(ym[:4]), int(ym[5:7])
        last_day = calendar.monthrange(y, m)[1]
        ts = int(calendar.timegm(time.strptime(f"{ym}-{last_day:02d} 23:59:59",
                                               "%Y-%m-%d %H:%M:%S")))
        if genesis_ts and ts < genesis_ts:
            cache[ym] = None  # chain not live yet
            print(f"{ym}: pre-genesis, None")
        else:
            b = block_at_ts(rpc, ts, head)
            blk = rpc_call(rpc, "eth_getBlockByNumber", [hex(b), False])
            if blk and int(blk["timestamp"], 16) <= ts:
                cache[ym] = b
                print(f"{ym}: block {b} @ {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(blk['timestamp'],16)))}")
            else:
                cache[ym] = None
                print(f"{ym}: search failed")
        open(BLOCK_CACHE, "w").write(json.dumps(cache, indent=1))
        time.sleep(0.15)

    bals = json.loads(open(BAL_CACHE).read()) if os.path.exists(BAL_CACHE) else {}
    for ym in yms:
        if ym in bals:
            continue
        b = cache.get(ym)
        if b is None:
            bals[ym] = None
            continue
        v = int(rpc_call(rpc, "eth_getBalance", [CHZ_STAKING, hex(b)]), 16) / 1e18
        bals[ym] = v
        print(f"{ym}: staked {v:,.0f} CHZ")
        open(BAL_CACHE, "w").write(json.dumps(bals, indent=1))
        time.sleep(0.15)
    open(BAL_CACHE, "w").write(json.dumps(bals, indent=1))

    series = {ym: v for ym, v in bals.items() if v}
    if not series:
        raise RuntimeError("no non-zero CHZ balances found")
    latest_ym = max(series)
    latest = series[latest_ym]
    drift = (latest - ANCHOR) / ANCHOR
    print(f"CHZ cross-check: latest series ({latest_ym}) {latest:,.0f} vs anchor {ANCHOR:,.0f} -> drift {drift:+.2%}")
    if abs(drift) > 0.05:
        raise RuntimeError("CHZ balance vs anchor drift >5%; verify contract address before shipping")

    up = pd.read_csv(os.path.join(ROOT, "03_data", "universe_panel.csv"),
                     usecols=["cmc_id", "symbol", "month_end", "circulating_supply"])
    up = up[up.cmc_id == 4066].set_index("month_end")["circulating_supply"]

    source = ("chiliz-chain-pubRPC eth_getBalance(0x...1000) at month-end blocks "
              "(native CHZ balance of the CC2 staking contract; anchor 2,416,757,292 "
              "CHZ confirmed 2026-07-25 vs staking.chiliz.com)")
    flag = ("native-balance series; CC2 launched ~2023-Q3; pre-launch months = NaN; "
            "balance includes any queued-but-not-yet-withdrawn undelegations if any")

    rows = []
    for ym in yms:
        v = bals.get(ym)
        if v == 0:
            v = None  # staking not yet live
        last_day = calendar.monthrange(int(ym[:4]), int(ym[5:7]))[1]
        me = f"{ym}-{last_day:02d}"
        supply = up.get(me)
        ratio = (v / supply) if (v and supply and supply > 0) else None
        rows.append({"cmc_id": 4066, "symbol": "CHZ", "month_end": me,
                     "staked_native": v, "circulating_supply": supply,
                     "staking_ratio": ratio, "source": source, "flag": flag})
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    built = df.staked_native.notna().sum()
    r = df.staking_ratio.dropna()
    print(f"WROTE {OUT_CSV}: {len(df)} rows, {built} with staked balance; "
          f"staking ratio range {r.min():.2%}..{r.max():.2%}" if len(r) else "no ratios")

if __name__ == "__main__":
    main()
