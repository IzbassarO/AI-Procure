# backend/routers/tenders.py
from fastapi import APIRouter
from models.tender import SearchRequest, SearchResponse
from services.tender_service import search_tenders
from repositories.tenders_csv import csv_tender_repo

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_tenders_endpoint(body: SearchRequest):
    print("🔎 amountSort from client:", body.filters.amountSort if body.filters else None)

    items, total, pages = search_tenders(
        repo=csv_tender_repo,
        query=body.query,
        filters=body.filters,
        page=body.page,
        page_size=body.pageSize,
    )

    return SearchResponse(
        items=items,
        total=total,
        page=body.page,
        pageSize=body.pageSize,
        pages=pages,
    )
