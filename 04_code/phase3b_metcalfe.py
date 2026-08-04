"""
phase3b_metcalfe.py -- Phase 3b Task C appendix (spec 8.3): Metcalfe descriptive panel,
ETH + legacy PoW baselines ONLY (Entry 96: BitInfoCharts has no real active-addresses
series for TRX/ADA/SOL and the rest of the 24-coin sample; page-exists != series-exists,
so every fetch is validated for actual data rows).

Build: /comparison/activeaddresses-{ticker}.html, sentinusd Dygraph regex, monthly AVG
of daily active addresses. Metcalfe ratio = ln(MC) - 2 ln(AA_monthly_avg), MC from
universe_panel (join on cmc_id). Descriptive outputs:
  - per-asset summary of the ratio
  - own-asset time-series predictive regression r_{t+1} on z(metcalfe ratio) (expanding
    z uses full-sample mean/sd -- DESCRIPTIVE ONLY, look-ahead in the z is acknowledged;
    this panel is an appendix baseline, not part of the cross-sectional race).

Outputs: 03_data/phase3/metcalfe_panel.csv, 03_data/phase3/tables/metcalfe_summary.csv
Raw HTML cached under 03_data/raw/bitinfocharts/activeaddresses_{ticker}.html.
"""
import re
import time
import urllib.request
import numpy as np
import pandas as pd
from pathlib import Path
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"
RAW = REPO / "03_data" / "raw" / "bitinfocharts"
H = {"User-Agent": "Mozilla/5.0 (research; AFA 2027 QTM Crypto)"}

TICKERS = {
    "btc": 1, "eth": 1027, "ltc": 2, "doge": 74, "bch": 1831,
    "dash": 131, "etc": 1321, "zec": 1437, "btg": 2083,
}
# expected <title> prefix per ticker: unknown tickers redirect to the default
# btc-ltc-eth comparison page (BTG landmine, this session) -- title must match.
TITLES = {
    "btc": "Bitcoin Active", "eth": "Ethereum Active", "ltc": "Litecoin Active",
    "doge": "Dogecoin Active", "bch": "Bitcoin Cash Active", "dash": "Dash Active",
    "etc": "Ethereum Classic Active", "zec": "Zcash Active", "btg": "Bitcoin Gold Active",
}


def fetch(ticker):
    f = RAW / f"activeaddresses_{ticker}.html"
    if f.exists():
        return f.read_text(encoding="utf-8", errors="ignore")
    url = f"https://bitinfocharts.com/comparison/activeaddresses-{ticker}.html"
    html = urllib.request.urlopen(urllib.request.Request(url, headers=H),
                                  timeout=60).read().decode("utf-8", "ignore")
    f.write_text(html, encoding="utf-8")
    time.sleep(1.0)
    return html


def parse_daily(html):
    rows = re.findall(r'new Date\("(\d{4})/(\d{2})/(\d{2})"\),(null|[0-9.eE+-]+)', html)
    return [(f"{y}-{mo}-{d}", float(v)) for y, mo, d, v in rows if v != "null"]


def main():
    frames = []
    for tk, cid in TICKERS.items():
        html = fetch(tk)
        m = re.search(r"<title>([^<]*)", html)
        if not m or not m.group(1).startswith(TITLES[tk]):
            print(f"  {tk:5s} WRONG PAGE (title={m.group(1)[:40] if m else '?'}) -- "
                  f"redirected to default chart, no series; skipped")
            continue
        daily = parse_daily(html)
        if len(daily) < 100:   # stub-page guard (Entry 96)
            print(f"  {tk:5s} STUB or thin page ({len(daily)} rows) -- skipped")
            continue
        s = pd.Series(dict(daily))
        s.index = pd.DatetimeIndex(s.index)
        aa = s.resample("ME").mean().rename("aa_avg")
        n = s.resample("ME").count()
        aa = aa[n >= 15]      # require at least half a month of daily obs
        df = aa.reset_index()
        df.columns = ["month_end", "aa_avg"]
        df["cmc_id"] = cid
        df["ticker"] = tk
        frames.append(df)
        print(f"  {tk:5s} {len(daily):6d} daily obs -> {len(df)} months "
              f"({df.month_end.min().date()}..{df.month_end.max().date()})")
    panel = pd.concat(frames, ignore_index=True)

    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv", parse_dates=["month_end"])
    obs = uni[(uni.status == "observed") & uni.cmc_id.isin(set(TICKERS.values()))]
    panel = panel.merge(obs[["cmc_id", "month_end", "market_cap", "price"]],
                        on=["cmc_id", "month_end"], how="inner")
    panel = panel[(panel.market_cap > 0) & (panel.aa_avg > 0)].sort_values(["cmc_id", "month_end"])
    panel["metcalfe"] = np.log(panel.market_cap) - 2 * np.log(panel.aa_avg)
    panel["r_fwd1"] = panel.groupby("cmc_id")["price"].transform(
        lambda s: s.pct_change().shift(-1))
    panel.to_csv(OUT / "metcalfe_panel.csv", index=False)

    rows = []
    for tk, g in panel.groupby("ticker"):
        g = g.dropna(subset=["metcalfe", "r_fwd1"])
        if len(g) < 24:
            continue
        z = (g.metcalfe - g.metcalfe.mean()) / g.metcalfe.std()
        m = sm.OLS(g.r_fwd1.values, sm.add_constant(z.values)).fit(
            cov_type="HAC", cov_kwds={"maxlags": 3})
        rows.append(dict(ticker=tk, n=len(g), metcalfe_mean=g.metcalfe.mean(),
                         metcalfe_sd=g.metcalfe.std(), b=m.params[1], t=m.tvalues[1]))
    summ = pd.DataFrame(rows)
    summ.to_csv(TAB / "metcalfe_summary.csv", index=False)
    print("\n=== own-asset predictive: r_{t+1} on z(Metcalfe ratio), NW-3 (descriptive) ===")
    for r in summ.itertuples():
        print(f"  {r.ticker:5s} n={r.n:3d} mean={r.metcalfe_mean:+.2f} "
              f"b={r.b:+.4f} (t={r.t:+.2f})")


if __name__ == "__main__":
    main()
