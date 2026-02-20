from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AGENCY_USERNAME = os.getenv("AGENCY_USERNAME")
AGENCY_CHAT_ID = int(os.getenv("AGENCY_CHAT_ID"))

