"""WebSocket route — uses ConnectionManager for efficient broadcast."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.ws_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket) -> None:
    """Accept WS connection and keep alive. Broadcast handled by manager."""
    await manager.connect(websocket)
    try:
        # Keep connection alive — wait for client messages (ping/pong)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
