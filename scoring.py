def calculate_score(data: dict) -> int:
    score = 0

    if data.get("strategy") == "Да":
        score += 20
    elif data.get("strategy") == "Частично":
        score += 10

    if data.get("source") in ["Да, реклама", "Да, соцсети"]:
        score += 20

    if data.get("stability") == "Да":
        score += 20

    if data.get("geo") == "Да, продвигаем":
        score += 20

    if data.get("content") == "Да":
        score += 10

    return score


def get_segment(score: int) -> str:
    if score >= 70:
        return "VIP"
    elif score >= 40:
        return "WARM"
    return "COLD"