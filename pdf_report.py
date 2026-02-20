import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import HRFlowable
from datetime import datetime


# ========= BRAND COLORS =========

COLOR_DARK = colors.HexColor("#292b2d")
COLOR_LIGHT = colors.HexColor("#f6f5ea")
COLOR_BLUE = colors.HexColor("#024a68")
COLOR_BLACK = colors.HexColor("#000000")


def register_fonts():
    pdfmetrics.registerFont(TTFont("Jost-Regular", "fonts/Jost-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Jost-SemiBold", "fonts/Jost-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("Jost-Bold", "fonts/Jost-Bold.ttf"))


def generate_pdf(data: dict, segment: str):

    register_fonts()

    filename = f"report_{data.get('telegram_id')}.pdf"
    doc = SimpleDocTemplate(
        filename,
        rightMargin=30,
        leftMargin=30,
        topMargin=40,
        bottomMargin=40
    )

    elements = []

    styles = getSampleStyleSheet()

    # ========= STYLES =========

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Jost-Bold",
        fontSize=26,
        textColor=COLOR_BLUE,
        spaceAfter=20,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Jost-SemiBold",
        fontSize=16,
        textColor=COLOR_DARK,
        spaceAfter=10,
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Jost-Regular",
        fontSize=12,
        leading=18,
        textColor=COLOR_BLACK,
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontName="Jost-Regular",
        fontSize=10,
        textColor=COLOR_DARK,
    )

    # ========= LOGO =========

    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=120, height=40)
        elements.append(logo)
        elements.append(Spacer(1, 20))

    # ========= COVER =========

    elements.append(Paragraph("Маркетинговая диагностика", title_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"Для: @{data.get('username', 'клиента')}",
        normal_style
    ))

    elements.append(Paragraph(
        f"Дата: {datetime.now().strftime('%d.%m.%Y')}",
        small_style
    ))

    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(color=COLOR_BLUE))
    elements.append(Spacer(1, 30))

    # ========= RESULT =========

    elements.append(Paragraph("Результат диагностики", subtitle_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        f"<b>Сегмент:</b> {segment}",
        normal_style
    ))

    score = data.get("score", 0)

    elements.append(Paragraph(
        f"<b>Индекс готовности:</b> {score} / 10",
        normal_style
    ))

    elements.append(Spacer(1, 30))

    # ========= ANALYSIS =========

    elements.append(Paragraph("Ключевые зоны роста", subtitle_style))
    elements.append(Spacer(1, 10))

    weaknesses = []

    if data.get("strategy") == "Нет":
        weaknesses.append("Отсутствует маркетинговая стратегия")

    if data.get("stability") == "Нет":
        weaknesses.append("Нестабильный поток заявок")

    if data.get("geo") == "Нет":
        weaknesses.append("Не используется геомаркетинг")

    if not weaknesses:
        weaknesses.append("Системность требует усиления")

    weakness_list = ListFlowable(
        [ListItem(Paragraph(item, normal_style)) for item in weaknesses],
        bulletType="bullet"
    )

    elements.append(weakness_list)
    elements.append(Spacer(1, 30))

    # ========= RECOMMENDATIONS =========

    elements.append(Paragraph("Рекомендации", subtitle_style))
    elements.append(Spacer(1, 10))

    recommendations = [
        "Сформировать стратегию на 3 месяца",
        "Оптимизировать распределение бюджета",
        "Усилить каналы с измеримой аналитикой"
    ]

    rec_list = ListFlowable(
        [ListItem(Paragraph(item, normal_style)) for item in recommendations],
        bulletType="1"
    )

    elements.append(rec_list)
    elements.append(Spacer(1, 40))

    # ========= CTA =========

    elements.append(HRFlowable(color=COLOR_BLUE))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        "Для детального разбора и построения стратегии\nзапишитесь на консультацию.",
        subtitle_style
    ))

    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "Telegram: @shift_motion",
        normal_style
    ))

    elements.append(Spacer(1, 30))

    doc.build(elements)

    return filename