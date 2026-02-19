import sqlite3
from datetime import datetime

DB_NAME = "leads.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            score INTEGER,
            segment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_lead(data: dict):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO leads (telegram_id, username, score, segment)
        VALUES (?, ?, ?, ?)
    """, (
        data["telegram_id"],
        data["username"],
        data["score"],
        data["segment"]
    ))

    conn.commit()
    conn.close()


def get_full_stats():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM leads")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment='VIP'")
    vip = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment='WARM'")
    warm = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment='COLD'")
    cold = cur.fetchone()[0]

    conn.close()

    return total, vip, warm, cold