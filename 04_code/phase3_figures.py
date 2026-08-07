"""phase3_figures.py -- Figures 1-2 for the paper (from regression_panel + LTW factors)."""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / '03_data' / 'phase3'
FIG = REPO / '05_paper' / 'figures'
FIG.mkdir(exist_ok=True)

p = pd.read_csv(P3/'regression_panel.csv'); p['month_end'] = pd.to_datetime(p['month_end'])
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})

# ---------- Figure 1: two panels ----------
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

# Panel A: coin quadrant cell mean returns
coin = p[(p.track=='coin') & p.conv.notna() & p.val.notna() & p.r_fwd1.notna()].copy()
cells = {k: [] for k in ['Star\n(high conv,\ncheap)','High conv,\nexpensive','Low conv,\ncheap','Avoid\n(low conv,\nexpensive)']}
for m, g in coin.groupby('month_end'):
    hi = g.conv > g.conv.median(); lo = g.val <= g.val.median()
    for key, mask in [('Star\n(high conv,\ncheap)', hi & lo), ('High conv,\nexpensive', hi & ~lo),
                      ('Low conv,\ncheap', ~hi & lo), ('Avoid\n(low conv,\nexpensive)', ~hi & ~lo)]:
        if mask.sum() > 0: cells[key].append(g[mask].r_fwd1.mean())
labels = list(cells)
means = [100*np.mean(v) for v in cells.values()]
ses = [100*np.std(v)/np.sqrt(len(v)) for v in cells.values()]
colors = ['0.25','0.55','0.55','0.8']
axes[0].bar(range(4), means, yerr=ses, capsize=3, color=colors, edgecolor='black', linewidth=0.6)
axes[0].axhline(0, color='black', linewidth=0.8)
axes[0].set_xticks(range(4)); axes[0].set_xticklabels(labels, fontsize=8.5)
axes[0].set_ylabel('Mean next-month return (%)')
axes[0].set_title('A. Coins: returns by conviction-valuation cell', fontsize=10.5)

# Panel B: token mean return by conviction quintile
tok = p[(p.track=='token') & p.conv.notna() & p.r_fwd1.notna()].copy()
qrets = {q: [] for q in range(5)}
for m, g in tok.groupby('month_end'):
    if len(g) < 15: continue
    try: b = pd.qcut(g.conv, 5, labels=False, duplicates='drop')
    except ValueError: continue
    if b.max()!=4: continue
    for q in range(5):
        sub = g[b==q]
        if len(sub): qrets[q].append(sub.r_fwd1.mean())
means = [100*np.mean(qrets[q]) for q in range(5)]
ses = [100*np.std(qrets[q])/np.sqrt(len(qrets[q])) for q in range(5)]
axes[1].bar(range(5), means, yerr=ses, capsize=3, color=['0.8','0.7','0.6','0.45','0.25'], edgecolor='black', linewidth=0.6)
axes[1].axhline(0, color='black', linewidth=0.8)
axes[1].set_xticks(range(5)); axes[1].set_xticklabels(['Q1\n(low conv)','Q2','Q3','Q4','Q5\n(high conv)'], fontsize=9)
axes[1].set_ylabel('Mean next-month return (%)')
axes[1].set_title('B. Tokens: returns by conviction quintile', fontsize=10.5)
plt.tight_layout()
plt.savefig(FIG/'fig1_conviction_returns.pdf', bbox_inches='tight')
plt.close()

# ---------- Figure 2: cumulative log return, token conviction q5 LS vs EW token benchmark ----------
def q5_ls(d):
    out = {}
    for m, g in d.groupby('month_end'):
        try: b = pd.qcut(g.conv, 5, labels=False, duplicates='drop')
        except ValueError: continue
        if b.max()!=4: continue
        top, bot = g[b==4], g[b==0]
        if len(top)<3 or len(bot)<3: continue
        out[m] = top.r_fwd1.mean() - bot.r_fwd1.mean()
    s = pd.Series(out); s.index = pd.DatetimeIndex(s.index); return s.sort_index()
ls = q5_ls(tok)
bench = tok.groupby('month_end').r_fwd1.mean()
bench = bench.loc[ls.index]
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(ls.index, np.cumsum(np.log1p(ls)), color='black', linewidth=1.8, label='Conviction quintile long-short (EW)')
ax.plot(bench.index, np.cumsum(np.log1p(bench)), color='0.55', linewidth=1.4, linestyle='--', label='EW token universe')
ax.axhline(0, color='black', linewidth=0.7)
ax.set_ylabel('Cumulative log return')
ax.legend(frameon=False, fontsize=9.5)
plt.tight_layout()
plt.savefig(FIG/'fig2_cumulative.pdf', bbox_inches='tight')
plt.close()
print('figures written:', list(str(x.name) for x in FIG.glob('*.pdf')))
print('LS months %d mean %.4f | bench mean %.4f' % (len(ls), ls.mean(), bench.mean()))
