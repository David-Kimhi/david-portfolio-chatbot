# backend/routes/chat_stream.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import json
import asyncio
from backend.utils.constants import MODEL

router = APIRouter(prefix="/chat", tags=["chat"])

client = OpenAI()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

async def openai_stream(messages):
    # stream from OpenAI and yield SSE events
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[m.model_dump() for m in messages],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            # SSE format: data: <json>\n\n
            yield f"data: {json.dumps({'delta': delta})}\n\n"
        await asyncio.sleep(0)  # let event loop breathe

    # signal end
    yield "data: [DONE]\n\n"

@router.post("/stream")
async def chat_stream(req: ChatRequest):
    async def event_generator():
        async for part in openai_stream(req.messages):
            yield part

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
