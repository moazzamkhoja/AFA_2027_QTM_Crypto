"""_s029_pol_fetch.py -- Session 029 (Entry 78): POL/MATIC staking history fetch.

Polygon PoS validator+delegator stake is managed by StakeManager on ETHEREUM MAINNET
(0x5e3Ef299fDDf15eAa0432E6e66473ace8c13D908, an UpgradableProxy). The chain's own
aggregate getter is `currentValidatorSetTotalStake()` (validatorState.amount = active
validator self-stake + ALL delegations; live 3.58B POL, matching the official staking
dashboard). NOT `totalStaked()` -- that tracks validator SELF-stake only (11.7M live).

Etherscan's proxy eth_call ignores historical tags (Entry-71 landmine), but
eth.drpc.org serves FULL mainnet archive eth_call KEYLESS (probed live this session:
block 11.0M/2020-10 -> 962M; 14.0M/2022-01 -> 2.24B; 20.1M/2024-06 -> 3.67B).
Same pattern as CELO/Forno (Entry 72).

Fetches month-end values 2020-06..2026-05 into pol_stakemanager_history.json, plus a
superset cross-check series (POL+MATIC token balanceOf(StakeManager) at the same
blocks -- balance = stake + unclaimed rewards, expected ratio slightly >= 1).
"""

import json
import time
from pathlib import Path

import requests

from _s028_evm import REPO, api, eth_call, keccak_topic
from phase1_channel1_pos_coins_evm import month_ends, monthend_blocks

RAW = REPO / "03_data" / "raw" / "phase1_onchain" / "pos_coins_evm"
SM = "0x5e3Ef299fDDf15eAa0432E6e66473ace8c13D908"
MATIC_TOK = "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0"
POL_TOK = "0x455e53CBB86018Ac2B8092FdCd39d8444aFFC3F6"
DRPC = "https://eth.drpc.org"
SEL_TOTAL = keccak_topic("currentValidatorSetTotalStake()")[:10]
SEL_BAL = keccak_topic("balanceOf(address)")[:10] + SM[2:].lower().rjust(64, "0")


def drpc_call(to, data, block, tries=5):
    for t in range(1, tries + 1):
        try:
            r = requests.post(DRPC, json={"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                                          "params": [{"to": to, "data": data}, block]},
                              timeout=30).json()
            if r.get("result") and r["result"] != "0x":
                return int(r["result"], 16)
            if r.get("error"):
                # historical-state miss or revert: report, do not retry-storm
                if t == tries:
                    return None
            time.sleep(0.4 * t)
        except Exception:
            time.sleep(0.8 * t)
    return None


def main():
    yms = month_ends("2020-06", "2026-05")
    blocks = monthend_blocks(yms, 1)
    cf = RAW / "pol_stakemanager_history.json"
    cache = json.loads(cf.read_text()) if cf.exists() else {}
    for ym in yms:
        b = blocks.get(ym)
        if b is None or ym in cache:
            continue
        total = drpc_call(SM, SEL_TOTAL, hex(b))
        balM = drpc_call(MATIC_TOK, SEL_BAL, hex(b))
        balP = drpc_call(POL_TOK, SEL_BAL, hex(b))
        cache[ym] = {"block": b, "total_stake": total, "matic_bal": balM, "pol_bal": balP}
        cf.write_text(json.dumps(cache))
        t = f"{total/1e18:,.0f}" if total is not None else "None"
        bal = (balM or 0) + (balP or 0)
        ratio = bal / total if (total and bal) else float("nan")
        print(f"  {ym} block {b:,}: total_stake={t} bal/stake={ratio:.4f}", flush=True)
        time.sleep(0.35)

    # live cross-checks:
    # (1) independent provider: drpc latest vs Etherscan proxy eth_call latest
    live_drpc = drpc_call(SM, SEL_TOTAL, "latest")
    live_scan = int(eth_call(SM, SEL_TOTAL, 1), 16)
    d = (live_drpc - live_scan) / live_scan
    print(f"live: drpc {live_drpc/1e18:,.0f} vs etherscan {live_scan/1e18:,.0f} "
          f"-> drift {d:+.5%}")
    # (2) superset: current POL balance >= stake
    balP = drpc_call(POL_TOK, SEL_BAL, "latest")
    print(f"live POL balanceOf(SM) {balP/1e18:,.0f} / stake = {balP/live_drpc:.4f} "
          f"(expected slightly >= 1: unclaimed rewards buffer)")


if __name__ == "__main__":
    main()
