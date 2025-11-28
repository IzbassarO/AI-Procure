# backend/routers/risk.py
from typing import Any, Dict

from fastapi import APIRouter

from models.risk import TenderRiskRequest
from services.tender_risk_service import call_external_risk_service

router = APIRouter()


@router.post("/tender-risk")
async def tender_risk_endpoint(body: TenderRiskRequest) -> Dict[str, Any]:
    """
    Проксируем запрос на внешний LLM-сервис.
    На вход: { "tenders": [ ... ] }
    На выход: JSON, который вернул LLM-сервис (report_metadata, tenders, analysis и т.д.)
    """
    data = await call_external_risk_service(body.tenders)
    return data
