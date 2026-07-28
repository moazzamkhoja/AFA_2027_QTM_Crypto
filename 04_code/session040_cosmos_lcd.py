# Session 040 — CRO/INJ/KAVA/SEI ch1 via Cosmos Archive LCD (Tasks A-D)
# Free, keyless. LCD staking pool at month-end blocks found via binary search.
import requests, json, time, calendar, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "03_data/phase1/channel1_cosmos_lcd.csv"
PROBE_JSON = ROOT / "03_data/phase1/session040_probe_results.json"

CHAIN_CONFIG = {
    "CRO": {
        "cmc_id": 3635, "symbol": "CRO", "denom": "basecro", "decimals": 8,
        "lcd_candidates": [
            "https://rest.mainnet.crypto.org",
            "https://cryptocom-api.polkachu.com",
            "https://rest-cryptoorgchain.ecostake.com",
            "https://cryptocom-api.w3coins.io",
            "https://cro-chain-rest.publicnode.com",
            "https://rest.cosmos.directory/cryptoorgchain",
        ],
        "genesis_date": "2021-03-25", "blocks_per_day": 14400,
    },
    "INJ": {
        "cmc_id": 7226, "symbol": "INJ", "denom": "inj", "decimals": 18,
        "lcd_candidates": [
            "https://injective-api.highstakes.ch",
            "https://rest.lavenderfive.com:443/injective",
            "https://injective-rest.publicnode.com",
            "https://public.stakewolle.com/cosmos/injective/rest",
            "https://injective.rpc.uquad.org:443",
            "https://sentry.lcd.injective.network",
            "https://rest.cosmos.directory/injective",
        ],
        "genesis_date": "2021-11-08", "blocks_per_day": 28800,
    },
    "KAVA": {
        "cmc_id": 4846, "symbol": "KAVA", "denom": "ukava", "decimals": 6,
        "lcd_candidates": [
            "https://api.data.kava.io",
            "https://kava-mainnet-lcd.autostake.com:443",
            "https://kava-rest.publicnode.com",
            "https://api.kava.nodestake.org",
            "https://kava.api.pocket.network",
            "https://rest.cosmos.directory/kava",
        ],
        "genesis_date": "2019-11-15", "blocks_per_day": 14400,
        "search_pace": 0.6,  # api.data.kava.io rate-limits hard (HTTP 420)
    },
    "SEI": {
        "cmc_id": 23149, "symbol": "SEI", "denom": "usei", "decimals": 6,
        "lcd_candidates": [
            "https://rest.lavenderfive.com:443/sei",
            "https://api-sei.stingray.plus",
            "https://lcd-sei.whispernode.com:443",
            "https://sei.api.kjnodes.com",
            "https://sei-rest.publicnode.com",
            "https://sei.api.pocket.network",
            "https://rest.sei-apis.com",
            "https://rest.cosmos.directory/sei",
        ],
        "genesis_date": "2023-08-15", "blocks_per_day": 216000,
    },
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AFA2027-QTM-research/1.0"})


def get_json(url, headers=None, timeout=20, retries=3):
    """GET with retry/backoff on 429/5xx and connection errors. Returns (ok, json_or_status)."""
    last_err = "retries exhausted"
    for attempt in range(retries):
        try:
            r = SESSION.get(url, headers=headers, timeout=timeout)
            if r.status_code >= 500 and "invalid denom" in r.text:
                # Deterministic: state at this height predates a codec/upgrade
                # boundary and will never decode -- retrying is pointless.
                return False, f"{r.status_code} {r.text[:160]}"
            if r.status_code in (420, 429):
                last_err = f"{r.status_code} {r.text[:160]}"
                time.sleep(15.0 * (attempt + 1))
                continue
            if r.status_code >= 500:
                last_err = f"{r.status_code} {r.text[:160]}"
                time.sleep(1.5 * (attempt + 1))
                continue
            if not r.ok:
                return False, f"{r.status_code} {r.text[:160]}"
            return True, r.json()
        except Exception as e:
            last_err = f"EXC {e}"
            time.sleep(1.0 * (attempt + 1))
    return False, last_err


# ---------- Task A: archive probe ----------
def probe_chain(sym, cfg):
    log = []
    for lcd in cfg["lcd_candidates"]:
        ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool")
        if not ok:
            print(f"  {lcd} pool: {res} -- skip"); log.append({"lcd": lcd, "liveness": f"FAIL {res}"}); continue
        live_bonded = res["pool"]["bonded_tokens"]
        print(f"  {lcd} LIVE -- bonded={live_bonded[:20]}")

        ok, res = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/latest")
        if not ok:
            print(f"  {lcd} latest block: {res}"); log.append({"lcd": lcd, "liveness": "OK", "latest": f"FAIL {res}"}); continue
        latest_height = int(res["block"]["header"]["height"])
        print(f"  {lcd} latest height={latest_height}")

        old_height = max(1, latest_height - cfg["blocks_per_day"] * 365)
        ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool",
                           headers={"x-cosmos-block-height": str(old_height)})
        if ok:
            bonded_old = res["pool"]["bonded_tokens"]
            # Guard against gateways that silently ignore the height header and
            # return live state: bonded a year ago must differ from live bonded.
            if bonded_old == live_bonded:
                print(f"  {lcd} FAKE ARCHIVE @ {old_height}: bonded identical to live -- header ignored")
                log.append({"lcd": lcd, "liveness": "OK",
                            "archive": "FAIL height header ignored (old bonded == live bonded)"})
                time.sleep(0.5)
                continue
            print(f"  {lcd} ARCHIVE OK @ {old_height}: bonded={bonded_old[:20]}")
            log.append({"lcd": lcd, "liveness": "OK", "archive": f"PASS @ {old_height}"})
            return lcd, latest_height, log
        print(f"  {lcd} archive probe FAILED @ {old_height}: {res}")
        log.append({"lcd": lcd, "liveness": "OK", "archive": f"FAIL {res}"})
        time.sleep(0.5)
    return None, None, log


