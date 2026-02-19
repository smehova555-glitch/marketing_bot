import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, AGENCY_USERNAME
from states import Diagnostic
from scoring import calculate_score, get_segment
from recommendations import generate_recommendations
from db import init_db, save_lead, get_full_stats


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ========================
# Клавиатура
# ========================

def kb(options):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )


# ========================
# START
# ========================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Диагностика маркетинга Shift Motion.\n\nВыберите формат:",
        reply_markup=kb(["Короткая диагностика", "Полная диагностика"])
    )

    await state.set_state(Diagnostic.format)


# ========================
# ВЫБОР ФОРМАТА
# ========================

@dp.message(Diagnostic.format)
async def choose_format(message: Message, state: FSMContext):

    if message.text == "Короткая диагностика":
        await message.answer(
            "Кто вы?",
            reply_markup=kb(["Собственник", "Личный бренд", "Маркетолог"])
        )
        await state.set_state(Diagnostic.short_role)

    elif message.text == "Полная диагностика":
        await message.answer(
            "Кто вы?",
            reply_markup=kb(["Собственник", "Личный бренд", "Маркетолог"])
        )
        await state.set_state(Diagnostic.role)

    else:
        await message.answer("Выберите формат кнопкой.")


# =====================================================
# КОРОТКАЯ ДИАГНОСТИКА
# =====================================================

@dp.message(Diagnostic.short_role)
async def short_q1(message: Message, state: FSMContext):

    await state.update_data(role=message.text)

    await message.answer(
        "Есть ли маркетинговая стратегия?",
        reply_markup=kb(["Да", "Частично", "Нет"])
    )

    await state.set_state(Diagnostic.short_strategy)


@dp.message(Diagnostic.short_strategy)
async def short_finish(message: Message, state: FSMContext):

    await state.update_data(strategy=message.text)

    data = await state.get_data()

    save_lead({
        "telegram_id": message.from_user.id,
        "username": message.from_user.username,
        "type": "short",
        **data
    })

    await message.answer(
        "Краткая рекомендация:\n\n"
        "— Проверьте упаковку оффера\n"
        "— Выберите один основной канал привлечения\n"
        "— Усильте геомаркетинг\n",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.clear()


# =====================================================
# ПОЛНАЯ ДИАГНОСТИКА
# =====================================================

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
        "Есть ли основной системный канал привлечения?",
        reply_markup=kb([
            "Да, реклама",
            "Да, соцсети",
            "Да, сарафан",
            "Нет стабильного канала"
        ])
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
async def deep_finish(message: Message, state: FSMContext):

    await state.update_data(geo=message.text)

    data = await state.get_data()

    score = calculate_score(data)
    segment = get_segment(score)

    save_lead({
        "telegram_id": message.from_user.id,
        "username": message.from_user.username,
        "type": "deep",
        "score": score,
        "segment": segment,
        **data
    })

    text = generate_recommendations(data, segment)

    await message.answer(text, reply_markup=ReplyKeyboardRemove())

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

    await message.answer("Готовы обсудить внедрение?", reply_markup=contact_kb)

    await state.clear()


# =====================================================
# STATS
# =====================================================

@dp.message(Command("stats"))
async def stats(message: Message):
    total, vip, warm, cold = get_full_stats()

    await message.answer(
        f"📊 Статистика\n\n"
        f"Всего лидов: {total}\n"
        f"VIP: {vip}\n"
        f"WARM: {warm}\n"
        f"COLD: {cold}"
    )


# =====================================================
# RUN
# =====================================================

async def main():
    init_db()
    print("ShiftMotion Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
