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
    contact = State()


# =========================
# HEALTHCHECK SERVER
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

    print("Web server started on port", port)


# =========================
# START HANDLER
# =========================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    print("START RECEIVED")

    await message.answer("Бот работает ✅")


# =========================
# MAIN
# =========================

async def main():
    init_db()

    await start_web_server()

    print("STARTING POLLING")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())