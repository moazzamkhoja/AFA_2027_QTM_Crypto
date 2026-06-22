"""
carry_forward_split.py  --  Phase 0 follow-up, deliverable 1
Implements DATA_DECISIONS_LOG.md Entry 10.

Every asset-month currently marked status='carried_forward' in
03_data/universe_panel.csv is split into one of two subtypes:

  presumed_failed   the asset never reappears in the observed top-1000 snapshot
                    for the remainder of the sample (i.e. this CF month lies in the
                    asset's trailing tail, after its last-ever observation).
  temporarily_out   the asset drops out of the top-1000 snapshot but reappears
                    (status='observed') in a later month -- a visibility gap, not
                    a failure.

Rule (vectorised, equivalent to gap analysis): for asset j, let L_j be the last
month it is observed. A carried_forward month at t is
  temporarily_out  iff  t <  L_j   (a later observation exists -> gap will close)
  presumed_failed  iff  t >= L_j   (no later observation -> trailing tail)
Every asset enters the panel via an observed top-250 month, so L_j always exists.

This DOES NOT pick or implement a death-return formula (Entry 10 defers that). It
only produces the split + the diagnostics needed to choose one with real numbers,
including an explicit right-censoring flag for presumed_failed assets whose trailing
gap is short enough that, had the sample run longer, they might have looked like a
still-mid-gap temporarily_out case.

Adds a new column `carry_forward_subtype` to universe_panel.csv (the existing
`status` column is left untouched). Writes a diagnostics block to
03_data/_carry_forward_split_diagnostics.txt for the report.
"""

from pathlib import Path
import io
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "03_data"
SAMPLE_END = "2026-05-31"


