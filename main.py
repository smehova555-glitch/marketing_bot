print("MAIN FILE LOADED")

import os
import logging
import asyncio
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


# =========================
# WEBHOOK START
# =========================

async def main():
    init_db()

    # 🔥 Жёстко устанавливаем webhook
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    print("WEBHOOK SET")

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    asyncio.run(main())