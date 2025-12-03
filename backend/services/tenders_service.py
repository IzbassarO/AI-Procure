from typing import Any, Dict, List, Optional
from math import ceil
import json

from db.firestore_repo import FirestoreTenderRepo

repo = FirestoreTenderRepo()

MAX_FETCH = 5
_SEARCH_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def _make_cache_key(
    query: Optional[str],
    normalized_filters: Dict[str, Any],
    sort_amount: Optional[str],
) -> str:
    return json.dumps(
        {
            "q": query or "",
            "f": normalized_filters,
            "sort": sort_amount or "",
        },
        ensure_ascii=False,
        sort_keys=True,
    )

def _apply_features_filter(rows: List[Dict], features) -> List[Dict]:
    if not features:
        return rows

    # приводим признаки к lower-case для сравнения
    target = {str(f).lower() for f in features}

    filtered: List[Dict] = []

    for row in rows:
        raw = row.get("Общие_Признаки")
        if raw is None:
            continue

        # поле может быть строкой или массивом
        if isinstance(raw, list):
            values = [str(v).lower() for v in raw]
        else:
            values = [str(raw).lower()]

        if target.intersection(values):
            filtered.append(row)

    return filtered

def search_tenders_prod(
    query: Optional[str],
    filters: Dict,
    page: int,
    page_size: int,
    sort_amount: Optional[str],
):
    if page < 1:
        page = 1
    if page_size <= 0:
        page_size = 15

    filters = filters or {}

    # сортировку берём в первую очередь из filters.amountSort (то, что шлёт фронт),
    # а sort_amount из роутера используем как fallback
    effective_sort = filters.get("amountSort") or sort_amount or None

    cache_key = _make_cache_key(query, filters, effective_sort)

    if cache_key in _SEARCH_CACHE:
        # Уже есть в кэше – НЕ ходим в Firestore
        all_items = _SEARCH_CACHE[cache_key]
    else:
        # Первый запрос – идём в Firestore
        raw_rows, _ = repo.search_page(
            filters=filters,
            limit=MAX_FETCH,
            cursor=None,
            sort_amount=effective_sort,
        )

        # 🔹 Текстовый поиск по названию/организатору
        rows_after_text = _apply_text_query(raw_rows, query)

        # 🔹 Фильтрация по признакам закупки
        rows_after_features = _apply_features_filter(
            rows_after_text,
            filters.get("features"),
        )

        # 🔹 Ограничиваем до MAX_FETCH
        all_items = rows_after_features[:MAX_FETCH]

        # Кладём в кэш
        _SEARCH_CACHE[cache_key] = all_items

    total = len(all_items)

        # ----- здесь у тебя уже есть all_items (максимум MAX_FETCH) -----

    # определяем, пустой ли запрос
    # filters — это то, что пришло с фронта (category, method, purchaseType, features, amountSort)
    raw_filters = filters or {}

    has_any_filter = any(
        [
            raw_filters.get("category"),
            raw_filters.get("method"),
            raw_filters.get("purchaseType"),
            raw_filters.get("features"),
            raw_filters.get("status"),
        ]
    )

    has_query = bool(query and str(query).strip())

    is_initial_request = not has_any_filter and not has_query

    if is_initial_request:
        # 1️⃣ начальный запрос или сброс фильтров:
        # считаем total по метаданным (вся коллекция, ~10k)
        total = repo.get_total_count_from_metadata()
    else:
        # 2️⃣ любые фильтры/поиск: total = то, что реально отфильтровали (ограничено MAX_FETCH)
        total = len(all_items)

    if total == 0:
        return {
            "items": [],
            "total": 0,
            "page": 1,
            "pageSize": page_size,
            "pages": 1,
        }

    pages = max(1, ceil(total / page_size))

    if page < 1:
        page = 1
    if page > pages:
        page = pages

    start = (page - 1) * page_size
    end = start + page_size
    items = all_items[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "pages": pages,
    }

def _apply_text_query(
    rows: List[Dict[str, Any]],
    query: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Фильтрация по ключевым словам.

    Ищем подстроку (case-insensitive) в нескольких текстовых полях:
      - Наименование объявления
      - Детали_Наименование объявления
      - Общие_Организатор
      - Организатор
    """

    if not query:
        return rows

    q = str(query).strip().lower()
    if not q:
        return rows

    result: List[Dict[str, Any]] = []

    for row in rows:
        for field in (
            "Наименование объявления",
            "Детали_Наименование объявления",
            "Общие_Организатор",
            "Организатор",
        ):
            value = row.get(field)
            if not value:
                continue

            if q in str(value).lower():
                result.append(row)
                break  # уже нашли совпадение по одному из полей

    return result