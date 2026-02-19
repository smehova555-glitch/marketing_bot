import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, AGENCY_USERNAME
from states import Diagnostic
from scoring import calculate_score, get_segment
from recommendations import generate_recommendations
from notifications import notify_manager
from db import init_db, save_lead


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =============================
# Helper keyboard
# =============================

def kb(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )


# =============================
# START
# =============================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вы проходите системную диагностику маркетинга от коммуникационного агентства Shift Motion.\n\nКто вы?",
        reply_markup=kb(["Собственник", "Личный бренд", "Маркетолог"])
    )
    await state.set_state(Diagnostic.role)


# =============================
# ДИАГНОСТИКА
# =============================

@dp.message(Diagnostic.role)
async def q2(message: Message, state: FSMContext):
    await state.update_data(role=message.text)
    await message.answer(
        "Есть ли маркетинговая стратегия?",
        reply_markup=kb(["Да", "Частично", "Нет"])
    )
    await state.set_state(Diagnostic.strategy)


@dp.message(Diagnostic.strategy)
async def q3(message: Message, state: FSMContext):
    await state.update_data(strategy=message.text)
    await message.answer(
        "Основной источник заявок?",
        reply_markup=kb(["Реклама", "Соцсети", "Сарафан", "Нестабильно"])
    )
    await state.set_state(Diagnostic.source)


@dp.message(Diagnostic.source)
async def q4(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    await message.answer(
        "Есть ли стабильный поток заявок?",
        reply_markup=kb(["Да", "Иногда", "Нет"])
    )
    await state.set_state(Diagnostic.stability)


@dp.message(Diagnostic.stability)
async def q5(message: Message, state: FSMContext):
    await state.update_data(stability=message.text)
    await message.answer(
        "Есть ли карточка в Яндекс/2ГИС?",
        reply_markup=kb(["Да и продвигаем", "Есть, но не продвигаем", "Нет"])
    )
    await state.set_state(Diagnostic.geo)


@dp.message(Diagnostic.geo)
async def q6(message: Message, state: FSMContext):
    await state.update_data(geo=message.text)
    await message.answer(
        "Есть ли контент-стратегия?",
        reply_markup=kb(["Да", "Частично", "Нет"])
    )
    await state.set_state(Diagnostic.content)


@dp.message(Diagnostic.content)
async def finish(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    await generate_final_result(message, state)


# =============================
# ФИНАЛ
# =============================

async def generate_final_result(message: Message, state: FSMContext):

    data = await state.get_data()

    data["telegram_id"] = message.from_user.id
    data["username"] = message.from_user.username

    score = calculate_score(data)
    segment = get_segment(score)

    data["score"] = score
    data["segment"] = segment

    save_lead(data)
    await notify_manager(bot, data, score, segment)

    text = generate_recommendations(data, segment)

    await message.answer(text, reply_markup=ReplyKeyboardRemove())

    # ✅ КОРРЕКТНАЯ INLINE КНОПКА
    contact_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Обсудить стратегию",
                    url=f"https://t.me/{AGENCY_USERNAME}"
                )
            ]
        ]
    )

    await message.answer(
        "Готовы обсудить внедрение?",
        reply_markup=contact_kb
    )

    await state.clear()


# =============================
# RUN
# =============================

async def main():
    init_db()
    print("ShiftMotion Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())