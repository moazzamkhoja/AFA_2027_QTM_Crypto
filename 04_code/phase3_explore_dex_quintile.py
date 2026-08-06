import pandas as pd, numpy as np
p = pd.read_csv('regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
sm = pd.read_csv('sector_coarse_map.csv')
f = pd.read_csv('ltw_factors_monthly.csv'); f['month_end'] = pd.to_datetime(f['month_end']); f = f.set_index('month_end')
tok = p[(p.track=='token') & p.conv.notna() & p.r_fwd1.notna()].merge(sm[['cmc_id','sector_coarse']], on='cmc_id', how='left')

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
    return b[0], b[0]/np.sqrt(V[0,0]) if False else b[0]/np.sqrt((XtXi @ S @ XtXi)[0,0]), len(df)

def q_ls(d, q, mn):
    out = {}
    for m, g in d.groupby('month_end'):
        if len(g) < q*mn: continue
        try: b = pd.qcut(g['conv'], q, labels=False, duplicates='drop')
        except ValueError: continue
        if b.max() != q-1: continue
        top, bot = g[b==q-1], g[b==0]
        if len(top)<mn or len(bot)<mn: continue
        out[m] = top.r_fwd1.mean() - bot.r_fwd1.mean()
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index); return s.sort_index()

print("%-34s %8s %8s %7s %4s %10s" % ('portfolio','mean/mo','alpha','t','N','avg/leg'))
dex = tok[tok.sector_coarse=='DEX']
for name, d, q, mn in [('DEX-only conviction quintile', dex, 5, 3),
                       ('DEX-only conviction tercile', dex, 3, 4),
                       ('all-token quintile (reference)', tok, 5, 3)]:
    s = q_ls(d, q, mn)
    if len(s) < 12: print("%-34s too few months (%d)" % (name, len(s))); continue
    a, t, n = nw_alpha(s)
    # avg leg size
    legs=[]
    for m, g in d.groupby('month_end'):
        try: b = pd.qcut(g['conv'], q, labels=False, duplicates='drop')
        except ValueError: continue
        if b.max()==q-1: legs.append(((b==q-1).sum()+(b==0).sum())/2)
    print("%-34s %+8.4f %+8.4f %+7.2f %4d %10.1f" % (name, s.mean(), a, t, n, np.mean(legs)))
print()
print('DEX tokens: %d unique, median/month %d' % (dex.cmc_id.nunique(), int(dex.groupby('month_end').size().median())))
