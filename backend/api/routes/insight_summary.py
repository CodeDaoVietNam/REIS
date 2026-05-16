from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from backend.api.db import get_pool
from backend.api.rate_limit import general_limiter
from backend.insights.eda_findings import build_insight_summary_payload

router = APIRouter(tags=["insight-summary"])


@router.get("/api/insight-summary")
async def get_insight_summary(request: Request) -> dict[str, Any]:
    """Return EDA-backed findings enriched with live DB metrics when available."""
    general_limiter.check(request)
    return await build_insight_summary_payload(get_pool(request))