def main():
    p = pd.read_csv(DATA / "universe_panel.csv")
    p["month_end"] = pd.to_datetime(p["month_end"])
    p = p.sort_values(["cmc_id", "month_end"]).reset_index(drop=True)

    # Last observed month per asset (every asset has >=1 observed month).
    last_obs = (p[p["status"] == "observed"]
                .groupby("cmc_id")["month_end"].max()
                .rename("last_obs_month"))
    p = p.merge(last_obs, on="cmc_id", how="left")

    # Subtype only applies to carried_forward rows.
    is_cf = p["status"] == "carried_forward"
    subtype = np.where(p["month_end"] < p["last_obs_month"],
                       "temporarily_out", "presumed_failed")
    p["carry_forward_subtype"] = np.where(is_cf, subtype, "")

    # ---- Diagnostics -------------------------------------------------------
    cf = p[is_cf].copy()
    buf = io.StringIO()
    w = lambda s="": buf.write(s + "\n")

    w("CARRY-FORWARD SPLIT DIAGNOSTICS (deliverable 1, Entry 10)")
    w("=" * 60)
    total_cf = len(cf)
    by_sub = cf["carry_forward_subtype"].value_counts()
    w(f"Total carried_forward asset-months: {total_cf}")
    for k in ["presumed_failed", "temporarily_out"]:
        n = int(by_sub.get(k, 0))
        w(f"  {k:16s}: {n:7d} asset-months ({100*n/total_cf:5.1f}%)")

    # Distinct assets per subtype (an asset can contribute to BOTH: a closed gap
    # earlier + a terminal failed tail later).
    assets_failed = set(cf.loc[cf.carry_forward_subtype == "presumed_failed", "cmc_id"])
    assets_temp = set(cf.loc[cf.carry_forward_subtype == "temporarily_out", "cmc_id"])
    both = assets_failed & assets_temp
    w("")
    w("Distinct assets:")
    w(f"  with >=1 presumed_failed month : {len(assets_failed)}")
    w(f"  with >=1 temporarily_out month : {len(assets_temp)}")
    w(f"  with BOTH (closed gap then later failed tail): {len(both)}")

    # ---- temporarily_out gap lengths (closed gaps) -------------------------
    # A gap = a maximal run of consecutive CF months bounded on BOTH sides by the
    # asset timeline such that an observation follows. All temporarily_out months
    # belong to such closed gaps. Count length of each closed gap (= months out).
    to = cf[cf.carry_forward_subtype == "temporarily_out"].copy()
    to = to.sort_values(["cmc_id", "month_end"])
    # contiguous-run id: break where the month gap from the previous CF row > ~1 month
    # within the same asset. Using period index keeps month arithmetic exact.
    to["mp"] = to["month_end"].dt.to_period("M")
    to["prev_mp"] = to.groupby("cmc_id")["mp"].shift(1)
    to["new_run"] = (to["prev_mp"].isna()) | ((to["mp"] - to["prev_mp"]).apply(
        lambda x: x.n if pd.notna(x) else 99) != 1)
    to["run_id"] = to.groupby("cmc_id")["new_run"].cumsum()
    gap_lengths = to.groupby(["cmc_id", "run_id"]).size()
    w("")
    w(f"temporarily_out closed gaps: {len(gap_lengths)} distinct gap episodes")
    if len(gap_lengths):
        w(f"  gap length (months out)  min={gap_lengths.min()}  "
          f"median={int(gap_lengths.median())}  mean={gap_lengths.mean():.1f}  "
          f"max={gap_lengths.max()}")
        w("  gap-length distribution (months out -> #episodes):")
        vc = gap_lengths.value_counts().sort_index()
        for length, cnt in vc.items():
            w(f"    {int(length):3d} mo : {int(cnt)}")
    max_to_gap = int(gap_lengths.max()) if len(gap_lengths) else 0
    med_to_gap = int(gap_lengths.median()) if len(gap_lengths) else 0

    # ---- presumed_failed terminal-gap lengths + right-censoring ------------
    # Terminal gap = trailing run of CF months from (last_obs+1) through sample end.
    pf = cf[cf.carry_forward_subtype == "presumed_failed"].copy()
    term_gap = pf.groupby("cmc_id").size().rename("terminal_gap_months")
    # also record when the gap STARTED (first presumed_failed month) for recency.
    gap_start = pf.groupby("cmc_id")["month_end"].min().rename("gap_start")
    tg = pd.concat([term_gap, gap_start], axis=1)
    w("")
    w(f"presumed_failed terminal gaps: {len(tg)} assets")
    w(f"  terminal gap (months to sample end)  min={tg.terminal_gap_months.min()}  "
      f"median={int(tg.terminal_gap_months.median())}  "
      f"mean={tg.terminal_gap_months.mean():.1f}  max={tg.terminal_gap_months.max()}")

    # RIGHT-CENSORING FLAG: a presumed_failed asset whose terminal gap is no longer
    # than the longest OBSERVED temporarily_out gap could, in principle, still be a
    # case that would have reappeared had the sample run longer -- i.e. "never seen
    # again so far" != "permanently dead" for these. Report at several thresholds.
    w("")
    w("RIGHT-CENSORING RISK (presumed_failed that could still be mid-gap):")
    for label, thr in [("<= max temporarily_out gap", max_to_gap),
                        ("<= median temporarily_out gap", med_to_gap),
                        ("<= 3 months", 3),
                        ("<= 6 months", 6),
                        ("<= 12 months", 12)]:
        n = int((tg.terminal_gap_months <= thr).sum())
        w(f"  terminal gap {label} ({thr} mo): {n} assets "
          f"({100*n/len(tg):4.1f}% of presumed_failed)")
    # recency: gaps that only started in the last 12 months of the sample
    end = pd.Timestamp(SAMPLE_END)
    for win in [6, 12, 24]:
        cutoff = end - pd.DateOffset(months=win)
        n = int((tg.gap_start > cutoff).sum())
        w(f"  trailing gap STARTED within last {win:2d} months (after "
          f"{cutoff.date()}): {n} assets")
    w("")
    w("NOTE: death-return formula intentionally NOT chosen here (Entry 10). The "
      "right-censoring counts above are exactly the input that decision needs.")

    diag = buf.getvalue()
    (DATA / "_carry_forward_split_diagnostics.txt").write_text(diag, encoding="utf-8")
    print(diag)

    # ---- write back (status column untouched; new column added) ------------
    out = p.drop(columns=["last_obs_month"])
    out["month_end"] = out["month_end"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA / "universe_panel.csv", index=False)
    try:
        out.to_parquet(DATA / "universe_panel.parquet", index=False)
    except Exception as e:
        print(f"(parquet write skipped: {e})")
    print(f"Wrote carry_forward_subtype to universe_panel.csv ({len(out)} rows).")


if __name__ == "__main__":
    main()
