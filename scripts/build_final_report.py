from __future__ import annotations

import html
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.shared import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
BASE_REPORT = ROOT / "final_report.md"
COMPLETE_MD = REPORTS_DIR / "final_report_complete.md"
DOCX_OUT = REPORTS_DIR / "final_report_complete.docx"
PDF_OUT = REPORTS_DIR / "final_report_complete.pdf"

CODE_APPENDICES = [
    ("automation/main.py", ROOT / "automation" / "main.py"),
    ("automation/translator.py", ROOT / "automation" / "translator.py"),
    ("automation/content_enricher.py", ROOT / "automation" / "content_enricher.py"),
    ("automation/image_generator.py", ROOT / "automation" / "image_generator.py"),
    ("automation/strapi_api.py", ROOT / "automation" / "strapi_api.py"),
    ("automation/data/places.json", ROOT / "automation" / "data" / "places.json"),
]


def build_complete_markdown() -> str:
    report = BASE_REPORT.read_text(encoding="utf-8").rstrip()
    parts = [report, "\n\n---\n\n# Ekler: Python Betiğinin Tam Metni\n"]
    for label, path in CODE_APPENDICES:
        language = "json" if path.suffix == ".json" else "python"
        code = path.read_text(encoding="utf-8")
        parts.append(f"\n## Ek - {label}\n\n```{language}\n{code.rstrip()}\n```\n")
    return "\n".join(parts).strip() + "\n"


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_markdown_lines(markdown_text: str):
    lines = markdown_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            lang = line.strip("`").strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            yield ("code", lang, "\n".join(code_lines))
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[i + 1]):
            header = split_table_row(line)
            rows = []
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            yield ("table", header, rows)
            continue
        else:
            yield ("line", line)
        i += 1


def clean_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text


def add_docx_text(doc: Document, text: str, style: str | None = None):
    paragraph = doc.add_paragraph(style=style)
    paragraph.add_run(clean_inline_markdown(text))
    return paragraph


def create_docx(markdown_text: str):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    for style_name, size in [("Heading 1", 18), ("Heading 2", 14), ("Heading 3", 12)]:
        styles[style_name].font.name = "Arial"
        styles[style_name].font.size = Pt(size)
        styles[style_name].font.bold = True

    for item in parse_markdown_lines(markdown_text):
        kind = item[0]
        if kind == "line":
            line = item[1].rstrip()
            if not line:
                continue
            if line == "---":
                doc.add_page_break()
            elif line.startswith("# "):
                doc.add_heading(clean_inline_markdown(line[2:]), level=1)
            elif line.startswith("## "):
                doc.add_heading(clean_inline_markdown(line[3:]), level=2)
            elif line.startswith("### "):
                doc.add_heading(clean_inline_markdown(line[4:]), level=3)
            elif line.startswith("- "):
                add_docx_text(doc, line[2:], "List Bullet")
            elif re.match(r"^\d+\.\s", line):
                add_docx_text(doc, re.sub(r"^\d+\.\s", "", line), "List Number")
            elif line.startswith("> "):
                add_docx_text(doc, line[2:], "Intense Quote")
            else:
                add_docx_text(doc, line)
        elif kind == "code":
            _, lang, code = item
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(code)
            run.font.name = "Courier New"
            run.font.size = Pt(7.5 if len(code.splitlines()) > 80 else 8.5)
        elif kind == "table":
            _, header, rows = item
            table = doc.add_table(rows=1, cols=len(header))
            table.style = "Table Grid"
            for idx, cell in enumerate(header):
                table.rows[0].cells[idx].text = clean_inline_markdown(cell)
            for row in rows:
                cells = table.add_row().cells
                for idx, cell in enumerate(row[: len(header)]):
                    cells[idx].text = clean_inline_markdown(cell)
            doc.add_paragraph()

    doc.save(DOCX_OUT)


def register_fonts():
    arial = Path(r"C:\Windows\Fonts\arial.ttf")
    arial_bold = Path(r"C:\Windows\Fonts\arialbd.ttf")
    consolas = Path(r"C:\Windows\Fonts\consola.ttf")
    if arial.exists():
        pdfmetrics.registerFont(TTFont("Arial", str(arial)))
    if arial_bold.exists():
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(arial_bold)))
    if consolas.exists():
        pdfmetrics.registerFont(TTFont("Consolas", str(consolas)))


def create_pdf(markdown_text: str):
    register_fonts()
    styles = getSampleStyleSheet()
    base_font = "Arial" if "Arial" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    bold_font = "Arial-Bold" if "Arial-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    code_font = "Consolas" if "Consolas" in pdfmetrics.getRegisteredFontNames() else base_font

    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName=base_font, fontSize=9, leading=12, spaceAfter=6)
    title = ParagraphStyle("Title", parent=body, fontName=bold_font, fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=14)
    h1 = ParagraphStyle("H1", parent=body, fontName=bold_font, fontSize=15, leading=18, spaceBefore=10, spaceAfter=8, textColor=colors.HexColor("#1f4e79"))
    h2 = ParagraphStyle("H2", parent=body, fontName=bold_font, fontSize=12, leading=15, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#244062"))
    h3 = ParagraphStyle("H3", parent=body, fontName=bold_font, fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=4)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, bulletIndent=3)
    code_style = ParagraphStyle("Code", parent=body, fontName=code_font, fontSize=6.2, leading=7.4, leftIndent=6, rightIndent=4)

    story = []
    first_heading = True
    for item in parse_markdown_lines(markdown_text):
        kind = item[0]
        if kind == "line":
            line = item[1].rstrip()
            if not line:
                continue
            if line == "---":
                story.append(PageBreak())
            elif line.startswith("# "):
                text = html.escape(clean_inline_markdown(line[2:]))
                story.append(Paragraph(text, title if first_heading else h1))
                first_heading = False
            elif line.startswith("## "):
                story.append(Paragraph(html.escape(clean_inline_markdown(line[3:])), h2))
            elif line.startswith("### "):
                story.append(Paragraph(html.escape(clean_inline_markdown(line[4:])), h3))
            elif line.startswith("- "):
                story.append(Paragraph(html.escape(clean_inline_markdown(line[2:])), bullet, bulletText="•"))
            elif re.match(r"^\d+\.\s", line):
                story.append(Paragraph(html.escape(clean_inline_markdown(line)), body))
            elif line.startswith("> "):
                story.append(Paragraph(html.escape(clean_inline_markdown(line[2:])), body))
            else:
                story.append(Paragraph(html.escape(clean_inline_markdown(line)), body))
        elif kind == "code":
            _, lang, code = item
            story.append(Preformatted(code, code_style, maxLineLength=110))
            story.append(Spacer(1, 0.15 * cm))
        elif kind == "table":
            _, header, rows = item
            data = [[Paragraph(html.escape(clean_inline_markdown(c)), body) for c in header]]
            for row in rows:
                data.append([Paragraph(html.escape(clean_inline_markdown(c)), body) for c in row])
            table = Table(data, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9eaf7")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                        ("FONTNAME", (0, 0), (-1, 0), bold_font),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9eabb8")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 0.2 * cm))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(base_font, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 1.5 * cm, 0.9 * cm, f"Sayfa {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.25 * cm,
        bottomMargin=1.25 * cm,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    complete = build_complete_markdown()
    COMPLETE_MD.write_text(complete, encoding="utf-8")
    create_docx(complete)
    create_pdf(complete)
    print(f"Wrote {COMPLETE_MD}")
    print(f"Wrote {DOCX_OUT}")
    print(f"Wrote {PDF_OUT}")


if __name__ == "__main__":
    main()
