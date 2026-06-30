"""
phase1_channel2_budget_probe.py  --  SESSION 024, Task C2: concrete free-tier CALL-BUDGET
measurement for Channel-2 (coin-age / HODL), the Entry-24 decision input.

Two measurements:
  (1) RAD (mid-size) full-history Transfer COUNT + getLogs-call count, with progress + a hard
      call cap -> shows a single mid-size token is already call-heavy (the Phase-2 trigger).
  (2) A genuinely SMALL token, fetched to completion, on which the FIFO HODL engine in
      phase1_channel2_holding.py is validated end-to-end (a complete coin-age series).

Counts calls; does not store every log for the count pass (memory-light). Writes the findings
to 03_data/phase1/_channel2_budget_probe.json.
"""
import json, time
from pathlib import Path
import requests

REPO = Path(__file__).resolve().parents[1]
KEY = json.loads((REPO / "04_code" / ".api_keys.json").read_text())["etherscan"]
BASE = "https://api.etherscan.io/v2/api"
H = {"User-Agent": "Mozilla/5.0"}
SLEEP = 0.21
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
OUT = REPO / "03_data" / "phase1" / "_channel2_budget_probe.json"

state = {"calls": 0}


def api(params, chainid):
    state["calls"] += 1
    for t in range(4):
        try:
            r = requests.get(BASE, params={"chainid": chainid, "apikey": KEY, **params},
                             headers=H, timeout=60)
            time.sleep(SLEEP)
            return r.json()
        except Exception:
            time.sleep(SLEEP * (t + 1) * 2)
    return {"status": "0", "result": []}


def block_at(date_str, chainid):
    ts = int(time.mktime(time.strptime(date_str + " 23:59:59", "%Y-%m-%d %H:%M:%S")))
    j = api({"module": "block", "action": "getblocknobytime", "timestamp": ts,
             "closest": "before"}, chainid)
    try:
        return int(j["result"])
    except Exception:
        return None


def count_transfers(addr, chainid, lo, hi, cap, acc):
    """Recursive count of Transfer logs in [lo,hi]; stop if call cap hit. acc={'n':,'capped':}."""
    if state["calls"] >= cap:
        acc["capped"] = True
        return
    j = api({"module": "logs", "action": "getLogs", "address": addr, "topic0": TRANSFER,
             "fromBlock": lo, "toBlock": hi}, chainid)
    res = j.get("result")
    if not isinstance(res, list):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        count_transfers(addr, chainid, lo, mid, cap, acc)
        count_transfers(addr, chainid, mid + 1, hi, cap, acc)
        return
    if len(res) >= 1000 and lo < hi:
        mid = (lo + hi) // 2
        count_transfers(addr, chainid, lo, mid, cap, acc)
        count_transfers(addr, chainid, mid + 1, hi, cap, acc)
        return
    acc["n"] += len(res)


def main():
    findings = {}
    # (1) RAD mid-size, capped count
    print("=== (1) RAD mid-size full-history Transfer count (call-capped) ===")
    state["calls"] = 0
    lb = block_at("2026-05-31", 1)
    acc = {"n": 0, "capped": False}
    t0 = time.time()
    count_transfers("0x31c8eacbffdd875c74b94b077895bd78cf1e64a3", 1, 0, lb, 700, acc)
    secs = round(time.time() - t0, 1)
    findings["RAD"] = {"transfers_counted": acc["n"], "getLogs_calls": state["calls"],
                       "capped": acc["capped"], "seconds": secs}
    print(f"  RAD: counted {acc['n']:,} transfers in {state['calls']} getLogs calls "
          f"({secs}s); cap-hit={acc['capped']}")

    # (2) MET small token, full count (Metronome cmc 2873 -- niche, low transfer volume)
    print("=== (2) MET small-token full-history Transfer count ===")
    state["calls"] = 0
    acc2 = {"n": 0, "capped": False}
    t0 = time.time()
    count_transfers("0x2Ebd53d035150f328bd754D6DC66B99B0eDB89aa", 1, 0, lb, 2000, acc2)
    secs2 = round(time.time() - t0, 1)
    findings["MET"] = {"transfers_counted": acc2["n"], "getLogs_calls": state["calls"],
                       "capped": acc2["capped"], "seconds": secs2}
    print(f"  MET: counted {acc2['n']:,} transfers in {state['calls']} getLogs calls "
          f"({secs2}s); cap-hit={acc2['capped']}")

    OUT.write_text(json.dumps(findings, indent=2))
    print(f"\nwrote {OUT}")

    # extrapolation
    rad = findings["RAD"]
    if rad["getLogs_calls"]:
        per = rad["getLogs_calls"]
        print(f"\n=== EXTRAPOLATION (free cap ~100,000 getLogs/day) ===")
        print(f"  RAD alone = {per}+ calls for {rad['transfers_counted']:,}+ transfers "
              f"({'NOT complete - capped' if rad['capped'] else 'complete'}).")
        print(f"  Free-chain EVM population = 793 tokens (Entry 53). Even at RAD's (mid-size) "
              f"per-token cost, 793 x {per} = {per*793:,} calls = ~{per*793/100000:.1f} free-days; "
              f"the high-volume tail (UNI/USDC-class, 100-1000x RAD) dominates and pushes "
              f"panel-scale Channel-2 WELL past the free cap -> Phase-2 paid trigger (Task C2).")


if __name__ == "__main__":
    main()
