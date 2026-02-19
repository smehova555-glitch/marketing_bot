import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from db import get_unfollowed_leads, mark_followup_sent

FOLLOWUP_DELAY_HOURS = 24


async def followup_worker(bot: Bot):
    while True:
        try:
            leads = get_unfollowed_leads()

            for lead_id, telegram_id, created_at in leads:
                created_at = datetime.fromisoformat(created_at)

                if datetime.now() - created_at >= timedelta(hours=FOLLOWUP_DELAY_HOURS):
                    try:
                        await bot.send_message(
                            telegram_id,
                            "Вы проходили диагностику, но не обсудили внедрение.\n\n"
                            "Если хотите системный маркетинг — напишите нам."
                        )
                        mark_followup_sent(lead_id)
                    except Exception:
                        pass

        except Exception as e:
            print("FOLLOWUP ERROR:", e)

        await asyncio.sleep(300)