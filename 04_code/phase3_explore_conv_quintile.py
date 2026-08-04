import pandas as pd, numpy as np

p = pd.read_csv('regression_panel.csv')
p['month_end'] = pd.to_datetime(p['month_end'])
f = pd.read_csv('ltw_factors_monthly.csv'); f['month_end'] = pd.to_datetime(f['month_end']); f = f.set_index('month_end')
tok = p[(p.track=='token') & p.conv.notna() & p.r_fwd1.notna()].copy()

# proper sector-neutral: keep only sector-months with >=3 tokens, demean within
tok['sec_n'] = tok.groupby(['month_end','sector'])['conv'].transform('count')
sn = tok[tok.sec_n >= 3].copy()
sn['conv_sn'] = sn.groupby(['month_end','sector'])['conv'].transform(lambda g: g - g.mean())

def ls_series(d, sig, q, vw=False, min_names=4):
    out = {}
    for m, g in d.groupby('month_end'):
        g = g.dropna(subset=[sig])
        if len(g) < q*min_names: continue
        try: b = pd.qcut(g[sig], q, labels=False, duplicates='drop')
        except ValueError: continue
        if b.max() != q-1: continue
        top, bot = g[b==q-1], g[b==0]
        if len(top)<min_names or len(bot)<min_names: continue
        if vw:
            rt = np.average(top.r_fwd1, weights=top.market_cap); rb = np.average(bot.r_fwd1, weights=bot.market_cap)
        else:
            rt, rb = top.r_fwd1.mean(), bot.r_fwd1.mean()
        out[m] = rt - rb
    s = pd.Series(out)
    s.index = pd.DatetimeIndex(s.index)
    return s.sort_index()

def nw_alpha(s, lags=3):
    df = pd.concat([s.rename('y'), f[['cmkt','csmb','cmom']]], axis=1, join='inner').dropna()
    y = df['y'].values; X = np.column_stack([np.ones(len(df)), df[['cmkt','csmb','cmom']].values])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X@b; n,k = X.shape
    XtX_inv = np.linalg.inv(X.T@X); S = np.zeros((k,k))
    for l in range(lags+1):
        w = 1 - l/(lags+1)
        for t in range(l, n):
            S += w*np.outer(X[t]*e[t], X[t-l]*e[t-l])
            if l>0: S += w*np.outer(X[t-l]*e[t-l], X[t]*e[t])
    V = XtX_inv @ S @ XtX_inv
    return b[0], b[0]/np.sqrt(V[0,0]), len(df)

def report(name, d, sig, q, vw, mn, since=None):
    s = ls_series(d, sig, q, vw=vw, min_names=mn)
    if since: s = s[s.index >= since]
    if len(s) < 12:
        print("%-40s  too few months (%d)" % (name, len(s))); return
    a, t, n = nw_alpha(s)
    sh = s.mean()/s.std()*np.sqrt(12)
    print("%-40s %+8.4f %+8.4f %+7.2f %4d %+7.2f" % (name, s.mean(), a, t, n, sh))

print("%-40s %8s %8s %7s %4s %7s" % ('variant','mean/mo','alpha','t(NW3)','N','Sharpe'))
print('--- full sample ---')
report('conv median EW (= session 043)', tok,'conv',2,False,4)
report('conv tercile EW', tok,'conv',3,False,4)
report('conv tercile VW', tok,'conv',3,True,4)
report('conv quintile EW (min3)', tok,'conv',5,False,3)
report('conv quintile VW (min3)', tok,'conv',5,True,3)
report('sector-neutral median EW (sec>=3)', sn,'conv_sn',2,False,4)
report('sector-neutral tercile EW (sec>=3)', sn,'conv_sn',3,False,4)
print('--- post-2023 ---')
report('conv tercile EW', tok,'conv',3,False,4,'2023-01-01')
report('conv quintile EW (min3)', tok,'conv',5,False,3,'2023-01-01')
report('conv quintile VW (min3)', tok,'conv',5,True,3,'2023-01-01')
report('sector-neutral median EW (sec>=3)', sn,'conv_sn',2,False,4,'2023-01-01')
# leg sizes for quintile
s5 = []
for m, g in tok.groupby('month_end'):
    try: b = pd.qcut(g['conv'],5,labels=False,duplicates='drop')
    except ValueError: continue
    if b.max()==4: s5.append(((b==4).sum()+(b==0).sum())/2)
print('quintile avg names/leg: %.1f' % np.mean(s5))
# sector-neutral coverage
print('sector-neutral universe: %d tokens, %d asset-months (of %d), months %d' % (
    sn.cmc_id.nunique(), len(sn), len(tok), sn.month_end.nunique()))
