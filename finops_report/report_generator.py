# finops_report/report_generator.py
import os
from datetime import datetime
from typing import Any, Dict, Tuple

from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def _register_fonts():
    """Register Arial on Windows for PDF text rendering."""
    for name, path in [
        ("Arial", os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf")),
        ("ArialBold", os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf")),
    ]:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:
                pass

_register_fonts()


def _build_pdf(analysis: Dict[str, Any], output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BodyCustom", fontName="Arial", fontSize=10, leading=14))
    styles.add(ParagraphStyle(name="CustomHeading1", fontName="ArialBold", fontSize=18, leading=22, textColor=colors.HexColor("#1a1a2e")))
    styles.add(ParagraphStyle(name="CustomHeading2", fontName="ArialBold", fontSize=13, leading=18, textColor=colors.HexColor("#16213e")))
    story = []

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles["Heading1"]))
    summary = analysis.get("executive_summary", "No summary available.")
    story.append(Paragraph(summary, styles["BodyCustom"]))
    story.append(Spacer(1, 0.25*inch))

    # Cost Drivers
    story.append(Paragraph("Top Cost Drivers", styles["Heading2"]))
    drivers = analysis.get("cost_drivers", [])
    for d in drivers[:5]:
        name = d.get("name", d.get("description", "Unknown"))
        amount = d.get("amount", "?")
        story.append(Paragraph(f"<b>{name}</b> — ${amount:,.2f}/mo" if isinstance(amount, (int, float)) else f"<b>{name}</b>", styles["BodyCustom"]))
    story.append(Spacer(1, 0.25*inch))

    # Recommendations
    story.append(Paragraph("Recommendations", styles["Heading2"]))
    recs = sorted(analysis.get("recommendations", []), key=lambda r: r.get("priority", 99))
    for r in recs:
        title = r.get("title", "Recommendation")
        desc = r.get("description", "")
        savings = r.get("estimated_monthly_savings", 0)
        risk = r.get("risk_level", "?").upper()
        story.append(Paragraph(f"<b>{title}</b> (${savings:,.0f}/mo) [{risk}]", styles["BodyCustom"]))
        story.append(Paragraph(f"&nbsp;&nbsp;{desc}", styles["BodyCustom"]))
    story.append(PageBreak())

    # Terraform Snippets
    story.append(Paragraph("Implementation Snippets", styles["Heading2"]))
    snippets = analysis.get("tf_snippets", [])
    if snippets:
        for s in snippets[:3]:
            code = s.get("code", s) if isinstance(s, dict) else str(s)
            story.append(Paragraph("<b>Terraform</b>", styles["BodyCustom"]))
            story.append(Paragraph(f"<pre>{code}</pre>", styles["BodyCustom"]))
            story.append(Spacer(1, 0.15*inch))
    else:
        story.append(Paragraph("No Terraform snippets available.", styles["BodyCustom"]))

    doc.build(story)


def generate_report(
    analysis: Dict[str, Any],
    raw_data: Dict[str, Any],
    output_dir: str,
) -> Tuple[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    base = f"FinOps_Report_{date_str}"
    pdf_path = os.path.join(output_dir, f"{base}.pdf")
    html_path = os.path.join(output_dir, f"{base}.html")

    _build_pdf(analysis, pdf_path)

    # Also write a simple HTML version
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    tpl = env.get_template("report.html.j2")
    html = tpl.render(
        analysis=analysis,
        raw_data=raw_data,
        date=date_str,
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    return pdf_path, html_path