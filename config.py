import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
AGENCY_USERNAME = os.getenv("AGENCY_USERNAME")

MANAGER_ID = os.getenv("MANAGER_ID")

if MANAGER_ID is not None:
    MANAGER_ID = int(MANAGER_ID)