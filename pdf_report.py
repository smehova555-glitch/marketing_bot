from io import BytesIO
import os
from typing import Dict, Any, List, Tuple

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
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
BRAND_LIGHT = colors.HexColor("#FFFFFF")

BORDER = colors.HexColor("#D6D3C8")
MUTED = colors.HexColor("#6B7280")
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

def _priority_from_score(score: int) -> str:
    if score >= 7:
        return "HIGH"
    elif score >= 4:
        return "MEDIUM"
    return "LOW"

def _headline(score: int) -> str:
    if score <= 3:
        return "Маркетинг работает ниже потенциала — заявки теряются на пути к покупке."
    if score <= 6:
        return "Есть база, но нет системы масштабирования — рост идёт волнами."
    return "Сильная основа — можно масштабировать каналы и докручивать конверсию."

def _interpret_score(score: int):
    # текст + подсветка
    if score <= 3:
        return ("Система почти не управляет заявками: рост упирается в случайность.", colors.HexColor("#FEF3C7"))
    if 4 <= score <= 6:
        return ("Есть база, но нет рычагов масштабирования: нужна воронка и управляемые источники лидов.", colors.HexColor("#EEF2FF"))
    return ("Сильная основа: можно усиливать конверсию и масштабировать каналы.", colors.HexColor("#DCFCE7"))

def _money_framing(score: int, budget: str) -> str:
    if score <= 3:
        loss = "25–45%"
    elif score <= 6:
        loss = "15–35%"
    else:
        loss = "8–20%"
    return (
        f"По нашей практике, при такой конфигурации бизнес теряет порядка <b>{loss}</b> потенциальных обращений "
        f"из-за отсутствия связки «оффер → прогрев → CTA» и управляемых источников лидов. "
        f"Ваш текущий бюджет: <b>{_safe(budget)}</b>."
    )

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

def _card(rows, col_widths, bg=BRAND_LIGHT, pad=10):
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.9, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0, bg),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# =========================
# Header on each page
# =========================
def _make_onpage(logo_reader, font_bold: str):
    def _on_page(canvas, doc):
        canvas.saveState()

        # page background
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

        # top brand bar
        bar_h = 16 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

        # logo in header
        if logo_reader is not None:
            x = doc.leftMargin
            y = A4[1] - bar_h + 3 * mm
            canvas.drawImage(logo_reader, x, y, width=38*mm, height=10*mm, mask='auto')

        # footer page number
        canvas.setFillColor(BRAND_GRAPHITE)
        canvas.setFont(font_bold, 9)
        canvas.drawRightString(A4[0] - doc.rightMargin, 10*mm, f"стр. {canvas.getPageNumber()}")

        canvas.restoreState()
    return _on_page


