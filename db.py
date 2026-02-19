import sqlite3


def init_db():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            type TEXT,
            score INTEGER,
            segment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_lead(data: dict):
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO leads (telegram_id, username, type, score, segment)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("telegram_id"),
        data.get("username"),
        data.get("type"),
        data.get("score"),
        data.get("segment")
    ))

    conn.commit()
    conn.close()


def get_full_stats():
    conn = sqlite3.connect("leads.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment='VIP'")
    vip = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment='WARM'")
    warm = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment='COLD'")
    cold = cursor.fetchone()[0]

    conn.close()

    return total, vip, warm, cold