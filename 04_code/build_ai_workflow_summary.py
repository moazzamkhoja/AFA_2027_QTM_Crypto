"""Compact AI workflow documentation: 2-page summary + 1-page time table.
Output: 05_paper/AI_WORKFLOW_DOCUMENTATION.pdf (verbatim record = Volume II, separate)."""
import subprocess, re, collections
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]

SUMMARY = r"""% AI Workflow Documentation
% Supplementary Appendix to "Skin in the Chain: Locked Supply and the Cross-Section of Cryptocurrency Returns"
% Moazzam Khoja --- AFA 2027 Special Session of Papers Written with Generative AI Workflows

# Summary of AI Conversations (June 10 -- August 10, 2026)

The project comprised 46 logged AI sessions across two environments: interactive
Cowork conversations (Claude, Anthropic), where the author set direction, critiqued
output, and made every substantive decision, and autonomous Claude Code build
sessions, each launched from a written kickoff prompt fixed in advance and reviewed
afterward under an honest-results clause forbidding specification changes after
results were seen. Full verbatim transcripts are in Volume II; the repository
(github.com/moazzamkhoja/AFA_2027_QTM_Crypto) archives the 46 contemporaneous session
logs, 33 verbatim kickoff prompts, a 127-entry decisions log, and all code and data.

**Phase A --- Theory and literature (June 10--19; sessions 001--005, Cowork).**
The author shared the AFA call and a two-page QTM valuation framework. Conversations
established the theoretical foundations: convenience yield (Sockin-Xiong) and
monetary search (Kiyotaki-Wright) as primary frames, seigniorage (Cong et al.) as
the income mechanism, the coin/token distinction, and the central construct --- the
conviction ratio lambda, the locked fraction of supply, with the SoV/MoE
decomposition following from QTM. The author rejected an early theta-coefficient
formulation, demanded a rigorous continuum-of-agents aggregation to replace a flawed
step, challenged an artificial model split, and approved the hypotheses (conviction
level; valuation conditioning; quadrant portfolio). First drafts of the
introduction and theory were written and revised through detailed author critique
(eight tracked issues in one round).

**Phase B --- Data construction (June 22 -- July 30; sessions 006--041, mostly
Claude Code).** Autonomous sessions built the empirical infrastructure from free,
verifiable sources under standing constraints (no paid tiers; all joins on
CoinMarketCap id; engine guards immutable): a 1,939-asset monthly universe
(2015--2026); the three-channel conviction panel (staking from chain-native
archives, HODL-6m from full transfer-log replay on thirteen EVM chains, governance
delegation/voting); on-chain transaction-volume series validated within 5 percent of
chain totals; the TVL panel; and the growth-levelized valuation ratios. The phase
was iterative and adversarial with the data: fake archive nodes were detected and
excluded, identity mismatches purged, contamination guards enforced, and every dead
end (Monero's hidden amounts, pruned nodes, paid-only vendors) logged rather than
papered over. Final samples: 24 proof-of-stake coins (718 asset-months) and 101
tokens (2,771 asset-months).

**Phase C --- Empirical testing (August 4; sessions 042--045).** A Cowork session
fixed the analysis specification in advance (regression ladders, self-built monthly
Liu-Tsyvinski-Wu factor analogs, portfolio rules); three Claude Code sessions then
executed it. Results: the conviction level is rejected for coins but its interaction
with valuation is strongly negative and survives a twelve-signal joint race; for
tokens conditioning fails under six valuation measures, while conviction is priced
through the extremes of its distribution --- a quintile long-short earning 1.7
percent monthly factor-adjusted alpha that no competitor portfolio spans. Nulls (the
quadrant portfolio, scarcity models) were reported at equal prominence. Mechanism
tests (M1--M4) were postulated after the coin/token asymmetry emerged and tested
once each; author-directed review analyses (within-sector quintiles, long-only
implementation, channel decomposition) were run once and disclosed as exploratory.

**Phase D --- Writing, revision, and submission (August 4--10; Cowork).** The
author directed successive pruning and rewriting rounds: hypotheses unified across
asset classes, mechanisms moved to robustness with a postulate-then-test framing,
tables restructured around the questions they answer, three introduction iterations
(motivation-first opening; lambda as the bridge between QTM and tokenized models;
findings led by the joint-race and spanning results), the final abstract in the
author's own words, and the title. The author caught and corrected several AI
errors along the way, including a mischaracterization of practitioner valuation
methods, a stale significance claim, and a misleading between-sector framing that a
requested power analysis overturned. The phase closed with assembly of this
documentation package.

**Division of labor.** The author contributed direction, theory judgment, all
hypothesis and identification decisions, quality control, and final language; the
AI contributed drafting, literature synthesis, all data engineering and estimation
code, execution of pre-specified analyses, and revision mechanics. Every
substantive claim in the paper traces to a decision recorded in the logs.

**Line attribution (human vs.\ AI).** Counted from the repository at submission:
17,502 lines of code (Python builders, analysis scripts, utilities), 2,019 lines of
paper source (LaTeX), and 28,262 lines of documentation (session logs, decisions
log, kickoff prompts, specifications, literature review) --- 47,783 committed lines
in total. Measured by who typed the committed line, the AI contributed over 99.9
percent: the author's directly typed contributions are the final abstract text
(drafted verbatim by the author) and scattered sentence-level wordings dictated in
conversation. The author's contribution is instead concentrated in the layer the
line counts do not capture: the initial prompt and all subsequent direction, the
theoretical judgments, every methodological decision (127 logged entries), quality
control that caught and reversed AI errors, and approval of all final language ---
approximately 53 hours of logged human time against roughly two person-months of
AI-executed construction, estimation, and writing.

\newpage

# Time Log by Conversation

Human time from the contemporaneous time log (66 entries; durations marked * are
author estimates). AI session wall-clock time where recorded in session logs;
autonomous sessions ran unattended.

"""

