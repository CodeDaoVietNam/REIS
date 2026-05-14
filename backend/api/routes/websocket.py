from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.routes.provinces import build_province_summaries

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            pool = getattr(websocket.app.state, "db_pool", None)
            try:
                provinces = await build_province_summaries(pool)
            except Exception as exc:
                logger.warning("WebSocket live payload fallback: %s", exc)
                provinces = []

            await websocket.send_json(
                {
                    "type": "live_update",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "provinces": provinces,
                }
            )
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
