# services/tenders_service.py
from typing import Optional, Dict, List
from math import ceil
import json

from db.firestore_repo import FirestoreTenderRepo

repo = FirestoreTenderRepo()

# Максимум документов, которые мы держим в памяти для одного поиска
MAX_FETCH = 1

_SEARCH_CACHE: Dict[str, List[Dict]] = {}


def _make_cache_key(query: Optional[str], filters: Dict, sort_amount: Optional[str]) -> str:
    """
    Формируем ключ кэша на основе query + filters + sort.
    Чтобы одинаковые запросы повторно не ходили в Firestore.
    """
    payload = {
        "query": (query or "").strip(),
        "filters": filters or {},
        "sort": sort_amount or "",
    }
    # sort_keys=True, чтобы порядок ключей не влиял на ключ
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _apply_text_query(rows: List[Dict], query: Optional[str]) -> List[Dict]:
    """
    Псевдо-fulltext: фильтрация по названию и организатору.
    Реальный поиск потом можно вынести в отдельный сервис.
    """
    if not query:
        return rows

    ql = query.lower()
    filtered: List[Dict] = []

    for row in rows:
        title = (
            row.get("Наименование объявления")
            or row.get("Детали_Наименование объявления")
            or ""
        )
        organizer = (
            row.get("Общие_Организатор")
            or row.get("Организатор")
            or ""
        )
        text = f"{title} {organizer}".lower()
        if ql in text:
            filtered.append(row)

    return filtered


def search_tenders_prod(
    query: Optional[str],
    filters: Dict,
    page: int,
    page_size: int,
    sort_amount: Optional[str],
):
    """
    Главная точка входа для /api/tenders/search.

    ✅ За один уникальный запрос (query+filters+sort) читаем из Firestore
       максимум MAX_FETCH документов (сейчас 500).
    ✅ Результаты кладём в RAM (_SEARCH_CACHE).
    ✅ Любые переходы по страницам дальше – БЕЗ Firestore READ.
    ✅ total = количество документов в кэше (<= 500).
    """

    if page < 1:
        page = 1
    if page_size <= 0:
        page_size = 15

    filters = filters or {}

    cache_key = _make_cache_key(query, filters, sort_amount)

    if cache_key in _SEARCH_CACHE:
        # 🔹 Уже есть в кэше – НЕ ходим в Firestore
        all_items = _SEARCH_CACHE[cache_key]
    else:
        # 🔹 Первый запрос с такой комбинацией – идём в Firestore
        raw_rows, _ = repo.search_page(
            filters=filters,
            limit=MAX_FETCH,     # читаем максимум 500
            cursor=None,
            sort_amount=sort_amount,
        )

        # 🔹 Текстовый поиск по названию/организатору
        filtered_rows = _apply_text_query(raw_rows, query)

        # 🔹 Ограничиваем на всякий случай до MAX_FETCH
        all_items = filtered_rows[:MAX_FETCH]

        # 🔹 Кладём в кэш
        _SEARCH_CACHE[cache_key] = all_items

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
