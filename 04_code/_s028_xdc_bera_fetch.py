"""_s028_xdc_bera_fetch.py -- Session 028 A4/A5: fetch XDC validator + Berachain deposit events.

XDC (chainid 50): XDCValidator 0x...0088 holds staked XDC natively.
  Replay = cumsum(Propose._cap) + cumsum(Vote._cap) - cumsum(Unvote._cap) - cumsum(Withdraw._cap)
  which should equal the contract's native balance; live cross-check = sum getCandidateCap
  over getCandidates() (active stake) and the contract balance (stake incl. pending withdrawals).

BERA (chainid 80094): BeaconDeposit 0x4242...4242, ETH2-style
  Deposit(bytes pubkey, bytes credentials, uint64 amountGwei, bytes signature, uint64 index).
  Deposits-only replay (withdrawals are consensus-side, invisible in EVM logs) -- cross-check
  decides whether that is shippable.
"""

import json

from _s028_evm import REPO, keccak_topic, getlogs_window, latest_block

RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
RAW.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("xdc", 50, "0x0000000000000000000000000000000000000088", {
        "propose": "Propose(address,address,uint256)",
        "vote": "Vote(address,address,uint256)",
        "unvote": "Unvote(address,address,uint256)",
        "withdraw": "Withdraw(address,uint256,uint256)",
        "resign": "Resign(address,address)",
    }),
    ("bera", 80094, "0x4242424242424242424242424242424242424242", {
        "deposit": "Deposit(bytes,bytes,uint64,bytes,uint64)",
    }),
]


def main():
    for chain_name, cid, addr, events in JOBS:
        hi = latest_block(cid)
        print(f"{chain_name}: scanning {addr} from 1 to {hi:,} (chainid {cid})")
        for name, sig in events.items():
            cf = RAW / f"{chain_name}_{name}.json"
            if cf.exists() and json.loads(cf.read_text()).get("complete"):
                print(f"  {name}: cached, skip")
                continue
            logs = getlogs_window(addr, keccak_topic(sig), 1, hi, cid)
            slim = [{"b": int(l["blockNumber"], 16), "t": int(l["timeStamp"], 16),
                     "topics": l["topics"], "data": l["data"]} for l in logs]
            slim.sort(key=lambda x: x["b"])
            cf.write_text(json.dumps({"scan_to": hi, "complete": True, "logs": slim}))
            print(f"  {name}: {len(slim)} logs, first {slim[0]['b'] if slim else '-'}, "
                  f"last {slim[-1]['b'] if slim else '-'}")


if __name__ == "__main__":
    main()
