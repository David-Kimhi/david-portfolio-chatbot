# backend/utils/responses.py
import json
import time
from typing import List, Optional, Any
import asyncio

from backend.utils.settings import get_async_openai
from backend.utils.constants import MODEL, SECURE_SYSTEM_PROMPT


async def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """Non-streaming LLM call — returns the full response text.

    Used for ingest-time preprocessing (e.g. question generation) where we
    need the complete output before continuing, not a stream of chunks.
    """
    client = get_async_openai()
    try:
        resp = await client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=max_tokens,
            timeout=30,
        )
        return resp.output_text or ""
    except Exception:
        # fallback to chat.completions
        cmpl = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_completion_tokens=max_tokens,
            timeout=30,
        )
        return cmpl.choices[0].message.content or ""


async def stream_llm(
    user_prompt: str,
    ctx_sources: Optional[List[Any]] = None,
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 600,
    throttle_sec: float = 0.1,
    context_embedding: Optional[List[float]] = None,
):
    """
    Generic streaming helper.

    Yields JSON lines:
      {"type":"chunk","data":"..."}
      ...
      {"type":"sources","data":[...]}
    """
    if ctx_sources is None:
        ctx_sources = []

    system_instr = system_prompt or SECURE_SYSTEM_PROMPT

    try:
        # OpenAI responses API – streaming
        resp = await get_async_openai().responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_instr},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            max_output_tokens=max_tokens,
            timeout=30
        )
        async for event in resp:
            delta = event.output_text_delta
            if delta:
                if throttle_sec:
                    await asyncio.sleep(throttle_sec)
                yield json.dumps(
                    {"type": "chunk", "data": delta},
                    ensure_ascii=False,
                ) + "\n"

    except Exception:
        # fallback to chat.completions streaming
        cmpl = await get_async_openai().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_instr},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            temperature=temperature,
            max_completion_tokens=max_tokens,
            timeout=30

        )
        async for chunk in cmpl:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield json.dumps(
                    {"type": "chunk", "data": delta},
                    ensure_ascii=False,
                ) + "\n"

    # after text – send sources and the updated context embedding
    payload: dict[str, Any] = {"type": "sources", "data": ctx_sources}
    if context_embedding is not None:
        payload["context_embedding"] = context_embedding
    yield json.dumps(payload, ensure_ascii=False) + "\n"