# ---- build per-session time table ----
rows = [l for l in open(REPO/'06_documentation'/'time_log.md') if l.startswith('| 202')]
sess_min = collections.defaultdict(int); sess_est = collections.defaultdict(bool)
date_of = {}
logs = sorted((REPO/'06_documentation'/'ai_conversations').glob('session_*.md'))
sess_dates = {}
for f in logs:
    m = re.match(r'session_(\d+)', f.name)
    d = re.search(r'(\d{4}-\d{2}-\d{2})', f.name)
    if m: sess_dates.setdefault(int(m.group(1)), d.group(1) if d else '')
unmatched = collections.defaultdict(int)
for r in rows:
    parts = [p.strip() for p in r.split('|')[1:-1]]
    date, dur, desc = parts[0], parts[1], parts[3]
    # duration column is uniformly MINUTES (hour-denominated estimates were
    # normalized to minutes on 2026-08-10; see decisions log Entry 128)
    m = re.search(r'(\d+)', dur); v = int(m.group(1)) if m else 0
    est = 'est' in dur
    sm = re.search(r'[Ss]ession[s]?\s0*(\d+)', desc)
    if sm:
        k = int(sm.group(1)); sess_min[k] += v; sess_est[k] |= est
    else:
        unmatched[date] += v
# fold unmatched by date onto sessions of that date (else general row)
for d, v in list(unmatched.items()):
    hits = [k for k, dd in sess_dates.items() if dd == d]
    if len(hits) >= 1:
        sess_min[hits[0]] += v; del unmatched[d]

table = ['| Session | Date | Topic | Human (min) |', '|---|---|---|---|']
topics = {}
for f in logs:
    m = re.match(r'session_(\d+)_?([\d-]*)_?(.*)\.md', f.name)
    if m: topics[int(m.group(1))] = (m.group(3) or 'general').replace('_',' ')[:44]
total = 0
for k in sorted(sess_dates):
    v = sess_min.get(k, 0); total += v
    flag = '*' if sess_est.get(k) else ''
    table.append(f"| {k:03d} | {sess_dates[k]} | {topics.get(k,'')} | {v}{flag} |")
for d, v in sorted(unmatched.items()):
    total += v
    table.append(f"| --- | {d} | general (unmapped entries) | {v}* |")
table.append(f"| | | **Total human time** | **{total} min (~{total/60:.0f} h)** |")
table.append('')
table.append('AI compute: 36 autonomous Claude Code build sessions (typically 1--3 h '
             'wall-clock each where logged) plus interactive Cowork sessions concurrent '
             'with the human time above. Autonomous sessions required no human attention '
             'between launch and review.')

md = SUMMARY + '\n'.join(table) + '\n'
src = REPO/'06_documentation'/'AI_WORKFLOW_SUMMARY.md'
src.write_text(md)
out = REPO/'05_paper'/'AI_WORKFLOW_DOCUMENTATION.pdf'
r = subprocess.run(['pandoc', str(src), '-o', str(out), '-V','geometry:margin=1in',
                    '-V','fontsize=10pt'], capture_output=True, text=True)
print(r.stderr[-800:] if r.returncode else f'OK -> {out}')
