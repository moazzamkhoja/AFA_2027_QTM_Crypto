"""_s028_avax_fetch.py -- Session 028 A8: AVAX daily staking weights, KEYLESS.

Ava Labs' official Metrics API (the source behind the Avalanche explorer graphs)
answers WITHOUT any key at:
    GET https://metrics.avax.network/v2/networks/mainnet/metrics/validatorWeight
    GET https://metrics.avax.network/v2/networks/mainnet/metrics/delegatorWeight
Daily values in nAVAX (1e9), history back to network genesis (2020-09), paginated
via nextPageToken. Entry 42/47 left the free-vs-paid gate "unclear from pricing
pages" -- resolved live this session: the network staking metrics are keyless.

Semantics verified live: validatorWeight EXCLUDES delegations -- P-Chain
platform.getTotalStake (199.87M AVAX live) matches validatorWeight+delegatorWeight
(196.7M at yesterday's snapshot, stake currently moving ~2M/day), not
validatorWeight alone (159.9M). Total staked = validatorWeight + delegatorWeight.
"""

import json
import time

import requests

from _s028_evm import REPO

RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
RAW.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (research; academic)"}
BASE = "https://metrics.avax.network/v2/networks/mainnet/metrics/"


def fetch_metric(metric):
    rows, token, tries = [], None, 0
    while True:
        params = {"pageSize": 2000}
        if token:
            params["pageToken"] = token
        try:
            r = requests.get(BASE + metric, params=params, timeout=30, headers=H)
            j = r.json()
        except Exception as e:
            tries += 1
            if tries > 5:
                raise
            time.sleep(2 * tries)
            continue
        tries = 0
        rows.extend(j.get("results", []))
        token = j.get("nextPageToken")
        print(f"  {metric}: {len(rows)} rows...", end="\r")
        if not token:
            break
        time.sleep(0.3)
    print(f"  {metric}: {len(rows)} rows total")
    return rows


def main():
    for metric in ["validatorWeight", "delegatorWeight"]:
        cf = RAW / f"avax_{metric}.json"
        if cf.exists() and json.loads(cf.read_text()).get("complete"):
            print(f"  {metric}: cached, skip")
            continue
        rows = fetch_metric(metric)
        cf.write_text(json.dumps({"complete": True, "rows": rows}))


if __name__ == "__main__":
    main()
