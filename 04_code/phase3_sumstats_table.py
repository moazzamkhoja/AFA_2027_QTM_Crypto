import pandas as pd, numpy as np
p = pd.read_csv('regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
fc = pd.read_csv('fee_comparators.csv'); fc['month_end'] = pd.to_datetime(fc['month_end'])
tvl = pd.read_csv('../phase2/nv_tvl_gl_panel.csv'); tvl['month_end'] = pd.to_datetime(tvl['month_end'])
p = p.merge(fc[['cmc_id','month_end','pf']], on=['cmc_id','month_end'], how='left')
p = p.merge(tvl[['cmc_id','month_end','tvl_usd']], on=['cmc_id','month_end'], how='left')

def stats(s, name, scale=1.0, pct=False):
    s = s.dropna() / scale
    f = (lambda x: 100*x) if pct else (lambda x: x)
    return [name, len(s)] + [f(v) for v in [s.mean(), s.std(), s.quantile(.10), s.quantile(.25), s.median(), s.quantile(.75), s.quantile(.90)]]

rows = []
coin = p[p.track=='coin']
c1 = coin[coin.conv_source=='ch1_lnodds'] if 'conv_source' in coin else coin
lam = 1/(1+np.exp(-c1.conv))         # staking share from log-odds
rows.append(('COINS', None))
rows.append(stats(lam, 'Staking share $\\lambda$ (\\%)', pct=True))
rows.append(stats(np.exp(c1.conv), 'SoV/MoE ratio $\\lambda/(1-\\lambda)$'))
rows.append(stats(coin.val_raw, 'NVT\\_GL'))
rows.append(stats(coin.market_cap, 'Market cap (\\$M)', scale=1e6))
rows.append(stats(coin.r_fwd1, 'Monthly return $t{+}1$ (\\%)', pct=True))
rows.append(stats(coin.beta36, 'Beta (36m)'))
tok = p[p.track=='token']
rows.append(('TOKENS', None))
rows.append(stats(tok.conv, 'Conviction index $\\lambda_z$'))
rows.append(stats(tok.val_raw, 'NV/TVL\\_GL'))
rows.append(stats(tok.tvl_usd, 'TVL (\\$M)', scale=1e6))
rows.append(stats(tok.pf, 'Price-to-fees (P/F)'))
rows.append(stats(tok.market_cap, 'Market cap (\\$M)', scale=1e6))
rows.append(stats(tok.r_fwd1, 'Monthly return $t{+}1$ (\\%)', pct=True))
rows.append(stats(tok.beta36, 'Beta (36m)'))

def fmt(v):
    if abs(v) >= 1000: return f'{v:,.0f}'
    if abs(v) >= 10: return f'{v:.1f}'
    return f'{v:.2f}'
for r in rows:
    if r[1] is None: print('--- ' + r[0]); continue
    print('%-38s & %5d & %s \\\\' % (r[0], r[1], ' & '.join(fmt(v) for v in r[2:])))
print()
print('ch1 coin-months:', len(c1), 'of', len(coin))
