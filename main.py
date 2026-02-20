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


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# STATES
# =========================

class Diagnostic(StatesGroup):
    role = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()
    budget = State()


# =========================
# KEYBOARDS
# =========================

def kb(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )


def post_pdf_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Заполнить бриф",
                    url="https://docs.google.com/document/d/1E5p85-RmJdx4rxQB9vj0GBIMY_mqRSxI/edit"
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
async def q1(message: Message, state: FSMContext):
    await state.update_data(role=message.text)
    await message.answer(
        "Есть ли маркетинговая стратегия?",
        reply_markup=kb(["Да", "Частично", "Нет"])
    )
    await state.set_state(Diagnostic.strategy)


@dp.message(Diagnostic.strategy)
async def q2(message: Message, state: FSMContext):
    await state.update_data(strategy=message.text)
    await message.answer(
        "Основной источник заявок?",
        reply_markup=kb(["Реклама", "Соцсети", "Сарафан", "Нестабильно"])
    )
    await state.set_state(Diagnostic.source)


@dp.message(Diagnostic.source)
async def q3(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    await message.answer(
        "Есть ли стабильный поток заявок?",
        reply_markup=kb(["Да", "Иногда", "Нет"])
    )
    await state.set_state(Diagnostic.stability)


@dp.message(Diagnostic.stability)
async def q4(message: Message, state: FSMContext):
    await state.update_data(stability=message.text)
    await message.answer(
        "Есть ли карточка в Яндекс/2ГИС?",
        reply_markup=kb(["Да, продвигаем", "Есть, но не продвигаем", "Нет"])
    )
    await state.set_state(Diagnostic.geo)


@dp.message(Diagnostic.geo)
async def q5(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    await message.answer(
        "Какой маркетинговый бюджет в месяц?",
        reply_markup=kb(["до 50 тыс", "50–150 тыс", "150–300 тыс", "300+ тыс"])
    )
    await state.set_state(Diagnostic.budget)


# =========================
# FINISH
# =========================

@dp.message(Diagnostic.budget)
async def finish(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    data = await state.get_data()

    data["telegram_id"] = message.from_user.id
    data["username"] = message.from_user.username

    score = calculate_score(data)
    segment = get_segment(score)

    save_lead(data)

    text = generate_recommendations(data, segment)
    await message.answer(text, reply_markup=ReplyKeyboardRemove())

    # Отправка лида в личный Telegram агентства
    await bot.send_message(
        AGENCY_CHAT_ID,
        f"""🔥 Новый лид

Сегмент: {segment}
Score: {score}

User: @{message.from_user.username}
ID: {message.from_user.id}
"""
    )

    # PDF
    pdf_path = generate_pdf(data, segment)

    if pdf_path and os.path.exists(pdf_path):
        await message.answer_document(
            FSInputFile(os.path.abspath(pdf_path)),
            caption="📄 Ваш персональный маркетинговый разбор готов."
        )

    # Кнопки
    await message.answer(
        "Что делаем дальше?",
        reply_markup=post_pdf_menu()
    )

    await state.clear()


# =========================
# RUN
# =========================

async def main():
    init_db()
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())