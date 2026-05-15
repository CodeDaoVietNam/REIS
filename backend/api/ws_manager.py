"""
ws_manager.py — WebSocket connection manager with single-source broadcast.

Instead of each client polling the DB independently (N clients = N queries/15s),
a single background task polls the DB once, then broadcasts to all connected clients.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates efficiently.

    Architecture:
        - ONE background task polls DB every 15 seconds
        - Broadcasts the SAME payload to ALL connected clients
        - 100 clients = 1 DB query (not 100 queries)
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._broadcast_task: asyncio.Task | None = None
        self._latest_payload: dict[str, Any] | None = None

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("WS client connected (total=%d)", self.active_count)

        # Send cached payload immediately so client doesn't wait 15s
        if self._latest_payload:
            try:
                await websocket.send_json(self._latest_payload)
            except Exception:
                pass

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("WS client disconnected (total=%d)", self.active_count)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        """Send payload to all connected clients. Remove dead connections."""
        self._latest_payload = payload
        dead: list[WebSocket] = []

        for ws in list(self._connections):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections.discard(ws)

        if dead:
            logger.info("Removed %d dead WS connections", len(dead))

    async def start_broadcast_loop(self, app: Any, interval: int = 15) -> None:
        """Background task: poll DB once, broadcast to all clients."""
        from backend.api.routes.provinces import build_province_summaries

        logger.info("WS broadcast loop started (interval=%ds)", interval)
        while True:
            try:
                if not self._connections:
                    await asyncio.sleep(interval)
                    continue  # No clients → skip DB query entirely

                pool = getattr(app.state, "db_pool", None)
                try:
                    provinces = await build_province_summaries(pool)
                except Exception as exc:
                    logger.warning("WS broadcast DB query failed: %s", exc)
                    provinces = []

                payload = {
                    "type": "live_update",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "provinces": provinces,
                    "client_count": self.active_count,
                }
                await self.broadcast(payload)
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("WS broadcast loop cancelled")
                break
            except Exception as exc:
                logger.error("WS broadcast loop error: %s", exc)
                await asyncio.sleep(5)

    def start(self, app: Any) -> None:
        """Start the broadcast loop as a background task."""
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(
                self.start_broadcast_loop(app)
            )

    async def stop(self) -> None:
        """Stop the broadcast loop."""
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        # Close all connections
        for ws in list(self._connections):
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()


# Singleton instance
manager = ConnectionManager()
