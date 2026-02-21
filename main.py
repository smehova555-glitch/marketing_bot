print("MAIN FILE LOADED")

import os
import logging
from aiohttp import web

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
# KEYBOARDS
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


def post_pdf_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Заполнить бриф", url="https://shiftmotion.ru/brief")],
            [InlineKeyboardButton(text="📅 Записаться", url=f"https://t.me/{AGENCY_USERNAME}")],
            [InlineKeyboardButton(text="📂 Кейсы", url="https://shiftmotion.ru/cases")]
        ]
    )


# =========================
# FLOW
# =========================

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

    score = calculate_score(data)
    segment = get_segment(score)

    await state.update_data(score=score, segment=segment)

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

    # Отправка менеджеру
    try:
        await bot.send_message(
            AGENCY_CHAT_ID,
            f"""🔥 Новый лид

📊 Сегмент: {data.get("segment")}
📈 Score: {data.get("score")}

📞 Телефон: {phone}
🆔 Telegram ID: {message.from_user.id}
👤 Username: @{message.from_user.username}
"""
        )
    except Exception as e:
        print("ERROR SENDING LEAD:", e)

    # PDF
    try:
        pdf_path = generate_pdf(data, data["segment"], message.from_user.id)

        if pdf_path and os.path.exists(pdf_path):
            await message.answer_document(
                FSInputFile(os.path.abspath(pdf_path)),
                caption="📄 Ваш персональный маркетинговый разбор готов."
            )
    except Exception as e:
        print("PDF ERROR:", e)

    await message.answer("Спасибо! Менеджер свяжется с вами.", reply_markup=ReplyKeyboardRemove())
    await message.answer("Что делаем дальше?", reply_markup=post_pdf_menu())

    await state.clear()


# =========================
# WEBHOOK INIT
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