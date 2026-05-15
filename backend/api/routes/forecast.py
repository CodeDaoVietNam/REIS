from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request

from backend.api.db import get_pool
from backend.api.inference_cache import get_cached_inference
from backend.api.rate_limit import general_limiter
from backend.api.routes.provinces import province_meta
from backend.models.predict import DEFAULT_FORECAST, predict_forecast

logger = logging.getLogger(__name__)

router = APIRouter(tags=["forecast"])


@router.get("/api/forecast/{province_id}")
async def get_forecast(province_id: int, request: Request) -> dict[str, Any]:
    general_limiter.check(request)
    province_meta(province_id)
    pool = get_pool(request)
    try:
        inference, _source = await get_cached_inference(province_id, pool=pool)
        forecast = inference.get("forecast", DEFAULT_FORECAST)
    except Exception as exc:
        logger.warning("Forecast fallback for province %s: %s", province_id, exc)
        try:
            forecast = await predict_forecast(province_id, pool=pool)
        except Exception:
            forecast = DEFAULT_FORECAST

    return {"province_id": province_id, **forecast}
