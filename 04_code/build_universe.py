"""
build_universe.py  --  Phase 0, step 2

Construct the point-in-time monthly asset-universe panel from the cached CMC
snapshots, per DATA_SPECIFICATION.md Section 2.1-2.2.

Inclusion rule (Section 2.1):
  - At each month-end, rank ALL tracked assets by market cap.
  - An asset becomes eligible the first month it appears in the top N (default 250).
  - Once eligible, it stays in the panel every subsequent month through the end
    of the sample, even if it later falls out of the top N, delists, or dies.
  - We pull the top 1000 each month, so an asset that merely drifts down (e.g. to
    rank 600) is still OBSERVED. Only when it falls below rank 1000 do we lose
    price visibility; such asset-months are marked status='carried_forward' with
    the last observed price retained (not silently dropped) for Phase 3 to handle.

Ranking is recomputed by market cap among the returned set (not CMC's stored
rank), matching the spec's "rank all tracked assets by market cap" wording.

Stablecoins (per project decision, logged): ranking is computed INCLUSIVE of
stablecoins so the top-250 cutoff reflects true market structure, but stablecoins
are then DROPPED from the output panel so they never enter downstream phases.

Outputs (03_data/):
  universe_panel.parquet / .csv   asset-month membership panel
  universe_assets.csv             one row per asset that ever qualified (entry date, meta)
  universe_stablecoins_excluded.csv  the stablecoins that hit top-N but were dropped
  universe_rank_sensitivity.csv   qualifying-asset counts under N in {200,250,300}
"""

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SNAP_DIR = REPO / "03_data" / "raw" / "cmc_snapshots"
OUT_DIR = REPO / "03_data"

TOP_N = 250                       # Section 2.1 default; sensitivity also reported
SENSITIVITY_N = [200, 250, 300]


