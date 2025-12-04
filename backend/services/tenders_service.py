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
    target = {str(f).lower() for f in features}

    filtered: List[Dict] = []

    for row in rows:
        raw = row.get("Общие_Признаки")
        if raw is None:
            continue
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
    effective_sort = filters.get("amountSort") or sort_amount or None
    cache_key = _make_cache_key(query, filters, effective_sort)

    if cache_key in _SEARCH_CACHE:
        all_items = _SEARCH_CACHE[cache_key]
    else:
        raw_rows, _ = repo.search_page(
            filters=filters,
            limit=MAX_FETCH,
            cursor=None,
            sort_amount=effective_sort,
        )

        rows_after_text = _apply_text_query(raw_rows, query)
        rows_after_features = _apply_features_filter(
            rows_after_text,
            filters.get("features"),
        )
        all_items = rows_after_features[:MAX_FETCH]
        _SEARCH_CACHE[cache_key] = all_items

    total = len(all_items)

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
        total = repo.get_total_count_from_metadata()
    else:
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
                break
    return result