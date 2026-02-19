from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):

    # выбор формата
    format = State()

    # короткая
    short_role = State()
    short_strategy = State()

    # полная
    role = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()