# ---------- Task B helpers ----------
def parse_block_time(lcd, height):
    ok, res = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/{height}", timeout=15)
    if not ok:
        raise RuntimeError(f"block {height}: {res}")
    t_str = res["block"]["header"]["time"]  # RFC3339, ns precision
    base, _, frac = t_str.rstrip("Z").partition(".")
    frac = (frac + "000000")[:6]
    return datetime.fromisoformat(f"{base}.{frac}+00:00")


def get_earliest_block(lcd):
    """Return (height, time) of the earliest block the node serves."""
    ok, res = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/1", timeout=15)
    if ok:
        return 1, parse_block_time(lcd, 1)
    # Pruned block store: error text usually reveals the floor, e.g.
    # "lowest height is 12345" or "base height: 12345"
    import re
    m = re.search(r"(?:lowest height is|base height:)\s*(\d+)", str(res))
    if m:
        h = int(m.group(1))
        return h, parse_block_time(lcd, h)
    raise RuntimeError(f"cannot determine earliest block: {res}")


def find_month_end_block(lcd, year, month, lo, hi, pace=0.05):
    last_day = calendar.monthrange(year, month)[1]
    target = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        t = parse_block_time(lcd, mid)
        if t <= target:
            lo = mid
        else:
            hi = mid
        time.sleep(pace)
    t_lo = parse_block_time(lcd, lo)
    if t_lo > target:
        # Chain's earliest stored block postdates this month-end (e.g. chain
        # restarted at height 1 after the panel window began) -- no valid block.
        raise RuntimeError(
            f"no block at/before {target.date()}: earliest candidate {lo} is at {t_lo.isoformat()}")
    return lo, t_lo


def get_observed_months(panel, cmc_id):
    rows = panel[(panel["cmc_id"] == cmc_id) & (panel["status"] == "observed")]
    return sorted(rows["month_end"].str[:7].unique())


