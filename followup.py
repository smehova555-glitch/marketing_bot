import asyncio
from datetime import datetime, timedelta
from config import FOLLOWUP_DELAY_HOURS
from db import get_unfollowed_leads, mark_followup_sent


async def followup_worker(bot):
    while True:
        leads = get_unfollowed_leads()

        now = datetime.utcnow()

        for lead in leads:
            lead_id, telegram_id, created_at = lead

            if now - created_at >= timedelta(hours=FOLLOWUP_DELAY_HOURS):
                try:
                    await bot.send_message(
                        chat_id=telegram_id,
                        text=(
                            "Вы прошли диагностику Shift Motion, "
                            "но не обсудили рекомендации.\n\n"
                            "Готовы разобрать стратегию?"
                        )
                    )
                    mark_followup_sent(lead_id)
                except:
                    pass

        await asyncio.sleep(3600)