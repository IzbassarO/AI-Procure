import asyncio
from db.firestore_repo import FirestoreTenderRepo
from parsers.ai_procure_parser import scrape_tenders_sync
import logging

repo = FirestoreTenderRepo()
logger = logging.getLogger(__name__)
async def refresh_tenders_once() -> dict:
    logger.info("[scheduler] Запускаем обновление тендеров...")
    records = await asyncio.to_thread(scrape_tenders_sync)
    logger.info("Парсер вернул %d записей", len(records))
    logger.info("[scheduler] Парсинг завершён. Сейчас начнётся проверка ID и Firestore READ/WRITE")
    new_count = repo.upsert_many_if_new(records, dry_run=True)
    logger.info("[scheduler] Обновление завершено. Новых тендеров (по расчёту): %d. Режим DRY_RUN=%s",
        new_count,
        True,
    )
    
    return {
        "parsed_total": len(records),
        "inserted_new": new_count,
    }
