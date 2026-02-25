from io import BytesIO
import os
from typing import Dict, Any, List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
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
BRAND_CREAM = colors.HexColor("#f6f5ea")
BRAND_TEAL = colors.HexColor("#024a68")
BORDER = colors.HexColor("#D6D3C8")
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

def _loss_range(score: int) -> str:
    if score <= 3:
        return "25–45%"
    if score <= 6:
        return "15–35%"
    return "8–20%"

def _card(rows, width, bg=colors.white, pad=14):
    t = Table(rows, colWidths=[width], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t

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


def _build_recommendations_universal(data: Dict[str, Any]) -> List[str]:
    """
    Универсальные рекомендации (не требуют, чтобы клиент заполнял оффер/продуктовую линейку).
    Мы всё равно мягко учитываем ответы (источник/стабильность/гео/стратегия/бюджет),
    но формулировки универсальные и применимы почти всем.
    """
    strategy = _safe(data.get("strategy"))
    source = _safe(data.get("source"))
    stability = _safe(data.get("stability"))
    geo = _safe(data.get("geo"))
    budget = _safe(data.get("budget"))

    rec: List[str] = []

    # 1) Управляемость и учет
    rec.append("Ввести учет обращений: источник, дата, статус, причина отказа. Это дает рычаг управления, а не ощущение “волнами”.")

    # 2) Скорость обработки
    rec.append("Настроить регламент обработки: время ответа, скрипт первого сообщения, следующий шаг (созвон/бриф/предоплата).")

    # 3) Понятный путь до заявки
    rec.append("Собрать 1–2 стабильные точки входа в заявку: кнопка/форма/директ/телефон + единый CTA, чтобы не распылять внимание.")

    # 4) Контент/доверие (универсально, без оффера)
    rec.append("Собрать базовые блоки доверия: кейсы, процесс работы, ответы на вопросы, социальное доказательство (отзывы/результаты).")

    # 5) Источники (адаптивно)
    if source in ("Сарафан", "Нестабильно"):
        rec.append("Добавить управляемый источник обращений (контент/реклама/партнерства), чтобы снизить зависимость от случайных рекомендаций.")
    else:
        rec.append("Проверить качество основного канала: откуда приходят обращения и где теряется конверсия на пути к записи/покупке.")

    # 6) Стабильность (адаптивно)
    if stability in ("Нет", "Иногда"):
        rec.append("Ввести недельный контур управления: план активностей и контроль результата раз в 7 дней (что сделали → что получили).")
    else:
        rec.append("Закрепить стабильность: держать минимум активностей/касаний в неделю и не допускать провалов по регулярности.")

    # 7) Гео (адаптивно)
    if geo in ("Нет", "Есть, но не продвигаем"):
        rec.append("Если бизнес локальный: оформить карточки в Яндекс/2ГИС и поддерживать актуальность (услуги, фото, отзывы, ответы).")
    else:
        rec.append("Если гео уже ведется: измерять вклад — сколько обращений/звонков/маршрутов приходит из карточек.")

    # 8) Стратегия/KPI (универсально)
    if strategy in ("Нет", "Частично"):
        rec.append("Зафиксировать цель на 30 дней и 2 метрики: обращения и конверсия в запись/покупку. Этого достаточно для управления.")
    else:
        rec.append("Уточнить KPI: что считаем обращением, где фиксируем, и как принимаем решения раз в неделю по цифрам.")

    # 9) Бюджет (без конкретных сумм в расчетах)
    rec.append(f"Бюджет: {budget}. Разделить усилия на 2 части: стабильная база (регулярность) + тесты (1–2 гипотезы в неделю).")

    # Чтобы влезало на 1 страницу: 7–9 пунктов максимум
    if len(rec) > 9:
        rec = rec[:9]
    return rec


# =========================
# Header
# =========================
def _make_onpage(logo_reader, font_bold: str):
    def _on_page(canvas, doc):
        canvas.saveState()

        # фон страницы
        canvas.setFillColor(BRAND_CREAM)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

        # верхняя полоса
        bar_h = 16 * mm
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, A4[1] - bar_h, A4[0], bar_h, stroke=0, fill=1)

        # лого: без плашки, прозрачность через mask="auto"
        if logo_reader is not None:
            try:
                img_w, img_h = logo_reader.getSize()
                ratio = (img_w / img_h) if img_h else 3.0

                target_h = 10.0 * mm
                target_w = min(52.0 * mm, target_h * ratio)

                x = doc.leftMargin
                y = A4[1] - bar_h + (bar_h - target_h) / 2

                try:
                    canvas.drawImage(
                        logo_reader,
                        x, y,
                        width=target_w,
                        height=target_h,
                        preserveAspectRatio=True,
                        mask="auto"
                    )
                except Exception:
                    canvas.drawImage(
                        logo_reader,
                        x, y,
                        width=target_w,
                        height=target_h,
                        preserveAspectRatio=True
                    )
            except Exception as e:
                print(f"[PDF] Logo draw error: {e}")

        # номер страницы
        canvas.setFillColor(BRAND_GRAPHITE)
        canvas.setFont(font_bold, 9)
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"стр. {canvas.getPageNumber()}")

        canvas.restoreState()
    return _on_page


