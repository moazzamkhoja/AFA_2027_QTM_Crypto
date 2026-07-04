"""_s028_sonic_fetch.py -- Session 028 A3: fetch full Sonic SFC event history (chainid 146).

SFC proxy 0xFC00FACE...0000; implementation ABI (verified) has:
  Delegated(address indexed delegator, uint256 indexed toValidatorID, uint256 amount)
  Undelegated(address indexed delegator, uint256 indexed toValidatorID, uint256 indexed wrID, uint256 amount)
  RestakedRewards(address indexed delegator, uint256 indexed toValidatorID, uint256 rewards)
totalStake replay = cumsum(Delegated) + cumsum(RestakedRewards) - cumsum(Undelegated);
cross-check vs live totalStake() getter. Raw streams cached per event type.
"""

import json

from _s028_evm import REPO, keccak_topic, getlogs_window, latest_block

SFC = "0xFC00FACE00000000000000000000000000000000"
RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
RAW.mkdir(parents=True, exist_ok=True)

EVENTS = {
    "delegated": "Delegated(address,uint256,uint256)",
    "undelegated": "Undelegated(address,uint256,uint256,uint256)",
    "restaked": "RestakedRewards(address,uint256,uint256)",
}


def main():
    hi = latest_block(146)
    print(f"scanning Sonic SFC events from 1 to {hi:,}")
    for name, sig in EVENTS.items():
        cf = RAW / f"sonic_{name}.json"
        if cf.exists() and json.loads(cf.read_text()).get("complete"):
            print(f"  {name}: cached, skip")
            continue
        logs = getlogs_window(SFC, keccak_topic(sig), 1, hi, 146)
        slim = [{"b": int(l["blockNumber"], 16), "t": int(l["timeStamp"], 16),
                 "topics": l["topics"], "data": l["data"]} for l in logs]
        slim.sort(key=lambda x: x["b"])
        cf.write_text(json.dumps({"scan_to": hi, "complete": True, "logs": slim}))
        print(f"  {name}: {len(slim)} logs, first {slim[0]['b'] if slim else '-'}, "
              f"last {slim[-1]['b'] if slim else '-'}")


if __name__ == "__main__":
    main()
