"""Build the English STAT3013 full report with UIT-style page geometry.

Run with Codex's bundled Python, which contains python-docx and Pillow. Source
results remain in the repo; raw visitor records are never inserted here.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/full-report/GhostCustomer_Full_Report_EN.md"
TARGET = ROOT / "reports/full-report/GhostCustomer_STAT3013_Full_Report_EN.docx"
FIGURES = ROOT / "reports/full-report/figures"
AI_FIGURES = ROOT / "ai/evaluation/figures"
REGRESSION = ROOT / "research/regression/results"


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


STAT = read_json("research/statistics/results.json")
AUDIT = read_json("research/statistics/inference_audit.json")
OLS = read_json("research/regression/results/ols_results.json")
LOGIT = read_json("research/regression/results/logit_results.json")
FORECAST = read_json("research/forecasting/analysis_manifest.json")
ML = read_json("ai/evaluation/metrics.json")
TREE = read_json("research/baselines/decision_tree_results.json")
NB = read_json("research/baselines/gaussian_nb_results.json")

FIGURE_MAP = {
    "study_design": (FIGURES / "study_design.png", "Proposed four plus two plus two week design and the score time T, E-02."),
    "cohort_status": (FIGURES / "cohort_status.png", "History-eligible snapshots by operational status; rows are not distinct people, E-02."),
    "visitor_recency": (FIGURES / "visitor_recency.png", "Pre-T recency among selected mature Ghost and Active visitors, E-04."),
    "ols_residuals": (REGRESSION / "ols_residuals.png", "Held-out OLS residual and normal Q-Q diagnostics, E-05."),
    "logit_roc_pr": (REGRESSION / "logit_roc_pr.png", "Ghost-versus-rest logistic discrimination on its later test set, E-05."),
    "weekly_forecast": (FIGURES / "weekly_forecast.png", "Twelve mature weekly rates and a two-week naive continuation, E-06."),
    "benchmark_pr_auc": (FIGURES / "benchmark_pr_auc.png", "Shared-test precision-recall comparison; 430 Ghost/Active rows, E-07 and E-11."),
    "model_pr_roc": (AI_FIGURES / "model_pr_roc.png", "Held-out precision-recall and ROC curves for primary candidates, E-07."),
    "model_confusion_matrix": (AI_FIGURES / "model_confusion_matrix.png", "Selected XGBoost plus Platt confusion matrix at the validation cost threshold, E-07."),
    "model_calibration": (AI_FIGURES / "model_calibration.png", "Held-out calibration diagnostic for the selected model, E-07."),
    "ablation_pr_auc": (FIGURES / "ablation_pr_auc.png", "Full, named-component and observation-only feature sensitivity, E-07."),
    "importance": (AI_FIGURES / "shap_or_permutation_importance.png", "Global feature attribution; descriptive, not causal, E-07."),
    "architecture": (FIGURES / "architecture.png", "Research data, model, API and web interface flow, E-08 and E-10."),
    "dashboard_real": (FIGURES / "dashboard_real.png", "Real-data overview on the local demonstration machine, E-10."),
}


def fmt(value: object, places: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{float(value):,.{places}f}"


def set_cell_fill(cell, fill: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    shd = tcpr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcpr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    borders = tcpr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcpr.append(borders)
    for side in ("top", "left", "bottom", "right"):
        el = borders.find(qn(f"w:{side}"))
        if el is None:
            el = OxmlElement(f"w:{side}")
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D9D9D9")


def set_cell_padding(cell) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    mar = tcpr.find(qn("w:tcMar"))
    if mar is None:
        mar = OxmlElement("w:tcMar")
        tcpr.append(mar)
    for side, amount in (("top", 80), ("bottom", 80), ("left", 100), ("right", 100)):
        el = mar.find(qn(f"w:{side}"))
        if el is None:
            el = OxmlElement(f"w:{side}")
            mar.append(el)
        el.set(qn("w:w"), str(amount))
        el.set(qn("w:type"), "dxa")


def repeat_header(row) -> None:
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def keep_row_together(row) -> None:
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def add_field(paragraph, instruction: str) -> None:
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    code = OxmlElement("w:instrText")
    code.set(qn("xml:space"), "preserve")
    code.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for el in (begin, code, separate, end):
        run = OxmlElement("w:r")
        run.append(el)
        paragraph._p.append(run)


def add_runs(paragraph, value: str) -> None:
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", value):
        if not part:
            continue
        if part.startswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`"):
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def configure(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(1.18)
    section.right_margin = Inches(.79)
    section.top_margin = Inches(.87)
    section.bottom_margin = Inches(.87)
    section.different_first_page_header_footer = True
    for holder in (section.header, section.first_page_header, section.footer, section.first_page_footer):
        for paragraph in holder.paragraphs:
            paragraph.clear()
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header.add_run("STAT3013  |  GHOST CUSTOMER  |  2026").font.size = Pt(9)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(footer, "PAGE")

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    force_times_new_roman(normal)
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25
    for name, size in (("Title", 18), ("Heading 1", 15), ("Heading 2", 12)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        force_times_new_roman(style)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.keep_with_next = True
    sectpr = section._sectPr
    old = sectpr.find(qn("w:pgBorders"))
    if old is not None:
        sectpr.remove(old)
    borders = OxmlElement("w:pgBorders")
    borders.set(qn("w:display"), "firstPage")
    borders.set(qn("w:offsetFrom"), "page")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "double")
        el.set(qn("w:sz"), "12")
        el.set(qn("w:space"), "18")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    sectpr.append(borders)
    settings = doc.settings._element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def force_times_new_roman(style) -> None:
    rpr = style._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attribute in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn(f"w:{attribute}"), None)
    for attribute in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{attribute}"), "Times New Roman")


def cover_line(doc: Document, text: str, size: float, after: float, bold: bool = True) -> None:
    p = doc.add_paragraph(style="Normal")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)


def front_matter(doc: Document) -> None:
    cover_line(doc, "VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY", 12, 2)
    cover_line(doc, "UNIVERSITY OF INFORMATION TECHNOLOGY", 12, 55)
    cover_line(doc, "STAT3013  |  STATISTICAL ANALYSIS", 12, 26)
    cover_line(doc, "FULL COURSE PROJECT REPORT", 13, 12)
    title = doc.add_paragraph(style="Normal")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(12)
    title_run = title.add_run("GHOST CUSTOMER PREDICTION")
    title_run.bold = True
    title_run.font.size = Pt(18)
    cover_line(doc, "Early Detection of Silent Customer Disengagement in E Commerce Using Statistics and Machine Learning", 13, 35)
    cover_line(doc, "PROJECT TEAM", 11, 10)
    for name, role in (
        ("Hà Nguyễn Việt Thành", "Team lead, frontend, Decision Tree and integration"),
        ("Cao Phan Lâm", "Data engineering, cohort audit and Gaussian Naive Bayes"),
        ("Đặng Hoàng Long", "Backend, regression and forecasting"),
        ("Trần Quốc Kiệt", "Machine learning, evaluation and inference"),
    ):
        cover_line(doc, f"{name}  |  {role}", 10.5, 4, False)
    cover_line(doc, "HO CHI MINH CITY, 2026", 11, 0)
    doc.add_page_break()

    doc.add_heading("Abstract", 1)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    begin = lines.index("## Abstract") + 1
    end = lines.index("## 1 Introduction")
    for line in lines[begin:end]:
        if line.strip():
            p = doc.add_paragraph(style="Normal")
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs(p, line)
    doc.add_page_break()

    doc.add_heading("Contents", 1)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-2" \\h \\z \\u')
    doc.add_page_break()
    doc.add_heading("List of figures and tables", 1)
    for index, (_, caption) in enumerate(FIGURE_MAP.values(), 1):
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(2)
        p.add_run(f"Figure {index}. {caption}")
    table_captions = (
        "Source event fields and analytical use",
        "Operational status counts",
        "Window sensitivity in the audit cohort",
        "Threshold and session-gap sensitivity",
        "Descriptive measures: Active",
        "Descriptive measures: Ghost",
        "Descriptive measures: Inactive",
        "Descriptive measures: Recovered",
        "Independent visitor-level recency contrast",
        "Multiple OLS coefficients",
        "OLS fit and later test behavior",
        "Logistic odds ratios",
        "Logistic test support and threshold behavior",
        "Naive rate forecast",
        "Purged visitor-disjoint ML split",
        "Shared Ghost/Active test metrics",
        "XGBoost feature-set sensitivity",
        "Research API demonstrated locally",
        "Local software verification",
        "Evidence register summary",
        "Documented team contributions",
    )
    for index, caption in enumerate(table_captions, 1):
        p = doc.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(2)
        p.add_run(f"Table {index}. {caption}")
    doc.add_page_break()


TABLE_NO = 0
FIGURE_NO = 0


def add_table(doc: Document, caption: str, headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    global TABLE_NO
    TABLE_NO += 1
    cp = doc.add_paragraph(style="Normal")
    cp.paragraph_format.keep_with_next = True
    cp.paragraph_format.space_before = Pt(7)
    cp.paragraph_format.space_after = Pt(4)
    cp.add_run(f"Table {TABLE_NO}. {caption}").italic = True
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    if widths:
        for i, width in enumerate(widths):
            table.columns[i].width = Inches(width)
    for i, value in enumerate(headers):
        table.rows[0].cells[i].text = str(value)
    repeat_header(table.rows[0])
    for values in rows:
        row = table.add_row()
        for cell, value in zip(row.cells, values):
            cell.text = str(value)
    for ri, row in enumerate(table.rows):
        keep_row_together(row)
        for ci, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            set_cell_padding(cell)
            if widths:
                cell.width = Inches(widths[ci])
            if ri == 0:
                set_cell_fill(cell, "183C52")
            elif ri % 2 == 0:
                set_cell_fill(cell, "F0F5F7")
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.1
                if ri == 0:
                    p.paragraph_format.keep_with_next = True
                if ci > 1 and len(headers) > 3:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(8.5 if len(headers) > 5 else 9)
                    run.font.color.rgb = RGBColor(255, 255, 255) if ri == 0 else RGBColor(0, 0, 0)
                    if ri == 0:
                        run.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_figure(doc: Document, key: str) -> None:
    global FIGURE_NO
    path, caption = FIGURE_MAP[key]
    if not path.exists():
        raise FileNotFoundError(path)
    FIGURE_NO += 1
    with Image.open(path) as im:
        width, height = im.size
    max_width, max_height = 6.05, 3.75
    physical_width = min(max_width, max_height * width / height)
    p = doc.add_paragraph(style="Normal")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Inches(physical_width))
    c = doc.add_paragraph(style="Normal")
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(9)
    r = c.add_run(f"Figure {FIGURE_NO}. {caption}")
    r.italic = True
    r.font.size = Pt(9)


def add_named_tables(doc: Document, key: str) -> None:
    if key == "source_fields":
        add_table(doc, "Source event fields and analytical use, E-01", ["Field", "Meaning", "Use"], [
            ["timestamp", "Milliseconds since epoch", "UTC event time and session ordering"],
            ["visitorid", "Anonymous visitor identifier", "Longitudinal grouping; never a model feature"],
            ["event", "View, add-to-cart or transaction", "Behavioral counts"],
            ["itemid", "Item identifier", "Distinct-item feature"],
            ["transactionid", "Transaction identifier when present", "Purchase-event audit"],
        ], [1.15, 2.15, 3.0])
    elif key == "cohort_status":
        add_table(doc, "Operational status counts in the history-eligible cohort, E-02", ["Status", "Snapshots", "Maturity / interpretation"], [
            ["Inactive", "71,301", "Mature; no confirmation events"],
            ["Active", "9,263", "Mature; rule does not mark decline"],
            ["Recovered", "2,716", "Mature; improvement after observation decline"],
            ["Ghost", "2,619", "Mature; nonzero future activity below the ratio threshold"],
            ["Unknown", "11,590", "Right-censored or otherwise immature; null target"],
        ], [1.3, 1.1, 3.9])
    elif key == "sensitivity":
        add_table(doc, "Window sensitivity in the audit cohort, E-02", ["B+O+C weeks", "History-eligible", "Censored", "Reading"], [
            ["4+2+2", "97,489", "11,590", "Main proposed scenario"],
            ["4+3+2", "100,140", "13,511", "Longer observation"],
            ["6+2+4", "128,323", "40,043", "Longer confirmation loses mature outcomes"],
        ], [1.1, 1.25, 1.1, 2.85])
        add_table(doc, "Threshold and inferred-session-gap sensitivity, E-02", ["Parameter", "Setting", "Ghost snapshots"], [
            ["Ratio threshold", "0.5 / 0.4 / 0.3", "2,619 / 1,740 / 1,188"],
            ["Session gap", "15 / 30 / 60 minutes", "2,998 / 2,619 / 2,310"],
        ], [1.6, 2.15, 2.55])
    elif key == "descriptive":
        names = {"feature_sessions_4w": "Sessions 4w", "feature_views_4w": "Views 4w",
                 "feature_carts_4w": "Carts 4w", "feature_purchases_4w": "Purchases 4w",
                 "feature_active_days_4w": "Active days 4w", "feature_recency_days": "Recency days",
                 "feature_decay_ratio": "Decay ratio"}
        for group in ("active", "ghost", "inactive", "recovered"):
            rows = []
            for item in STAT["groups"]:
                if item["name"] != group:
                    continue
                rows.append([names.get(item["metric"], item["metric"]), fmt(item["n"], 0),
                             fmt(item["missing_n"], 0), fmt(item["mean"]), fmt(item["sd"]),
                             fmt(item["median"]), f"{fmt(item['q1'])}–{fmt(item['q3'])}"])
            add_table(doc, f"Descriptive pre-T measures for mature {group.title()} snapshots, E-03",
                      ["Feature", "N", "Missing", "Mean", "SD", "Median", "Q1–Q3"], rows,
                      [1.28, .64, .72, .76, .76, .78, 1.36])
    elif key == "inference":
        test = STAT["tests"][0]
        add_table(doc, "Independent visitor-level recency contrast, E-04", ["Quantity", "Result", "Scope"], [
            ["Ghost / Active visitors", "371 / 896", "One latest mature snapshot per visitor"],
            ["Mean recency", "16.54 / 5.14 days", "Ghost / Active"],
            ["Mean difference", "11.39 days", "Ghost minus Active"],
            ["Welch 95% CI", "[10.27, 12.51] days", "Two-sided mean difference"],
            ["Welch t; p-value", f"{fmt(test['statistic'], 2)}; 7.52 × 10⁻⁶³", "df approximately 414"],
            ["Cohen d", fmt(test["effect_size"], 2), "Standardized descriptive effect"],
        ], [1.65, 1.65, 3.0])
    elif key == "ols":
        coeff = OLS["models"]["multiple"]["coefficients"]
        add_table(doc, "Multiple OLS coefficients with clustered 95% intervals, E-05",
                  ["Term", "Estimate", "95% CI", "p-value"],
                  [[c["term"].replace("feature_", ""), fmt(c["coefficient"], 4),
                    f"[{fmt(c['ci_low'], 4)}, {fmt(c['ci_high'], 4)}]", f"{c['p_value']:.2g}"] for c in coeff],
                  [1.6, 1.0, 2.3, 1.4])
        add_table(doc, "OLS fit and later test behavior, E-05", ["Model", "Train R²", "Test RMSE", "Negative test predictions"], [
            ["Sessions-only", fmt(OLS["models"]["simple"]["r_squared"]), fmt(OLS["models"]["simple"]["test_rmse"]), "5,928"],
            ["Multiple", fmt(OLS["models"]["multiple"]["r_squared"]), fmt(OLS["models"]["multiple"]["test_rmse"]), "5,927"],
        ], [1.5, 1.1, 1.3, 2.4])
    elif key == "logit":
        add_table(doc, "Logistic odds ratios for Ghost versus other mature states, E-05",
                  ["Predictor", "Odds ratio", "95% CI", "p-value"],
                  [[c["term"], fmt(c["odds_ratio"]), f"[{fmt(c['or_ci_low'])}, {fmt(c['or_ci_high'])}]", f"{c['p_value']:.2g}"]
                   for c in LOGIT["coefficients"] if c["term"] != "const"],
                  [1.5, 1.2, 2.25, 1.35])
        t = LOGIT["test"]
        add_table(doc, "Logistic test support and threshold behavior, E-05", ["Metric", "Value", "Interpretation"], [
            ["Test / Ghost", f"{t['n']:,} / {t['positive_support']:,}", "Ghost versus all other mature labels"],
            ["PR-AUC / ROC-AUC", f"{t['pr_auc_average_precision']:.3f} / {t['roc_auc']:.3f}", "Prevalence 0.020"],
            ["Precision / recall", f"{t['precision']:.3f} / {t['recall']:.3f}", "Validation threshold 0.10"],
            ["TP / FP / FN", "18 / 76 / 298", "Most positives missed at this threshold"],
        ], [1.8, 1.6, 2.9])
    elif key == "forecast":
        m = FORECAST["test_metrics"]["selected"]
        add_table(doc, "Naive rate forecast from three historical origins, E-06", ["Mature weeks", "Origins", "MAE", "RMSE", "sMAPE"], [
            ["12", str(m["n"]), fmt(m["mae"], 5), fmt(m["rmse"], 5), f"{m['smape_percent']:.2f}%"],
        ], [1.3, 1.0, 1.25, 1.25, 1.5])
    elif key == "ml_split":
        add_table(doc, "Purged visitor-disjoint ML split, E-07", ["Partition", "Rows", "Ghost", "Purpose"], [
            ["Train", "2,214", "433", "Fit estimators and training-fold calibration"],
            ["Validation", "454", "119", "Select family and operating threshold"],
            ["Test", "430", "109", "Final later-visitor evaluation"],
        ], [1.2, 1.0, 1.0, 3.1])
    elif key == "models":
        select = {x["name"]: x for x in ML["comparison"] if x["name"] in
                  ("majority", "rule_eds", "logistic_regression", "random_forest", "xgboost+platt")}
        rows = [[name, fmt(select[key]["test_pr_auc"]), fmt(select[key]["test_roc_auc"]),
                 fmt(select[key].get("test_precision")), fmt(select[key].get("test_recall"))]
                for key, name in (("majority", "No-skill prior"), ("rule_eds", "EDS rule"),
                                  ("logistic_regression", "ML logistic"), ("random_forest", "Random Forest"),
                                  ("xgboost+platt", "XGBoost + Platt"))]
        rows += [["Decision Tree", fmt(TREE["test"]["pr_auc"]), fmt(TREE["test"]["roc_auc"]),
                  fmt(TREE["test"]["precision"]), fmt(TREE["test"]["recall"])],
                 ["Gaussian NB", fmt(NB["test"]["pr_auc"]), fmt(NB["test"]["roc_auc"]),
                  fmt(NB["test"]["precision"]), fmt(NB["test"]["recall"])]]
        add_table(doc, "Shared Ghost/Active test metrics (n=430; 109 Ghost), E-07 and E-11",
                  ["Candidate", "PR-AUC", "ROC-AUC", "Precision", "Recall"], rows,
                  [2.05, 1.0, 1.0, 1.1, 1.15])
    elif key == "ablation":
        add_table(doc, "XGBoost feature-set sensitivity on the same test, E-07",
                  ["Feature set", "Inputs", "Test PR-AUC", "Interpretation"], [
                      ["Full", "41", "0.928", "Baseline history included"],
                      ["No named target components", "overlapping history", "0.909", "Baseline reconstructable"],
                      ["Observation-only", "10", "0.607", "Baseline-period counts removed"],
                  ], [2.0, 1.15, 1.15, 2.0])
    elif key == "api":
        add_table(doc, "Real research API demonstrated locally, E-10", ["Route", "Purpose"], [
            ["GET /api/overview", "Cohort counts and source notice"],
            ["GET /api/customers", "Search, filter and page dated visitor snapshots"],
            ["GET /api/customers/{id}", "Dated detail and timeline; snapshot_date query"],
            ["GET /api/statistics", "Descriptive groups, inference and intervals"],
            ["GET /api/forecast", "Mature history and short naive continuation"],
            ["POST /api/predict", "Real model score for visitor ID and T"],
            ["GET /api/model/metrics", "Held-out support, curves, threshold and calibration"],
        ], [2.7, 3.6])
    elif key == "verification":
        add_table(doc, "Local software verification on 20 November 2026, E-10", ["Check", "Observed result"], [
            ["Python suite", "122 passed"],
            ["Frontend lint and production build", "Passed in real mode"],
            ["Detail-file structural checker", "97,489 passed; zero missing or invalid"],
            ["Real API smoke", "Seven routes; valid prediction; 404 and 422"],
            ["Browser walkthrough", "Desktop and mobile routes loaded without page errors"],
        ], [2.5, 3.8])
    elif key == "evidence":
        add_table(doc, "Evidence register summary", ["ID", "Research output", "Repository path"], [
            ["E-01/02", "Source, cohort and sensitivity", "data/config/pipeline.json; research/feasibility"],
            ["E-03/04", "Descriptive and visitor-level inference", "research/statistics"],
            ["E-05", "OLS and logistic regression", "research/regression/results"],
            ["E-06", "Mature weekly forecast", "research/forecasting"],
            ["E-07/11", "ML and Decision Tree comparison", "ai/evaluation; research/baselines"],
            ["E-08/10", "Inference and seven-route demo", "ai/inference; scripts/verify_real_demo.py"],
            ["E-09", "SEM lecturer decision", "Pending; docs/sem_feasibility.md"],
        ], [.8, 2.2, 3.3])
    elif key == "roles":
        add_table(doc, "Documented team contributions and current code ownership", ["Member", "Primary areas"], [
            ["Hà Nguyễn Việt Thành", "Team lead, frontend, Decision Tree, integration and reproducibility"],
            ["Cao Phan Lâm", "Data processing, cohort audit, descriptive data and Gaussian NB"],
            ["Đặng Hoàng Long", "Backend foundation, regression and weekly forecasting"],
            ["Trần Quốc Kiệt", "AI training, evaluation, calibration and inference runtime"],
        ], [2.1, 4.2])
    else:
        raise KeyError(key)


def body(doc: Document) -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    start = lines.index("## 1 Introduction")
    for raw in lines[start:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[[FIG:"):
            add_figure(doc, line[6:-2])
        elif line.startswith("[[TABLE:"):
            add_named_tables(doc, line[8:-2])
        elif line.startswith("## "):
            doc.add_heading(line[3:], 1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], 2)
        elif line.startswith("# "):
            continue
        else:
            p = doc.add_paragraph(style="Normal")
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Inches(.18)
            if line.startswith("[") and re.match(r"^\[\d+\]", line):
                p.paragraph_format.first_line_indent = Inches(-.2)
                p.paragraph_format.left_indent = Inches(.2)
            add_runs(p, line)


def main() -> None:
    doc = Document()
    configure(doc)
    front_matter(doc)
    body(doc)
    doc.core_properties.title = "Ghost Customer Prediction Full Course Project Report"
    doc.core_properties.subject = "STAT3013 Statistical Analysis, University of Information Technology"
    doc.core_properties.author = "Ghost Customer project team"
    doc.save(TARGET)
    print(f"{TARGET}\n{FIGURE_NO} figures; {TABLE_NO} tables")


if __name__ == "__main__":
    main()
