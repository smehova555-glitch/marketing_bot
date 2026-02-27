from io import BytesIO
import os
from typing import Dict, Any, Tuple, List

import re
import html

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
BRAND_CREAM = colors.HexColor("#f6f5ea")  # если "слишком белый" — тест: #FFE4E6
BRAND_TEAL = colors.HexColor("#024a68")
BORDER = colors.HexColor("#D6D3C8")
GREY_200 = colors.HexColor("#E5E7EB")
MUTED_TEXT = colors.HexColor("#5B5F62")

LOGO_PATH = os.path.join("assets", "shift_logo.png")


# =========================
# Helpers
# =========================
def _safe(v, default="—"):
    if v is None or v == "":
        return default
    return str(v)


def _clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def _quotes(text: str) -> str:
    """
    Приводит любые кавычки к «».
    Ловит: ", “ ”, „ ‟, &quot;, а также уже существующие «».
    """
    if not text:
        return ""

    t = html.unescape(str(text))

    # нормализация “умных” кавычек
    t = (
        t.replace("“", "«")
         .replace("”", "»")
         .replace("„", "«")
         .replace("‟", "«")
    )

    # пары прямых кавычек "..." -> «...»
    t = re.sub(r'"([^"]+)"', r'«\1»', t)

    # если остались одиночные " — заменим по очереди: « потом »
    if '"' in t:
        out = []
        open_q = True
        for ch in t:
            if ch == '"':
                out.append("«" if open_q else "»")
                open_q = not open_q
            else:
                out.append(ch)
        t = "".join(out)

    # одинарные кавычки -> ’
    t = t.replace("‘", "’").replace("’", "’").replace("'", "’")

    return t


def _stage_from_score(score: int) -> Tuple[str, str]:
    score = _clamp(int(score), 0, 10)
    if score <= 3:
        return (
            "Этап 1. Система формируется",
            "Сейчас маркетинг работает точечно. Наша задача — собрать управляемый контур, чтобы обращения стали предсказуемыми."
        )
    if score <= 6:
        return (
            "Этап 2. Есть база, нужен контур управления",
            "Основа уже есть. Следующий шаг — закрепить стабильные каналы, измеримость и регулярность действий."
        )
    if score <= 8:
        return (
            "Этап 3. Система работает, можно масштабировать",
            "Есть понятная логика привлечения. Рост даст оптимизация конверсии и расширение каналов."
        )
    return (
        "Этап 4. Уровень роста и оптимизации",
        "Система зрелая. Фокус — эффективность, повышение LTV и масштабирование лучших связок."
    )


def _progress_bar(score: int, width=160 * mm, height=8 * mm):
    score = _clamp(int(score), 0, 10)
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


