from io import BytesIO
import os
from typing import Dict, Any

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

LOGO_PATH = os.path.join("assets", "shift_logo.png")


# =========================
# Helpers
# =========================
def _loss_range(score: int) -> str:
    if score <= 3:
        return "25–45%"
    if score <= 6:
        return "15–35%"
    return "8–20%"


def _progress_bar(score: int, width=160*mm, height=7*mm):
    score = max(0, min(10, score))
    fill = width * (score / 10)
    empty = width - fill

    t = Table([["", ""]], colWidths=[fill, empty], rowHeights=[height])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BRAND_TEAL),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# =========================
# Header
# =========================
def _make_onpage(logo_reader, font_bold: str):
    def _on_page(canvas, doc):
        canvas.saveState()

        # фон
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

        # верхняя полоса
        bar_h = 20 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

        # увеличенный логотип
        if logo_reader:
            canvas.drawImage(
                logo_reader,
                doc.leftMargin,
                A4[1] - bar_h + 3 * mm,
                height=14 * mm,
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
    logo_reader = None
    if os.path.exists(logo_abs):
        logo_reader = ImageReader(logo_abs)

    # Doc
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=30 * mm,
        bottomMargin=22 * mm,
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=21,
        leading=25,
        textColor=BRAND_GRAPHITE,
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=13,
        leading=18,
        textColor=BRAND_GRAPHITE,
    )

    strong = ParagraphStyle(
        "Strong",
        parent=body,
        fontName=FONT_BOLD,
    )

    score = int(data.get("score", 0))
    loss = _loss_range(score)

    elements = []

    # Заголовок
    elements.append(Paragraph(
        "Маркетинговая диагностика от коммуникационного агентства Shift Motion",
        title
    ))
    elements.append(Spacer(1, 10 * mm))

    # Оценка
    elements.append(Paragraph(f"<b>{score}/10</b> — текущий уровень управляемости маркетинга.", strong))
    elements.append(Paragraph(f"Потенциальные потери: {loss} обращений из-за системных разрывов.", body))
    elements.append(Spacer(1, 6 * mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 12 * mm))

    # Интерпретация (универсально)
    elements.append(Paragraph(
        "Что это означает:",
        strong
    ))
    elements.append(Spacer(1, 4 * mm))

    interpretation = """
    • Маркетинг работает частично, но не как управляемая система.<br/>
    • Заявки возникают, однако не масштабируются предсказуемо.<br/>
    • Отсутствует единая связка: источник → обработка → повторное касание.<br/>
    • Часть бюджета или усилий не конвертируется в стабильный рост.
    """

    elements.append(Paragraph(interpretation, body))
    elements.append(Spacer(1, 10 * mm))

    # Блок роста
    elements.append(Paragraph(
        "Зона быстрого усиления (14 дней):",
        strong
    ))
    elements.append(Spacer(1, 4 * mm))

    growth = """
    • Зафиксировать 1–2 стабильных канала привлечения.<br/>
    • Ввести учёт обращений и контроль конверсии.<br/>
    • Настроить регламент обработки заявок.<br/>
    • Сформировать систему регулярных маркетинговых действий.
    """

    elements.append(Paragraph(growth, body))
    elements.append(Spacer(1, 12 * mm))

    elements.append(Paragraph(
        "Следующий шаг — 30-минутная стратегическая сессия. Мы определим точки роста и сформируем план внедрения на 14 дней.",
        strong
    ))

    # Build
    onpage = _make_onpage(logo_reader, FONT_BOLD)
    doc.build(elements, onFirstPage=onpage)

    buffer.seek(0)
    return buffer