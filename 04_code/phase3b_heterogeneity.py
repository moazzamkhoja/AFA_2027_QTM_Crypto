"""
phase3b_heterogeneity.py -- Phase 3b Tasks D and E (spec sections 8.4 / 8.6).

Task D (run ALL, report ALL):
 (1) Delta-lambda: 1m/3m changes in conv_lz (lambda_z both tracks), levels + changes
     jointly (s2 controls), plus token quintile EW (min 3) sorts on the changes.
 (2) ve vs plain split (token_gov_classification.csv): s2 per group + pooled
     conv x ve interaction; robustness excluding low-confidence rows.
 (3) fee vs nofee split: same design.
 (4) size terciles and turnover terciles (turnover = volume_24h / MC, universe_panel),
     terciles within month: s2 per bucket.
 (5) regimes: bull/bear = sign of CMKT in the RETURN month (t+1); pre/post-2023.
     Token conv slope (s2) and coin interaction (s4) per regime.
 (6) measurement: raw NV/TVL / raw NVT val (signals panel); exclude g_capped months
     (GL panels); exclude B4 months (screened HODL-6m > 80%, channel2_holding --
     tokens only, coins have no ch2); exclude coin conv_source fallback months;
     MRP 20%/40% re-derivation of PQ*/TVL* from emitted pq0/tvl0, g, beta (Entry 93
     machinery, re_floor 5%), val rebuilt, winsorized, re-standardized.

Task E (mechanism discrimination M1-M4, spec 8.6):
  M1: token conv x turnover interaction (+ size/turnover splits from D4).
  M2: token s4 with val demeaned within coarse sector-month (n>=3, else class-month);
      portfolio version: quadrant SMA with sector-neutralized valuation.
  M3: = D6 raw NV/TVL + g-cap-excluded interaction (reported in the M-verdict table).
  M4: coin s4 + staking_yield + conv x staking_yield; staking_yield = supply_g12 /
      lambda_ch1, lambda_ch1 = logistic(conv) on conv_source=='ch1_lnodds' rows
      (12m trailing issuance spread over the staked share; winsorized 1/99; Entry 104).

Estimator everywhere: dep r_fwd1_w, month FE, SEs two-way clustered (asset, month).
Outputs: tables/heterogeneity.csv, tables/het_portfolios.csv, tables/mechanisms.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path
from linearmodels.panel import PanelOLS
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "03_data" / "phase3"
TAB = OUT / "tables"

CONTROLS = ["size_std", "mom_3m_std", "mom_12_2_std", "r_1m_std", "beta36_std"]
RF, G_INF, N_YRS, RE_FLOOR = 0.04, 0.03, 10, 0.05


def winsorize(s, lo=0.01, hi=0.99):
    if s.notna().sum() < 3:
        return s
    return s.clip(s.quantile(lo), s.quantile(hi))


def zs(s):
    sd = s.std()
    return (s - s.mean()) / sd if sd and np.isfinite(sd) and sd > 0 else s * np.nan


def dcf_star(x0, g, r):
    if not np.isfinite(x0) or x0 <= 0 or not np.isfinite(g) or not np.isfinite(r):
        return np.nan
    r = max(r, G_INF + 0.02)
    s = np.arange(1, N_YRS + 1)
    pv = np.sum(x0 * (1 + g) ** s / (1 + r) ** s)
    term = x0 * (1 + g) ** N_YRS * (1 + G_INF) / ((r - G_INF) * (1 + r) ** N_YRS)
    af = (1 - (1 + r) ** (-N_YRS)) / r
    return (pv + term) / af


def run(d, dep, xcols, label, rows, report=None):
    d = d.dropna(subset=[dep] + xcols).copy()
    if d.cmc_id.nunique() < 3 or d.month_end.nunique() < 3:
        return
    X = d[xcols].copy()
    d = d.set_index(["cmc_id", "month_end"])
    X.index = d.index
    res = PanelOLS(d[dep], X, time_effects=True, check_rank=False).fit(
        cov_type="clustered", cluster_entity=True, cluster_time=True)
    for v in (report or xcols):
        rows.append(dict(spec=label, var=v, coef=res.params[v], se=res.std_errors[v],
                         t=res.tstats[v], p=res.pvalues[v], n=int(res.nobs)))


def sort_ls(d, sig, q, min_leg=3):
    rets = {}
    for t, g in d.groupby("month_end"):
        g = g.dropna(subset=[sig, "r_fwd1"])
        if len(g) < 2 * min_leg:
            continue
        try:
            b = pd.qcut(g[sig], q, labels=False, duplicates="drop")
        except ValueError:
            continue
        if b.max() != q - 1:
            continue
        top, bot = g[b == q - 1], g[b == 0]
        if len(top) < min_leg or len(bot) < min_leg:
            continue
        rets[t] = top.r_fwd1.mean() - bot.r_fwd1.mean()
    s = pd.Series(rets).sort_index()
    s.index = pd.DatetimeIndex(s.index)
    return s


def nw_alpha(s, F, lags=3):
    j = pd.concat([s.rename("y"), F], axis=1, sort=True).dropna()
    if len(j) < 12:
        return None
    m = sm.OLS(j["y"], sm.add_constant(j[F.columns]), missing="drop").fit(
        cov_type="HAC", cov_kwds={"maxlags": lags})
    return dict(alpha=m.params["const"], alpha_t=m.tvalues["const"],
                mean=float(j["y"].mean()), n=int(m.nobs))


def main():
    p = pd.read_csv(OUT / "regression_panel.csv", parse_dates=["month_end"])
    cmap = pd.read_csv(OUT / "sector_coarse_map.csv")[["cmc_id", "sector_coarse"]]
    sig = pd.read_csv(OUT / "horserace_signals.csv", parse_dates=["month_end"])
    gov = pd.read_csv(OUT / "token_gov_classification.csv")
    fac = (pd.read_csv(OUT / "ltw_factors_monthly.csv", parse_dates=["month_end"])
           .set_index("month_end"))
    F = fac[["cmkt", "csmb", "cmom"]]

    p = p.merge(cmap, on="cmc_id", how="left")
    p = p.merge(sig[["cmc_id", "month_end", "raw_val_std", "supply_g12"]],
                on=["cmc_id", "month_end"], how="left")
    p = p.merge(gov[["cmc_id", "ve_lock", "fee_share", "confidence"]], on="cmc_id", how="left")
    p["conv_x_val"] = p["conv_std"] * p["val_std"]
    p["conv_x_rawval"] = p["conv_std"] * p["raw_val_std"]

    # volume turnover
    uni = pd.read_csv(REPO / "03_data" / "universe_panel.csv", parse_dates=["month_end"])
    obs = uni[uni.status == "observed"][["cmc_id", "month_end", "volume_24h"]]
    p = p.merge(obs, on=["cmc_id", "month_end"], how="left")
    p["turn"] = p.volume_24h / p.market_cap
    p["turn"] = p.groupby("track")["turn"].transform(winsorize)
    p["turn_std"] = p.groupby(["track", "month_end"])["turn"].transform(zs)

    # g_capped flags
    nvt = pd.read_csv(REPO / "03_data" / "phase2" / "nvt_gl_panel.csv",
                      parse_dates=["month_end"])
    tvl = pd.read_csv(REPO / "03_data" / "phase2" / "nv_tvl_gl_panel.csv",
                      parse_dates=["month_end"])
    gc = pd.concat([nvt[["cmc_id", "month_end", "g_capped"]],
                    tvl[["cmc_id", "month_end", "g_capped"]]]).drop_duplicates(
        ["cmc_id", "month_end"], keep="last")
    p = p.merge(gc, on=["cmc_id", "month_end"], how="left")

    # B4 flag (tokens only; coins have no ch2 checkpoints -- Entry 96)
    ch2 = pd.read_csv(REPO / "03_data" / "phase1" / "channel2_holding.csv",
                      parse_dates=["month_end"])
    ch2["hodl_scr"] = ch2["hodl_6m_contractscreened"].fillna(ch2["hodl_6m"])
    ch2["b4_flag"] = ch2["hodl_scr"] > 0.80
    p = p.merge(ch2[["cmc_id", "month_end", "b4_flag"]], on=["cmc_id", "month_end"], how="left")
    p["b4_flag"] = p["b4_flag"].fillna(False).astype(bool)

    # MRP re-derivations
    nvt["re20"] = (RF + nvt.beta * 0.20).clip(lower=RE_FLOOR)
    nvt["re40"] = (RF + nvt.beta * 0.40).clip(lower=RE_FLOOR)
    tvl["re20"] = (RF + tvl.beta * 0.20).clip(lower=RE_FLOOR)
    tvl["re40"] = (RF + tvl.beta * 0.40).clip(lower=RE_FLOOR)
    for df, x0col in ((nvt, "pq0_annual"), (tvl, "tvl0_smooth")):
        for tag in ("20", "40"):
            df[f"star{tag}"] = [dcf_star(x, g, r) for x, g, r in
                                zip(df[x0col], df.g, df["re" + tag])]
            df[f"val{tag}"] = np.log(df.market_cap / df[f"star{tag}"])
    mrp = pd.concat([
        nvt[["cmc_id", "month_end", "val20", "val40"]],
        tvl[tvl.asset_class == "token"][["cmc_id", "month_end", "val20", "val40"]],
    ]).drop_duplicates(["cmc_id", "month_end"], keep="last")
    p = p.merge(mrp, on=["cmc_id", "month_end"], how="left")
    for tag in ("20", "40"):
        c = "val" + tag
        p[c] = p[c].replace([np.inf, -np.inf], np.nan)
        p[c] = p.groupby("track")[c].transform(winsorize)
        p[c + "_std"] = p.groupby(["track", "month_end"])[c].transform(zs)
        p[f"conv_x_val{tag}"] = p["conv_std"] * p[c + "_std"]

    # delta-lambda (conv_lz both tracks; consecutive calendar months required)
    p = p.sort_values(["cmc_id", "month_end"])
    g = p.groupby("cmc_id")
    gap1 = g["month_end"].diff().dt.days.between(28, 31)
    p["dconv_1m"] = g["conv_lz"].diff().where(gap1)
    gap3 = g["month_end"].diff(3).dt.days.between(85, 95)
    p["dconv_3m"] = g["conv_lz"].diff(3).where(gap3)
    for c in ("dconv_1m", "dconv_3m"):
        p[c + "_std"] = p.groupby(["track", "month_end"])[c].transform(zs)

    # M4 staking yield (coins, ch1 months): supply_g12 / lambda_ch1
    lam_ch1 = 1.0 / (1.0 + np.exp(-p["conv"]))
    sy = np.where((p.track == "coin") & (p.conv_source == "ch1_lnodds"),
                  p.supply_g12 / lam_ch1.clip(0.001, 0.999), np.nan)
    p["stake_yield"] = pd.Series(sy, index=p.index)
    p["stake_yield"] = p.groupby("track")["stake_yield"].transform(winsorize)
    p["sy_std"] = p.groupby(["track", "month_end"])["stake_yield"].transform(zs)
    p["conv_x_sy"] = p["conv_std"] * p["sy_std"]

    # M2 sector-neutral valuation (tokens)
    tokmask = p.track == "token"
    tk = p[tokmask].copy()
    tk["sec_n"] = tk.groupby(["month_end", "sector_coarse"])["val"].transform("count")
    smean = tk.groupby(["month_end", "sector_coarse"])["val"].transform("mean")
    cmean = tk.groupby("month_end")["val"].transform("mean")
    tk["val_sn"] = np.where(tk.sec_n >= 3, tk.val - smean, tk.val - cmean)
    tk["val_sn_std"] = tk.groupby("month_end")["val_sn"].transform(zs)
    tk["conv_x_valsn"] = tk["conv_std"] * tk["val_sn_std"]

    coin = p[p.track == "coin"]
    tok = p[tokmask]
    dep = "r_fwd1_w"
    S2 = ["conv_std"] + CONTROLS
    S4 = ["conv_std"] + CONTROLS + ["val_std", "conv_x_val"]
    rows, prows, mrows = [], [], []

    # ---------------- D1 delta-lambda ----------------
    for tr, d in (("token", tok), ("coin", coin)):
        run(d, dep, S2 + ["dconv_1m_std"], f"D1_{tr}_lvl+d1m", rows,
            report=["conv_std", "dconv_1m_std"])
        run(d, dep, S2 + ["dconv_3m_std"], f"D1_{tr}_lvl+d3m", rows,
            report=["conv_std", "dconv_3m_std"])
    for sname, scol in (("d1m", "dconv_1m"), ("d3m", "dconv_3m")):
        s = sort_ls(tok[tok[scol].notna()], scol, 5)
        a = nw_alpha(s, F)
        if a:
            prows.append(dict(portfolio=f"D1_token_q5_{sname}", **a))

    # ---------------- D2/D3 ve and fee splits ----------------
    for dcol, dval, tag in (("ve_lock", "ve", "D2_ve"), ("ve_lock", "plain", "D2_plain"),
                            ("fee_share", "fee", "D3_fee"), ("fee_share", "nofee", "D3_nofee")):
        run(tok[tok[dcol] == dval], dep, S2, f"{tag}", rows, report=["conv_std"])
    for dcol, tag in (("ve_lock", "D2"), ("fee_share", "D3")):
        d = tok.copy()
        d["grp"] = (d[dcol] == ("ve" if dcol == "ve_lock" else "fee")).astype(float)
        d["conv_x_grp"] = d["conv_std"] * d["grp"]
        run(d, dep, S2 + ["grp", "conv_x_grp"], f"{tag}_interaction", rows,
            report=["conv_std", "conv_x_grp"])
        hi = d[d.confidence != "low"]
        run(hi, dep, S2 + ["grp", "conv_x_grp"], f"{tag}_interaction_hiconf", rows,
            report=["conv_std", "conv_x_grp"])

    # ---------------- D4 size / turnover terciles ----------------
    for col, tag in (("size", "D4_size"), ("turn", "D4_turn")):
        d = tok.copy()
        def tercile(s):
            b = pd.qcut(s, 3, labels=False, duplicates="drop")
            if b.max() != 2:      # collapsed edges: skip the month
                return pd.Series(np.nan, index=s.index)
            return b.map({0: "lo", 1: "mid", 2: "hi"})
        d["bucket"] = d.groupby("month_end")[col].transform(tercile)
        for b in ("lo", "mid", "hi"):
            run(d[d.bucket == b], dep, S2, f"{tag}_{b}", rows, report=["conv_std"])

    # ---------------- D5 regimes ----------------
    ret_month = fac["cmkt"]
    p_bull = ret_month[ret_month > 0].index
    for tr, d, xs, rep in (("token", tok, S2, ["conv_std"]),
                           ("coin", coin, S4, ["conv_std", "conv_x_val"])):
        nxt = d.month_end + pd.offsets.MonthEnd(1)
        bull = d[nxt.isin(p_bull)]
        bear = d[~nxt.isin(p_bull)]
        run(bull, dep, xs, f"D5_{tr}_bull", rows, report=rep)
        run(bear, dep, xs, f"D5_{tr}_bear", rows, report=rep)
        run(d[d.month_end < "2023-01-01"], dep, xs, f"D5_{tr}_pre2023", rows, report=rep)
        run(d[d.month_end >= "2023-01-01"], dep, xs, f"D5_{tr}_post2023", rows, report=rep)

    # ---------------- D6 measurement ----------------
    S4raw = ["conv_std"] + CONTROLS + ["raw_val_std", "conv_x_rawval"]
    run(tok, dep, S4raw, "D6_token_rawval", rows, report=["conv_std", "conv_x_rawval"])
    run(coin, dep, S4raw, "D6_coin_rawval", rows, report=["conv_std", "conv_x_rawval"])
    run(tok[tok.g_capped != True], dep, S4, "D6_token_nogcap", rows,   # noqa: E712
        report=["conv_std", "conv_x_val"])
    run(coin[coin.g_capped != True], dep, S4, "D6_coin_nogcap", rows,  # noqa: E712
        report=["conv_std", "conv_x_val"])
    run(tok[~tok.b4_flag], dep, S4, "D6_token_noB4", rows, report=["conv_std", "conv_x_val"])
    run(coin[coin.conv_source == "ch1_lnodds"], dep, S4, "D6_coin_noconvfallback", rows,
        report=["conv_std", "conv_x_val"])
    for tag in ("20", "40"):
        xs = ["conv_std"] + CONTROLS + [f"val{tag}_std", f"conv_x_val{tag}"]
        run(tok, dep, xs, f"D6_token_mrp{tag}", rows, report=["conv_std", f"conv_x_val{tag}"])
        run(coin, dep, xs, f"D6_coin_mrp{tag}", rows, report=["conv_std", f"conv_x_val{tag}"])

    # ---------------- E mechanisms ----------------
    d = tok.copy()
    d["conv_x_turn"] = d["conv_std"] * d["turn_std"]
    run(d, dep, S2 + ["turn_std", "conv_x_turn"], "M1_token_convxturn", mrows,
        report=["conv_std", "turn_std", "conv_x_turn"])
    run(tk, dep, ["conv_std"] + CONTROLS + ["val_sn_std", "conv_x_valsn"],
        "M2_token_secneutral_val", mrows, report=["conv_std", "conv_x_valsn"])
    # M2 portfolio: quadrant with sector-neutral valuation
    q = tk.dropna(subset=["conv", "val_sn", "r_fwd1"]).copy()
    med_c = q.groupby("month_end")["conv"].transform("median")
    med_v = q.groupby("month_end")["val_sn"].transform("median")
    q["star"] = (q.conv > med_c) & (q.val_sn <= med_v)
    q["avoid"] = (q.conv <= med_c) & (q.val_sn > med_v)
    cnt = q.groupby("month_end").agg(ns=("star", "sum"), na=("avoid", "sum"))
    okm = cnt[(cnt.ns >= 4) & (cnt.na >= 4)].index
    qq = q[q.month_end.isin(okm)]
    sma = (qq[qq.star].groupby("month_end").r_fwd1.mean()
           - qq[qq.avoid].groupby("month_end").r_fwd1.mean())
    sma.index = pd.DatetimeIndex(sma.index)
    a = nw_alpha(sma, F)
    if a:
        prows.append(dict(portfolio="M2_token_quadrant_secneutral_val", **a))
    # M4
    run(coin, dep, S4 + ["sy_std", "conv_x_sy"], "M4_coin_stakeyield", mrows,
        report=["conv_std", "conv_x_val", "sy_std", "conv_x_sy"])

    pd.DataFrame(rows).to_csv(TAB / "heterogeneity.csv", index=False)
    pd.DataFrame(prows).to_csv(TAB / "het_portfolios.csv", index=False)
    pd.DataFrame(mrows).to_csv(TAB / "mechanisms.csv", index=False)

    for name, rr in (("heterogeneity", rows), ("mechanisms", mrows)):
        print(f"\n=== {name} ===")
        for r in rr:
            print(f"  {r['spec']:32s} {r['var']:15s} {r['coef']:+.4f} (t={r['t']:+.2f}) n={r['n']}")
    print("\n=== portfolios ===")
    for r in prows:
        print(f"  {r['portfolio']:36s} mean={r['mean']:+.4f} alpha={r['alpha']:+.4f} "
              f"(t={r['alpha_t']:+.2f}) n={r['n']}")


if __name__ == "__main__":
    main()
