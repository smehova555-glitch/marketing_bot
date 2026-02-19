from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):
    role = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()