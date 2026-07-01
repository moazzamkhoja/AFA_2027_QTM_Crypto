"""
phase1_channel2_validate.py  --  SESSION 025, Task B3: clean single-deployment validation of
the panel-scale Channel-2 engine BEFORE wiring it into lambda. Session 024 noted MET's v2
migration muddied its 12m window; CRV and AAVE are clean single-deployment governance tokens
for which we already hold Channel-1/3 series. Runs the SAME panel functions (fetch_token +
compute_rows, with the all-month contract screen) and prints the raw-vs-screened HODL-6m
series so we can judge it's economically reasonable (not 95%+ or 0.1% degenerate). Writes its
own per-token checkpoints so a later panel run reuses them.

Run: PYTHONUTF8=1 PER_TOKEN_CAP=12000 python 04_code/phase1_channel2_validate.py
"""
import json, os, time
from pathlib import Path
import pandas as pd

import phase1_channel2_holding as eng
import phase1_channel2_panel as panel

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "03_data" / "universe_panel.csv"

# cmc_id, symbol, chainid, address  (clean single-deployment governance tokens that COMPLETE
# under a sane cap -- AAVE/CRV were swapped out: their multi-year Transfer histories are 1M+
# events / high-volume tail, the same throughput wall as OP, and validation needs a token that
# finishes. RAD (Radicle, ~204k transfers, the session-024 mid-size budget probe) and FORTH
# (Ampleforth governance) are clean single-deployment governance tokens whose screened HODL is
# economically interpretable.)
TARGETS = [
    (6843, "RAD",   1, "0x31c8eacbffdd875c74b94b077895bd78cf1e64a3"),
]


def main():
    eng.SLEEP = float(os.environ.get("SLEEP", "0.12"))
    pf = pd.read_csv(PANEL)
    pf["ym"] = pf["month_end"].str[:7]
    for cmc_id, sym, chainid, addr in TARGETS:
        ckf = panel.ck_path(cmc_id, sym)
        obs = pf[(pf.cmc_id == cmc_id) & (pf.status == "observed")][
            ["month_end", "ym", "circulating_supply"]].sort_values("ym")
        months = list(obs.month_end)
        print(f"\n=== {sym} (cmc {cmc_id}) — {len(months)} observed months ===")
        if ckf.exists():
            blob = json.loads(ckf.read_text())
            if blob.get("deferred"):
                print(f"  checkpoint says DEFERRED: {blob.get('reason')}")
                continue
            rows = blob["rows"]; screen = blob.get("screen", {})
            print(f"  (loaded from checkpoint: {blob.get('n_transfers')} transfers)")
        else:
            try:
                ev, mblocks, decimals, calls = panel.fetch_token(cmc_id, sym, chainid, addr, months)
            except panel._CapHit:
                print(f"  EXCEEDED PER_TOKEN_CAP={panel.PER_TOKEN_CAP} getLogs calls -> raise cap for validation")
                continue
            rows, screen, contracts = panel.compute_rows(cmc_id, sym, chainid, addr, ev,
                                                          mblocks, decimals, obs)
            blob = {"cmc_id": cmc_id, "symbol": sym, "chainid": chainid, "address": addr,
                    "decimals": decimals, "n_transfers": len(ev),
                    "getLogs_calls": eng._CALLS["getLogs"], "other_calls": eng._CALLS["other"],
                    "screen": screen, "contracts": contracts,
                    "events": [[e[0], e[1], e[2], e[3], e[4], str(e[5])] for e in ev],
                    "mblocks": mblocks, "rows": rows}
            ckf.write_text(json.dumps(blob))
            print(f"  transfers={len(ev)} getLogs_calls={eng._CALLS['getLogs']} "
                  f"getcode_calls={screen['getcode_calls']} contracts={screen['n_contracts']}/{screen['n_candidate_addr']}")
        nz = [r for r in rows if r.get("hodl_6m") is not None]
        print(f"  {'month':10} {'raw_hodl6m':>11} {'screened6m':>11} {'hodl12m':>9}")
        for r in nz[::max(1, len(nz)//12)]:  # ~12 sampled rows
            raw = r["hodl_6m"]; scr = r["hodl_6m_contractscreened"]; h12 = r.get("hodl_12m")
            print(f"  {r['month_end']:10} {raw*100:>10.1f}% "
                  f"{(scr*100 if scr is not None else float('nan')):>10.1f}% "
                  f"{(h12*100 if h12 is not None else float('nan')):>8.1f}%")
        if nz:
            last = nz[-1]
            print(f"  LATEST {last['month_end']}: raw={last['hodl_6m']:.1%} "
                  f"screened={last['hodl_6m_contractscreened']:.1%}")


if __name__ == "__main__":
    main()
