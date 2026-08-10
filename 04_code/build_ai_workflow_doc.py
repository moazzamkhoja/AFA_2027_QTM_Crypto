"""build_ai_workflow_doc.py -- Assemble the supplementary AI Workflow Documentation PDF.
Concatenates: cover/summary + human time log + decisions log + all kickoff prompts
(verbatim initial prompts) + all session logs (+ transcripts index if present)."""
import subprocess, glob, re
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]

parts = ["""% AI Workflow Documentation
% Supplementary Appendix to "Skin in the Chain: Locked Supply and the Cross-Section of Cryptocurrency Returns"
% Moazzam Khoja -- AFA 2027 Special Session of Papers Written with Generative AI Workflows

# Overview

This document is the complete contemporaneous record of the generative-AI workflow used
to produce the paper, per the AFA 2027 Call for Papers. The project began on June 10,
2026 with an initial prompt to Claude (Anthropic); all subsequent work proceeded through
a two-tier workflow: interactive strategy-and-writing sessions (Claude in Cowork) in
which the human author set direction, reviewed output, and made all substantive
decisions, and autonomous build sessions (Claude Code) launched with written kickoff
prompts and reviewed after completion. Contents: (1) the human time log; (2) the
data-decisions log (126 numbered entries recording every methodological decision and
its rationale); (3) all {n_prompts} verbatim kickoff prompts -- the literal initial
prompts given to AI sessions; (4) all {n_logs} session logs written contemporaneously.
Complete machine-readable session transcripts are archived in the project repository
(06_documentation/ai_transcripts/).

\\newpage

# Part 1: Human Time Log

"""]
klist = sorted(glob.glob(str(REPO/'04_code'/'CLAUDE_CODE_*PROMPT*.md')))
slist = sorted(glob.glob(str(REPO/'06_documentation'/'ai_conversations'/'*.md')))
parts[0] = parts[0].replace('{n_prompts}', str(len(klist))).replace('{n_logs}', str(len(slist)))
parts.append(open(REPO/'06_documentation'/'time_log.md').read())
parts.append('\n\\newpage\n\n# Part 2: Data Decisions Log\n\n')
parts.append(open(REPO/'04_code'/'DATA_DECISIONS_LOG.md').read())
parts.append('\n\\newpage\n\n# Part 3: Kickoff Prompts (verbatim initial prompts to AI sessions)\n\n')
for k in klist:
    parts.append(f"\n\\newpage\n\n## {Path(k).name}\n\n" + open(k, encoding='utf-8', errors='replace').read())
parts.append('\n\\newpage\n\n# Part 4: Session Logs (contemporaneous)\n\n')
for s in slist:
    parts.append(f"\n\\newpage\n\n## {Path(s).name}\n\n" + open(s, encoding='utf-8', errors='replace').read())
md = '\n'.join(parts)
# sanitize characters that break latex engines
for a, b in [('\u03bb','lambda'),('\u2192','->'),('\u00d7','x'),('\u2265','>='),('\u2264','<='),
             ('\u2248','~'),('\u2260','!='),('\u03b8','theta'),('\u03b4','delta'),('\u2013','--'),('\u2014','---'),
             ('\u2018',"'"),('\u2019',"'"),('\u201c','"'),('\u201d','"'),('\u221e','inf'),('\u03c6','phi'),
             ('\u03b7','eta'),('\u03b5','eps'),('\u03ba','kappa'),('\u2113','l'),('\u03c8','psi'),('\u2211','sum'),
             ('\u221a','sqrt'),('\u00b1','+/-'),('\u03c1','rho'),('\u03b2','beta'),('\u03b1','alpha'),('\u2208','in')]:
    md = md.replace(a, b)
md = md.encode('ascii', 'replace').decode()
# escape stray backslashes in archived content (Windows paths, latex fragments) --
# everything after the cover section is documentation text, not latex source
cover_end = md.index('# Part 1')
head, body = md[:cover_end], md[cover_end:]
body = body.replace('\\', '/')
md = head + body
src = REPO/'06_documentation'/'AI_WORKFLOW_DOCUMENTATION.md'
src.write_text(md)
out = REPO/'05_paper'/'AI_WORKFLOW_DOCUMENTATION.pdf'
r = subprocess.run(['pandoc', str(src), '-o', str(out), '--from', 'markdown',
                    '-V', 'geometry:margin=1in', '-V', 'fontsize=10pt', '--toc'],
                   capture_output=True, text=True)
print(r.stderr[-2000:] if r.returncode else f'OK -> {out}')
