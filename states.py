from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):

    # выбор формата
    format = State()

    # базовая диагностика
    role = State()
    turnover = State()
    strategy = State()
    channel = State()
    stability = State()
    geo = State()
    budget = State()

    # ветвление
    branch_start = State()
    branch_growth = State()
    branch_scale = State()

    # финал
    finished = State()