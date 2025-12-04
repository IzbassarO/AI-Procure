import os
from typing import List, Dict, Any

import httpx
from services.report_generator import ReportGenerator
from models.risk import TenderRiskItem

LLM_BASE_URL = os.getenv("LLM_URL", "").rstrip("/")
LLM_ENDPOINT = f"{LLM_BASE_URL}/api/v1/tender-risk" if LLM_BASE_URL else ""

report_generator = ReportGenerator()

def _tenders_to_payload(tenders: List[TenderRiskItem]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for t in tenders:
        payload.append(
            {
                "id": t.id,
                "name": t.name,
                "price": t.price,
                "organizer": t.organizer,
                "invited_supplier": t.invited_supplier,
                "method": t.method,
                "start_date": t.start_date,
                "end_date": t.end_date,
            }
        )
    return payload


async def call_llm_with_tenders(tenders: List[TenderRiskItem]) -> Dict[str, Any]:
    if not LLM_ENDPOINT:
        raise RuntimeError("LLM_URL is not set")

    payload = {
        "tenders": _tenders_to_payload(tenders)
    }

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🤖 SENDING RAW TENDERS TO LLM:")
    print(payload)
    print("🔗 LLM_ENDPOINT:", LLM_ENDPOINT)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(LLM_ENDPOINT, json=payload)
        resp.raise_for_status()
        llm_json = resp.json()

    print("\n✅ LLM RESPONSE RECEIVED")
    print(llm_json)

    return llm_json


async def call_local_risk_model(
    tenders: List[TenderRiskItem],
) -> Dict[str, Any]:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📥 NEW RISK REQUEST RECEIVED (LLM only)")
    print(f"📝 Count: {len(tenders)} tenders")

    for t in tenders:
        print("\n➡️ Incoming Tender:")
        print(t.model_dump())

    llm_output = await call_llm_with_tenders(tenders)

    print("\n📦 FINAL RESPONSE (LLM):")
    print(llm_output)

    return llm_output


async def generate_pdf_report_from_tenders(
    tenders: List[TenderRiskItem],
) -> bytes:
    llm_output = await call_llm_with_tenders(tenders)
    results = llm_output.get("results", [])

    if not results:
        raise RuntimeError("LLM не вернул результатов для генерации PDF-отчёта")
    pdf_filename = await report_generator.generate_pdf_report(results)
    pdf_path = os.path.join(report_generator.reports_dir, pdf_filename)
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"Файл PDF отчёта не найден: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    return pdf_bytes
