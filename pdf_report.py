from io import BytesIO
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def generate_pdf(data, segment):

    buffer = BytesIO()

    # Путь к шрифту
    font_path = os.path.join(os.getcwd(), "fonts", "Jost-Regular.ttf")

    # Регистрируем фирменный шрифт
    pdfmetrics.registerFont(TTFont("Jost", font_path))

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        'BrandStyle',
        parent=styles['Normal'],
        fontName='Jost',
        fontSize=12,
        leading=16
    )

    elements = []

    elements.append(Paragraph("Shift Motion — Персональный разбор", brand_style))
    elements.append(Spacer(1, 0.4 * inch))

    score = data.get("score", 0)

    if score >= 7:
        priority = "HIGH"
    elif score >= 4:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    lines = [
        f"Сегмент: {segment}",
        f"Score: {score}/10",
        f"Приоритет: {priority}",
        "",
        f"Город: {data.get('city')}",
        f"Ниша: {data.get('niche')}",
        f"Роль: {data.get('role')}",
        f"Бюджет: {data.get('budget')}",
        f"Стратегия: {data.get('strategy')}",
        f"Гео: {data.get('geo')}",
        f"Источник: {data.get('source')}",
        f"Стабильность: {data.get('stability')}",
        f"Телефон: {data.get('phone')}",
    ]

    for line in lines:
        elements.append(Paragraph(line, brand_style))
        elements.append(Spacer(1, 0.25 * inch))

    doc.build(elements)

    buffer.seek(0)
    return buffer