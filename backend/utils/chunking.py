from typing import List


def chunk_text(text: str, min_chunk_chars: int = 100) -> List[str]:
    """Split *text* on single newlines, then greedily merge short fragments.

    Lines shorter than *min_chunk_chars* are merged with the next line so that
    standalone headings and short bullets become part of a larger, more
    meaningful chunk.  Empty lines are skipped outright.
    """
    lines = text.split("\n")
    chunks: List[str] = []
    buf = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if buf:
            buf += "\n" + stripped
        else:
            buf = stripped

        if len(buf) >= min_chunk_chars:
            chunks.append(buf)
            buf = ""

    if buf:
        if chunks:
            chunks[-1] += "\n" + buf
        else:
            chunks.append(buf)

    return chunks
