"""_s028_selftransfer_diag.py -- Session 028 Entry-74 DIAGNOSTIC (offline, no writes).

Measures the effect of the self-transfer skip (the AAVE poisoning fix) on every
non-streamed checkpoint (raw events stored): re-runs phase1_channel2_panel._replay
(now patched to skip from==to) on the stored events and diffs the resulting
hodl_6m_contractscreened series against the STORED rows (built pre-fix).

Output: console table of tokens where any month moves by more than 1pp.
Nothing is overwritten -- evidence for Entry 74 / a future recompute decision only.
"""

import json
from pathlib import Path

import pandas as pd

import phase1_channel2_panel as panel

REPO = Path(__file__).resolve().parents[1]
HOLD = REPO / "03_data" / "raw" / "phase1_onchain" / "holding"

changed, clean, skipped = [], 0, 0
for f in sorted(HOLD.glob("*.json")):
    try:
        b = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        skipped += 1
        continue
    if "events" not in b or "rows" not in b or not b.get("rows"):
        skipped += 1
        continue
    rows_old = pd.DataFrame(b["rows"])
    months = list(rows_old.month_end)
    circ = dict(zip(rows_old.month_end, rows_old.circulating_supply))
    ev = [(e[0], e[1], e[2], e[3], e[4], int(e[5])) for e in b["events"]]
    panel.set_val_cap(pd.Series(list(circ.values())), b["decimals"])
    state = panel._replay(ev, b["mblocks"], months)
    rows_new, _ = panel.rows_from_state(b["cmc_id"], b["symbol"], state, months,
                                        b["decimals"], set(b.get("contracts", [])), circ)
    new = pd.DataFrame(rows_new)
    m = rows_old.merge(new, on="month_end", suffixes=("_o", "_n"))
    col = "hodl_6m_contractscreened"
    mm = m[m[f"{col}_o"].notna() & m[f"{col}_n"].notna()]
    if mm.empty:
        clean += 1
        continue
    diff = (mm[f"{col}_n"] - mm[f"{col}_o"]).abs().max()
    nullchange = (m[f"{col}_o"].isna() != m[f"{col}_n"].isna()).sum()
    if diff > 0.01 or nullchange:
        changed.append((b["symbol"], b["cmc_id"], diff, nullchange, len(mm)))
    else:
        clean += 1

print(f"\nchecked {clean + len(changed)} stored-event tokens ({skipped} streamed/unreadable skipped)")
print(f"UNCHANGED (max move <= 1pp, no null flips): {clean}")
print(f"CHANGED   (> 1pp somewhere or null flip):   {len(changed)}")
for sym, cid, diff, nc, n in sorted(changed, key=lambda x: -x[2]):
    print(f"  {sym:10} cmc={cid:6}  max|dHODL|={diff:.4f}  null-flips={nc}  months={n}")
