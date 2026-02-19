from aiogram.fsm.state import StatesGroup, State


class Diagnostic(StatesGroup):
    # Базовая диагностика
    role = State()
    strategy = State()
    source = State()
    stability = State()
    geo = State()
    content = State()

    # Выбор уровня
    level_choice = State()

    # Расширенная диагностика
    avg_check = State()
    geography = State()
    team = State()
    ads = State()
    goal = State()
    budget = State()

    # Финал
    finished = State()