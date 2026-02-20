from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import ListFlowable
from reportlab.lib.pagesizes import A4
import os


def generate_pdf(data, segment):
    file_name = f"report_{data['telegram_id']}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)

    elements = []

    # Регистрируем шрифт
    font_path = os.path.join("fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))

    styles = getSampleStyleSheet()

    normal_style = ParagraphStyle(
        'NormalRu',
        parent=styles['Normal'],
        fontName='DejaVu',
        fontSize=12,
        leading=16
    )

    title_style = ParagraphStyle(
        'TitleRu',
        parent=styles['Title'],
        fontName='DejaVu',
        fontSize=18,
        leading=22,
        textColor=colors.black
    )

    elements.append(Paragraph("Shift Motion — Диагностика маркетинга", title_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(f"Сегмент: {segment}", normal_style))
    elements.append(Spacer(1, 10))

    recommendations = [
        "Проверить упаковку оффера",
        "Определить главный канал привлечения",
        "Зафиксировать бюджет",
        "Усилить геомаркетинг"
    ]

    bullet_points = []
    for rec in recommendations:
        bullet_points.append(ListItem(Paragraph(rec, normal_style)))

    elements.append(Paragraph("Рекомендации:", normal_style))
    elements.append(Spacer(1, 5))
    elements.append(ListFlowable(bullet_points, bulletType='bullet'))

    doc.build(elements)

    return file_name