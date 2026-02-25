from io import BytesIO
import os

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# -------------------------
# Helpers
# -------------------------

def _safe(v, default="—"):
    if v is None or v == "":
        return default
    return str(v)

def _priority_from_score(score: int) -> str:
    if score >= 7:
        return "HIGH"
    elif score >= 4:
        return "MEDIUM"
    return "LOW"

def _interpret_score(score: int):
    # текст + подсветка
    if score <= 3:
        return ("Система почти не управляет заявками: рост упирается в случайность.", colors.HexColor("#FEF3C7"))
    if 4 <= score <= 6:
        return ("Есть база, но нет рычагов масштабирования: нужно собрать воронку и источники лидов.", colors.HexColor("#EEF2FF"))
    return ("Сильная основа: можно усиливать конверсию и масштабировать каналы.", colors.HexColor("#DCFCE7"))

def _progress_bar(score: int, width=160*mm, height=6*mm):
    # Таблица-бар: заполненная часть + пустая
    score = max(0, min(int(score), 10))
    fill = width * (score / 10)
    empty = width - fill
    t = Table([["", ""]], colWidths=[fill, empty], rowHeights=[height])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#111827")),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
    ]))
    return t

def _card(rows, col_widths, bg="#FFFFFF", border="#E5E7EB", pad=10):
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(border)),
        ("INNERGRID", (0, 0), (-1, -1), 0, colors.HexColor(bg)),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# -------------------------
# Main
# -------------------------

