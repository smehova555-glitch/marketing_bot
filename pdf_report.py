from io import BytesIO
import os
from typing import Dict, Any, List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
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
    return default if not v else str(v)

def _loss_range(score: int) -> str:
    if score <= 3:
        return "25–45%"
    if score <= 6:
        return "15–35%"
    return "8–20%"


# =========================
# HEADER
# =========================
def _make_onpage(logo_reader, font_bold):
    def _on_page(canvas, doc):
        canvas.saveState()

        # фон
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

        # верхняя полоса
        bar_h = 18 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

        # лого
        if logo_reader:
            img_w, img_h = logo_reader.getSize()
            ratio = img_w / img_h if img_h else 3
            h = 10 * mm
            w = h * ratio

            canvas.drawImage(
                logo_reader,
                doc.leftMargin,
                A4[1] - bar_h + (bar_h - h) / 2,
                width=w,
                height=h,
                preserveAspectRatio=True,
                mask="auto"
            )

        canvas.restoreState()
    return _on_page


# =========================
# MAIN
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):

    buffer = BytesIO()
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Fonts
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

    # Logo
    logo_abs = os.path.join(base_path, LOGO_PATH)
    logo_reader = ImageReader(logo_abs) if os.path.exists(logo_abs) else None

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=32 * mm,
        bottomMargin=20 * mm,
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

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=13,     # 🔥 крупнее
        leading=19,
        textColor=BRAND_GRAPHITE,
        wordWrap="CJK",
    )

    muted = ParagraphStyle(
        "Muted",
        parent=body,
        fontSize=12,
        textColor=colors.HexColor("#5B5F62"),
    )

    elements: List[Any] = []

    # ===== DATA =====
    score = int(data.get("score", 0) or 0)
    loss = _loss_range(score)

    city = _safe(data.get("city"))
    niche = _safe(data.get("niche"))
    budget = _safe(data.get("budget"))
    source = _safe(data.get("source"))
    stability = _safe(data.get("stability"))
    geo = _safe(data.get("geo"))

    width = A4[0] - doc.leftMargin - doc.rightMargin

    # ===== TITLE =====
    elements.append(Paragraph("Маркетинговая диагностика", title))
    elements.append(Spacer(1, 10 * mm))

    # ===== RESULT BLOCK =====
    elements.append(Paragraph(f"<b>{score}/10</b> — потенциал роста не реализован полностью.", body))
    elements.append(Paragraph(f"Оценка потерь: <b>{loss}</b> обращений.", body))
    elements.append(Spacer(1, 8 * mm))

    # ===== META (компактно, 2 колонки) =====
    meta_rows = [
        ["Город", city],
        ["Ниша", niche],
        ["Бюджет", budget],
        ["Источник", source],
        ["Стабильность", stability],
        ["Гео", geo],
    ]

    table_data = []
    for k, v in meta_rows:
        table_data.append([
            Paragraph(f"<b>{k}</b>", muted),
            Paragraph(v, body)
        ])

    meta = Table(table_data, colWidths=[35 * mm, width - 35 * mm])
    meta.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(meta)
    elements.append(Spacer(1, 12 * mm))

    # ===== RECOMMENDATION (компактно) =====
    recommendation = (
        "Рекомендуем: выстроить управляемую систему привлечения "
        "с чётким учётом обращений, регулярным контролем метрик "
        "и 1–2 стабильными каналами трафика."
    )

    elements.append(Paragraph(recommendation, body))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(
        "Следующий шаг: 30-минутная стратегическая сессия и план действий на 14 дней.",
        body
    ))

    onpage = _make_onpage(logo_reader, FONT_BOLD)
    doc.build(elements, onFirstPage=onpage)

    buffer.seek(0)
    return buffer