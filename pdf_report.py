from io import BytesIO
import os
from typing import Dict, Any, List

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader


# =========================
# BRAND
# =========================
BRAND_GRAPHITE = colors.HexColor("#292b2d")
BRAND_CREAM = colors.HexColor("#f6f5ea")
BRAND_TEAL = colors.HexColor("#024a68")
BORDER = colors.HexColor("#D6D3C8")
GREY_200 = colors.HexColor("#E5E7EB")

LOGO_PATH = os.path.join("assets", "shift_logo.png")


# =========================
# Helpers
# =========================
def _safe(v, default="—"):
    if v is None or v == "":
        return default
    return str(v)

def _priority(score: int):
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"

def _loss_range(score: int):
    if score <= 3:
        return "25-45%"
    if score <= 6:
        return "15-35%"
    return "8-20%"

def _card(rows, width, bg=colors.white, pad=14):
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]))
    return t


# =========================
# Header
# =========================
def _on_page(canvas, doc, logo_reader, font_bold):
    canvas.saveState()

    # background
    canvas.setFillColor(BRAND_CREAM)
    canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

    # top bar
    bar_h = 16 * mm
    canvas.setFillColor(BRAND_TEAL)
    canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

    if logo_reader:
        canvas.drawImage(
            logo_reader,
            doc.leftMargin,
            A4[1] - bar_h + 3 * mm,
            width=38 * mm,
            height=10 * mm,
            mask='auto'
        )

    canvas.setFillColor(BRAND_GRAPHITE)
    canvas.setFont(font_bold, 9)
    canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"page {canvas.getPageNumber()}")

    canvas.restoreState()


# =========================
# MAIN
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):

    buffer = BytesIO()
    base_path = os.getcwd()

    # fonts
    reg = os.path.join(base_path, "fonts", "Jost-Regular.ttf")
    bold = os.path.join(base_path, "fonts", "Jost-Bold.ttf")

    if os.path.exists(reg) and os.path.exists(bold):
        pdfmetrics.registerFont(TTFont("Jost-Regular", reg))
        pdfmetrics.registerFont(TTFont("Jost-Bold", bold))
        FONT_REG = "Jost-Regular"
        FONT_BOLD = "Jost-Bold"
    else:
        FONT_REG = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"

    logo_reader = None
    logo_abs = os.path.join(base_path, LOGO_PATH)
    if os.path.exists(logo_abs):
        logo_reader = ImageReader(logo_abs)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=BRAND_GRAPHITE,
    )

    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=15,
        leading=20,
        textColor=BRAND_GRAPHITE,
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=11.5,
        leading=17,
        textColor=BRAND_GRAPHITE,
    )

    cta_white = ParagraphStyle(
        "CTAWhite",
        parent=body,
        textColor=colors.white,
    )

    score = int(data.get("score", 0) or 0)
    loss = _loss_range(score)

    elements: List[Any] = []

    width = A4[0] - doc.leftMargin - doc.rightMargin

    # =========================
    # PAGE 1 - COVER
    # =========================
    elements.append(Paragraph("Marketing system audit", title))
    elements.append(Spacer(1, 12 * mm))

    elements.append(Paragraph(f"<b>{score}/10</b>", h2))
    elements.append(Paragraph(f"Estimated loss: <b>{loss}</b> potential inquiries.", body))
    elements.append(Spacer(1, 12 * mm))

    elements.append(_card(
        [[Paragraph(
            "Current growth is not fully controlled. "
            "We see structural gaps between offer, positioning and lead conversion.",
            body
        )]],
        width
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 2 - STRATEGIC GAP
    # =========================
    elements.append(Paragraph("Strategic gap", title))
    elements.append(Spacer(1, 8 * mm))

    bullets = [
        "Offer is not clearly structured.",
        "Lead path is not engineered.",
        "Traffic sources are not diversified.",
        "Conversion logic is not measurable."
    ]

    elements.append(_card(
        [[Paragraph("<br/>".join([f"- {b}" for b in bullets]), body)]],
        width
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 3 - 30 DAY PLAN
    # =========================
    elements.append(Paragraph("30 day transformation model", title))
    elements.append(Spacer(1, 10 * mm))

    plan = [
        "Define core offer and value structure.",
        "Build conversion scenario (content to action).",
        "Launch 2 stable lead sources.",
        "Implement performance tracking."
    ]

    elements.append(_card(
        [[Paragraph("<br/>".join([f"- {p}" for p in plan]), body)]],
        width
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 4 - ABOUT
    # =========================
    elements.append(Paragraph("Shift Motion", title))
    elements.append(Spacer(1, 8 * mm))

    elements.append(_card(
        [[Paragraph(
            "We design controlled marketing systems. "
            "Strategy, structure, execution, measurable growth.",
            body
        )]],
        width
    ))

    elements.append(Spacer(1, 10 * mm))

    elements.append(_card(
        [[Paragraph(
            "30 minute executive session. "
            "You receive clear priorities and implementation map.",
            cta_white
        )]],
        width,
        bg=BRAND_TEAL
    ))

    def onpage(canvas, doc):
        _on_page(canvas, doc, logo_reader, FONT_BOLD)

    doc.build(elements, onFirstPage=onpage, onLaterPages=onpage)

    buffer.seek(0)
    return buffer