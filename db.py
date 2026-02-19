import sqlite3
from datetime import datetime

DB_NAME = "leads.db"


# =============================
# INIT DB
# =============================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        username TEXT,
        role TEXT,
        strategy TEXT,
        source TEXT,
        stability TEXT,
        geo TEXT,
        content TEXT,
        avg_check TEXT,
        geography TEXT,
        team TEXT,
        ads TEXT,
        goal TEXT,
        budget TEXT,
        score INTEGER,
        segment TEXT,
        followup_sent INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# =============================
# SAVE LEAD
# =============================

def save_lead(data: dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO leads (
        telegram_id, username, role, strategy, source,
        stability, geo, content, avg_check, geography,
        team, ads, goal, budget, score, segment
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("telegram_id"),
        data.get("username"),
        data.get("role"),
        data.get("strategy"),
        data.get("source"),
        data.get("stability"),
        data.get("geo"),
        data.get("content"),
        data.get("avg_check"),
        data.get("geography"),
        data.get("team"),
        data.get("ads"),
        data.get("goal"),
        data.get("budget"),
        data.get("score"),
        data.get("segment"),
    ))

    conn.commit()
    conn.close()


# =============================
# FOLLOWUP
# =============================

def get_unfollowed_leads():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, telegram_id, created_at
        FROM leads
        WHERE followup_sent = 0
    """)

    rows = cursor.fetchall()
    conn.close()

    leads = []
    for row in rows:
        lead_id = row[0]
        telegram_id = row[1]
        created_at = datetime.fromisoformat(row[2])
        leads.append((lead_id, telegram_id, created_at))

    return leads


def mark_followup_sent(lead_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE leads
        SET followup_sent = 1
        WHERE id = ?
    """, (lead_id,))

    conn.commit()
    conn.close()


# =============================
# STATS
# =============================

def get_full_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment = 'VIP'")
    vip = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment = 'WARM'")
    warm = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment = 'COLD'")
    cold = cursor.fetchone()[0]

    conn.close()

    return total, vip, warm, cold