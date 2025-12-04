import os
from typing import List, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

CHATBOT_ENDPOINT = os.getenv("CHATBOT_ENDPOINT")


class HistoryMessage(BaseModel):
    role: Literal["user", "bot"]
    text: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: List[HistoryMessage] = []


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    payload = {
        "message": body.message,
        # при желании сюда можно позже пробрасывать history:
        "conversation_history": [
            {"role": m.role, "text": m.text} for m in body.conversation_history
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(CHATBOT_ENDPOINT, json=payload)
            resp.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502, detail="Chatbot service temporarily unavailable"
        )

    data = resp.json()
    answer = data.get("response") or ""
    if not isinstance(answer, str):
        answer = str(answer)

    return ChatResponse(answer=answer)
