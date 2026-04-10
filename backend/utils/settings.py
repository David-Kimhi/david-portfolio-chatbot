import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI
import chromadb


@lru_cache(maxsize=1)
def get_async_openai() -> AsyncOpenAI:
    """Create the client on first use so missing OPENAI_API_KEY does not block app import."""
    return AsyncOpenAI()


# Persistent Chroma directory: prefer CHROMA_DIR, fall back to a repo-local
# data directory, and finally /tmp if creation fails (e.g. read-only /app).
DEFAULT_PERSIST = os.getenv("CHROMA_DIR", "./data/chroma_store")
FALLBACK_PERSIST = os.getenv("CHROMA_DIR_FALLBACK", "/tmp/chroma_store")

PERSIST_DIR = DEFAULT_PERSIST
try:
    os.makedirs(PERSIST_DIR, exist_ok=True)
except OSError:
    # If we can't create the preferred path (read-only filesystem),
    # fall back to a writable temporary location.
    PERSIST_DIR = FALLBACK_PERSIST
    os.makedirs(PERSIST_DIR, exist_ok=True)

chroma = chromadb.PersistentClient(path=PERSIST_DIR)
coll = chroma.get_or_create_collection("portfolio_docs")
