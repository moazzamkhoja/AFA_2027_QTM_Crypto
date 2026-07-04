"""_s028_bnb_fetch.py -- Session 028 A1: fetch full BSC StakeHub event history (chainid 56).

Fetches and caches ALL pool-affecting StakeHub events from genesis to the latest block:
  Delegated / Undelegated / RewardDistributed / ValidatorSlashed / MigrateSuccess
Each stream cached as JSON under 03_data/raw/phase1_onchain/pos_coins_evm/.
Reconciliation & month-end series happen in a separate step so a fetch crash never
corrupts analysis. NetworkErrors raise (session-025 lesson: never swallow into empty).
"""

import json
from pathlib import Path

from _s028_evm import REPO, keccak_topic, getlogs_window, latest_block

HUB = "0x0000000000000000000000000000000000002002"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
RAW.mkdir(parents=True, exist_ok=True)

EVENTS = {
    "delegated": "Delegated(address,address,uint256,uint256)",
    "undelegated": "Undelegated(address,address,uint256,uint256)",
    "reward": "RewardDistributed(address,uint256)",
    "slashed": "ValidatorSlashed(address,uint256,uint256,uint8)",
    "migrate": "MigrateSuccess(address,address,uint256,uint256)",
    "redelegated": "Redelegated(address,address,address,uint256,uint256,uint256)",
}

# StakeHub activated with the BC-fusion first phase (2024-03); scan from 2024-01-01
# block (~34,850,000) to be safe -- earlier ranges return zero logs cheaply.
SCAN_FROM = 34_000_000


def main():
    hi = latest_block(56)
    print(f"scanning StakeHub events from {SCAN_FROM:,} to {hi:,}")
    meta = {"scan_from": SCAN_FROM, "scan_to": hi}
    (RAW / "bnb_scan_meta.json").write_text(json.dumps(meta))
    for name, sig in EVENTS.items():
        cf = RAW / f"bnb_{name}.json"
        if cf.exists():
            d = json.loads(cf.read_text())
            if d.get("scan_to") == hi or d.get("complete"):
                print(f"  {name}: cached ({len(d['logs'])} logs), skip")
                continue
        topic = keccak_topic(sig)
        logs = getlogs_window(HUB, topic, SCAN_FROM, hi, 56)
        slim = [{"b": int(l["blockNumber"], 16), "t": int(l["timeStamp"], 16),
                 "topics": l["topics"], "data": l["data"]} for l in logs]
        slim.sort(key=lambda x: x["b"])
        cf.write_text(json.dumps({"scan_to": hi, "complete": True, "logs": slim}))
        print(f"  {name}: {len(slim)} logs fetched, first block "
              f"{slim[0]['b'] if slim else '-'}, last {slim[-1]['b'] if slim else '-'}")


if __name__ == "__main__":
    main()
