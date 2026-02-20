import sqlite3

DB_NAME = "leads_v3.db"


# =====================================
# INIT DB (пересоздание структуры)
# =====================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Удаляем старую таблицу (если была старая структура)
    cursor.execute("DROP TABLE IF EXISTS leads")

    # Создаём новую таблицу
    cursor.execute("""
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            username TEXT,
            role TEXT,
            strategy TEXT,
            source TEXT,
            stability TEXT,
            analytics TEXT,
            budget TEXT,
            score INTEGER,
            segment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =====================================
# SAVE LEAD
# =====================================

def save_lead(data: dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO leads (
            telegram_id,
            username,
            role,
            strategy,
            source,
            stability,
            analytics,
            budget,
            score,
            segment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("telegram_id"),
        data.get("username"),
        data.get("role"),
        data.get("strategy"),
        data.get("source"),
        data.get("stability"),
        data.get("analytics"),
        data.get("budget"),
        data.get("score"),
        data.get("segment"),
    ))

    conn.commit()
    conn.close()


# =====================================
# STATS
# =====================================

def get_full_stats():
    conn = sqlite3.connect(DB_NAME)
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