import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect("leads.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            segment TEXT,
            created_at TIMESTAMP,
            followup_sent INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_lead(telegram_id, username, segment):
    conn = sqlite3.connect("leads.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO leads (telegram_id, username, segment, created_at)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, username, segment, datetime.now()))

    conn.commit()
    conn.close()


def get_full_stats():
    conn = sqlite3.connect("leads.db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM leads")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment='diagnostic'")
    diagnostic = cur.fetchone()[0]

    conn.close()
    return total, diagnostic


def get_unfollowed_leads():
    conn = sqlite3.connect("leads.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, telegram_id, created_at
        FROM leads
        WHERE followup_sent = 0
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def mark_followup_sent(lead_id):
    conn = sqlite3.connect("leads.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE leads
        SET followup_sent = 1
        WHERE id = ?
    """, (lead_id,))

    conn.commit()
    conn.close()