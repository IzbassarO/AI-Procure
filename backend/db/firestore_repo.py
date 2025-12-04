from typing import Dict, Optional, List, Tuple
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)

class FirestoreTenderRepo:
    def __init__(self, collection_name: str = "tenders"):
        self.db = firestore.Client()
        self.collection = self.db.collection(collection_name)

    def get_total_count_from_metadata(self) -> int:
        meta = self.db.collection("metadata").document("tenders").get()
        data = meta.to_dict() or {}
        return data.get("total", 0)

    def search_page(
        self,
        filters: Dict,
        limit: int,
        cursor: Optional[str],
        sort_amount: Optional[str],
    ) -> Tuple[List[Dict], Optional[str]]:
        q = self.collection

        category_vals = filters.get("category") or []
        method_vals = filters.get("method") or []
        purchase_vals = filters.get("purchaseType") or []
        status_vals = filters.get("status") or []

        if category_vals:
            q = q.where("`Общие_Вид предмета закупок`", "in", category_vals)

        if method_vals:
            q = q.where("`Общие_Способ проведения закупки`", "in", method_vals)

        if purchase_vals:
            q = q.where("`Общие_Тип закупки`", "in", purchase_vals)

        if status_vals:
            q = q.where("`Статус`", "in", status_vals)

        if sort_amount in ("asc", "desc"):
            direction = (
                firestore.Query.DESCENDING
                if sort_amount == "desc"
                else firestore.Query.ASCENDING
            )
            q = q.order_by("`Сумма, тг.`", direction=direction)
        else:
            q = q.order_by("__name__")

        if cursor:
            q = q.start_after({"ID": cursor})

        docs = q.limit(limit).stream()

        items: List[Dict] = []
        last_cursor: Optional[str] = None

        for d in docs:
            data = d.to_dict()
            data["ID"] = data.get("ID") or d.id
            items.append(data)
            last_cursor = d.id

        return items, last_cursor
    
    def upsert_many_if_new(self, items: List[Dict], dry_run: bool = False) -> int:
        batch = self.db.batch()
        new_count = 0
        for item in items:
            tender_id = str(item.get("ID") or "").strip()
            if not tender_id:
                continue
            if dry_run:
                logger.debug(f"[DRY_RUN] Проверка наличия тендера ID={tender_id} в Firestore")
                is_new = True
            else:
                doc_ref = self.collection.document(tender_id)
                doc = doc_ref.get()
                is_new = not doc.exists

            if not is_new:
                continue
            item["ID"] = tender_id

            if dry_run:
                logger.info(f"[DRY_RUN] Добавили бы НОВЫЙ тендер ID={tender_id}")
            else:
                batch.set(self.collection.document(tender_id), item)

            new_count += 1

        if new_count > 0 and not dry_run:
            batch.commit()

            meta_ref = self.db.collection("metadata").document("tenders")
            meta_ref.set({"total": firestore.Increment(new_count)}, merge=True)

        logger.info(
            "[upsert_many_if_new] %s режим. Новых тендеров: %d",
            "DRY_RUN" if dry_run else "REAL",
            new_count,
        )

        return new_count