# =========================
# MAIN
# =========================
def generate_pdf(data: Dict[str, Any], segment: str):
    """
    segment приходит из main, но В PDF НЕ выводим.
    """
    buffer = BytesIO()

    # Надежно для Render
    base_path = os.path.dirname(os.path.abspath(__file__))

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
            print(f"[PDF] Logo loaded: {logo_abs} ({os.path.getsize(logo_abs)} bytes)")
        except Exception as e:
            print(f"[PDF] Logo read error: {logo_abs} -> {e}")
            logo_reader = None
    else:
        print(f"[PDF] Logo missing/empty: {logo_abs}")

    # Doc
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
        title="Shift Motion — Диагностика",
        author="Shift Motion",
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=20,
        leading=24,
        textColor=BRAND_GRAPHITE,
    )

    h2 = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14.5,
        leading=19,
        textColor=BRAND_GRAPHITE,
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=FONT_REG,
        fontSize=11.3,
        leading=17,
        textColor=BRAND_GRAPHITE,
    )

    muted = ParagraphStyle(
        "Muted",
        parent=body,
        textColor=colors.HexColor("#5B5F62"),
        fontSize=10.6,
        leading=16,
    )

    cta_white = ParagraphStyle(
        "CTAWhite",
        parent=body,
        textColor=colors.white,
    )

    # Data
    score = int(data.get("score", 0) or 0)
    loss = _loss_range(score)

    city = _safe(data.get("city"))
    niche = _safe(data.get("niche"))
    role = _safe(data.get("role"))
    budget = _safe(data.get("budget"))
    strategy = _safe(data.get("strategy"))
    source = _safe(data.get("source"))
    stability = _safe(data.get("stability"))
    geo = _safe(data.get("geo"))

    width = A4[0] - doc.leftMargin - doc.rightMargin
    elements: List[Any] = []

    # =========================
    # PAGE 1
    # =========================
    elements.append(Paragraph("Shift Motion — маркетинговая диагностика", title))
    elements.append(Spacer(1, 8 * mm))

    # ✅ Ровная таблица: 2 колонки (метка/значение), никаких узких ячеек
    meta_rows = [
        [Paragraph("Город", muted), Paragraph(city, body)],
        [Paragraph("Ниша", muted), Paragraph(niche, body)],
        [Paragraph("Роль", muted), Paragraph(role, body)],
        [Paragraph("Бюджет", muted), Paragraph(budget, body)],
        [Paragraph("Стратегия", muted), Paragraph(strategy, body)],
    ]
    meta = Table(meta_rows, colWidths=[28 * mm, width - 28 * mm], hAlign="LEFT")
    meta.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(meta)
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(f"Результат: <b>{score}/10</b>", h2))
    elements.append(Paragraph(f"Оценка потерь: <b>{loss}</b> потенциальных обращений.", body))
    elements.append(Spacer(1, 6 * mm))
    elements.append(_progress_bar(score))
    elements.append(Spacer(1, 10 * mm))

    summary = f"Источник обращений: <b>{source}</b>. Стабильность: <b>{stability}</b>. Гео (Яндекс/2ГИС): <b>{geo}</b>."
    elements.append(_card([[Paragraph(summary, body)]], width, bg=colors.white))

    elements.append(PageBreak())

    # =========================
    # PAGE 2
    # =========================
    elements.append(Paragraph("Рекомендации (универсальные приоритеты)", title))
    elements.append(Spacer(1, 6 * mm))

    recs = _build_recommendations_universal(data)
    rec_text = "<br/>".join([f"• {r}" for r in recs])
    elements.append(_card([[Paragraph(rec_text, body)]], width, bg=colors.white))

    elements.append(Spacer(1, 10 * mm))

    elements.append(_card(
        [[Paragraph(
            "Следующий шаг: 30-минутная сессия. Мы уточним контекст, зафиксируем приоритеты и дадим план внедрения на 14 дней.",
            cta_white
        )]],
        width,
        bg=BRAND_TEAL
    ))

    # Build
    onpage = _make_onpage(logo_reader, FONT_BOLD)
    doc.build(elements, onFirstPage=onpage, onLaterPages=onpage)

    buffer.seek(0)
    return buffer