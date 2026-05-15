"""
rate_limit.py — Simple in-memory rate limiter for API endpoints.

Protects expensive endpoints (especially LLM insight generation)
from being spammed. Uses a sliding window counter per IP.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory sliding window rate limiter.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Time window in seconds.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, client_id: str) -> None:
        """Remove expired entries from the window."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[client_id] = [
            t for t in self._requests[client_id] if t > cutoff
        ]

    def check(self, request: Request) -> None:
        """Check rate limit. Raises HTTPException(429) if exceeded."""
        client_id = self._get_client_ip(request)
        self._cleanup(client_id)

        if len(self._requests[client_id]) >= self.max_requests:
            logger.warning(
                "Rate limit exceeded for %s (%d/%d in %ds)",
                client_id, len(self._requests[client_id]),
                self.max_requests, self.window_seconds,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
            )

        self._requests[client_id].append(time.time())


# Pre-configured limiters for different endpoint types
general_limiter = RateLimiter(max_requests=120, window_seconds=60)  # 120 req/min
insight_limiter = RateLimiter(max_requests=10, window_seconds=60)   # 10 req/min (LLM is expensive)
