# backend/services/tender_risk_service.py

import os
import httpx
from typing import List, Dict, Any
from models.risk import TenderRiskItem

RISK_API_URL = os.getenv("RISK_API_URL")

print("🔍 DEBUG: RISK_API_URL =", RISK_API_URL)


async def call_external_risk_service(
    tenders: List[TenderRiskItem],
) -> Dict[str, Any]:
    """
    Отправляет список тендеров на внешний LLM-сервис риск-анализа
    и возвращает его JSON-ответ как dict.
    """
    payload = {
        "tenders": [t.model_dump() for t in tenders]
    }

    # 🔥 ЛОГ ПОЛНОГО ПЕЙЛОАДА
    print("🔼 SENDING TO RISK API:")
    print(payload)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(RISK_API_URL, json=payload)

    # 🔥 ЛОГ СТАТУСА И ТЕКСТА ОТВЕТА
    print("🔽 RISK API RESPONSE STATUS:", resp.status_code)
    print("🔽 RISK API RESPONSE TEXT:", resp.text)

    resp.raise_for_status()
    return resp.json()
