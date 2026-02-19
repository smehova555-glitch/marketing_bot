from config import COLD_THRESHOLD, WARM_THRESHOLD, VIP_THRESHOLD


def calculate_score(data: dict) -> int:
    """
    Рассчитывает скоринг на основе ответов пользователя.
    """

    score = 0

    # Стратегия
    if data.get("strategy") == "Нет":
        score += 3
    elif data.get("strategy") == "Частично":
        score += 1

    # Стабильность заявок
    if data.get("stability") == "Нет":
        score += 3
    elif data.get("stability") == "Иногда":
        score += 2

    # Геомаркетинг
    if data.get("geo") == "Нет":
        score += 3
    elif data.get("geo") == "Есть, но не продвигаем":
        score += 2

    # Контент-стратегия
    if data.get("content") == "Нет":
        score += 2

    # Команда
    if data.get("team") == "Нет":
        score += 2

    # Реклама
    if data.get("ads") == "Нет":
        score += 2
    elif data.get("ads") == "Пробовали":
        score += 1

    # Средний чек
    if data.get("avg_check") == "200k+":
        score += 3
    elif data.get("avg_check") == "50–200k":
        score += 2

    # Бюджет
    if data.get("budget") == "500k+":
        score += 5
    elif data.get("budget") == "350–500k":
        score += 4
    elif data.get("budget") == "200–350k":
        score += 3
    elif data.get("budget") == "100–200k":
        score += 2
    elif data.get("budget") == "50–100k":
        score += 1

    return score


def get_segment(score: int) -> str:
    """
    Определяет сегмент пользователя по score.
    """

    if score >= VIP_THRESHOLD:
        return "VIP"

    if score > COLD_THRESHOLD and score <= WARM_THRESHOLD:
        return "WARM"

    return "COLD"