import os
import time

def generate_pdf(data, segment, user_id):
    timestamp = int(time.time())
    filename = f"report_{user_id}_{timestamp}.pdf"

    content = f"""
Shift Motion — Персональный разбор

Сегмент: {segment}

Город: {data.get("city")}
Ниша: {data.get("niche")}
Роль: {data.get("role")}
Бюджет: {data.get("budget")}
Стратегия: {data.get("strategy")}
Гео: {data.get("geo")}
Источник: {data.get("source")}
Стабильность: {data.get("stability")}
Телефон: {data.get("phone")}
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    print("PDF BUILT:", filename)

    return filename