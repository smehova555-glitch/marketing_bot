print("MAIN FILE LOADED")

import asyncio
import os
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State

from config import BOT_TOKEN, AGENCY_USERNAME, AGENCY_CHAT_ID
from scoring import calculate_score, get_segment
from recommendations import generate_recommendations
from pdf_report import generate_pdf
from db import init_db, save_lead

from aiohttp import web

logging.basicConfig(level=logging.INFO)

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
    contact = State()   # 🔥 обязательный контакт


# =========================
# KEYBOARDS
# =========================

def kb(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )


def contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📲 Поделиться контактом",
                request_contact=True
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def post_pdf_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Заполнить бриф",
                    url="https://shiftmotion.ru/brief"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Записаться",
                    url=f"https://t.me/{AGENCY_USERNAME}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Кейсы",
                    url="https://shiftmotion.ru/cases"
                )
            ]
        ]
    )


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Диагностика маркетинга Shift Motion.\n\nКто вы?",
        reply_markup=kb(["Собственник", "Личный бренд", "Маркетолог"])
    )

    await state.set_state(Diagnostic.role)


# =========================
# QUESTIONS
# =========================

@dp.message(Diagnostic.role)
async def q_role(message: Message, state: FSMContext):
    await state.update_data(role=message.text)

    await message.answer(
        "В каком городе или регионе вы работаете?",
        reply_markup=ReplyKeyboardRemove()
    )

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

    await message.answer(
        "Есть ли маркетинговая стратегия?",
        reply_markup=kb(["Да", "Частично", "Нет"])
    )

    await state.set_state(Diagnostic.strategy)


@dp.message(Diagnostic.strategy)
async def q_strategy(message: Message, state: FSMContext):
    await state.update_data(strategy=message.text)

    await message.answer(
        "Основной источник заявок?",
        reply_markup=kb(["Реклама", "Соцсети", "Сарафан", "Нестабильно"])
    )

    await state.set_state(Diagnostic.source)


@dp.message(Diagnostic.source)
async def q_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text)

    await message.answer(
        "Есть ли стабильный поток заявок?",
        reply_markup=kb(["Да", "Иногда", "Нет"])
    )

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


# =========================
# ПЕРЕД КОНТАКТОМ
# =========================

@dp.message(Diagnostic.budget)
async def finish_before_contact(message: Message, state: FSMContext):

    await state.update_data(budget=message.text)
    data = await state.get_data()

    data["telegram_id"] = message.from_user.id
    data["username"] = message.from_user.username

    score = calculate_score(data)
    segment = get_segment(score)

    await state.update_data(score=score, segment=segment)

    await message.answer(
        "Чтобы получить персональный PDF-разбор, пожалуйста, поделитесь контактом.",
        reply_markup=contact_kb()
    )

    await state.set_state(Diagnostic.contact)


# =========================
# ПОЛУЧЕНИЕ КОНТАКТА
# =========================

@dp.message(Diagnostic.contact)
async def receive_contact(message: Message, state: FSMContext):

    if not message.contact:
        await message.answer("Пожалуйста, используйте кнопку для передачи контакта.")
        return

    data = await state.get_data()

    phone = message.contact.phone_number
    data["phone"] = phone

    score = data["score"]
    segment = data["segment"]

    save_lead(data)

    # 🔥 Приоритет
    if score >= 7:
        priority = "🔥 HIGH"
    elif score >= 4:
        priority = "⚡ MEDIUM"
    else:
        priority = "LOW"

    # ===== Отправка менеджеру =====
    try:
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
    except Exception as e:
        print("ERROR SENDING LEAD:", e)

    # ===== PDF =====
    pdf_path = generate_pdf(data, segment)

    if pdf_path and os.path.exists(pdf_path):
        await message.answer_document(
            FSInputFile(os.path.abspath(pdf_path)),
            caption="📄 Ваш персональный маркетинговый разбор готов."
        )

    await message.answer(
        "Спасибо! Менеджер свяжется с вами в ближайшее время.",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        "Что делаем дальше?",
        reply_markup=post_pdf_menu()
    )

    await state.clear()


# =========================
# HEALTHCHECK (Render)
# =========================

async def healthcheck(request):
    return web.Response(text="Bot is running")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", healthcheck)

    port = int(os.environ.get("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    init_db()
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())