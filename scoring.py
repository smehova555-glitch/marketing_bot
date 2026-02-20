def calculate_score(data: dict) -> int:
    score = 0

    # стратегия
    if data.get("strategy") == "Нет":
        score += 2
    elif data.get("strategy") == "Частично":
        score += 1

    # канал
    if data.get("source") == "Нет стабильного канала":
        score += 2

    # стабильность
    if data.get("stability") == "Нет":
        score += 2
    elif data.get("stability") == "Иногда":
        score += 1

    # аналитика
    if data.get("analytics") == "Нет":
        score += 2
    elif data.get("analytics") == "Частично":
        score += 1

    # бюджет
    if data.get("budget") == "Нет":
        score += 2
    elif data.get("budget") == "Нестабильный":
        score += 1

    return score


def get_segment(score: int) -> str:
    if score <= 3:
        return "VIP"
    elif score <= 7:
        return "WARM"
    else:
        return "COLD"