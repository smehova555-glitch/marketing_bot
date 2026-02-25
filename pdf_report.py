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
def _safe(v, default="—"):
    if v is None or v == "":
        return default
    return str(v)


def _loss_range(score: int) -> str:
    if score <= 3:
        return "25–45%"
    if score <= 6:
        return "15–35%"
    return "8–20%"


def _progress_bar(score: int, width=160 * mm, height=7 * mm):
    score = max(0, min(10, int(score)))
    fill = width * (score / 10)
    empty = width - fill

    t = Table([["", ""]], colWidths=[fill, empty], rowHeights=[height], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BRAND_TEAL),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _meta_table(data: Dict[str, Any], width, body, muted):
    rows = [
        [Paragraph("Город", muted), Paragraph(_safe(data.get("city")), body)],
        [Paragraph("Ниша", muted), Paragraph(_safe(data.get("niche")), body)],
        [Paragraph("Роль", muted), Paragraph(_safe(data.get("role")), body)],
        [Paragraph("Бюджет", muted), Paragraph(_safe(data.get("budget")), body)],
        [Paragraph("Стратегия", muted), Paragraph(_safe(data.get("strategy")), body)],
        [Paragraph("Источник", muted), Paragraph(_safe(data.get("source")), body)],
        [Paragraph("Стабильность", muted), Paragraph(_safe(data.get("stability")), body)],
        [Paragraph("Гео (Яндекс/2ГИС)", muted), Paragraph(_safe(data.get("geo")), body)],
    ]
    t = Table(rows, colWidths=[34 * mm, width - 34 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _make_onpage(logo_reader):
    def _on_page(canvas, doc):
        canvas.saveState()

        # фон страницы
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

        # верхняя полоса
        bar_h = 20 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

        # увеличенный логотип
        if logo_reader is not None:
            try:
                canvas.drawImage(
                    logo_reader,
                    doc.leftMargin,
                    A4[1] - bar_h + 3 * mm,
                    height=14 * mm,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except Exception:
                # не роняем PDF
                pass

        canvas.restoreState()

    return _on_page


# =========================
# MAIN
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):
    # Маркер версии, чтобы увидеть в Render Logs, что работает именно этот файл
    print("PDF VERSION: PREMIUM-ONE-PAGE-AGENCY v1")

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
    if os.path.exists(logo_abs) and os.path.getsize(logo_abs) > 0:
        try:
            logo_reader = ImageReader(logo_abs)
            print(f"[PDF] Logo loaded: {logo_abs} ({os.path.getsize(logo_abs)} bytes)")
        except Exception as e:
            print(f"[PDF] Logo read error: {e}")

    # Doc
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=32 * mm,      # под шапку/полосу
        bottomMargin=22 * mm,
        title="Shift Motion — Маркетинговая диагностика",
        author="Shift Motion",
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=25,
        textColor=BRAND_GRAPHITE,
        spaceAfter=6 * mm
    )

    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14.5,
        leading=19,
        textColor=BRAND_GRAPHITE,
        spaceAfter=2 * mm
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=12.8,
        leading=18,
        textColor=BRAND_GRAPHITE,
    )

    muted = ParagraphStyle(
        "Muted",
        parent=body,
        textColor=colors.HexColor("#5B5F62"),
        fontSize=11.2,
        leading=16.5,
    )

    cta_white = ParagraphStyle(
        "CTAWhite",
        parent=body,
        fontName=FONT_BOLD,
        textColor=colors.white,
    )

    # Data
    score = int(data.get("score", 0) or 0)
    loss = _loss_range(score)

    width = A4[0] - doc.leftMargin - doc.rightMargin

    elements = []

    # Заголовок
    elements.append(Paragraph(
        "Маркетинговая диагностика от коммуникационного агентства Shift Motion",
        title
    ))

    # Таблица входных данных (аккуратно, ровно)
    elements.append(_meta_table(data, width, body, muted))
    elements.append(Spacer(1, 8 * mm))

    # Оценка
    elements.append(Paragraph(f"Результат: <b>{score}/10</b>", h2))
    elements.append(Paragraph(f"Оценка потерь: <b>{loss}</b> потенциальных обращений из-за несобранной системы.", body))
    elements.append(Spacer(1, 5 * mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 8 * mm))

    # Универсальная интерпретация (без “оффера”)
    elements.append(Paragraph("Что это означает на практике:", h2))

    interpretation = """
    • Маркетинг работает частично, но не как управляемая система.<br/>
    • Заявки возникают, однако не воспроизводятся предсказуемо (эффект “волнами”).<br/>
    • Чаще всего провал происходит на одном из этапов: вход → обработка → повторное касание → конверсия.<br/>
    • Без учёта и регулярного контура управления рост становится случайным.
    """
    elements.append(Paragraph(interpretation, body))
    elements.append(Spacer(1, 7 * mm))

    # 14 дней — универсальная зона усиления
    elements.append(Paragraph("Зона быстрого усиления (14 дней):", h2))

    growth = """
    • Ввести учёт обращений и контроль конверсии (что считается заявкой, где фиксируется, какой итог).<br/>
    • Настроить регламент обработки: время ответа, следующий шаг, сценарий повторного касания.<br/>
    • Сфокусироваться на 1–2 стабильных источниках обращения и довести их до управляемости.<br/>
    • Сделать недельный цикл управления: план → действие → цифры → корректировка.
    """
    elements.append(Paragraph(growth, body))
    elements.append(Spacer(1, 8 * mm))

    # CTA
    cta = Table(
        [[Paragraph(
            "Следующий шаг: 30-минутная стратегическая сессия. Мы уточним контекст, определим приоритеты и дадим план внедрения на 14 дней.",
            cta_white
        )]],
        colWidths=[width],
        hAlign="LEFT"
    )
    cta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_TEAL),
        ("BOX", (0, 0), (-1, -1), 0, BRAND_TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(cta)

    onpage = _make_onpage(logo_reader)
    doc.build(elements, onFirstPage=onpage)

    buffer.seek(0)
    return buffer