def _meta_table(data: Dict[str, Any], width, body, muted):
    rows = [
        [Paragraph("Город", muted), Paragraph(_quotes(_safe(data.get("city"))), body)],
        [Paragraph("Ниша", muted), Paragraph(_quotes(_safe(data.get("niche"))), body)],
        [Paragraph("Роль", muted), Paragraph(_quotes(_safe(data.get("role"))), body)],
        [Paragraph("Бюджет", muted), Paragraph(_quotes(_safe(data.get("budget"))), body)],
        [Paragraph("Стратегия", muted), Paragraph(_quotes(_safe(data.get("strategy"))), body)],
        [Paragraph("Источник", muted), Paragraph(_quotes(_safe(data.get("source"))), body)],
        [Paragraph("Стабильность", muted), Paragraph(_quotes(_safe(data.get("stability"))), body)],
        [Paragraph("Гео (Яндекс/2ГИС)", muted), Paragraph(_quotes(_safe(data.get("geo"))), body)],
    ]

    t = Table(rows, colWidths=[38 * mm, width - 38 * mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _make_onpage(logo_reader):
    """
    Фон/полоса/лого рисуются на каждой странице: onFirstPage + onLaterPages.
    """
    def _on_page(canvas, doc):
        canvas.saveState()

        page_w, page_h = doc.pagesize

        # фон
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)

        # верхняя полоса
        bar_h = 22 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, page_h - bar_h, page_w, bar_h, stroke=0, fill=1)

        # лого
        if logo_reader is not None:
            try:
                logo_h = 15 * mm
                x = doc.leftMargin
                y = page_h - bar_h + (bar_h - logo_h) / 2
                canvas.drawImage(
                    logo_reader,
                    x, y,
                    height=logo_h,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except Exception as e:
                print("LOGO DRAW ERROR:", repr(e))

        canvas.restoreState()

    return _on_page


def _build_growth_zones_universal(data: Dict[str, Any]) -> List[str]:
    stability = _safe(data.get("stability"))
    geo = _safe(data.get("geo"))
    strategy = _safe(data.get("strategy"))

    zones: List[str] = []
    zones.append("Учёт обращений и управляемость: фиксировать источник, статус, причину отказа и следующий шаг.")
    zones.append("Скорость обработки: регламент первого ответа и сценарий повторного касания (чтобы обращения не “остывали”).")
    zones.append("Единый маршрут до действия: одна понятная точка входа + единый CTA (без распыления на разные варианты).")

    if stability in ("Нет", "Иногда", "Нестабильно"):
        zones.append("Стабильность: недельный цикл управления (план → действия → цифры → корректировка), чтобы убрать эффект “волнами”.")
    else:
        zones.append("Стабильность: закрепить регулярность и измерять вклад каждого канала (что даёт обращения, а что создаёт шум).")

    if geo in ("Нет", "Есть, но не продвигаем"):
        zones.append("Если бизнес локальный: оформить/усилить карточки Яндекс/2ГИС (фото, услуги, отзывы, ответы) как отдельный канал спроса.")
    else:
        zones.append("Если гео уже ведётся: считать вклад карточек (звонки/маршруты/переходы) и дожимать конверсию в обращение.")

    if strategy in ("Нет", "Частично"):
        zones.append("Мини-стратегия на 30 дней: цель + 2 метрики (обращения и конверсия в запись/покупку) — этого достаточно для управления.")
    else:
        zones.append("Стратегия: уточнить KPI и правила принятия решений раз в неделю на цифрах (что оставляем, что усиливаем, что выключаем).")

    return zones[:6]


# =========================
# MAIN
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):
    """
    ✅ Фирменный фон/полоса/лого — на ВСЕХ страницах
    ✅ Шрифт крупнее
    ✅ Лого не “пропадает”: абсолютный путь + логирование
    ✅ Кавычки только «»
    """
    buffer = BytesIO()
    base_path = os.path.dirname(os.path.abspath(__file__))

    # DEBUG (временно): чтобы видеть в Render logs, что грузится именно этот файл
    print("PDF_REPORT LOADED FROM:", __file__)

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
            print("LOGO LOADED:", logo_abs)
        except Exception as e:
            print("LOGO READ ERROR:", repr(e))
            logo_reader = None
    else:
        print("LOGO NOT FOUND:", logo_abs)

    # Doc
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=34 * mm,   # чтобы контент не залезал в верхнюю полосу
        bottomMargin=20 * mm,
        title="Shift Motion — Маркетинговая диагностика",
        author="Shift Motion",
    )

    styles = getSampleStyleSheet()

    # Styles (крупнее)
    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=27,
        textColor=BRAND_GRAPHITE,
        spaceAfter=6 * mm
    )

    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=16,
        leading=21,
        textColor=BRAND_GRAPHITE,
        spaceAfter=1.5 * mm
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=13.5,
        leading=18.5,
        textColor=BRAND_GRAPHITE,
    )

    muted = ParagraphStyle(
        "Muted",
        parent=body,
        textColor=MUTED_TEXT,
        fontSize=12,
        leading=17,
    )

    # Score (внутренний)
    score = int(data.get("score", 0) or 0)
    stage_title, stage_text = _stage_from_score(score)

    width = A4[0] - doc.leftMargin - doc.rightMargin
    elements = []

    # Заголовок
    elements.append(Paragraph(
        _quotes("Маркетинговая диагностика от коммуникационного агентства Shift Motion"),
        title
    ))

    # Вводные
    elements.append(_meta_table(data, width, body, muted))
    elements.append(Spacer(1, 7 * mm))

    # Этап + шкала
    elements.append(Paragraph(_quotes(stage_title), h2))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(_quotes(stage_text), body))
    elements.append(Spacer(1, 5 * mm))
    elements.append(Paragraph(
        _quotes("Визуальная шкала зрелости системы (ваша текущая точка отмечена цветом):"),
        muted
    ))
    elements.append(Spacer(1, 3 * mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 7 * mm))

    # Зоны роста
    elements.append(Paragraph(_quotes("Стратегические зоны роста (универсальные):"), h2))
    elements.append(Spacer(1, 3 * mm))

    zones = _build_growth_zones_universal(data)
    zones_html = "<br/>".join([_quotes(f"• {z}") for z in zones])

    card = Table([[Paragraph(zones_html, body)]], colWidths=[width], hAlign="LEFT")
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(card)
    elements.append(Spacer(1, 7 * mm))

    # CTA
    cta_text = _quotes(
        "Если хотите — проведем 30-минутную стратегическую сессию: "
        "уточним контекст, выделим приоритеты и соберем план внедрения на 14 дней."
    )
    cta_style = ParagraphStyle("CTA", parent=body, fontName=FONT_BOLD, textColor=colors.white)

    cta = Table([[Paragraph(cta_text, cta_style)]], colWidths=[width], hAlign="LEFT")
    cta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_TEAL),
        ("BOX", (0, 0), (-1, -1), 0, BRAND_TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(cta)

    print("PDF BUILD HOOKS: onFirstPage+onLaterPages enabled")

    # Build — ВАЖНО: onLaterPages тоже!
    onpage = _make_onpage(logo_reader)
    doc.build(
        elements,
        onFirstPage=onpage,
        onLaterPages=onpage
    )

    buffer.seek(0)
    return buffer