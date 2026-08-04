import pandas as pd, numpy as np

p = pd.read_csv('regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
fc = pd.read_csv('fee_comparators.csv'); fc['month_end'] = pd.to_datetime(fc['month_end'])
f = pd.read_csv('ltw_factors_monthly.csv'); f['month_end'] = pd.to_datetime(f['month_end']); f = f.set_index('month_end')

tok = p[(p.track=='token') & p.conv.notna() & p.r_fwd1.notna()].copy()
tok = tok.merge(fc[['cmc_id','month_end','pf_ln','prev_gl_ln']], on=['cmc_id','month_end'], how='left')

def nw_alpha(s, lags=3):
    df = pd.concat([s.rename('y'), f[['cmkt','csmb','cmom']]], axis=1, join='inner').dropna()
    y = df['y'].values; X = np.column_stack([np.ones(len(df)), df[['cmkt','csmb','cmom']].values])
    b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X@b; n,k = X.shape
    XtXi = np.linalg.inv(X.T@X); S = np.zeros((k,k))
    for l in range(lags+1):
        w = 1 - l/(lags+1)
        for t in range(l, n):
            S += w*np.outer(X[t]*e[t], X[t-l]*e[t-l])
            if l>0: S += w*np.outer(X[t-l]*e[t-l], X[t]*e[t])
    V = XtXi @ S @ XtXi
    return b[0], b[0]/np.sqrt(V[0,0]), len(df)

def quadrant_sma(d, valcol, min_leg=4, vw=False):
    out, excl = {}, 0
    for m, g in d.groupby('month_end'):
        g = g.dropna(subset=['conv', valcol])
        if len(g) < 8: excl += 1; continue
        hi_c = g.conv > g.conv.median()
        lo_v = g[valcol] <= g[valcol].median()
        star, avoid = g[hi_c & lo_v], g[~hi_c & ~lo_v]
        if len(star) < min_leg or len(avoid) < min_leg: excl += 1; continue
        if vw:
            rs = np.average(star.r_fwd1, weights=star.market_cap)
            ra = np.average(avoid.r_fwd1, weights=avoid.market_cap)
        else:
            rs, ra = star.r_fwd1.mean(), avoid.r_fwd1.mean()
        out[m] = rs - ra
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index)
    return s.sort_index(), excl

print("%-42s %8s %8s %7s %4s %6s %7s" % ('H3 quadrant (Stars-Avoid), valuation =','mean/mo','alpha','t(NW3)','N','excl','Sharpe'))
for valcol, name in [('val','NV/TVL_GL (baseline, fee-cov subsample)'), ('pf_ln','ln P/F'), ('prev_gl_ln','ln MC/REV* (revenue DCF)')]:
    d = tok if valcol != 'val' else tok[tok.pf_ln.notna()]
    s, ex = quadrant_sma(d, valcol)
    if len(s) < 12:
        print("%-42s  too few months (%d, excl %d)" % (name, len(s), ex)); continue
    a, t, n = nw_alpha(s)
    sh = s.mean()/s.std()*np.sqrt(12)
    print("%-42s %+8.4f %+8.4f %+7.2f %4d %6d %+7.2f" % (name, s.mean(), a, t, n, ex, sh))
    s23 = s[s.index >= '2023-01-01']
    if len(s23) >= 12:
        a2, t2, n2 = nw_alpha(s23)
        print("%-42s %+8.4f %+8.4f %+7.2f %4d" % ('   post-2023', s23.mean(), a2, t2, n2))
# also full-sample baseline for reference (from 043: token EW SMA alpha +1.19% t=0.84)
s, ex = quadrant_sma(tok, 'val')
a, t, n = nw_alpha(s)
print("%-42s %+8.4f %+8.4f %+7.2f %4d %6d" % ('reference: NV/TVL_GL full sample', s.mean(), a, t, n, ex))
