# backend/routes/trunslate.py
import json
from enum import Enum

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.utils.settings import openai_client
from backend.utils.constants import MODEL, HEB_RANGE
from backend.utils.responses import stream_llm

router = APIRouter(prefix="/trunslate", tags=["trunslate"])


def is_hebrew_text(text: str) -> bool:
    return bool(HEB_RANGE.search(text or ""))


class TargetLang(str, Enum):
    he = "he"
    en = "en"


class TranslateReq(BaseModel):
    text: str
    target_lang: TargetLang  # "he" or "en"


TRANSLATE_SYSTEM_PROMPT = (
    "You are a careful, high-quality translation engine. "
    "You translate between Hebrew and English. "
    "Always output only the translated text, without explanations or markup."
)


def _build_prompt(text: str, target_lang: str) -> str:
    lang_name = "Hebrew" if target_lang == "he" else "English"
    return (
        f"Translate the following text to {lang_name}. "
        f"Keep the original meaning, be natural and fluent, "
        f"and don't add explanations.\n\n{text}"
    )


# ---------- INTERNAL HELPER (non-streaming) ----------

def translate_text(text: str, target_lang: str) -> str:
    """
    Internal helper – non-streaming translation.
    target_lang: 'he' or 'en'
    """
    if not text or not text.strip():
        return text

    prompt = _build_prompt(text, target_lang)

    resp = openai_client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_output_tokens=600,
    )
    return resp.output_text.strip()


# ---------- ROUTES ----------

@router.post("/")
def translate_route(req: TranslateReq) -> str:
    """
    Non-streaming HTTP endpoint.
    Returns translated text as plain string.
    """
    return translate_text(req.text, req.target_lang.value)


@router.post("/stream")
def translate_stream_route(req: TranslateReq):
    """
    Streaming HTTP endpoint (SSE) for translation.
    Same SSE JSON format as /ask/stream:
    - {"type":"chunk","data": "..."}
    - ...
    - {"type":"sources","data":[]}
    """
    text = req.text or ""
    if not text.strip():
        # Fast no-op: just emit empty sources
        def _empty():
            yield json.dumps({"type": "sources", "data": []}, ensure_ascii=False) + "\n"

        return StreamingResponse(_empty(), media_type="text/event-stream")

    user_prompt = _build_prompt(text, req.target_lang.value)

    return StreamingResponse(
        stream_llm(
            user_prompt=user_prompt,
            ctx_sources=[],  # no RAG sources for translation
            system_prompt=TRANSLATE_SYSTEM_PROMPT,
            temperature=0.0,
        ),
        media_type="text/event-stream",
    )
