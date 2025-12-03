from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.tenders import router as tenders_router
from routers.risk import router as risk_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders_router)
app.include_router(risk_router, prefix="/api/v1", tags=["risk"])

@app.get("/")
def root():
    return {"status": "ok"}
