# backend/repositories/tenders_csv.py
from typing import Protocol, List, Dict, Optional
from models.filters import TenderFilters
from db.csv_store import get_all_tenders


class TenderRepository(Protocol):
    def search_raw(
        self,
        query: Optional[str],
        filters: Optional[TenderFilters],
    ) -> List[Dict]:
        """Возвращает список сырых словарей (строк) без пагинации."""
        ...


class CsvTenderRepository:
    def __init__(self) -> None:
        # сейчас ничего не нужно, данные уже в памяти
        pass

    def _match_text(self, row: Dict, query: Optional[str]) -> bool:
        if not query:
            return True
        q = query.lower()
        fields = [
            row.get("Наименование объявления", ""),
            row.get("Организатор", ""),
            row.get("ID", ""),
        ]
        return any(q in (str(f) or "").lower() for f in fields)

    def _match_filters(self, row: Dict, filters: Optional[TenderFilters]) -> bool:
        if not filters:
            return True

        # ---------- Способ закупки (method) ----------
        # filters.method: List[str]
        if filters.method:
            value = row.get(
                "Общие_Способ проведения закупки",
                row.get("Способ", "")
            )
            if value not in filters.method:
                return False

        # ---------- Тип закупки (purchaseType) ----------
        if filters.purchaseType:
            value = row.get("Общие_Тип закупки", "")
            if value not in filters.purchaseType:
                return False

        # ---------- Вид предмета закупок (category) ----------
        if filters.category:
            value = row.get("Общие_Вид предмета закупок", "")
            if value not in filters.category:
                return False

        # ---------- Признаки закупки (features) ----------
        # в CSV строка типа: "['Без учета НДС', 'Закупка среди организаций инвалидов']"
        if filters.features:
            raw = row.get("Общие_Признаки", "")
            parsed: List[str] = []

            if isinstance(raw, str):
                inner = raw.strip().strip("[]")
                if inner:
                    parsed = [
                        part.strip().strip("'").strip('"')
                        for part in inner.split(",")
                        if part.strip()
                    ]
            elif isinstance(raw, list):
                parsed = [str(x) for x in raw]

            # если у строки нет признаков — она не проходит фильтр по признакам
            if not parsed:
                return False

            # хотя бы один признак из фильтра должен совпасть
            if not any(f in parsed for f in filters.features):
                return False

        # ---------- Статус (если будешь использовать в UI) ----------
        if filters.status:
            value = row.get("Детали_Статус объявления", row.get("Статус", ""))
            if value not in filters.status:
                return False

        # dateRange можно добавить позже
        return True

    def search_raw(
        self,
        query: Optional[str],
        filters: Optional[TenderFilters],
    ) -> List[Dict]:
        rows = get_all_tenders()
        return [
            row
            for row in rows
            if self._match_text(row, query) and self._match_filters(row, filters)
        ]


# Один глобальный репозиторий на всё приложение
csv_tender_repo = CsvTenderRepository()
