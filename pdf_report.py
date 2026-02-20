import os
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    ListFlowable,
    ListItem,
    HRFlowable
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


print("PDF MODULE LOADED")


# ========= BRAND COLORS =========

COLOR_DARK = colors.HexColor("#292b2d")
COLOR_BLUE = colors.HexColor("#024a68")
COLOR_BLACK = colors.HexColor("#000000")


# ========= SAFE FONT REGISTER =========

def register_fonts():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        fonts_path = os.path.join(base_path, "fonts")

        pdfmetrics.registerFont(
            TTFont("Jost-Regular", os.path.join(fonts_path, "Jost-Regular.ttf"))
        )
        pdfmetrics.registerFont(
            TTFont("Jost-SemiBold", os.path.join(fonts_path, "Jost-SemiBold.ttf"))
        )
        pdfmetrics.registerFont(
            TTFont("Jost-Bold", os.path.join(fonts_path, "Jost-Bold.ttf"))
        )

        print("Jost fonts loaded successfully")
        return True

    except Exception as e:
        print("Font loading failed:", e)
        return False


def generate_pdf(data: dict, segment: str):

    print("PDF VERSION 3 EXECUTED")

    fonts_loaded = register_fonts()

    # если Jost не загрузился — используем системные шрифты
    if fonts_loaded:
        FONT_REG = "Jost-Regular"
        FONT_SEMI = "Jost-SemiBold"
        FONT_BOLD = "Jost-Bold"
    else:
        FONT_REG = "Helvetica"
        FONT_SEMI = "Helvetica-Bold"
        FONT_BOLD = "Helvetica-Bold"

    # уникальное имя (убираем кэш Telegram)
    filename = f"report_{data.get('telegram_id')}_{int(datetime.now().timestamp())}.pdf"

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
        fontName=FONT_BOLD,
        fontSize=26,
        textColor=COLOR_BLUE,
        spaceAfter=20,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName=FONT_SEMI,
        fontSize=16,
        textColor=COLOR_DARK,
        spaceAfter=10,
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=12,
        leading=18,
        textColor=COLOR_BLACK,
    )

    # ========= LOGO =========

    if os.path.exists("logo.png"):
        elements.append(Image("logo.png", width=120, height=40))
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
        normal_style
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

    # ========= WEAKNESSES =========

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
        weaknesses.append("Требуется усиление системности")

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(w, normal_style)) for w in weaknesses],
            bulletType="bullet"
        )
    )

    elements.append(Spacer(1, 30))

    # ========= RECOMMENDATIONS =========

    elements.append(Paragraph("Рекомендации", subtitle_style))
    elements.append(Spacer(1, 10))

    recommendations = [
        "Сформировать стратегию на 3 месяца",
        "Оптимизировать маркетинговый бюджет",
        "Внедрить измеримую аналитику"
    ]

    elements.append(
        ListFlowable(
            [ListItem(Paragraph(r, normal_style)) for r in recommendations],
            bulletType="1"
        )
    )

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

    doc.build(elements)

    print("PDF BUILT:", filename)

    return filename