from typing import List


def chunk_text(text: str) -> List[str]:
    """Return the full text as a single chunk (no splitting)."""
    stripped = text.strip()
    return [stripped] if stripped else []
