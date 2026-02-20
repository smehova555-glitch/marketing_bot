from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):
    format = State()

    role = State()
    strategy = State()
    source = State()
    stability = State()
    analytics = State()
    budget = State()