import os
import psycopg2


DATABASE_URL = os.getenv("DATABASE_URL")


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT,
        username TEXT,
        type TEXT,
        role TEXT,
        strategy TEXT,
        source TEXT,
        stability TEXT,
        geo TEXT,
        budget TEXT,
        score INTEGER,
        segment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()


def save_lead(data):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO leads (
        telegram_id,
        username,
        type,
        role,
        strategy,
        source,
        stability,
        geo,
        budget,
        score,
        segment
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("telegram_id"),
        data.get("username"),
        data.get("type"),
        data.get("role"),
        data.get("strategy"),
        data.get("source"),
        data.get("stability"),
        data.get("geo"),
        data.get("budget"),
        data.get("score"),
        data.get("segment"),
    ))

    conn.commit()
    cursor.close()
    conn.close()


def get_full_stats():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment = 'VIP'")
    vip = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment = 'WARM'")
    warm = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE segment = 'COLD'")
    cold = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return total, vip, warm, cold