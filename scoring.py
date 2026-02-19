def get_branch(turnover: str) -> str:
    if turnover == "до 300 000":
        return "START"
    elif turnover == "300 000 – 3 млн":
        return "GROWTH"
    else:
        return "SCALE"


def calculate_score(data: dict) -> int:
    score = 0

    if data.get("strategy") == "Да":
        score += 2
    if data.get("channel") in ["Реклама", "Да, реклама"]:
        score += 2
    if data.get("stability") == "Да":
        score += 2
    if data.get("geo") == "Да, продвигаем":
        score += 2
    if data.get("budget") == "Есть системный бюджет":
        score += 2

    return score