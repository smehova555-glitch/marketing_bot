from aiogram import Bot
from config import MANAGER_ID


async def notify_manager(bot: Bot, data: dict, score: int, segment: str):

    if not MANAGER_ID:
        return

    # Красивый заголовок
    if segment == "VIP":
        header = "💎 VIP ЛИД ShiftMotion"
    elif segment == "WARM":
        header = "🔥 WARM ЛИД ShiftMotion"
    else:
        header = "❄ COLD ЛИД ShiftMotion"

    # Заменяем None
    def safe(value):
        return value if value else "Не проходил расширенную диагностику"

    text = (
        f"{header}\n\n"
        f"👤 Username: @{data.get('username', '—')}\n"
        f"🆔 Telegram ID: {data.get('telegram_id')}\n\n"
        f"🎯 Сегмент: {segment}\n"
        f"📊 Score: {score}\n\n"
        f"📌 Ответы:\n"
        f"— Роль: {safe(data.get('role'))}\n"
        f"— Стратегия: {safe(data.get('strategy'))}\n"
        f"— Источник: {safe(data.get('source'))}\n"
        f"— Стабильность: {safe(data.get('stability'))}\n"
        f"— Гео: {safe(data.get('geo'))}\n"
        f"— Контент: {safe(data.get('content'))}\n"
        f"— Средний чек: {safe(data.get('avg_check'))}\n"
        f"— География: {safe(data.get('geography'))}\n"
        f"— Команда: {safe(data.get('team'))}\n"
        f"— Реклама: {safe(data.get('ads'))}\n"
        f"— Цель: {safe(data.get('goal'))}\n"
        f"— Бюджет: {safe(data.get('budget'))}\n"
    )

    await bot.send_message(chat_id=MANAGER_ID, text=text)