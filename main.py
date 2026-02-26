# =========================
# MAIN.PY — ПОЛНАЯ ВЕРСИЯ (ФИНАЛ)
# ✅ Сегмент НЕ показываем клиенту нигде
# ✅ Сегмент остаётся только в сообщении менеджеру (AGENCY_CHAT_ID)
# ✅ 2 кнопки после PDF + кейсы текстом
# ✅ Ник + телефон приводим к надежному виду
# =========================

print("MAIN FILE LOADED")

import os
import logging
from datetime import datetime
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, AGENCY_USERNAME, AGENCY_CHAT_ID
from scoring import calculate_score, get_segment
from pdf_report import generate_pdf
from db import init_db, save_lead

logging.basicConfig(level=logging.INFO)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://marketing-bot-tb33.onrender.com/webhook"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# STATES
# =========================
class Diagnostic(StatesGroup):
    role = State()
    city = State()
    niche = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()
    budget = State()
    contact = State()


# =========================
# UI HELPERS
# =========================
def kb(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )


def contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Поделиться контактом", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ✅ Только 2 кнопки: написать + бриф
def post_pdf_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📩 Написать в Shift Motion", url=f"https://t.me/{AGENCY_USERNAME}")],
            [InlineKeyboardButton(text="📋 Заполнить бриф", url="https://shiftmotion.ru/brief")]
        ]
    )


# =========================
# CONTACT HELPERS (ник + телефон)
# =========================
def _normalize_phone(phone):
    """
    Приводим к единому виду:
    - убираем пробелы/скобки/дефисы
    - если начинается с 00 -> меняем на +
    - если только цифры -> добавляем +
    """
    if not phone:
        return "—"
    p = str(phone).strip()
    for ch in [" ", "-", "(", ")", "\u00A0"]:
        p = p.replace(ch, "")
    if p.startswith("00"):
        p = "+" + p[2:]
    if not p.startswith("+") and p.isdigit():
        p = "+" + p
    return p


def _tg_contact_line(message: Message) -> str:
    """
    Надежная идентификация:
    - если есть username -> @username
    - если нет -> "Имя (tg://user?id=...)" — кликается в большинстве клиентов Telegram
    """
    u = message.from_user
    if u.username:
        return f"@{u.username}"
    name = (u.full_name or "Пользователь").strip()
    return f"{name} (tg://user?id={u.id})"


# =========================
# LEADGEN FOLLOW-UP (тон "мы") — БЕЗ СЕГМЕНТА
# =========================
def leadgen_followup_text(score: int) -> str:
    """
    Клиенту мы не "пришиваем" жёсткие диагнозы. Формулировки мягче и экологичнее.
    """
    if score >= 7:
        level = "сильная база"
        pain = "Сейчас логичнее всего докрутить конверсию и усилить 1–2 канала, чтобы масштабировать без перегруза."
        offer = "На 30-минутной сессии мы покажем, где быстрее всего вырастут обращения и что делать в ближайшие 14 дней."
    elif score >= 4:
        level = "есть фундамент, но рост не всегда управляем"
        pain = "Чаще всего обращения идут волнами: не хватает связки «контент → доверие → действие», из-за этого теряется часть аудитории."
        offer = "На 30-минутном разборе мы соберём мини-контур управления и дадим план действий на 7–14 дней."
    else:
        level = "систему можно усилить"
        pain = "Обычно теряются обращения на маршруте: вход → обработка → повторное касание → конверсия."
        offer = "За 30 минут мы покажем 3 быстрые правки, которые дадут первые стабильные результаты."

    return (
        f"Короткий вывод по результату: *{score}/10*.\n"
        f"Уровень: *{level}*.\n\n"
        f"{pain}\n\n"
        f"{offer}"
    )


# =========================
# FLOW
# =========================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Маркетинговая диагностика Shift Motion.\n\nКто вы?",
        reply_markup=kb(["Собственник", "Личный бренд", "Маркетолог"])
    )
    await state.set_state(Diagnostic.role)


