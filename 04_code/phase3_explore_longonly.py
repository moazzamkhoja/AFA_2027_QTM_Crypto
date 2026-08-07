import pandas as pd, numpy as np
p = pd.read_csv('regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
f = pd.read_csv('ltw_factors_monthly.csv'); f['month_end'] = pd.to_datetime(f['month_end']); f = f.set_index('month_end')
tok = p[(p.track=='token') & p.conv.notna() & p.r_fwd1.notna()].copy()

Q5, Q1, BENCH = {}, {}, {}
for m, g in tok.groupby('month_end'):
    try: b = pd.qcut(g.conv, 5, labels=False, duplicates='drop')
    except ValueError: continue
    if b.max()!=4: continue
    top, bot = g[b==4], g[b==0]
    if len(top)<3 or len(bot)<3: continue
    Q5[m] = top.r_fwd1.mean(); Q1[m] = bot.r_fwd1.mean(); BENCH[m] = g.r_fwd1.mean()
q5 = pd.Series(Q5).sort_index(); q1 = pd.Series(Q1).sort_index(); bench = pd.Series(BENCH).sort_index()
for s in (q5, q1, bench): s.index = pd.DatetimeIndex(s.index)

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
    return b[0], b[0]/np.sqrt(V[0,0]), b[1], len(df)

def stats(s, name):
    a, t, beta, n = nw_alpha(s)
    sh = (s.mean() - 0.04/12)/s.std()*np.sqrt(12)
    act = s - bench.loc[s.index]
    ir = act.mean()/act.std()*np.sqrt(12)
    t_act = act.mean()/(act.std()/np.sqrt(len(act)))
    print('%-22s mean %+6.2f%%  Sharpe %+5.2f  alpha %+6.2f%% (t %+0.2f)  b_mkt %.2f  active %+5.2f%%/mo (t %+0.2f)  IR %+5.2f  n %d' % (
        name, 100*s.mean(), sh, 100*a, t, beta, 100*act.mean(), t_act, ir, n))

stats(q5, 'Q5 long-only (high conv)')
stats(q1, 'Q1 long-only (low conv)')
a,t,beta,n = nw_alpha(bench)
sh = (bench.mean()-0.04/12)/bench.std()*np.sqrt(12)
print('%-22s mean %+6.2f%%  Sharpe %+5.2f  alpha %+6.2f%% (t %+0.2f)  b_mkt %.2f' % ('EW token benchmark', 100*bench.mean(), sh, 100*a, t, beta))
