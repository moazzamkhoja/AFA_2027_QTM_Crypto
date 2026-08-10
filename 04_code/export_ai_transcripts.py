"""export_ai_transcripts.py -- Convert Claude .jsonl session transcripts to readable Markdown.

USAGE (run on your own machine, where the transcripts live):
  python 04_code/export_ai_transcripts.py "<folder-with-jsonl-files>" [more folders...]

Transcript locations on Windows:
  Claude Code sessions for this repo:
      C:\\Users\\<you>\\.claude\\projects\\C--AFA-2027-QTM-Crypto\\*.jsonl
  Cowork (desktop app) sessions:
      C:\\Users\\<you>\\AppData\\Roaming\\Claude\\local-agent-mode-sessions\\**\\.claude\\projects\\**\\*.jsonl

Output: 06_documentation/ai_transcripts/<source-file>.md  (verbatim user/assistant text;
tool calls summarized by name; tool outputs truncated to 500 chars — the analytical
outputs are already committed in the repo).
"""
import json, sys, glob, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / '06_documentation' / 'ai_transcripts'
OUT.mkdir(exist_ok=True)

def render_content(content):
    parts = []
    if isinstance(content, str):
        return content
    for block in content or []:
        t = block.get('type')
        if t == 'text':
            parts.append(block.get('text', ''))
        elif t == 'thinking':
            parts.append('*[extended thinking omitted]*')
        elif t == 'tool_use':
            parts.append(f"*[tool call: {block.get('name','?')}]*")
        elif t == 'tool_result':
            c = block.get('content')
            s = c if isinstance(c, str) else json.dumps(c)[:500] if c else ''
            parts.append(f"*[tool result]* `{str(s)[:500]}`")
    return '\n\n'.join(p for p in parts if p)

def convert(path):
    lines_out = [f"# Transcript: {os.path.basename(path)}\n"]
    n = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: rec = json.loads(line)
            except json.JSONDecodeError: continue
            msg = rec.get('message') or rec
            role = msg.get('role') or rec.get('type')
            if role not in ('user', 'assistant'): continue
            body = render_content(msg.get('content'))
            if not body.strip(): continue
            ts = rec.get('timestamp', '')
            lines_out.append(f"\n---\n\n**{role.upper()}** {ts}\n\n{body}\n")
            n += 1
    if n == 0: return None
    # date-prefix for chronological ordering
    first_ts = ''
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            try: rec = json.loads(line)
            except Exception: continue
            ts = rec.get('timestamp')
            if ts: first_ts = str(ts)[:10]; break
    prefix = (first_ts + '_') if first_ts else ''
    dest = OUT / (prefix + Path(path).stem + '.md')
    dest.write_text('\n'.join(lines_out), encoding='utf-8')
    return dest, n

if __name__ == '__main__':
    args = sys.argv[1:] or [str(REPO)]
    files = []
    for a in args:
        # Windows long-path support: Cowork session transcripts sit behind paths
        # longer than MAX_PATH (260); the \\?\ prefix lets us traverse them.
        if os.name == 'nt' and not a.startswith('\\\\?\\'):
            try: a_ext = '\\\\?\\' + str(Path(a).resolve())
            except OSError: a_ext = a
        else:
            a_ext = a
        p = Path(a_ext)
        files += [str(x) for x in p.rglob('*.jsonl')] if p.is_dir() else glob.glob(a)
    files = [f for f in files if 'audit.jsonl' not in f.lower()]  # audit logs handled separately
    print(f"found {len(files)} .jsonl files")
    for fp in sorted(files):
        r = convert(fp)
        if r: print(f"  {fp} -> {r[0].name} ({r[1]} messages)")
