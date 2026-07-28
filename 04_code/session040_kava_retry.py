# Session 040 -- retry KAVA months lost to HTTP 420 rate limits, slower pacing.
# Appends recovered months to channel1_cosmos_lcd.csv and re-sorts.
# Also: drift diagnostic -- bonded at 2026-06-30 and ~2026-07-14 to see whether
# the 23% live-vs-May drift is a genuine recent staking surge.
import csv, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from session040_cosmos_lcd import (
    CHAIN_CONFIG, get_json, find_month_end_block, get_earliest_block, OUT_CSV,
    ROOT, get_observed_months,
)

LCD = "https://api.data.kava.io"
CFG = CHAIN_CONFIG["KAVA"]
CFG["search_pace"] = 1.5  # much gentler
PACE = 1.5

def main():
    df = pd.read_csv(OUT_CSV)
    have = set(df[df["symbol"] == "KAVA"]["month_end"].str[:7])
    panel = pd.read_csv(ROOT / "03_data/universe_panel.csv")
    months = get_observed_months(panel, CFG["cmc_id"])
    # Only months at/after the state codec boundary are worth retrying
    todo = [ym for ym in months if ym >= "2024-04" and ym not in have and ym <= "2026-05"]
    print("Retry months:", todo)

    ok, res = get_json(f"{LCD}/cosmos/base/tendermint/v1beta1/blocks/latest")
    latest_height = int(res["block"]["header"]["height"])

    panel_cid = panel[(panel["cmc_id"] == CFG["cmc_id"]) & panel["circulating_supply"].notna()][
        ["month_end", "circulating_supply"]].set_index("month_end")

    import calendar
    new_rows = []
    lo = 1
    for ym in todo:
        year, mon = int(ym[:4]), int(ym[5:7])
        last_day = calendar.monthrange(year, mon)[1]
        try:
            block_h, block_t = find_month_end_block(LCD, year, mon, lo, latest_height, pace=PACE)
        except RuntimeError as e:
            print(f"  KAVA {ym}: binary search failed again: {e}")
            time.sleep(30)
            continue
        lo = 1  # months are non-contiguous; don't carry lo forward past gaps we own
        ok, res = get_json(f"{LCD}/cosmos/staking/v1beta1/pool",
                           headers={"x-cosmos-block-height": str(block_h)})
        if not ok:
            print(f"  KAVA {ym}: pool query failed at {block_h}: {res}")
            continue
        bonded_raw = int(res["pool"]["bonded_tokens"])
        staked_native = bonded_raw / 10**6
        month_end_str = f"{year}-{mon:02d}-{last_day:02d}"
        if month_end_str not in panel_cid.index:
            print(f"  KAVA {ym}: no circulating supply -- skip")
            continue
        circ = float(panel_cid.loc[month_end_str, "circulating_supply"])
        ratio = staked_native / circ if circ > 0 else None
        new_rows.append({
            "cmc_id": CFG["cmc_id"], "symbol": "KAVA", "month_end": month_end_str,
            "staked_native": round(staked_native, 4),
            "circulating_supply": round(circ, 4),
            "staking_ratio": round(ratio, 6) if ratio else None,
            "source": f"cosmos_lcd_pool@{block_h}",
            "flag": f"ukava / 10^6; block_time={block_t.isoformat()[:19]}Z",
        })
        print(f"  KAVA {ym}: height={block_h}, staked={staked_native:,.0f}, ratio={ratio:.4f}")
        time.sleep(2)

    if new_rows:
        all_rows = df.to_dict("records") + new_rows
        all_rows.sort(key=lambda r: (r["symbol"], r["month_end"]))
        fieldnames = ["cmc_id", "symbol", "month_end", "staked_native",
                      "circulating_supply", "staking_ratio", "source", "flag"]
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_rows)
        print(f"\nCSV now {len(all_rows)} rows ({len(new_rows)} recovered)")

    # ---- drift diagnostic: KAVA bonded at 2026-06-30 and ~2026-07-14 ----
    print("\n=== KAVA drift diagnostic ===")
    try:
        h_jun, t_jun = find_month_end_block(LCD, 2026, 6, 1, latest_height, pace=PACE)
        ok, res = get_json(f"{LCD}/cosmos/staking/v1beta1/pool",
                           headers={"x-cosmos-block-height": str(h_jun)})
        if ok:
            print(f"  2026-06-30 ({t_jun.date()}): bonded={int(res['pool']['bonded_tokens'])/1e6:,.0f}")
        h_mid = h_jun + CFG["blocks_per_day"] * 14
        ok, res = get_json(f"{LCD}/cosmos/staking/v1beta1/pool",
                           headers={"x-cosmos-block-height": str(h_mid)})
        if ok:
            print(f"  ~2026-07-14 (block {h_mid}): bonded={int(res['pool']['bonded_tokens'])/1e6:,.0f}")
        ok, res = get_json(f"{LCD}/cosmos/staking/v1beta1/pool")
        if ok:
            print(f"  live: bonded={int(res['pool']['bonded_tokens'])/1e6:,.0f}")
    except Exception as e:
        print(f"  diagnostic failed: {e}")


if __name__ == "__main__":
    main()
