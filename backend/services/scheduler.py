import asyncio
from services.tenders_refresh_service import refresh_tenders_once
import logging
REFRESH_INTERVAL_SECONDS = 3 * 60 * 60  # 3 часа

logger = logging.getLogger(__name__)

async def start_tenders_scheduler():
    while True:
        try:
            logger.info("=== Scheduled tender refresh START ===")
            result = await refresh_tenders_once()
            logger.info("=== Scheduled tender refresh DONE: %s ===", result)
        except Exception:
            logger.exception("Ошибка во время обновления тендеров")
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
