"""Build review DOCX files with the bundled Codex document runtime."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def text_runs(paragraph, value: str) -> None:
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", value):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
        else:
            paragraph.add_run(part)


def add_footer(section, label: str) -> None:
    footer = section.footer.paragraphs[0]
    footer.clear()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(f"{label}   ·   ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)


def make_document(source: Path, target: Path, *, paper: bool) -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_height, section.page_width = Inches(11.69), Inches(8.27)
    section.top_margin = Inches(.75 if paper else .85)
    section.bottom_margin = Inches(.7)
    section.left_margin = Inches(.72 if paper else .9)
    section.right_margin = Inches(.72 if paper else .9)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10 if paper else 10.5)
    normal.paragraph_format.space_after = Pt(5 if paper else 7)
    normal.paragraph_format.line_spacing = 1.1 if paper else 1.18
    for name, size in (("Title", 19 if paper else 24), ("Heading 1", 11 if paper else 15),
                       ("Heading 2", 10 if paper else 12), ("Heading 3", 9 if paper else 11)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(5)
    add_footer(section, "STAT3013 review draft")

    lines = source.read_text(encoding="utf-8").splitlines()
    in_columns = False
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if not line:
            continue
        if line.startswith("# "):
            p = doc.add_paragraph(style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            text_runs(p, line[2:])
            continue
        if line.startswith("## "):
            heading = line[3:]
            if paper and heading.startswith("VII "):
                figures = [
                    (ROOT / "ai/evaluation/figures/model_pr_roc.png", "Fig. 1. Held-out PR and ROC curves, E-07."),
                    (ROOT / "ai/evaluation/figures/model_calibration.png", "Fig. 2. Held-out calibration, E-07."),
                    (ROOT / "research/regression/results/ols_residuals.png", "Fig. 3. OLS diagnostics, E-05."),
                ]
                for path, caption in figures:
                    if not path.exists():
                        continue
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run().add_picture(str(path), width=Inches(3.05))
                    c = doc.add_paragraph(caption)
                    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    c.paragraph_format.keep_with_next = False
                    for run in c.runs:
                        run.font.size = Pt(8)
            if paper and not in_columns and heading.startswith("I "):
                next_section = doc.add_section(WD_SECTION_START.CONTINUOUS)
                next_section.top_margin = section.top_margin
                next_section.bottom_margin = section.bottom_margin
                next_section.left_margin = section.left_margin
                next_section.right_margin = section.right_margin
                cols = next_section._sectPr.xpath("./w:cols")[0]
                cols.set(qn("w:num"), "2")
                cols.set(qn("w:space"), "360")
                next_section.footer.is_linked_to_previous = False
                add_footer(next_section, "STAT3013 review draft")
                in_columns = True
            doc.add_heading(heading, 1)
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:], 2)
            continue
        if line.startswith("| "):
            cells = [part.strip() for part in line.strip("|").split("|")]
            rows = [cells]
            while index < len(lines) and lines[index].strip().startswith("|"):
                candidate = [part.strip() for part in lines[index].strip().strip("|").split("|")]
                index += 1
                if all(set(part) <= {"-", ":", " "} for part in candidate):
                    continue
                rows.append(candidate)
            table = doc.add_table(rows=0, cols=len(cells))
            table.style = "Table Grid"
            table.autofit = True
            for row_number, values in enumerate(rows):
                row = table.add_row()
                for col, value in enumerate(values):
                    cell = row.cells[col]
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    if row_number == 0:
                        shade(cell, "DCEAF0")
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(2)
                    text_runs(p, value)
                    for run in p.runs:
                        run.font.size = Pt(7.5 if paper else 8.5)
                        if row_number == 0:
                            run.bold = True
            doc.add_paragraph("")
            continue
        if line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            text_runs(p, line[2:])
            continue
        p = doc.add_paragraph()
        text_runs(p, line)

    if not paper:
        doc.add_heading("Figures from the reproducible run", 1)
        figures = [
            (ROOT / "ai/evaluation/figures/model_pr_roc.png", "Held-out precision-recall and ROC curves, E-07"),
            (ROOT / "ai/evaluation/figures/model_calibration.png", "Held-out calibration, E-07"),
            (ROOT / "data/processed/forecasting/forecast.png", "Mature weekly rate and short naive forecast, E-06"),
            (ROOT / "research/regression/results/ols_residuals.png", "OLS residual and Q-Q diagnostics, E-05"),
        ]
        for path, caption in figures:
            if not path.exists():
                continue
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(path), width=Inches(5.9))
            c = doc.add_paragraph(caption)
            c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            c.paragraph_format.keep_with_next = False

    target.parent.mkdir(parents=True, exist_ok=True)
    doc.save(target)
    print(target)


if __name__ == "__main__":
    make_document(ROOT / "reports/full-report/defense_manuscript.md",
                  ROOT / "reports/full-report/defense_report_draft.docx", paper=False)
    make_document(ROOT / "reports/ieee-paper/paper_draft.md",
                  ROOT / "reports/ieee-paper/paper_draft.docx", paper=True)
