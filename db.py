# =========================
# db.py — ПОЛНАЯ ВЕРСИЯ (ХРАНИМ ВСЁ НУЖНОЕ)
# ✅ хранит city, niche, full_name, phone, is_own_contact
# ✅ не используем колонку name "type" (слишком конфликтное) → lead_type
# ✅ init_db делает CREATE + мягкую миграцию через ALTER TABLE
# =========================

import sqlite3

DB_PATH = "leads.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db():
    conn = _connect()
    cur = conn.cursor()

    # Базовая схема (новая)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER,
        username TEXT,
        full_name TEXT,

        phone TEXT,
        is_own_contact INTEGER,
        contact_user_id INTEGER,

        lead_type TEXT,

        role TEXT,
        city TEXT,
        niche TEXT,

        strategy TEXT,
        source TEXT,
        stability TEXT,
        geo TEXT,
        budget TEXT,

        score INTEGER,
        segment TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # Мягкая миграция для уже существующей таблицы (если она старая)
    # Добавляем недостающие колонки; если уже есть — игнорируем.
    def add_col(sql):
        try:
            cur.execute(sql)
            conn.commit()
        except sqlite3.OperationalError:
            pass

    add_col("ALTER TABLE leads ADD COLUMN full_name TEXT")
    add_col("ALTER TABLE leads ADD COLUMN phone TEXT")
    add_col("ALTER TABLE leads ADD COLUMN is_own_contact INTEGER")
    add_col("ALTER TABLE leads ADD COLUMN contact_user_id INTEGER")
    add_col("ALTER TABLE leads ADD COLUMN lead_type TEXT")
    add_col("ALTER TABLE leads ADD COLUMN city TEXT")
    add_col("ALTER TABLE leads ADD COLUMN niche TEXT")

    # Если в старой базе была колонка `type`, она останется.
    # Мы пишем в `lead_type`. При необходимости потом сделаем миграцию/копирование.

    conn.close()


def save_lead(data: dict):
    conn = _connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO leads (
        telegram_id,
        username,
        full_name,
        phone,
        is_own_contact,
        contact_user_id,
        lead_type,
        role,
        city,
        niche,
        strategy,
        source,
        stability,
        geo,
        budget,
        score,
        segment
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("telegram_id"),
        data.get("username"),
        data.get("full_name"),

        data.get("phone"),
        1 if data.get("is_own_contact") else 0,
        data.get("contact_user_id"),

        data.get("lead_type"),

        data.get("role"),
        data.get("city"),
        data.get("niche"),

        data.get("strategy"),
        data.get("source"),
        data.get("stability"),
        data.get("geo"),
        data.get("budget"),

        data.get("score"),
        data.get("segment"),
    ))

    conn.commit()
    conn.close()


def get_full_stats():
    conn = _connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM leads")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment = 'VIP'")
    vip = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment = 'WARM'")
    warm = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leads WHERE segment = 'COLD'")
    cold = cur.fetchone()[0]

    conn.close()
    return total, vip, warm, cold