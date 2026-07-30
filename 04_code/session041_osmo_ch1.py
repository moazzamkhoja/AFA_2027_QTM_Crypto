# Session 041 — OSMO (12220) ch1 via Cosmos Archive LCD (Task C)
# Free, keyless. Same pool-at-month-end-block approach as session 040 (CRO/KAVA).
# Archive sweep result (session 041): all 16 chain-registry REST endpoints pruned or
# fake-archive (osmosis.api.pocket.network ignores x-cosmos-block-height — same
# landmine family as sei.api.pocket.network, Entry 91); osmosis-api.noders.services
# is the ONLY real archive found, retention ~598 days (app state back to ~2024-12).
# Months predating the retention floor are skipped by the earliest-block guard.
import calendar
import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "03_data/phase1/channel1_cosmos_osmo.csv"
PROBE_JSON = ROOT / "03_data/phase1/session041_osmo_probe.json"

CFG = {
    "cmc_id": 12220, "symbol": "OSMO", "denom": "uosmo", "decimals": 6,
    "lcd": "https://osmosis-api.noders.services",
    "genesis_date": "2021-06-18", "blocks_per_day": 15000,
    "search_pace": 0.2,
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AFA2027-QTM-research/1.0"})


def get_json(url, headers=None, timeout=20, retries=3):
    last_err = "retries exhausted"
    for attempt in range(retries):
        try:
            r = SESSION.get(url, headers=headers, timeout=timeout)
            if r.status_code >= 500 and "invalid denom" in r.text:
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


def parse_block_time(lcd, height):
    ok, res = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/{height}", timeout=15)
    if not ok:
        raise RuntimeError(f"block {height}: {res}")
    t_str = res["block"]["header"]["time"]
    base, _, frac = t_str.rstrip("Z").partition(".")
    frac = (frac + "000000")[:6]
    return datetime.fromisoformat(f"{base}.{frac}+00:00")


def get_earliest_block(lcd, latest_height, pace):
    """(height, time) of the earliest block the node serves. blocks/1 error text
    usually reveals the floor; fall back to binary search if it doesn't."""
    ok, res = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/1", timeout=15)
    if ok:
        return 1, parse_block_time(lcd, 1)
    m = re.search(r"(?:lowest height is|base height:)\s*(\d+)", str(res))
    if m:
        h = int(m.group(1))
        return h, parse_block_time(lcd, h)
    bad, good = 1, latest_height
    while good - bad > 1:
        mid = (bad + good) // 2
        ok, _ = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/{mid}", timeout=15)
        if ok:
            good = mid
        else:
            bad = mid
        time.sleep(pace)
    return good, parse_block_time(lcd, good)


def find_month_end_block(lcd, year, month, lo, hi, pace):
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
        raise RuntimeError(
            f"no block at/before {target.date()}: earliest candidate {lo} is at {t_lo.isoformat()}")
    return lo, t_lo


def main():
    lcd, pace = CFG["lcd"], CFG["search_pace"]
    cmc_id, decimals, denom = CFG["cmc_id"], CFG["decimals"], CFG["denom"]
    probe = {"lcd": lcd}

    # Re-confirm archive (fake-archive guard) before building
    ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool")
    if not ok:
        print(f"pool liveness FAIL: {res}"); return
    live_bonded = res["pool"]["bonded_tokens"]
    ok, res = get_json(f"{lcd}/cosmos/base/tendermint/v1beta1/blocks/latest")
    if not ok:
        print(f"latest block FAIL: {res}"); return
    latest_height = int(res["block"]["header"]["height"])
    old_h = latest_height - CFG["blocks_per_day"] * 365
    ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool",
                       headers={"x-cosmos-block-height": str(old_h)})
    if not ok or res["pool"]["bonded_tokens"] == live_bonded:
        print(f"archive re-probe FAIL @ {old_h}: "
              f"{'header ignored (fake archive)' if ok else res}")
        return
    probe["archive"] = f"PASS @ {old_h}"
    print(f"{lcd} ARCHIVE CONFIRMED @ {old_h} (latest {latest_height})")

    earliest_h, earliest_t = get_earliest_block(lcd, latest_height, pace)
    probe["earliest_block"] = {"height": earliest_h, "time": earliest_t.isoformat()}
    print(f"earliest stored block {earliest_h} at {earliest_t.isoformat()[:19]}Z")
    PROBE_JSON.write_text(json.dumps(probe, indent=2))

    panel = pd.read_csv(ROOT / "03_data/universe_panel.csv")
    mine = panel[(panel["cmc_id"] == cmc_id) & (panel["status"] == "observed")]
    months = sorted(mine["month_end"].str[:7].unique())
    circ_by_month = mine[mine["circulating_supply"].notna()][
        ["month_end", "circulating_supply"]].set_index("month_end")
    genesis = datetime.fromisoformat(CFG["genesis_date"]).replace(tzinfo=timezone.utc)

    rows = []
    lo = earliest_h
    for ym in months:
        year, mon = int(ym[:4]), int(ym[5:7])
        last_day = calendar.monthrange(year, mon)[1]
        month_end_dt = datetime(year, mon, last_day, 23, 59, 59, tzinfo=timezone.utc)
        if month_end_dt < genesis or month_end_dt > datetime.now(timezone.utc):
            continue
        if month_end_dt < earliest_t:
            print(f"OSMO {ym}: predates earliest stored block ({earliest_t.date()}) -- skip")
            continue
        try:
            block_h, block_t = find_month_end_block(lcd, year, mon, lo, latest_height, pace)
        except RuntimeError as e:
            print(f"OSMO {ym}: binary search failed: {e}")
            continue
        lo = block_h

        ok, res = get_json(f"{lcd}/cosmos/staking/v1beta1/pool",
                           headers={"x-cosmos-block-height": str(block_h)})
        if not ok:
            print(f"OSMO {ym}: pool query failed at {block_h}: {res}")
            continue
        bonded_raw = int(res["pool"]["bonded_tokens"])
        staked_native = bonded_raw / (10 ** decimals)

        month_end_str = f"{year}-{mon:02d}-{last_day:02d}"
        if month_end_str not in circ_by_month.index:
            print(f"OSMO {ym}: no circulating supply in panel -- skip")
            continue
        circ = float(circ_by_month.loc[month_end_str, "circulating_supply"])
        ratio = staked_native / circ if circ > 0 else None

        rows.append({
            "cmc_id": cmc_id, "symbol": "OSMO", "month_end": month_end_str,
            "staked_native": round(staked_native, 4),
            "circulating_supply": round(circ, 4),
            "staking_ratio": round(ratio, 6) if ratio else None,
            "source": f"cosmos_lcd_pool@{block_h}",
            "flag": f"{denom} / 10^{decimals}; block_time={block_t.isoformat()[:19]}Z",
        })
        print(f"OSMO {ym}: height={block_h}, staked={staked_native:,.0f}, ratio={ratio:.4f}")

    if not rows:
        print("No rows built -- nothing written."); return

    fieldnames = ["cmc_id", "symbol", "month_end", "staked_native",
                  "circulating_supply", "staking_ratio", "source", "flag"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {OUT_CSV}")

    # Cross-check: latest built month vs live pool
    live = int(live_bonded) / (10 ** decimals)
    built = rows[-1]["staked_native"]
    drift = abs(built - live) / live * 100
    print(f"Cross-check: built_latest={built:,.0f} live={live:,.0f} drift={drift:.2f}% "
          f"{'PASS' if drift < 5 else 'WARN' if drift <= 20 else 'INVESTIGATE'}")


if __name__ == "__main__":
    main()
