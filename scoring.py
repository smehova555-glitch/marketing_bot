def calculate_score(data: dict) -> int:
    score = 0

    # Стратегия
    if data.get("strategy") == "Нет":
        score += 2
    elif data.get("strategy") == "Частично":
        score += 1

    # Источник заявок
    if data.get("source") == "Нестабильно":
        score += 2
    elif data.get("source") == "Сарафан":
        score += 1

    # Стабильность потока
    if data.get("stability") == "Нет":
        score += 2
    elif data.get("stability") == "Иногда":
        score += 1

    # Геомаркетинг
    if data.get("geo") == "Нет":
        score += 2
    elif data.get("geo") == "Есть, но не продвигаем":
        score += 1

    # Бюджет
    if data.get("budget") == "до 50 тыс":
        score += 2
    elif data.get("budget") == "50–150 тыс":
        score += 1

    return score


def get_segment(score: int) -> str:
    if score >= 7:
        return "VIP"
    elif score >= 4:
        return "WARM"
    else:
        return "COLD"