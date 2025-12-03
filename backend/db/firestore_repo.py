# db/firestore_repo.py
from typing import Dict, Optional, List, Tuple
from google.cloud import firestore

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
        """
        Возвращает до `limit` документов по фильтрам.
        Cursor пока не используем (передаём None), но параметр оставлен на будущее.
        """
        q = self.collection

        category_vals = filters.get("category") or []
        method_vals = filters.get("method") or []
        purchase_vals = filters.get("purchaseType") or []
        status_vals = filters.get("status") or []

        # поля с пробелами/знаками — в бэктиках
        if category_vals:
            q = q.where("`Общие_Вид предмета закупок`", "in", category_vals)

        if method_vals:
            q = q.where("`Общие_Способ проведения закупки`", "in", method_vals)

        if purchase_vals:
            q = q.where("`Общие_Тип закупки`", "in", purchase_vals)

        if status_vals:
            q = q.where("`Статус`", "in", status_vals)

        # сортировка по сумме
        if sort_amount in ("asc", "desc"):
            direction = (
                firestore.Query.DESCENDING
                if sort_amount == "desc"
                else firestore.Query.ASCENDING
            )
            q = q.order_by("`Сумма, тг.`", direction=direction)
        else:
            # базовый fallback, если сортировку не выбрали
            q = q.order_by("__name__")


        # Cursor на будущее – пока всегда None
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