@dp.message(Diagnostic.role)
async def q_role(message: Message, state: FSMContext):
    await state.update_data(role=message.text)
    await message.answer("В каком городе вы работаете?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Diagnostic.city)


@dp.message(Diagnostic.city)
async def q_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(
        "В какой сфере работает ваш бизнес?",
        reply_markup=kb([
            "Бьюти / Салон",
            "Эксперт / Онлайн",
            "Услуги",
            "E-commerce",
            "Производство",
            "Другое"
        ])
    )
    await state.set_state(Diagnostic.niche)


@dp.message(Diagnostic.niche)
async def q_niche(message: Message, state: FSMContext):
    await state.update_data(niche=message.text)
    await message.answer("Есть ли маркетинговая стратегия?", reply_markup=kb(["Да", "Частично", "Нет"]))
    await state.set_state(Diagnostic.strategy)


@dp.message(Diagnostic.strategy)
async def q_strategy(message: Message, state: FSMContext):
    await state.update_data(strategy=message.text)
    await message.answer("Основной источник заявок?", reply_markup=kb(["Реклама", "Соцсети", "Сарафан", "Нестабильно"]))
    await state.set_state(Diagnostic.source)


@dp.message(Diagnostic.source)
async def q_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    await message.answer("Есть ли стабильный поток заявок?", reply_markup=kb(["Да", "Иногда", "Нет"]))
    await state.set_state(Diagnostic.stability)


@dp.message(Diagnostic.stability)
async def q_stability(message: Message, state: FSMContext):
    await state.update_data(stability=message.text)
    await message.answer(
        "Есть ли карточка в Яндекс/2ГИС?",
        reply_markup=kb(["Да, продвигаем", "Есть, но не продвигаем", "Нет"])
    )
    await state.set_state(Diagnostic.geo)


@dp.message(Diagnostic.geo)
async def q_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    await message.answer(
        "Какой маркетинговый бюджет в месяц?",
        reply_markup=kb(["до 50 тыс", "50–150 тыс", "150–300 тыс", "300+ тыс"])
    )
    await state.set_state(Diagnostic.budget)


@dp.message(Diagnostic.budget)
async def finish_before_contact(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    data = await state.get_data()

    data["brand"] = "Shift Motion"
    data["telegram_id"] = message.from_user.id
    data["username"] = message.from_user.username or ""
    data["full_name"] = message.from_user.full_name or ""

    score = calculate_score(data)
    segment = get_segment(score)

    # сохраняем в state для внутренней логики + менеджера
    await state.update_data(score=score, segment=segment, brand="Shift Motion")

    await message.answer(
        "Чтобы получить персональный PDF-разбор, пожалуйста, поделитесь контактом.",
        reply_markup=contact_kb()
    )
    await state.set_state(Diagnostic.contact)


@dp.message(Diagnostic.contact)
async def receive_contact(message: Message, state: FSMContext):

    if not message.contact:
        await message.answer("Используйте кнопку для передачи контакта.")
        return

    data = await state.get_data()

    raw_phone = message.contact.phone_number
    phone = _normalize_phone(raw_phone)

    # проверка: контакт "свой" или "чужой"
    is_own_contact = (message.contact.user_id == message.from_user.id)

    data["phone"] = phone
    data["is_own_contact"] = is_own_contact

    save_lead(data)

    score = int(data.get("score", 0) or 0)
    segment = data.get("segment", "—")  # ✅ сегмент только менеджеру

    if score >= 7:
        priority = "🔥 HIGH"
    elif score >= 4:
        priority = "⚡ MEDIUM"
    else:
        priority = "LOW"

    tg_line = _tg_contact_line(message)

    # ✅ Уведомление менеджеру (сегмент оставляем)
    await bot.send_message(
        AGENCY_CHAT_ID,
        f"""🔥 Новый лид — Диагностика Shift Motion

📊 Сегмент: {segment}
📈 Внутренняя оценка: {score}/10
🎯 Приоритет: {priority}

📞 Телефон: {phone}{" (контакт не совпадает с аккаунтом)" if not is_own_contact else ""}
👤 Telegram: {tg_line}
🆔 Telegram ID: {data.get("telegram_id")}

🌍 Город: {data.get("city")}
🏷 Ниша: {data.get("niche")}

👤 Роль: {data.get("role")}
💰 Бюджет: {data.get("budget")}
🧠 Стратегия: {data.get("strategy")}
📍 Гео: {data.get("geo")}
📥 Источник: {data.get("source")}
📊 Стабильность: {data.get("stability")}
"""
    )

    # --- PDF (safe) ---
    try:
        # segment передаём по сигнатуре, но в клиентском PDF он НЕ выводится
        pdf_buffer = generate_pdf(data, segment)
        dt = datetime.now().strftime("%Y-%m-%d")
        filename = f"ShiftMotion_report_{dt}.pdf"

        await message.answer_document(
            BufferedInputFile(pdf_buffer.read(), filename=filename),
            caption="📄 Ваш персональный маркетинговый разбор готов."
        )
    except Exception as e:
        logging.exception("PDF generation failed: %s", e)
        await message.answer(
            "PDF сейчас не удалось сформировать из-за технической ошибки. "
            "Мы уже получили ваши ответы — мы свяжемся с вами и пришлём разбор."
        )

    # --- One screen CTA: 2 buttons + cases text (no segment) ---
    cases_line = "Кейсы: shiftmotion.ru/cases"
    await message.answer(
        leadgen_followup_text(score) + f"\n\n{cases_line}",
        parse_mode="Markdown",
        reply_markup=post_pdf_menu()
    )

    await state.clear()


# =========================
# WEBHOOK
# =========================
async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    print("WEBHOOK SET")


def main():
    init_db()
    app = web.Application()
    dp.startup.register(on_startup)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()