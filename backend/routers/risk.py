from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.risk import TenderRiskRequest
from services.tender_risk_service import (
    call_local_risk_model,
    generate_pdf_report_from_tenders,
)

router = APIRouter()

@router.post("/tender-risk")
async def tender_risk(body: TenderRiskRequest):
    print("...debug...")
    return await call_local_risk_model(body.tenders)


@router.post("/tender-risk/pdf")
async def tender_risk_pdf(body: TenderRiskRequest):
    try:
        pdf_bytes = await generate_pdf_report_from_tenders(body.tenders)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="PDF report generation is not implemented yet",
        )

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="tender_risk_report.pdf"'
        },
    )
