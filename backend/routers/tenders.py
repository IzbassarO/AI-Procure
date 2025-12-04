from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict

from services.tenders_service import search_tenders_prod
from db.firestore_repo import FirestoreTenderRepo
from services.tenders_refresh_service import refresh_tenders_once

router = APIRouter(prefix="/api/tenders", tags=["tenders"])

debug_repo = FirestoreTenderRepo()

class SearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Dict = {}
    page: int = 1
    pageSize: int = 15
    sortAmount: Optional[str] = None

@router.post("/search")
def search(req: SearchRequest):
    return search_tenders_prod(
        query=req.query,
        filters=req.filters,
        page=req.page,
        page_size=req.pageSize,
        sort_amount=req.sortAmount,
    )

@router.get("/debug/first")
def debug_first():
    docs = debug_repo.collection.limit(5).stream()
    out = []
    for d in docs:
        item = d.to_dict()
        item["__doc_id__"] = d.id
        out.append(item)
    return out

@router.post("/refresh")
async def refresh_tenders():
    result = await refresh_tenders_once()
    return result