def load_snapshots():
    """Return {month_end(str) -> DataFrame of that month's listing}."""
    snaps = {}
    for f in sorted(SNAP_DIR.glob("*.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        meta = payload.get("_meta", {})
        month_end = meta.get("requested_month_end", f.stem)
        rows = []
        for e in payload.get("data", []):
            q = (e.get("quotes") or [{}])[0]
            mc = q.get("marketCap")
            if mc is None or mc <= 0:
                continue
            rows.append({
                "cmc_id": e.get("id"),
                "symbol": e.get("symbol"),
                "name": e.get("name"),
                "slug": e.get("slug"),
                "date_added": e.get("dateAdded"),
                "tags": e.get("tags") or [],
                "circulating_supply": e.get("circulatingSupply"),
                "total_supply": e.get("totalSupply"),
                "max_supply": e.get("maxSupply"),
                "price": q.get("price"),
                "volume_24h": q.get("volume24h"),
                "market_cap": mc,
            })
        df = pd.DataFrame(rows)
        if df.empty:
            continue
        df = df.sort_values("market_cap", ascending=False).reset_index(drop=True)
        df["mcap_rank"] = df.index + 1
        df["month_end"] = month_end
        snaps[month_end] = df
    return snaps


def main():
    snaps = load_snapshots()
    months = sorted(snaps.keys())
    if not months:
        raise SystemExit("No snapshots found -- run fetch_cmc_snapshots.py first.")
    print(f"Loaded {len(months)} monthly snapshots: {months[0]} .. {months[-1]}")

    # --- asset metadata (union of tags across snapshots; latest name/slug) ---
    meta = {}
    for m in months:
        for _, r in snaps[m].iterrows():
            cid = r["cmc_id"]
            if cid not in meta:
                meta[cid] = {"cmc_id": cid, "symbol": r["symbol"], "name": r["name"],
                            "slug": r["slug"], "date_added": r["date_added"], "tags": set()}
            meta[cid]["tags"].update(r["tags"])
            meta[cid]["symbol"] = r["symbol"]
            meta[cid]["name"] = r["name"]
            meta[cid]["slug"] = r["slug"]
    for cid in meta:
        meta[cid]["is_stablecoin"] = "stablecoin" in meta[cid]["tags"]

    # --- determine entry month under each threshold (ranking inclusive of stablecoins) ---
    def entry_months(top_n):
        entry = {}
        for m in months:
            df = snaps[m]
            for cid in df.loc[df["mcap_rank"] <= top_n, "cmc_id"]:
                if cid not in entry:
                    entry[cid] = m
        return entry

    entry_250 = entry_months(TOP_N)

    # rank sensitivity: count distinct qualifying NON-stablecoin assets per N
    sens_rows = []
    for n in SENSITIVITY_N:
        em = entry_months(n)
        non_stable = [c for c in em if not meta[c]["is_stablecoin"]]
        stable = [c for c in em if meta[c]["is_stablecoin"]]
        sens_rows.append({"top_n": n, "qualifying_total": len(em),
                        "qualifying_non_stablecoin": len(non_stable),
                        "qualifying_stablecoin_excluded": len(stable)})
    pd.DataFrame(sens_rows).to_csv(OUT_DIR / "universe_rank_sensitivity.csv", index=False)
    print("Rank sensitivity:")
    for row in sens_rows:
        print("  ", row)

    # --- build the membership panel for the default threshold ---
    # qualifying non-stablecoin assets only enter the panel
    qualifying = {c: em for c, em in entry_250.items() if not meta[c]["is_stablecoin"]}
    excluded_stable = {c: em for c, em in entry_250.items() if meta[c]["is_stablecoin"]}

    panel_rows = []
    for cid, entry_m in qualifying.items():
        last_obs = None
        for m in months:
            if m < entry_m:
                continue
            df = snaps[m]
            hit = df.loc[df["cmc_id"] == cid]
            if not hit.empty:
                r = hit.iloc[0]
                last_obs = {"price": r["price"], "market_cap": r["market_cap"],
                            "mcap_rank": int(r["mcap_rank"]),
                            "circulating_supply": r["circulating_supply"],
                            "volume_24h": r["volume_24h"]}
                panel_rows.append({
                    "cmc_id": cid, "symbol": meta[cid]["symbol"], "month_end": m,
                    "status": "observed",
                    "price": r["price"], "market_cap": r["market_cap"],
                    "mcap_rank": int(r["mcap_rank"]),
                    "circulating_supply": r["circulating_supply"],
                    "volume_24h": r["volume_24h"],
                })
            else:
                # in-panel but not in this month's top-1000 -> carry forward last price
                panel_rows.append({
                    "cmc_id": cid, "symbol": meta[cid]["symbol"], "month_end": m,
                    "status": "carried_forward",
                    "price": last_obs["price"] if last_obs else None,
                    "market_cap": last_obs["market_cap"] if last_obs else None,
                    "mcap_rank": None,
                    "circulating_supply": last_obs["circulating_supply"] if last_obs else None,
                    "volume_24h": None,
                })

    panel = pd.DataFrame(panel_rows).sort_values(["cmc_id", "month_end"]).reset_index(drop=True)
    panel.to_csv(OUT_DIR / "universe_panel.csv", index=False)
    try:
        # cast numeric cols to float (some memecoin supplies overflow int64)
        ppq = panel.copy()
        for c in ["price", "market_cap", "circulating_supply", "volume_24h", "mcap_rank"]:
            ppq[c] = pd.to_numeric(ppq[c], errors="coerce").astype("float64")
        ppq.to_parquet(OUT_DIR / "universe_panel.parquet", index=False)
    except Exception as e:
        print(f"  (parquet skipped: {e})")

    # --- assets table ---
    assets_rows = []
    for cid, entry_m in qualifying.items():
        assets_rows.append({
            "cmc_id": cid, "symbol": meta[cid]["symbol"], "name": meta[cid]["name"],
            "slug": meta[cid]["slug"], "date_added": meta[cid]["date_added"],
            "entry_month": entry_m,
            "tags": ";".join(sorted(meta[cid]["tags"])),
        })
    assets = pd.DataFrame(assets_rows).sort_values("entry_month")
    assets.to_csv(OUT_DIR / "universe_assets.csv", index=False)

    excl_rows = [{
        "cmc_id": cid, "symbol": meta[cid]["symbol"], "name": meta[cid]["name"],
        "entry_month": em, "tags": ";".join(sorted(meta[cid]["tags"])),
    } for cid, em in excluded_stable.items()]
    pd.DataFrame(excl_rows).sort_values("entry_month").to_csv(
        OUT_DIR / "universe_stablecoins_excluded.csv", index=False)

    print(f"\nPanel rows: {len(panel)}")
    print(f"Qualifying non-stablecoin assets (N={TOP_N}): {len(qualifying)}")
    print(f"Stablecoins excluded (hit top-{TOP_N}): {len(excluded_stable)}")
    obs = (panel["status"] == "observed").sum()
    print(f"Observed asset-months: {obs} / {len(panel)} "
        f"({100*obs/len(panel):.1f}%); carried_forward: {len(panel)-obs}")


if __name__ == "__main__":
    main()
