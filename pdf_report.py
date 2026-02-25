from io import BytesIO
import os
from typing import Dict, Any, List, Tuple

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

def _priority(score: int) -> str:
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"

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


def _build_recommendations(data: Dict[str, Any]) -> List[str]:
    """
    Рекомендации строго на основе того, что клиент заполнил:
    strategy, source, stability, geo, budget (+ score для приоритета).
    Никаких «офферов», «упаковки линейки» и т.п.
    """
    strategy = _safe(data.get("strategy"))
    source = _safe(data.get("source"))
    stability = _safe(data.get("stability"))
    geo = _safe(data.get("geo"))
    budget = _safe(data.get("budget"))
    score = int(data.get("score", 0) or 0)

    rec: List[str] = []

    # 1) Стратегия
    if strategy in ("Нет",):
        rec.append("Зафиксировать базовую маркетинговую цель на 30 дней и 2 ключевых метрики: обращения и конверсию в запись/покупку.")
    elif strategy in ("Частично",):
        rec.append("Дособрать стратегию: один приоритетный канал + один резервный, и план тестов на 2 недели.")
    elif strategy in ("Да",):
        rec.append("Уточнить KPI по стратегии: что считаем обращением, где фиксируем, как контролируем динамику еженедельно.")

    # 2) Источник заявок
    if source == "Сарафан":
        rec.append("Добавить управляемый источник обращений (контент/реклама/партнерства), чтобы снизить зависимость от сарафана.")
    elif source == "Соцсети":
        rec.append("Сделать поток обращений измеримым: точки входа, CTA, учёт обращений и причины потерь.")
    elif source == "Реклама":
        rec.append("Проверить качество потока: откуда приходят обращения, как быстро обрабатываются, где падает конверсия.")
    elif source == "Нестабильно":
        rec.append("Стабилизировать источники: выбрать 2 канала и закрепить регулярность (минимум 2 недели без провалов).")

    # 3) Стабильность
    if stability in ("Иногда", "Нет"):
        rec.append("Внедрить недельный контур управления: план касаний/активностей и контроль результата раз в 7 дней.")
    else:
        rec.append("Усилить предсказуемость: зафиксировать минимум обращений в неделю и держать его через 2 источника.")

    # 4) Гео
    if geo == "Нет":
        rec.append("Если бизнес локальный: завести карточки в Яндекс/2ГИС и заполнить профиль (услуги, фото, часы, контакты).")
    elif geo == "Есть, но не продвигаем":
        rec.append("Если бизнес локальный: включить гео как канал спроса — отзывы, фото, актуальные услуги, регулярные обновления.")
    elif geo == "Да, продвигаем":
        rec.append("Продолжать гео и измерять вклад: сколько обращений/маршрутов/звонков приходит из карточек.")

    # 5) Бюджет (без советов «про оффер»)
    if budget in ("до 50 тыс",):
        rec.append("При бюджете до 50 тыс: фокус на регулярности, конверсии в обращение и усилении бесплатных точек входа.")
    elif budget in ("50–150 тыс", "150–300 тыс", "300+ тыс"):
        rec.append("При вашем бюджете: закрепить 1 основной платный источник и 1 органический, чтобы не зависеть от одного канала.")

    # подстрахуемся: максимум 6–7 пунктов, чтобы поместилось премиально
    # и минимум 4 пункта, чтобы было «не пусто»
    rec = [r for r in rec if r]
    if len(rec) > 7:
        rec = rec[:7]
    if len(rec) < 4:
        rec.append("Зафиксировать приоритеты: что делаем в первую очередь, что не делаем ближайшие 14 дней.")
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

        # лого: БЕЗ плашки, чтобы не было "квадрата".
        # Прозрачность PNG поддерживаем через mask="auto" (если PNG реально с альфой).
        if logo_reader is not None:
            try:
                img_w, img_h = logo_reader.getSize()
                ratio = (img_w / img_h) if img_h else 3.0

                target_h = 10.0 * mm
                target_w = min(52.0 * mm, target_h * ratio)

                x = doc.leftMargin
                y = A4[1] - bar_h + (bar_h - target_h) / 2

                # основной режим — прозрачность
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
                    # fallback без mask
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

    # Важно для Render: путь от файла, а не от рабочей директории процесса
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
    priority = _priority(score)

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
    # PAGE 1 — Summary (премиум, коротко)
    # =========================
    elements.append(Paragraph("Shift Motion — маркетинговая диагностика", title))
    elements.append(Spacer(1, 8 * mm))

    # компактная карточка данных (без растягивания)
    meta = Table(
        [
            [Paragraph("Город", muted), Paragraph(city, body), Paragraph("Ниша", muted), Paragraph(niche, body)],
            [Paragraph("Роль", muted), Paragraph(role, body), Paragraph("Бюджет", muted), Paragraph(budget, body)],
            [Paragraph("Стратегия", muted), Paragraph(strategy, body), Paragraph("Приоритет", muted), Paragraph(priority, body)],
        ],
        colWidths=[18*mm, 62*mm, 18*mm, 62*mm],
        hAlign="LEFT"
    )
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

    # короткий вывод только из заполненных полей
    summary_lines = [
        f"Источник обращений: <b>{source}</b>.",
        f"Стабильность: <b>{stability}</b>.",
        f"Гео (Яндекс/2ГИС): <b>{geo}</b>.",
    ]
    elements.append(_card([[Paragraph(" ".join(summary_lines), body)]], width, bg=colors.white))

    elements.append(PageBreak())

    # =========================
    # PAGE 2 — Recommendations + CTA (1 страница)
    # =========================
    elements.append(Paragraph("Рекомендации (приоритеты на 14 дней)", title))
    elements.append(Spacer(1, 6 * mm))

    recs = _build_recommendations(data)
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