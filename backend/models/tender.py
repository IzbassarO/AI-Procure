# backend/models/tender.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from models.filters import TenderFilters

class SearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Optional[TenderFilters] = None
    page: int = 1
    pageSize: int = 15

class SearchResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    pageSize: int
    pages: int
