def calculate_score(data: dict) -> int:
    score = 0

    if data.get("strategy") == "Да":
        score += 2
    elif data.get("strategy") == "Частично":
        score += 1

    if data.get("source") != "Нет стабильного канала":
        score += 2

    if data.get("stability") == "Да":
        score += 2
    elif data.get("stability") == "Иногда":
        score += 1

    if data.get("geo") == "Да, продвигаем":
        score += 2
    elif data.get("geo") == "Есть, но не продвигаем":
        score += 1

    return score


def get_segment(score: int) -> str:
    if score >= 6:
        return "VIP"
    elif score >= 3:
        return "WARM"
    return "COLD"