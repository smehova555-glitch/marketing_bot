from io import BytesIO
import os
from typing import Dict, Any, List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader


# =========================
# BRAND (твои цвета)
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

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

def _loss_range(score: int) -> str:
    if score <= 3:
        return "25-45%"
    if score <= 6:
        return "15-35%"
    return "8-20%"

def _card(rows, width, bg=colors.white, pad=14):
    t = Table(rows, colWidths=[width], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t

def _progress_bar(score: int, width=160*mm, height=6*mm):
    score = int(_clamp(score, 0, 10))
    fill = width * (score / 10)
    empty = width - fill
    t = Table([["", ""]], colWidths=[fill, empty], rowHeights=[height], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BRAND_TEAL),
        ("BACKGROUND", (1, 0), (1, 0), GREY_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
    ]))
    return t


# =========================
# Header (каждая страница)
# =========================
def _make_onpage(logo_reader, font_bold: str):
    def _on_page(canvas, doc):
        canvas.saveState()

        # фон
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

        # полоса
        bar_h = 16 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

        # лого (2 попытки: без mask и fallback)
        if logo_reader is not None:
            x = doc.leftMargin
            y = A4[1] - bar_h + 2.5 * mm
            try:
                canvas.drawImage(
                    logo_reader,
                    x, y,
                    width=42 * mm,
                    height=11 * mm,
                    preserveAspectRatio=True
                )
            except Exception:
                try:
                    canvas.drawImage(
                        logo_reader,
                        x, y,
                        width=42 * mm,
                        height=11 * mm
                    )
                except Exception:
                    pass

        # номер страницы
        canvas.setFillColor(BRAND_GRAPHITE)
        canvas.setFont(font_bold, 9)
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"стр. {canvas.getPageNumber()}")

        canvas.restoreState()
    return _on_page


# =========================
# MAIN
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):
    """
    segment приходит из main, но В PDF НЕ выводим.
    """

    buffer = BytesIO()

    # ✅ ВАЖНО: берём путь от файла, а не от текущей директории процесса (Render!)
    base_path = os.path.dirname(os.path.abspath(__file__))

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

    # logo
    logo_abs = os.path.join(base_path, LOGO_PATH)
    logo_reader = None
    if os.path.exists(logo_abs) and os.path.getsize(logo_abs) > 0:
        try:
            logo_reader = ImageReader(logo_abs)
            print(f"[PDF] Logo loaded: {logo_abs} ({os.path.getsize(logo_abs)} bytes)")
        except Exception as e:
            print(f"[PDF] Logo read error: {logo_abs} -> {e}")
            logo_reader = None
    else:
        print(f"[PDF] Logo missing/empty: {logo_abs}")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
        title="Shift Motion — Диагностика",
        author="Shift Motion",
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

    width = A4[0] - doc.leftMargin - doc.rightMargin
    elements: List[Any] = []

    # =========================
    # PAGE 1
    # =========================
    elements.append(Paragraph("Shift Motion — диагностика маркетинга", title))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(f"<b>{score}/10</b>", h2))
    elements.append(Paragraph(f"Оценка потерь: <b>{loss}</b> потенциальных обращений.", body))
    elements.append(Spacer(1, 8 * mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 12 * mm))

    elements.append(_card(
        [[Paragraph(
            "Короткий вывод: рост сейчас не полностью управляется системой. "
            "Мы видим разрывы между оффером, упаковкой и конверсией в заявку.",
            body
        )]],
        width
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 2
    # =========================
    elements.append(Paragraph("Ключевой разрыв", title))
    elements.append(Spacer(1, 8 * mm))

    bullets = [
        "Оффер не структурирован в понятную линейку.",
        "Путь пользователя до заявки не спроектирован.",
        "Источники трафика не диверсифицированы.",
        "Конверсия не измеряется как система."
    ]
    elements.append(_card(
        [[Paragraph("<br/>".join([f"• {b}" for b in bullets]), body)]],
        width
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 3
    # =========================
    elements.append(Paragraph("Модель усиления на 30 дней", title))
    elements.append(Spacer(1, 10 * mm))

    plan = [
        "Зафиксировать ключевой оффер и смыслы (что продаём и кому).",
        "Собрать сценарий конверсии: контент - доверие - действие.",
        "Запустить 2 стабильных источника обращений.",
        "Включить измеримость: заявки, конверсия, стоимость обращения."
    ]
    elements.append(_card(
        [[Paragraph("<br/>".join([f"• {p}" for p in plan]), body)]],
        width
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 4
    # =========================
    elements.append(Paragraph("Shift Motion", title))
    elements.append(Spacer(1, 8 * mm))

    elements.append(_card(
        [[Paragraph(
            "Мы проектируем управляемые маркетинговые системы: стратегия, структура, внедрение, рост метрик.",
            body
        )]],
        width
    ))

    elements.append(Spacer(1, 10 * mm))

    elements.append(_card(
        [[Paragraph(
            "30 минут. Мы определим приоритеты и дадим карту внедрения на 14 дней.",
            cta_white
        )]],
        width,
        bg=BRAND_TEAL
    ))

    onpage = _make_onpage(logo_reader, FONT_BOLD)
    doc.build(elements, onFirstPage=onpage, onLaterPages=onpage)

    buffer.seek(0)
    return buffer