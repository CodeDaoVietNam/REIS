from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from backend.api.routes.provinces import province_meta
from backend.models.predict import DEFAULT_FORECAST, predict_forecast

logger = logging.getLogger(__name__)

router = APIRouter(tags=["forecast"])


@router.get("/api/forecast/{province_id}")
async def get_forecast(province_id: int) -> dict[str, Any]:
    province_meta(province_id)
    try:
        forecast = await predict_forecast(province_id)
    except Exception as exc:
        logger.warning("Forecast fallback for province %s: %s", province_id, exc)
        forecast = DEFAULT_FORECAST

    return {"province_id": province_id, **forecast}