# =========================
# Main
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):
    """
    segment приходит из main, но в клиентский PDF НЕ выводим (по договорённости).
    Возвращаем BytesIO.
    """
    buffer = BytesIO()
    base_path = os.getcwd()

    # Fonts (Jost, fallback Helvetica)
    regular_font = os.path.join(base_path, "fonts", "Jost-Regular.ttf")
    bold_font = os.path.join(base_path, "fonts", "Jost-Bold.ttf")

    if os.path.exists(regular_font) and os.path.exists(bold_font):
        pdfmetrics.registerFont(TTFont("Jost-Regular", regular_font))
        pdfmetrics.registerFont(TTFont("Jost-Bold", bold_font))
        FONT_REG = "Jost-Regular"
        FONT_BOLD = "Jost-Bold"
    else:
        FONT_REG = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"

    # Logo
    logo_abs = os.path.join(base_path, LOGO_PATH)
    logo_reader = None
    if os.path.exists(logo_abs):
        try:
            logo_reader = ImageReader(logo_abs)
        except Exception:
            logo_reader = None

    # Doc (topMargin больше, чтобы контент не залезал на шапку)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=24*mm,
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
        fontSize=20,
        leading=24,
        textColor=BRAND_GRAPHITE,
        spaceAfter=8
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=13.5,
        leading=18,
        textColor=BRAND_GRAPHITE,
        spaceBefore=8,
        spaceAfter=8
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=11,
        leading=16,
        textColor=BRAND_GRAPHITE,
    )
    muted = ParagraphStyle(
        "Muted",
        parent=body,
        textColor=MUTED,
        fontSize=10.5,
        leading=15,
    )
    badge = ParagraphStyle(
        "Badge",
        parent=body,
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12,
        textColor=BRAND_GRAPHITE,
    )
    cta_white = ParagraphStyle(
        "CTAWhite",
        parent=body,
        textColor=colors.white,
        fontName=FONT_REG
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

    elements: List[Any] = []

    # =========================
    # PAGE 1 — Cover
    # =========================
    elements.append(Paragraph("Shift Motion — персональный разбор", title))
    elements.append(Paragraph("Формат: лидогенерация. Коротко фиксируем, где теряются заявки и что делать дальше.", muted))
    elements.append(Spacer(1, 10*mm))

    meta = _card(
        [
            # сегмент тут УБРАН
            [Paragraph("Город", muted), Paragraph(city, badge), Paragraph("Ниша", muted), Paragraph(niche, badge)],
            [Paragraph("Роль", muted), Paragraph(role, badge), Paragraph("Бюджет", muted), Paragraph(budget, badge)],
            [Paragraph("Приоритет", muted), Paragraph(priority, badge), Paragraph(" ", muted), Paragraph(" ", badge)],
        ],
        col_widths=[18*mm, 62*mm, 18*mm, 62*mm],
        bg=BRAND_LIGHT
    )
    elements.append(meta)
    elements.append(Spacer(1, 10*mm))

    elements.append(Paragraph(_headline(score), h2))
    elements.append(Paragraph(_money_framing(score, budget), body))
    elements.append(Spacer(1, 8*mm))

    elements.append(Paragraph("Оценка маркетинговой системы", h2))
    elements.append(Paragraph(f"<b>{score}/10</b> — {interpret_text}", body))
    elements.append(Spacer(1, 3*mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 8*mm))

    # персонализация по ответам
    personal_blocks = []
    if source == "Сарафан":
        personal_blocks.append("Сарафан — сильный фундамент, но он не масштабируется. Мы добавим управляемый источник лидов.")
    if strategy in ("Нет", "Частично"):
        personal_blocks.append("Без стратегии рост идёт «рывками». Мы соберём воронку и сценарии касаний по этапам.")
    if geo == "Есть, но не продвигаем":
        personal_blocks.append("Карточки в Яндекс/2ГИС есть, но не используются как канал спроса — это быстрый рычаг.")
    if stability in ("Иногда", "Нет"):
        personal_blocks.append("Нестабильность заявок обычно означает провал в одном из узлов: оффер / доверие / CTA / канал.")

    if personal_blocks:
        elements.append(_card(
            [[Paragraph("<b>Персональные наблюдения по вашим ответам</b><br/>" + "<br/>".join([f"• {x}" for x in personal_blocks]), body)]],
            col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
            bg=colors.HexColor("#FFFFFF"),
            pad=12
        ))
        elements.append(Spacer(1, 6*mm))

    elements.append(_card(
        [[Paragraph(
            "Важно: этот отчёт показывает верхний слой. На разборе мы раскладываем воронку по этапам и даём конкретные действия на 7–30 дней.",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=colors.HexColor("#FFFFFF"),
        pad=12
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 2 — Diagnosis
    # =========================
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
        ("TEXTCOLOR", (0, 0), (-1, -1), BRAND_GRAPHITE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, colors.HexColor("#FBFAF4")]),
        ("BOX", (0, 0), (-1, -1), 0.9, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
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
            "Если основной источник — сарафан и поток «иногда», то заявки неуправляемы. "
            "Цель — собрать 2–3 канала привлечения и связать их в воронку (контент → доверие → заявка).",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=BRAND_LIGHT
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 3 — Losses
    # =========================
    elements.append(Paragraph("Где теряются заявки", title))
    elements.append(Paragraph("Ниже — типовые точки потерь в модели «эксперт/онлайн», когда нет цельной воронки.", muted))
    elements.append(Spacer(1, 6*mm))

    losses = [
        ("Нет ясного оффера", "человек понимает «кто вы», но не понимает «что купить сейчас»."),
        ("Нет пути до заявки", "контент есть, но нет сценария «прогрев → аргументы → CTA»."),
        ("Один источник лидов", "сарафан не масштабируется и даёт провалы по неделям/месяцам."),
        ("Не используется гео", "упускается спрос из карт/поиска и локальных запросов."),
    ]

    loss_rows = []
    for t, d in losses:
        loss_rows.append([Paragraph(f"<b>{t}</b>", body), Paragraph(d, body)])

    inner = Table(
        loss_rows,
        colWidths=[52*mm, (A4[0] - doc.leftMargin - doc.rightMargin) - 52*mm]
    )
    inner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(_card(
        [[inner]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=BRAND_LIGHT
    ))

    elements.append(Spacer(1, 10*mm))
    elements.append(_card(
        [[Paragraph(
            "Коротко: мы не «улучшаем соцсети». Мы устраняем потери на пути к заявке и делаем поток предсказуемым.",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=colors.HexColor("#FBFAF4")
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 4 — Plan
    # =========================
    elements.append(Paragraph("План усиления (7 / 14 / 30 дней)", title))

    plan_7 = [
        "Сформулировать 1 главный оффер + 2 дополнительных (пакеты/форматы).",
        "Собрать мини-воронку: 3 прогревающих касания → 1 CTA.",
        "Обновить первый экран: кто вы → для кого → результат → как купить."
    ]
    plan_14 = [
        "Собрать контент-матрицу: доверие, кейсы, возражения, демонстрация процесса.",
        "Упаковать 5–7 сторис-шаблонов: прогрев, FAQ, кейс, приглашение, сбор заявок.",
        "Подготовить 1 лид-магнит (чек-лист/мини-разбор) для входа в воронку."
    ]
    plan_30 = [
        "Запустить 2 стабильных источника лидов (контент + один платный/партнёрский).",
        "Подключить гео (если актуально): карточки, отзывы, фото, позиционирование.",
        "Настроить измеримость: заявки / конверсия / стоимость обращения."
    ]

    def bullets(items):
        return "<br/>".join([f"• {_safe(x)}" for x in items])

    elements.append(KeepTogether([
        Paragraph("7 дней — собрать основу", h2),
        _card([[Paragraph(bullets(plan_7), body)]],
              [A4[0] - doc.leftMargin - doc.rightMargin],
              bg=BRAND_LIGHT)
    ]))

    elements.append(Spacer(1, 6*mm))
    elements.append(KeepTogether([
        Paragraph("14 дней — усилить конверсию", h2),
        _card([[Paragraph(bullets(plan_14), body)]],
              [A4[0] - doc.leftMargin - doc.rightMargin],
              bg=BRAND_LIGHT)
    ]))

    elements.append(Spacer(1, 6*mm))
    elements.append(KeepTogether([
        Paragraph("30 дней — сделать поток стабильным", h2),
        _card([[Paragraph(bullets(plan_30), body)]],
              [A4[0] - doc.leftMargin - doc.rightMargin],
              bg=BRAND_LIGHT)
    ]))

    elements.append(PageBreak())

    # =========================
    # PAGE 5 — About us
    # =========================
    elements.append(Paragraph("О нас", title))

    elements.append(_card(
        [[Paragraph(
            "<b>Shift Motion</b> — коммуникационное агентство. Мы строим управляемый маркетинг: "
            "стратегия → упаковка → внедрение → рост метрик.",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=BRAND_LIGHT,
        pad=12
    ))
    elements.append(Spacer(1, 8*mm))

    about_points = [
        "Фокус: лидогенерация и системная воронка (а не «вести соцсети»).",
        "Работаем через гипотезы, смыслы, структуру касаний, оффер и каналы.",
        "На выходе: план внедрения на 2–4 недели + измеримые KPI."
    ]
    elements.append(_card(
        [[Paragraph("<b>Как мы работаем</b><br/>" + "<br/>".join([f"• {x}" for x in about_points]), body)]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=colors.HexColor("#FBFAF4"),
        pad=12
    ))

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("Следующий шаг", h2))

    # CTA dark block
    cta = _card(
        [[Paragraph(
            "Хотите персональную карту роста? Мы проведём 30-минутный разбор и дадим 10–15 конкретных действий на ближайшие 2 недели.",
            cta_white
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=BRAND_TEAL,
        pad=12
    )
    elements.append(cta)

    elements.append(Spacer(1, 8*mm))
    elements.append(_card(
        [[Paragraph(f"<b>Контакт:</b> {phone}", body)],
         [Paragraph("Напишите «разбор» — мы предложим ближайшие слоты.", muted)]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=BRAND_LIGHT,
        pad=12
    ))

    elements.append(PageBreak())

    # =========================
    # PAGE 6 — Case
    # =========================
    elements.append(Paragraph("Кейс (пример логики работы)", title))
    elements.append(Paragraph("Мы показываем формат: как из диагностики делаем план и рост заявок.", muted))
    elements.append(Spacer(1, 6*mm))

    # Без конкретных цифр/брендов, чтобы не врать — но структура «кейс-сторителлинг»
    case_blocks = [
        ("Запрос", "Нужны стабильные обращения, а заявки приходят «волнами»."),
        ("Проблема", "Нет связки «оффер → прогрев → CTA», один источник лидов, слабая упаковка первого экрана."),
        ("Что сделали", "Собрали оффер и линейку, прописали прогревы, усилили доверие кейсами/процессом, настроили источники лидов."),
        ("Результат", "Появился управляемый поток обращений и понятные метрики: заявки/конверсия/стоимость.")
    ]
    rows = []
    for t, d in case_blocks:
        rows.append([Paragraph(f"<b>{t}</b>", body), Paragraph(d, body)])

    case_table = Table(
        rows,
        colWidths=[38*mm, (A4[0] - doc.leftMargin - doc.rightMargin) - 38*mm]
    )
    case_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, colors.HexColor("#FBFAF4")]),
        ("BOX", (0, 0), (-1, -1), 0.9, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))

    elements.append(case_table)
    elements.append(Spacer(1, 10*mm))

    elements.append(_card(
        [[Paragraph(
            "Если хотите — мы сделаем такой же разбор под ваш проект и соберём план внедрения на 2 недели.",
            body
        )]],
        col_widths=[A4[0] - doc.leftMargin - doc.rightMargin],
        bg=BRAND_LIGHT,
        pad=12
    ))

    # =========================
    # Build
    # =========================
    onpage = _make_onpage(logo_reader, FONT_BOLD)
    doc.build(elements, onFirstPage=onpage, onLaterPages=onpage)

    buffer.seek(0)
    return buffer