# ---------- Task C: build series ----------
def build_chain_series(sym, cfg, lcd, latest_height, panel):
    cmc_id, decimals, denom = cfg["cmc_id"], cfg["decimals"], cfg["denom"]
    panel_cid = panel[(panel["cmc_id"] == cmc_id) & panel["circulating_supply"].notna()][
        ["month_end", "circulating_supply"]].set_index("month_end")
    months = get_observed_months(panel, cmc_id)
    genesis = datetime.fromisoformat(cfg["genesis_date"]).replace(tzinfo=timezone.utc)
    pace = cfg.get("search_pace", 0.05)

    earliest_h, earliest_t = get_earliest_block(lcd)
    print(f"  {sym}: earliest stored block {earliest_h} at {earliest_t.isoformat()[:19]}Z")

    rows = []
    lo = earliest_h
    for ym in months:
        year, mon = int(ym[:4]), int(ym[5:7])
        last_day = calendar.monthrange(year, mon)[1]
        month_end_dt = datetime(year, mon, last_day, 23, 59, 59, tzinfo=timezone.utc)
        if month_end_dt < genesis:
            continue
        if month_end_dt > datetime.now(timezone.utc):
            continue
        if month_end_dt < earliest_t:
            print(f"  {sym} {ym}: predates earliest stored block ({earliest_t.date()}) -- skip")
            continue
        try:
            block_h, block_t = find_month_end_block(lcd, year, mon, lo, latest_height, pace=pace)
        except RuntimeError as e:
            print(f"  {sym} {ym}: binary search failed: {e}")
            continue
        lo = block_h

        ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool",
                           headers={"x-cosmos-block-height": str(block_h)})
        if not ok:
            print(f"  {sym} {ym}: pool query failed at {block_h}: {res}")
            continue
        bonded_raw = int(res["pool"]["bonded_tokens"])
        staked_native = bonded_raw / (10 ** decimals)

        month_end_str = f"{year}-{mon:02d}-{last_day:02d}"
        if month_end_str not in panel_cid.index:
            print(f"  {sym} {ym}: no circulating supply in panel -- skip")
            continue
        circ = float(panel_cid.loc[month_end_str, "circulating_supply"])
        staking_ratio = staked_native / circ if circ > 0 else None

        rows.append({
            "cmc_id": cmc_id, "symbol": sym, "month_end": month_end_str,
            "staked_native": round(staked_native, 4),
            "circulating_supply": round(circ, 4),
            "staking_ratio": round(staking_ratio, 6) if staking_ratio else None,
            "source": f"cosmos_lcd_pool@{block_h}",
            "flag": f"{denom} / 10^{decimals}; block_time={block_t.isoformat()[:19]}Z",
        })
        print(f"  {sym} {ym}: height={block_h}, staked={staked_native:,.0f}, ratio={staking_ratio:.4f}")
    return rows


def main():
    panel = pd.read_csv(ROOT / "03_data/universe_panel.csv")

    archive_confirmed = {}
    probe_log = {}
    for sym, cfg in CHAIN_CONFIG.items():
        print(f"\n=== {sym} probe ===")
        lcd, height, log = probe_chain(sym, cfg)
        probe_log[sym] = log
        if lcd:
            print(f"  --> USE: {lcd} (latest {height})")
            archive_confirmed[sym] = (lcd, height)
        else:
            print(f"  --> NO ARCHIVE NODE FOUND for {sym}")

    PROBE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PROBE_JSON.write_text(json.dumps(probe_log, indent=2))

    all_rows = []
    for sym, cfg in CHAIN_CONFIG.items():
        if sym not in archive_confirmed:
            continue
        lcd, latest_height = archive_confirmed[sym]
        print(f"\n=== {sym} build (lcd={lcd}) ===")
        chain_rows = build_chain_series(sym, cfg, lcd, latest_height, panel)
        all_rows.extend(chain_rows)
        print(f"{sym}: {len(chain_rows)} months built")

    if not all_rows:
        print("\nNo rows built -- nothing written.")
        return

    # stdlib csv writer: pandas.to_csv is broken in this env (partial pandas
    # install, missing pandas.io.formats.csvs on lazy import)
    import csv as _csv
    fieldnames = ["cmc_id", "symbol", "month_end", "staked_native",
                  "circulating_supply", "staking_ratio", "source", "flag"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} rows to {OUT_CSV}")
    df_out = pd.DataFrame(all_rows)
    print(df_out.groupby("symbol").agg(
        n=("month_end", "count"), first=("month_end", "min"),
        last=("month_end", "max"), mean_ratio=("staking_ratio", "mean")))

    # ---------- Task D: cross-check vs live pool ----------
    print("\n=== Cross-check (built latest vs live pool) ===")
    for sym, cfg in CHAIN_CONFIG.items():
        if sym not in archive_confirmed:
            continue
        lcd = archive_confirmed[sym][0]
        ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool", timeout=15)
        if not ok:
            print(f"{sym}: live pool query failed: {res}")
            continue
        live_bonded = int(res["pool"]["bonded_tokens"]) / (10 ** cfg["decimals"])
        df_sym = df_out[df_out["symbol"] == sym]
        last_row = df_sym.sort_values("month_end").iloc[-1]
        built_val = last_row["staked_native"]
        drift_pct = abs(built_val - live_bonded) / live_bonded * 100
        status = "PASS" if drift_pct < 5 else "WARN (staking shifted since last panel month)"
        print(f"{sym}: built_latest={built_val:,.0f}  live={live_bonded:,.0f}  drift={drift_pct:.2f}%  {status}")


if __name__ == "__main__":
    main()
