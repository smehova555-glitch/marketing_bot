from io import BytesIO
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def generate_pdf(data, segment):

    buffer = BytesIO()

    base_path = os.getcwd()
    regular_font = os.path.join(base_path, "fonts", "Jost-Regular.ttf")
    bold_font = os.path.join(base_path, "fonts", "Jost-Bold.ttf")

    pdfmetrics.registerFont(TTFont("Jost-Regular", regular_font))
    pdfmetrics.registerFont(TTFont("Jost-Bold", bold_font))

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleBrand',
        parent=styles['Normal'],
        fontName='Jost-Bold',
        fontSize=18,
        leading=22
    )

    text_style = ParagraphStyle(
        'TextBrand',
        parent=styles['Normal'],
        fontName='Jost-Regular',
        fontSize=12,
        leading=16
    )

    elements = []

    elements.append(Paragraph("Shift Motion — Персональный разбор", title_style))
    elements.append(Spacer(1, 0.5 * inch))

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
        elements.append(Paragraph(line, text_style))
        elements.append(Spacer(1, 0.3 * inch))

    doc.build(elements)

    buffer.seek(0)
    return buffer