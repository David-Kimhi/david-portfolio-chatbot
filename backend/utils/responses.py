# backend/utils/responses.py
import json
import time
from typing import List, Optional, Any

from backend.utils.settings import openai_client
from backend.utils.constants import MODEL, SECURE_SYSTEM_PROMPT


def stream_llm(
    user_prompt: str,
    ctx_sources: Optional[List[Any]] = None,
    *,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 600,
    throttle_sec: float = 0.1,
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
        resp = openai_client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_instr},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            max_output_tokens=max_tokens,
        )
        for event in resp:
            delta = event.output_text_delta
            if delta:
                if throttle_sec:
                    time.sleep(throttle_sec)
                yield json.dumps(
                    {"type": "chunk", "data": delta},
                    ensure_ascii=False,
                ) + "\n"

    except Exception:
        # fallback to chat.completions streaming
        cmpl = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_instr},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        for chunk in cmpl:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield json.dumps(
                    {"type": "chunk", "data": delta},
                    ensure_ascii=False,
                ) + "\n"

    # after text – send sources (empty list is fine)
    yield json.dumps(
        {"type": "sources", "data": ctx_sources},
        ensure_ascii=False,
    ) + "\n"