def generate_pdf(data, segment):
    """
    INPUT:
      data: dict with keys like city, niche, role, budget, strategy, geo, source, stability, phone, score
      segment: string (e.g. WARM)
    OUTPUT:
      BytesIO buffer (same as your old function)
    """

    buffer = BytesIO()

    # Fonts (keep your Jost)
    base_path = os.getcwd()
    regular_font = os.path.join(base_path, "fonts", "Jost-Regular.ttf")
    bold_font = os.path.join(base_path, "fonts", "Jost-Bold.ttf")

    # Safe font registration + fallback
    if os.path.exists(regular_font) and os.path.exists(bold_font):
        pdfmetrics.registerFont(TTFont("Jost-Regular", regular_font))
        pdfmetrics.registerFont(TTFont("Jost-Bold", bold_font))
        FONT_REG = "Jost-Regular"
        FONT_BOLD = "Jost-Bold"
    else:
        FONT_REG = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"

    # Doc
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=16*mm,
        bottomMargin=16*mm,
        title="Shift Motion — Персональный разбор",
        author="Shift Motion",
    )

    styles = getSampleStyleSheet()

    # Styles
    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#111827"),
        spaceAfter=10
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=8
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#111827"),
    )
    muted = ParagraphStyle(
        "Muted",
        parent=body,
        textColor=colors.HexColor("#6B7280"),
        fontSize=10.5,
        leading=15,
    )
    badge = ParagraphStyle(
        "Badge",
        parent=body,
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
    )

    # Data
    score = int(data.get("score", 0) or 0)
    priority = _priority_from_score(score)

    city = _safe(data.get("city"))
    niche = _safe(data.get("niche"))
    role = _safe(data.get("role"))
    budget = _safe(data.get("budget"))
    strategy = _safe(data.get("strategy"))
    geo = _safe(data.get("geo"))
    source = _safe(data.get("source"))
    stability = _safe(data.get("stability"))
    phone = _safe(data.get("phone"))

    interpret_text, interpret_bg = _interpret_score(score)

    elements = []

    # -------------------------
    # PAGE 1 — Cover (Leadgen)
    # -------------------------
    elements.append(Paragraph("Shift Motion — Персональный разбор", title))
    elements.append(Paragraph("Формат: лидогенерация. Коротко фиксируем, где теряются заявки и что делать дальше.", muted))
    elements.append(Spacer(1, 10*mm))

    meta = _card(
        [
            [Paragraph("Сегмент", muted), Paragraph(_safe(segment), badge), Paragraph("Город", muted), Paragraph(city, badge)],
            [Paragraph("Ниша", muted), Paragraph(niche, badge), Paragraph("Роль", muted), Paragraph(role, badge)],
            [Paragraph("Бюджет", muted), Paragraph(budget, badge), Paragraph("Приоритет", muted), Paragraph(priority, badge)],
        ],
        col_widths=[22*mm, 66*mm, 18*mm, 58*mm],
        bg="#FFFFFF"
    )
    elements.append(meta)
    elements.append(Spacer(1, 10*mm))

    elements.append(Paragraph("Оценка маркетинговой системы", h2))
    elements.append(Paragraph(f"<b>{score}/10</b> — {interpret_text}", body))
    elements.append(Spacer(1, 3*mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 8*mm))

    elements.append(_card(
        [[Paragraph(
            "Важно: этот отчёт показывает только верхний слой. "
            "На консультации мы раскладываем воронку по этапам и даём конкретные действия на 7–30 дней.",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#F9FAFB"
    ))

    elements.append(PageBreak())

    # -------------------------
    # PAGE 2 — Diagnosis (meaning)
    # -------------------------
    elements.append(Paragraph("Диагностика текущей модели", title))

    diag_table = Table(
        [
            [Paragraph("Стратегия", muted), Paragraph(strategy, body)],
            [Paragraph("Гео", muted), Paragraph(geo, body)],
            [Paragraph("Источник лидов", muted), Paragraph(source, body)],
            [Paragraph("Стабильность", muted), Paragraph(stability, body)],
        ],
        colWidths=[32*mm, A4[0] - doc.leftMargin - doc.rightMargin - 32*mm]
    )
    diag_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), FONT_REG),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F9FAFB")]),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(diag_table)
    elements.append(Spacer(1, 10*mm))

    elements.append(Paragraph("Что это значит для заявок", h2))
    elements.append(_card(
        [[Paragraph(
            "Если основной источник — сарафан, а продвижение «иногда», то поток заявок неуправляем. "
            "Цель — собрать 2–3 стабильных канала и увязать их в воронку (контент → доверие → заявка).",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#EEF2FF"
    ))

    elements.append(PageBreak())

    # -------------------------
    # PAGE 3 — Losses (money framing)
    # -------------------------
    elements.append(Paragraph("Где теряются заявки", title))
    elements.append(Paragraph("Ниже — типовые точки потерь в модели «эксперт/онлайн», когда нет цельной воронки.", muted))
    elements.append(Spacer(1, 6*mm))

    losses = [
        ("Нет ясного оффера", "человек понимает «кто вы», но не понимает «что купить прямо сейчас»."),
        ("Нет пути до заявки", "контент есть, но нет этапа «разогрев → аргументы → CTA»."),
        ("Один источник лидов", "сарафан не масштабируется и даёт провалы по месяцу/неделе."),
        ("Не используется гео", "упускается спрос из карт/поиска и локальных запросов.")
    ]

    loss_rows = []
    for t, d in losses:
        loss_rows.append([Paragraph(f"<b>{t}</b>", body), Paragraph(d, body)])

    elements.append(_card(
        [[Table(loss_rows, colWidths=[50*mm, (A4[0]-doc.leftMargin-doc.rightMargin)-50*mm],
               style=TableStyle([
                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                   ("INNERGRID", (0, 0), (-1, -1), 0.0, colors.white),
                   ("LEFTPADDING", (0, 0), (-1, -1), 0),
                   ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                   ("TOPPADDING", (0, 0), (-1, -1), 6),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
               ]))]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#FFFFFF"
    ))

    elements.append(Spacer(1, 10*mm))
    elements.append(_card(
        [[Paragraph(
            "Быстрый смысл: мы не «улучшаем инстаграм». Мы устраняем потери на пути к заявке и делаем поток предсказуемым.",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#F9FAFB"
    ))

    elements.append(PageBreak())

    # -------------------------
    # PAGE 4 — Plan (7/14/30)
    # -------------------------
    elements.append(Paragraph("План усиления (7 / 14 / 30 дней)", title))

    plan_7 = [
        "Сформулировать 1 главный оффер + 2 дополнительных (пакеты/форматы).",
        "Собрать мини-воронку: 3 прогревающих касания → 1 CTA.",
        "Обновить шапку/первый экран: кто вы → для кого → результат → как купить."
    ]
    plan_14 = [
        "Собрать контент-матрицу под сегмент WARM: доверие, кейсы, возражения, демонстрация процесса.",
        "Упаковать 5–7 сторис-шаблонов: прогрев, FAQ, кейс, приглашение, сбор заявок.",
        "Подготовить 1 лид-магнит (чек-лист/мини-разбор) под вход в воронку."
    ]
    plan_30 = [
        "Запустить 2 стабильных источника лидов (контент + один платный/партнёрский).",
        "Подключить гео (если актуально): карточки, отзывы, фото, позиционирование.",
        "Настроить измеримость: заявки/конверсия/стоимость обращения."
    ]

    def bullets(items):
        # Paragraph bullets without ListFlowable for simplicity
        return "<br/>".join([f"• {_safe(x)}" for x in items])

    elements.append(KeepTogether([
        Paragraph("7 дней — собрать основу", h2),
        _card([[Paragraph(bullets(plan_7), body)]],
              [A4[0] - doc.leftMargin - doc.rightMargin],
              bg="#FFFFFF")
    ]))

    elements.append(Spacer(1, 6*mm))
    elements.append(KeepTogether([
        Paragraph("14 дней — усилить конверсию", h2),
        _card([[Paragraph(bullets(plan_14), body)]],
              [A4[0] - doc.leftMargin - doc.rightMargin],
              bg="#FFFFFF")
    ]))

    elements.append(Spacer(1, 6*mm))
    elements.append(KeepTogether([
        Paragraph("30 дней — сделать поток стабильным", h2),
        _card([[Paragraph(bullets(plan_30), body)]],
              [A4[0] - doc.leftMargin - doc.rightMargin],
              bg="#FFFFFF")
    ]))

    elements.append(PageBreak())

    # -------------------------
    # PAGE 5 — CTA
    # -------------------------
    elements.append(Paragraph("Следующий шаг", title))

    elements.append(_card(
        [[Paragraph(
            "Если вы хотите получить персональную карту роста (что делать именно в вашей нише/городе/модели), "
            "я проведу 30-минутный разбор и дам 10–15 конкретных действий на ближайшие 2 недели.",
            body
        )]],
        [A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#111827",
        border="#111827"
    ))
    # white text inside dark card
    # (hack: same paragraph style but override color)
    cta_text = ParagraphStyle("CTA", parent=body, textColor=colors.white)
    cta_muted = ParagraphStyle("CTA_M", parent=muted, textColor=colors.HexColor("#D1D5DB"))

    # rebuild card with white text
    elements.pop()
    elements.append(_card(
        [[Paragraph(
            "Если вы хотите получить персональную карту роста (что делать именно в вашей нише/городе/модели), "
            "мы проведем 30-минутный разбор и дадим 10–15 конкретных действий на ближайшие 2 недели.",
            cta_text
        )]],
        [A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#111827",
        border="#111827"
    ))

    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("Контакт для связи", h2))
    elements.append(_card(
        [[Paragraph(f"<b>Телефон:</b> {phone}", body)],
         [Paragraph("Напишите «разбор», и я предложу 2–3 слота на ближайшие дни.", muted)]],
        [A4[0] - doc.leftMargin - doc.rightMargin],
        bg="#F9FAFB"
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer