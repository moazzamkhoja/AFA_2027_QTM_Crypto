import pandas as pd, numpy as np

p = pd.read_csv('regression_panel.csv')
p['month_end'] = pd.to_datetime(p['month_end'])
p = p[p.r_fwd1_w.notna()].copy()

def twoway_ols(d, yvar, xvars):
    d = d.dropna(subset=[yvar]+xvars).copy()
    # month FE via within-month demeaning of y and X
    for v in [yvar]+xvars:
        d[v+'_dm'] = d.groupby('month_end')[v].transform(lambda g: g - g.mean())
    y = d[yvar+'_dm'].values
    X = d[[v+'_dm' for v in xvars]].values
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X@b
    XtXi = np.linalg.inv(X.T@X)
    def clust(ids):
        S = np.zeros((X.shape[1], X.shape[1]))
        for _, idx in pd.Series(range(len(d)), index=ids).groupby(level=0):
            Xg = X[idx.values]; eg = e[idx.values]
            u = Xg.T@eg
            S += np.outer(u, u)
        return XtXi @ S @ XtXi
    Va = clust(d.cmc_id.values)
    Vm = clust(d.month_end.values)
    Vi = clust(pd.MultiIndex.from_arrays([d.cmc_id.values, d.month_end.values]))
    V = Va + Vm - Vi
    se = np.sqrt(np.diag(V))
    return {v: (b[i], b[i]/se[i]) for i, v in enumerate(xvars)}, len(d)

CONTROLS = ['size_std','mom_3m_std','mom_12_2_std','r_1m_std','beta36_std']

for track in ['token','coin']:
    d = p[p.track==track].copy()
    d['conv_x_size'] = d.conv_std * d.size_std
    d['conv_x_val'] = d.conv_std * d.val_std
    print('='*12, track.upper())
    # spec A: conv + controls + conv x size  (size-conditioned H2)
    res, n = twoway_ols(d, 'r_fwd1_w', ['conv_std'] + CONTROLS + ['conv_x_size'])
    print('A: conv x SIZE only          conv %.4f (%.2f)  conv_x_size %.4f (%.2f)  n=%d' %
          (res['conv_std'][0], res['conv_std'][1], res['conv_x_size'][0], res['conv_x_size'][1], n))
    # spec B: full s4 + conv x size (both interactions compete)
    res, n = twoway_ols(d, 'r_fwd1_w', ['conv_std'] + CONTROLS + ['val_std','conv_x_val','conv_x_size'])
    print('B: BOTH interactions         conv_x_val %.4f (%.2f)  conv_x_size %.4f (%.2f)  n=%d' %
          (res['conv_x_val'][0], res['conv_x_val'][1], res['conv_x_size'][0], res['conv_x_size'][1], n))
    # size-median split of conv slope
    d['med_sz'] = d.groupby('month_end')['size_std'].transform('median')
    for lab, sub in [('small', d[d.size_std <= d.med_sz]), ('large', d[d.size_std > d.med_sz])]:
        res, n = twoway_ols(sub, 'r_fwd1_w', ['conv_std'] + CONTROLS)
        print('   split %-5s               conv %.4f (%.2f)  n=%d' % (lab, res['conv_std'][0], res['conv_std'][1], n))
    # corr val vs size
    print('   corr(val_std, size_std) = %.3f' % d[['val_std','size_std']].corr().iloc[0,1])
