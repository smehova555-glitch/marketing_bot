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


def post_pdf_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Заполнить бриф", url="https://shiftmotion.ru/brief")],
            [InlineKeyboardButton(text="📅 Записаться", url=f"https://t.me/{AGENCY_USERNAME}")],
            [InlineKeyboardButton(text="📂 Кейсы", url="https://shiftmotion.ru/cases")]
        ]
    )


def quick_cta_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Записаться на 30 минут", url=f"https://t.me/{AGENCY_USERNAME}")],
            [InlineKeyboardButton(text="📋 Заполнить бриф (если хотите агентство)", url="https://shiftmotion.ru/brief")],
        ]
    )


def leadgen_followup_text(score: int, segment: str) -> str:
    """
    Прогрев после PDF от лица агентства (тон 'мы').
    """
    if score >= 7:
        level = "сильная база"
        pain = "Сейчас логичнее всего докрутить конверсию и усилить 1–2 канала, чтобы масштабировать без хаоса."
        offer = "Мы можем за 30 минут показать, где быстрее всего вырастут заявки — без абстрактного «вести соцсети лучше»."
    elif score >= 4:
        level = "есть фундамент, но рост неуправляем"
        pain = "Чаще всего заявки идут волнами: нет связки «контент → доверие → заявка», из-за этого теряется часть аудитории."
        offer = "На 30-минутном разборе мы соберём мини-воронку и дадим план действий на 7–14 дней."
    else:
        level = "система почти не управляет заявками"
        pain = "Обычно главный слив — нет ясного оффера и понятного пути до заявки, поэтому даже сильный продукт не конвертируется."
        offer = "За 30 минут мы покажем 3 быстрые правки, которые дадут первые обращения."

    return (
        f"Короткий вывод по результату: *{score}/10* (сегмент: *{segment}*).\n"
        f"Уровень: *{level}*.\n\n"
        f"{pain}\n\n"
        f"{offer}"
    )


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Диагностика маркетинга Shift Motion.\n\nКто вы?",
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
    await message.answer("Есть ли карточка в Яндекс/2ГИС?", reply_markup=kb(["Да, продвигаем", "Есть, но не продвигаем", "Нет"]))
    await state.set_state(Diagnostic.geo)


@dp.message(Diagnostic.geo)
async def q_geo(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    await message.answer("Какой маркетинговый бюджет в месяц?", reply_markup=kb(["до 50 тыс", "50–150 тыс", "150–300 тыс", "300+ тыс"]))
    await state.set_state(Diagnostic.budget)


@dp.message(Diagnostic.budget)
async def finish_before_contact(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    data = await state.get_data()

    data["brand"] = "Shift Motion"
    data["telegram_id"] = message.from_user.id
    data["username"] = message.from_user.username

    score = calculate_score(data)
    segment = get_segment(score)

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
    phone = message.contact.phone_number
    data["phone"] = phone

    save_lead(data)

    score = int(data.get("score", 0) or 0)
    segment = data.get("segment", "—")

    if score >= 7:
        priority = "🔥 HIGH"
    elif score >= 4:
        priority = "⚡ MEDIUM"
    else:
        priority = "LOW"

    await bot.send_message(
        AGENCY_CHAT_ID,
        f"""🔥 Новый лид — Диагностика Shift Motion

📊 Сегмент: {segment}
📈 Score: {score}/10
🎯 Приоритет: {priority}

📞 Телефон: {phone}
🆔 Telegram ID: {data.get("telegram_id")}
👤 Username: @{data.get("username")}

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

    # --- Leadgen upgrade (we-tone) ---
    await message.answer(
        leadgen_followup_text(score, segment),
        parse_mode="Markdown",
        reply_markup=quick_cta_menu()
    )

    await message.answer("Что делаем дальше?", reply_markup=post_pdf_menu())

    await state.clear()


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