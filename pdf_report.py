from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet

import os


def generate_pdf(data: dict, segment: str) -> str:
    filename = f"report_{data.get('telegram_id')}.pdf"

    doc = SimpleDocTemplate(filename)
    elements = []

    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    elements.append(Paragraph("Shift Motion — Диагностика маркетинга", styles["Title"]))
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(f"Сегмент: {segment}", normal))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Рекомендации:", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("• Выстроить системную стратегию", normal))
    elements.append(Paragraph("• Усилить основной канал привлечения", normal))
    elements.append(Paragraph("• Настроить аналитику", normal))

    doc.build(elements)

    return filename