"""
md_to_pdf.py  --  lightweight Markdown -> PDF converter (reportlab, no external engine)

Handles the Markdown constructs used in this project's reports: # / ## / ### headings,
paragraphs, '-'/'*' bullet and '1.' numbered lists, pipe tables, '---' rules, and inline
**bold**, *italic*, and `code`. Not a full Markdown engine -- just enough for the
project's status / coverage / decisions documents.

Usage:  python 04_code/md_to_pdf.py <input.md> [output.pdf]
"""

import html
import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, ListFlowable, ListItem)

STYLES = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=STYLES["Normal"], fontSize=9.5, leading=13,
                    spaceAfter=4)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8, leading=10)
H1 = ParagraphStyle("h1", parent=STYLES["Title"], fontSize=17, leading=21, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=STYLES["Heading2"], fontSize=13, leading=16,
                    spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#1a3a5c"))
H3 = ParagraphStyle("h3", parent=STYLES["Heading3"], fontSize=11, leading=14,
                    spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#33506b"))


def inline(text):
    """Convert inline markdown to reportlab markup (escaping HTML first)."""
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier" size="8.5">\1</font>', text)
    # italics: single * not adjacent to another * (avoid touching ** already consumed)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    return text


def parse_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    # drop the |---|---| separator row
    cells = [r for r in cells if not all(set(c) <= set("-: ") for c in r)]
    data = [[Paragraph(inline(c), CELL) for c in r] for r in cells]
    t = Table(data, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b8c0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f6")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def convert(md_path, pdf_path):
    lines = Path(md_path).read_text(encoding="utf-8").splitlines()
    story = []
    i = 0
    bullets = []

    def flush_bullets():
        if bullets:
            items = [ListItem(Paragraph(inline(b), BODY), leftIndent=12) for b in bullets]
            story.append(ListFlowable(items, bulletType="bullet", start="•",
                                    leftIndent=14))
            story.append(Spacer(1, 4))
            bullets.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        if re.match(r"^\s*[-*]\s+", ln):
            bullets.append(re.sub(r"^\s*[-*]\s+", "", ln))
            i += 1
            continue
        flush_bullets()
        if not ln.strip():
            story.append(Spacer(1, 4))
        elif ln.startswith("### "):
            story.append(Paragraph(inline(ln[4:]), H3))
        elif ln.startswith("## "):
            story.append(Paragraph(inline(ln[3:]), H2))
        elif ln.startswith("# "):
            story.append(Paragraph(inline(ln[2:]), H1))
        elif ln.strip() in ("---", "***", "___"):
            story.append(Spacer(1, 2))
            story.append(HRFlowable(width="100%", thickness=0.6,
                                    color=colors.HexColor("#b0b8c0")))
            story.append(Spacer(1, 4))
        elif ln.lstrip().startswith("|") and "|" in ln[1:]:
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            story.append(parse_table(block))
            story.append(Spacer(1, 6))
            continue
        elif re.match(r"^\d+\.\s+", ln):
            story.append(Paragraph(inline(ln), BODY))
        else:
            story.append(Paragraph(inline(ln), BODY))
        i += 1
    flush_bullets()

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch,
                            topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                            title=Path(md_path).stem)
    doc.build(story)
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".pdf")
    convert(src, out)
