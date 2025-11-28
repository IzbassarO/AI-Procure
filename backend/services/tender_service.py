# backend/services/tender_service.py
from typing import List, Dict, Optional, Tuple
from models.filters import TenderFilters
from repositories.tenders_csv import TenderRepository

def parse_amount(row: Dict) -> float:
    """
    Универсальный парсер суммы из строки CSV.
    Смотрим в несколько возможных колонок и приводим к float.
    """
    candidates = [
        row.get("Сумма, тг."),
        row.get("Сумма, тг"),
        row.get("Сумма, тг "),
        row.get("Общие_Сумма, тг"),
        row.get("Детали_Сумма"),
        row.get("Сумма"),
    ]

    raw = next((v for v in candidates if v not in (None, "", " ")), "0")

    s = str(raw)
    s = s.replace("\u00a0", "")  # NBSP
    s = s.replace(" ", "")       # обычные пробелы
    s = s.replace(",", ".")      # запятая -> точка

    try:
        return float(s)
    except ValueError:
        return 0.0


def search_tenders(
    repo: TenderRepository,
    query: Optional[str],
    filters: Optional[TenderFilters],
    page: int,
    page_size: int,
) -> Tuple[List[Dict], int, int]:
    rows = repo.search_raw(query, filters)
    if rows:
        print("🔬 Sample row keys:", list(rows[0].keys()))
    total = len(rows)

    if total == 0:
        return [], 0, 1

    if filters and filters.amountSort in ("asc", "desc"):
        reverse = filters.amountSort == "desc"
        rows.sort(key=parse_amount, reverse=reverse)

        # отладка: покажем первые 5 сумм после сортировки
        debug_amounts = [parse_amount(r) for r in rows[:5]]
        print(f"🔍 SORT BY amount ({filters.amountSort}), first 5:", debug_amounts)

    # ПАГИНАЦИЯ
    pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    items = rows[start:end]

    return items, total, pages
