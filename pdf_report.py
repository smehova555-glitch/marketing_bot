from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics


def generate_pdf(data, segment):
    buffer = BytesIO()

    # Поддержка кириллицы
    pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'NormalUnicode',
        parent=styles['Normal'],
        fontName='HYSMyeongJo-Medium'
    )

    elements = []

    elements.append(Paragraph("Shift Motion — Персональный разбор", normal_style))
    elements.append(Spacer(1, 0.3 * inch))

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
        elements.append(Paragraph(line, normal_style))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)

    buffer.seek(0)
    return buffer