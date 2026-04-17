"""Thin analytics layer backed by PostgreSQL (asyncpg).

All functions are no-op safe: if the connection pool is ``None`` (e.g. no
DATABASE_URL configured) every public function returns immediately so the rest
of the app keeps working without a database.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any, Optional

import asyncpg                      # type: ignore[import-untyped]

from backend.utils.logger import log

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id            SERIAL PRIMARY KEY,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    event_type    TEXT NOT NULL,
    ip_hash       TEXT NOT NULL,
    question      TEXT,
    language      TEXT,
    score         REAL,
    sources_count INTEGER,
    latency_ms    REAL
);
"""


async def init_pool() -> Optional[asyncpg.Pool]:
    """Create the asyncpg connection pool and ensure the events table exists."""
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        log.warning("ANALYTICS | DATABASE_URL not set — analytics disabled")
        return None
    try:
        pool: asyncpg.Pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
        async with pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE)
        log.info("ANALYTICS | pool ready, events table ensured")
        return pool
    except Exception as exc:
        log.error("ANALYTICS | pool init failed: %s", exc)
        return None


def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()


async def log_event(
    pool: Optional[asyncpg.Pool],
    *,
    event_type: str,
    ip: str,
    question: Optional[str] = None,
    language: Optional[str] = None,
    score: Optional[float] = None,
    sources_count: Optional[int] = None,
    latency_ms: Optional[float] = None,
) -> None:
    """Insert a single analytics row. Silently skipped when pool is None."""
    if pool is None:
        return
    try:
        await pool.execute(
            """
            INSERT INTO events (event_type, ip_hash, question, language, score, sources_count, latency_ms)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            event_type,
            _hash_ip(ip),
            (question or "")[:200],
            language,
            score,
            sources_count,
            latency_ms,
        )
    except Exception as exc:
        log.error("ANALYTICS | log_event failed: %s", exc)


async def get_stats(pool: Optional[asyncpg.Pool]) -> dict[str, Any]:
    """Return basic aggregates for the public /api/stats endpoint."""
    empty: dict[str, Any] = {"total_questions": 0, "languages": {}, "avg_relevance": None}
    if pool is None:
        return empty
    try:
        async with pool.acquire() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM events WHERE event_type = 'ask'"
            )
            lang_rows = await conn.fetch(
                "SELECT language, COUNT(*) AS cnt FROM events "
                "WHERE event_type = 'ask' AND language IS NOT NULL "
                "GROUP BY language"
            )
            avg_rel = await conn.fetchval(
                "SELECT AVG(score) FROM events WHERE event_type = 'relevance' AND score IS NOT NULL"
            )
        return {
            "total_questions": total or 0,
            "languages": {r["language"]: r["cnt"] for r in lang_rows},
            "avg_relevance": round(float(avg_rel), 4) if avg_rel is not None else None,
        }
    except Exception as exc:
        log.error("ANALYTICS | get_stats failed: %s", exc)
        return empty
