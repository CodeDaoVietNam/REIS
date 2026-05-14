from __future__ import annotations

import logging
from typing import Any

import asyncpg
from fastapi import Request

from backend.config.settings import settings

logger = logging.getLogger(__name__)


async def open_pool(app: Any) -> None:
    """Attach an asyncpg pool when Postgres is reachable."""
    try:
        app.state.db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=1,
            max_size=5,
            timeout=2,
            command_timeout=10,
        )
        logger.info("Database pool initialized")
    except Exception as exc:  # pragma: no cover - depends on local infra.
        app.state.db_pool = None
        logger.warning("Database pool unavailable; API will use fallbacks: %s", exc)


async def close_pool(app: Any) -> None:
    pool = getattr(app.state, "db_pool", None)
    if pool is not None:
        await pool.close()
        app.state.db_pool = None
        logger.info("Database pool closed")


def get_pool(request: Request) -> asyncpg.Pool | None:
    return getattr(request.app.state, "db_pool", None)
