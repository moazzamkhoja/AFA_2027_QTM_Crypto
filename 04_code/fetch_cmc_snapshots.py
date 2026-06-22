"""
fetch_cmc_snapshots.py  --  Phase 0, step 1

Pull point-in-time historical market-cap rankings from CoinMarketCap's free
historical listings endpoint, one snapshot per month-end, for the AFA 2027 QTM
Crypto asset universe (DATA_SPECIFICATION.md Section 2).

WHY THIS SOURCE (see DATA_DECISIONS_LOG.md):
  CoinGecko's public API caps historical data at the past 365 days (error
  10012), so it cannot build point-in-time rankings back to 2015 without a paid
  plan. CoinMarketCap's data-api historical listings endpoint is free, requires
  no key, serves daily snapshots back to 2013, and -- crucially for avoiding
  survivorship bias (Section 2.1) -- returns the assets *as ranked on that date*,
  including coins that later delisted or died.

Endpoint:
  https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical
  params: date=YYYY-MM-DD, start=1, limit=N, convertId=2781 (USD)

Output:
  03_data/raw/cmc_snapshots/<YYYY-MM-DD>.json   (one raw payload per month-end)
  Re-runs skip months already cached, so the API is hit at most once per month.
"""

import json
import time
import sys
from datetime import date, timedelta
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "03_data" / "raw" / "cmc_snapshots"
ENDPOINT = "https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listings/historical"
USD_CONVERT_ID = 2781
LIMIT = 1000          # headroom around the top-250 cutoff for rank-sensitivity analysis
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Sample period: Section 2.2 -- Aug 2015 through the most recently completed month.
START_YEAR, START_MONTH = 2015, 8
END_YEAR, END_MONTH = 2026, 5     # today is 2026-06-22, so May 2026 is the last complete month

SLEEP_BETWEEN = 2.5   # polite pacing
MAX_RETRIES = 4
FALLBACK_DAYS = 6     # if the exact last-of-month snapshot is empty, walk back up to N days


def month_ends(y0, m0, y1, m1):
    """Yield the last calendar day of each month in [start, end]."""
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        # first day of next month minus one day
        if m == 12:
            nxt = date(y + 1, 1, 1)
        else:
            nxt = date(y, m + 1, 1)
        yield nxt - timedelta(days=1)
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def fetch_one(d: date):
    """Fetch a single snapshot, walking back a few days if the target date is empty."""
    for back in range(FALLBACK_DAYS + 1):
        target = d - timedelta(days=back)
        params = {
            "date": target.isoformat(),
            "start": 1,
            "limit": LIMIT,
            "convertId": USD_CONVERT_ID,
        }
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = requests.get(ENDPOINT, params=params, headers=HEADERS, timeout=40)
                if r.status_code == 200:
                    payload = r.json()
                    data = payload.get("data") or []
                    if data:
                        return target, payload
                    break  # 200 but empty -> try an earlier day
                else:
                    time.sleep(SLEEP_BETWEEN * attempt)
            except Exception as e:
                print(f"    attempt {attempt} error: {e}")
                time.sleep(SLEEP_BETWEEN * attempt)
    return None, None


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = list(month_ends(START_YEAR, START_MONTH, END_YEAR, END_MONTH))
    print(f"Fetching {len(targets)} monthly snapshots -> {OUT_DIR}")
    fetched, skipped, failed = 0, 0, []
    for d in targets:
        out = OUT_DIR / f"{d.isoformat()}.json"
        if out.exists():
            skipped += 1
            continue
        actual, payload = fetch_one(d)
        if payload is None:
            print(f"  {d}  FAILED")
            failed.append(d.isoformat())
            continue
        n = len(payload.get("data") or [])
        # Stamp the requested month-end and the date actually served, for auditability.
        payload["_meta"] = {"requested_month_end": d.isoformat(),
                            "served_date": actual.isoformat(),
                            "n_assets": n}
        out.write_text(json.dumps(payload), encoding="utf-8")
        fetched += 1
        flag = "" if actual == d else f"  (fell back to {actual})"
        print(f"  {d}  n={n}{flag}")
        time.sleep(SLEEP_BETWEEN)
    print(f"\nDone. fetched={fetched} skipped(cached)={skipped} failed={len(failed)}")
    if failed:
        print("FAILED months:", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
