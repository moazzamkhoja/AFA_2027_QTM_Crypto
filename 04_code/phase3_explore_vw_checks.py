import pandas as pd, numpy as np
p = pd.read_csv('regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
hs = pd.read_csv('horserace_signals.csv'); hs['month_end'] = pd.to_datetime(hs['month_end'])
ts = pd.read_csv('technical_signals.csv'); ts['month_end'] = pd.to_datetime(ts['month_end'])
fc = pd.read_csv('fee_comparators.csv'); fc['month_end'] = pd.to_datetime(fc['month_end'])
f = pd.read_csv('ltw_factors_monthly.csv'); f['month_end'] = pd.to_datetime(f['month_end']); f = f.set_index('month_end')
tok = p[(p.track=='token') & p.r_fwd1.notna()].merge(hs.drop(columns=['track']), on=['cmc_id','month_end'], how='left')
tok = tok.merge(ts.drop(columns=['track']), on=['cmc_id','month_end'], how='left')
tok = tok.merge(fc[['cmc_id','month_end','pf_ln']], on=['cmc_id','month_end'], how='left')

def q_ls(d, sig, vw=False, invert=False, q=5, mn=3):
    out = {}
    for m, g in d.groupby('month_end'):
        g = g.dropna(subset=[sig])
        if len(g) < q*mn: continue
        try: b = pd.qcut(g[sig], q, labels=False, duplicates='drop')
        except ValueError: continue
        if b.max() != q-1: continue
        top, bot = g[b==q-1], g[b==0]
        if len(top)<mn or len(bot)<mn: continue
        if vw:
            rt = np.average(top.r_fwd1, weights=top.market_cap); rb = np.average(bot.r_fwd1, weights=bot.market_cap)
        else:
            rt, rb = top.r_fwd1.mean(), bot.r_fwd1.mean()
        out[m] = (rb - rt) if invert else (rt - rb)
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index); return s.sort_index()

def nw_alpha(y, X_extra=None, lags=3):
    df = pd.concat([y.rename('y'), f[['cmkt','csmb','cmom']]] + ([X_extra] if X_extra is not None else []), axis=1, join='inner').dropna()
    yv = df['y'].values; X = np.column_stack([np.ones(len(df)), df.drop(columns='y').values])
    b = np.linalg.lstsq(X, yv, rcond=None)[0]; e = yv - X@b; n,k = X.shape
    XtXi = np.linalg.inv(X.T@X); S = np.zeros((k,k))
    for l in range(lags+1):
        w = 1 - l/(lags+1)
        for t in range(l, n):
            S += w*np.outer(X[t]*e[t], X[t-l]*e[t-l])
            if l>0: S += w*np.outer(X[t-l]*e[t-l], X[t]*e[t])
    V = XtXi @ S @ XtXi
    return b[0], b[0]/np.sqrt(V[0,0]), len(df)

q5vw = q_ls(tok[tok.conv.notna()], 'conv', vw=True)
q5ew = q_ls(tok[tok.conv.notna()], 'conv', vw=False)
# 12 competitor EW long-shorts
comp = {}
for sig, inv in [('r_1m',True),('mom_3m',False),('mom_12_2',False),('high52',False),('size',False),
                 ('raw_val',True),('s2f_ln',False),('ma_dist',False),('vol12',False),('ivol',False),
                 ('amihud',False),('skew36',False)]:
    comp[sig] = q_ls(tok, sig, vw=False, invert=inv)
X12 = pd.DataFrame(comp)
for name, s in [('q5 VW: LTW only', None), ('q5 VW: + completed 12-battery', X12)]:
    a, t, n = nw_alpha(q5vw, s)
    print('%-34s alpha %+.4f  t %+0.2f  n %d' % (name, a, t, n))
a, t, n = nw_alpha(q5ew, X12)
print('%-34s alpha %+.4f  t %+0.2f  n %d  (check vs 3c: +1.74/2.45)' % ('q5 EW: + 12-battery (replication)', a, t, n))

# P/F quadrant VW
def quad(d, valcol, vw, mn=4):
    out = {}
    for m, g in d.groupby('month_end'):
        g = g.dropna(subset=['conv', valcol])
        if len(g) < 8: continue
        hi_c = g.conv > g.conv.median(); lo_v = g[valcol] <= g[valcol].median()
        star, avoid = g[hi_c & lo_v], g[~hi_c & ~lo_v]
        if len(star)<mn or len(avoid)<mn: continue
        if vw:
            rs = np.average(star.r_fwd1, weights=star.market_cap); ra = np.average(avoid.r_fwd1, weights=avoid.market_cap)
        else:
            rs, ra = star.r_fwd1.mean(), avoid.r_fwd1.mean()
        out[m] = rs - ra
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index); return s.sort_index()
for vw in [False, True]:
    s = quad(tok[tok.conv.notna()], 'pf_ln', vw)
    a, t, n = nw_alpha(s)
    sh = s.mean()/s.std()*np.sqrt(12)
    print('P/F quadrant %s: alpha %+.4f  t %+0.2f  n %d  Sharpe %+.2f' % ('VW' if vw else 'EW', a, t, n, sh))
