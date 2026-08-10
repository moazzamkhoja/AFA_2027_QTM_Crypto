"""build_ai_transcripts_volume.py -- Volume II: Verbatim AI Conversation Transcripts.
Run AFTER export_ai_transcripts.py has populated 06_documentation/ai_transcripts/.
Produces 05_paper/AI_TRANSCRIPTS_VOLUME_II.pdf (chronological, one section per session).
Chunked build: each transcript is pandoc-converted to a LaTeX fragment separately
(the single-file conversion exceeds pandoc's memory on modest machines), then a
master document \\input{}s the fragments and compiles with pdflatex."""
import subprocess, glob, tempfile, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
files = sorted(glob.glob(str(REPO/'06_documentation'/'ai_transcripts'/'*.md')))
if not files:
    raise SystemExit('No transcripts found. First run: python 04_code/export_ai_transcripts.py '
                     '"C:/Users/<you>/.claude/projects" '
                     '"C:/Users/<you>/AppData/Roaming/Claude/local-agent-mode-sessions"')

ABOUT = r"""Complete verbatim transcripts of the AI conversations behind the paper, exported from
the machine-readable session records and ordered chronologically. User and assistant
turns are reproduced in full; tool invocations are indicated by name and tool outputs
are truncated (the analytical outputs are committed in the project repository).
Volume I contains the contemporaneous session logs, time log, kickoff prompts, and
decisions log. Coverage note: machine transcripts survive on the author's system from
June 30, 2026 onward; the June 10--19 theory-formulation conversations (sessions
001--005) predate the earliest retained transcript files, and their contemporaneous
session logs in Volume I are the record for that phase. Conversations unrelated to
this project were excluded from the export."""

def sanitize(md):
    for a, b in [('\u03bb','lambda'),('\u2192','->'),('\u00d7','x'),('\u2013','--'),('\u2014','---'),
                 ('\u2018',"'"),('\u2019',"'"),('\u201c','"'),('\u201d','"')]:
        md = md.replace(a, b)
    md = md.encode('ascii','replace').decode()
    return md.replace('\\', '/')   # kill Windows-path backslashes before pandoc

work = Path(tempfile.mkdtemp(prefix='vol2_'))
frags = []
for i, f in enumerate(files):
    name = Path(f).name
    md = sanitize(open(f, encoding='utf-8', errors='replace').read())
    # drop the transcript's own H1 (fragment gets a \section from the master)
    lines = md.split('\n')
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    src = work / f'frag{i:02d}.md'
    src.write_text('\n'.join(lines), encoding='utf-8')
    tex = work / f'frag{i:02d}.tex'
    # -f commonmark: pandoc's default markdown reader has pathological (memory-
    # exhausting) behavior on emphasis-heavy transcript text; commonmark is linear.
    r = subprocess.run(['pandoc', str(src), '-f', 'commonmark', '-t', 'latex',
                        '-o', str(tex), '--shift-heading-level-by=1'],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'pandoc failed on {name}:\n{r.stderr[-1000:]}')
    frags.append((name, tex))

esc = lambda s: s.replace('_', r'\_')
master = [r"""\documentclass[9pt]{extarticle}
\usepackage[margin=1in]{geometry}
\usepackage[T1]{fontenc}\usepackage{lmodern}
\usepackage{longtable,booktabs,graphicx,fancyvrb,upquote,microtype,xcolor}
\usepackage[hidelinks]{hyperref}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\setcounter{tocdepth}{1}
\setlength{\emergencystretch}{3em}
\title{AI Workflow Documentation --- Volume II:\\Verbatim Conversation Transcripts\\
\large Supplementary Appendix to ``Skin in the Chain''}
\author{Moazzam Khoja --- AFA 2027 Special Session}
\date{}
\begin{document}
\maketitle
\section*{About this volume}
""" + ABOUT + r"""
\newpage
\tableofcontents
"""]
for name, tex in frags:
    master.append('\\newpage\n\\section{%s}\n\\input{%s}\n' % (esc(name), tex.stem))
master.append('\\end{document}\n')
(work/'master.tex').write_text(''.join(master), encoding='utf-8')

ok = True
for _ in range(2):
    r = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'master.tex'],
                       cwd=work, capture_output=True, text=True)
    if not (work/'master.pdf').exists():
        ok = False
        break
out = REPO/'05_paper'/'AI_TRANSCRIPTS_VOLUME_II.pdf'
if ok and (work/'master.pdf').exists():
    shutil.copy(work/'master.pdf', out)
    print(f'OK -> {out} ({len(files)} transcripts)')
else:
    tail = '\n'.join((work/'master.log').read_text(errors='replace').splitlines()[-40:]) \
           if (work/'master.log').exists() else r.stdout[-2000:]
    raise SystemExit('pdflatex failed:\n' + tail)
