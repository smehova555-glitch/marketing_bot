from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):
    format = State()

    # short
    short_role = State()
    short_strategy = State()

    # full
    role = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()

    finished = State()