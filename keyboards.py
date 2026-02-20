from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

post_pdf_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Получить стратегию", callback_data="strategy")],
    [InlineKeyboardButton(text="Записаться на консультацию", callback_data="consult")],
    [InlineKeyboardButton(text="Посмотреть кейсы", callback_data="cases")]
])