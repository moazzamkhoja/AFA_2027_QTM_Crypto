import pandas as pd, numpy as np
p = pd.read_csv('regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
lam = pd.read_csv('../phase1/lambda_panel.csv'); lam['month_end'] = pd.to_datetime(lam['month_end'])
f = pd.read_csv('ltw_factors_monthly.csv'); f['month_end'] = pd.to_datetime(f['month_end']); f = f.set_index('month_end')

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

# ---- Q4: coin quadrant with min_leg 2 and 3 ----
coin = p[(p.track=='coin') & p.conv.notna() & p.val.notna() & p.r_fwd1.notna()]
def quad(d, mn):
    out = {}
    for m, g in d.groupby('month_end'):
        hi_c = g.conv > g.conv.median(); lo_v = g.val <= g.val.median()
        star, avoid = g[hi_c & lo_v], g[~hi_c & ~lo_v]
        if len(star)<mn or len(avoid)<mn: continue
        out[m] = star.r_fwd1.mean() - avoid.r_fwd1.mean()
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index); return s.sort_index()
print('Q4: coin quadrant SMA EW by min names/leg')
for mn in [4,3,2,1]:
    s = quad(coin, mn)
    if len(s) < 10: print(' min %d: too few months (%d)' % (mn, len(s))); continue
    a, t, n = nw_alpha(s)
    print(' min %d: alpha %+.4f (t %+0.2f)  months %d  mean %+.4f  sd %.3f' % (mn, a, t, n, s.mean(), s.std()))

# ---- Q6: token conviction channels ----
tok = p[(p.track=='token') & p.r_fwd1.notna()].merge(
    lam[['cmc_id','month_end','raw_ch1_staking','raw_ch2_holding','raw_ch3_delegation','raw_ch3_voting']],
    on=['cmc_id','month_end'], how='left')
print()
print('Q6: token conviction channels — coverage, panel slope (month FE, 2-way cl.), quintile LS alpha')

def twoway(d, yvar, xvars):
    d = d.dropna(subset=[yvar]+xvars).copy()
    for v in [yvar]+xvars:
        d[v+'_dm'] = d.groupby('month_end')[v].transform(lambda g: g - g.mean())
    y = d[yvar+'_dm'].values; X = d[[v+'_dm' for v in xvars]].values
    b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X@b
    XtXi = np.linalg.inv(X.T@X)
    def clust(ids):
        S = np.zeros((X.shape[1],)*2)
        for _, idx in pd.Series(range(len(d)), index=ids).groupby(level=0):
            u = X[idx.values].T @ e[idx.values]; S += np.outer(u,u)
        return XtXi @ S @ XtXi
    V = clust(d.cmc_id.values) + clust(d.month_end.values) - clust(pd.MultiIndex.from_arrays([d.cmc_id.values,d.month_end.values]))
    return b[0], b[0]/np.sqrt(V[0,0]), len(d), d.cmc_id.nunique()

def q_ls(d, sig, q=5, mn=3):
    out = {}
    for m, g in d.groupby('month_end'):
        g = g.dropna(subset=[sig])
        if len(g) < q*mn: continue
        try: b = pd.qcut(g[sig], q, labels=False, duplicates='drop')
        except ValueError: continue
        if b.max()!=q-1: continue
        top, bot = g[b==q-1], g[b==0]
        if len(top)<mn or len(bot)<mn: continue
        out[m] = top.r_fwd1.mean() - bot.r_fwd1.mean()
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index); return s.sort_index()

CONTROLS = ['size_std','mom_3m_std','mom_12_2_std','r_1m_std','beta36_std']
for ch, lab in [('raw_ch1_staking','ch1 staking'), ('raw_ch2_holding','ch2 holding (HODL)'),
                ('raw_ch3_delegation','ch3 delegation'), ('raw_ch3_voting','ch3 voting')]:
    d = tok[tok[ch].notna()].copy()
    if len(d) < 100:
        print(' %-20s n=%d — too thin' % (lab, len(d))); continue
    d['ch_std'] = d.groupby('month_end')[ch].transform(lambda g: (g-g.mean())/g.std() if g.std()>0 else g*0)
    b, t, n, na = twoway(d, 'r_fwd1_w', ['ch_std']+CONTROLS)
    s = q_ls(d, ch)
    if len(s) >= 12:
        a, ta, nm = nw_alpha(s)
        port = 'q5 LS alpha %+.4f (t %+0.2f) mo %d' % (a, ta, nm)
    else:
        port = 'q5 LS infeasible (%d months)' % len(s)
    print(' %-20s n=%5d assets=%3d  slope %+.4f (t %+0.2f)  %s' % (lab, n, na, b, t, port))
# composite reference
d = tok[tok.conv.notna()].copy()
b, t, n, na = twoway(d, 'r_fwd1_w', ['conv_std']+CONTROLS)
print(' %-20s n=%5d assets=%3d  slope %+.4f (t %+0.2f)  q5 LS alpha +0.0171 (t +2.18) mo 50' % ('composite lambda_z', n, na, b, t))
