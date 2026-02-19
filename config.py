import os
from dotenv import load_dotenv

load_dotenv()


# =============================
# Telegram
# =============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
AGENCY_USERNAME = os.getenv("AGENCY_USERNAME")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")

if not AGENCY_USERNAME:
    raise ValueError("AGENCY_USERNAME is not set in .env file")


# =============================
# Admin / Manager
# =============================

MANAGER_ID = os.getenv("MANAGER_ID")
ADMIN_ID = os.getenv("ADMIN_ID")

if MANAGER_ID:
    MANAGER_ID = int(MANAGER_ID)

if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)


# =============================
# Environment
# =============================

ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# =============================
# Follow-up settings
# =============================

FOLLOWUP_DELAY_HOURS = int(os.getenv("FOLLOWUP_DELAY_HOURS", 24))


# =============================
# Scoring thresholds
# =============================

COLD_THRESHOLD = 6
WARM_THRESHOLD = 12
VIP_THRESHOLD = 13