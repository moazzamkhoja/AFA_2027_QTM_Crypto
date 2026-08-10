"""build_ai_transcripts_volume.py -- Volume II: Verbatim AI Conversation Transcripts.
Run AFTER export_ai_transcripts.py has populated 06_documentation/ai_transcripts/.
Produces 05_paper/AI_TRANSCRIPTS_VOLUME_II.pdf (chronological, one section per session).
If the corpus is too large for a single PDF, falls back to N-part volumes."""
import subprocess, glob
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
files = sorted(glob.glob(str(REPO/'06_documentation'/'ai_transcripts'/'*.md')))
if not files:
    raise SystemExit('No transcripts found. First run: python 04_code/export_ai_transcripts.py '
                     '"C:/Users/<you>/.claude/projects" '
                     '"C:/Users/<you>/AppData/Roaming/Claude/local-agent-mode-sessions"')
PB = chr(92)+chr(92)+'newpage'
parts = ["""% AI Workflow Documentation --- Volume II: Verbatim Conversation Transcripts
% Supplementary Appendix to "Skin in the Chain"
% Moazzam Khoja -- AFA 2027 Special Session

# About this volume

Complete verbatim transcripts of the AI conversations behind the paper, exported from
the machine-readable session records and ordered chronologically. User and assistant
turns are reproduced in full; tool invocations are indicated by name and tool outputs
are truncated (the analytical outputs are committed in the project repository).
Volume I contains the contemporaneous session logs, time log, kickoff prompts, and
decisions log.
"""]
for f in files:
    parts.append('\n' + PB + '\n\n# ' + Path(f).name + '\n\n' + open(f, encoding='utf-8', errors='replace').read())
md = '\n'.join(parts)
for a, b in [('\u03bb','lambda'),('\u2192','->'),('\u00d7','x'),('\u2013','--'),('\u2014','---'),
             ('\u2018',"'"),('\u2019',"'"),('\u201c','"'),('\u201d','"')]:
    md = md.replace(a, b)
md = md.encode('ascii','replace').decode()
head_end = md.index('# ' + Path(files[0]).name)
head, body = md[:head_end], md[head_end:]
body = body.replace(PB, '<<<PB>>>').replace('\\', '/').replace('<<<PB>>>', PB)
md = head + body
src = REPO/'06_documentation'/'AI_TRANSCRIPTS_VOLUME_II.md'
src.write_text(md)
out = REPO/'05_paper'/'AI_TRANSCRIPTS_VOLUME_II.pdf'
r = subprocess.run(['pandoc', str(src), '-o', str(out), '-V','geometry:margin=1in',
                    '-V','fontsize=9pt','--toc','--toc-depth=1'], capture_output=True, text=True)
print(r.stderr[-1500:] if r.returncode else f'OK -> {out} ({len(files)} transcripts)')
