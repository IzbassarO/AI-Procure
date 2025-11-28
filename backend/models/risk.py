# backend/models/risk.py
from typing import List, Optional
from pydantic import BaseModel


class TenderRiskItem(BaseModel):
    id: str
    name: str
    price: float
    organizer: str
    invited_supplier: Optional[str] = None
    method: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class TenderRiskRequest(BaseModel):
    tenders: List[TenderRiskItem]
