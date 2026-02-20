from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):

    # выбор формата
    format = State()

    # короткая версия
    short_role = State()
    short_strategy = State()

    # полная версия
    role = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()
    budget = State()