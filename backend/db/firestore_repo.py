# db/firestore_repo.py
from typing import Dict, Optional, List, Tuple
from google.cloud import firestore


class FirestoreTenderRepo:
    def __init__(self, collection_name: str = "tenders"):
        self.db = firestore.Client()
        self.collection = self.db.collection(collection_name)

    def get_total_count_from_metadata(self) -> int:
        """
        Читает metadata/tenders.total – можно использовать позже,
        но в текущей схеме мы total считаем как len(выборки <= 500).
        """
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
        Cursor сейчас не используем (передаём None), но оставляем подпись
        на будущее (если захотим true cursor-pagination).
        """
        q = self.collection

        # 🔹 Фильтры – только если список не пустой
        if filters.get("category") and len(filters["category"]) > 0:
            q = q.where("Общие_Вид предмета закупок", "in", filters["category"])

        if filters.get("method") and len(filters["method"]) > 0:
            q = q.where("Общие_Способ проведения закупки", "in", filters["method"])

        if filters.get("purchaseType") and len(filters["purchaseType"]) > 0:
            q = q.where("Общие_Тип закупки", "in", filters["purchaseType"])

        if filters.get("status") and len(filters["status"]) > 0:
            q = q.where("Статус", "in", filters["status"])

        # 🔹 Сортировка
        if sort_amount:
            direction = (
                firestore.Query.DESCENDING if sort_amount == "desc"
                else firestore.Query.ASCENDING
            )
            q = q.order_by("Сумма, тг.", direction=direction)
        else:
            # базовый порядок – по ID (или по дате, если захочешь)
            q = q.order_by("__name__")

        # 🔹 Cursor – пока не используем в новой схеме, но оставляем контракт
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
