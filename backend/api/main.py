"""
FastAPI entrypoint for the REIS API.

This module intentionally keeps startup lightweight so health checks and
Swagger docs do not depend on Kafka, TimescaleDB, Redis, or ML artifacts.
"""
from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api import db, websocket
from backend.api.routes import forecast, insights, provinces
from backend.config.settings import settings

logger = logging.getLogger(__name__)

API_VERSION = "0.1.0"
LOCAL_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize lightweight API resources without requiring external infra."""
    logger.info("Starting REIS API")
    await db.open_pool(app)
    yield
    await db.close_pool(app)
    logger.info("Shutting down REIS API")


app = FastAPI(
    title="REIS API",
    description="Realtime Environmental Intelligence System API",
    version=API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or LOCAL_DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(provinces.router)
app.include_router(forecast.router)
app.include_router(insights.router)
app.include_router(websocket.router)


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return a lightweight service health payload."""
    return {
        "status": "ok",
        "service": "reis-api",
        "version": API_VERSION,
    }


__all__ = ["app"]
