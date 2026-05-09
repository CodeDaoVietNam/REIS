"""
config/ — REIS configuration package.

Exports settings (from .settings) and constants (from .constants).
Import anywhere with: from config import settings, PROVINCES, KAFKA_TOPICS, etc.
"""
from .settings import settings
from .constants import (
    PROVINCES,
    KAFKA_TOPICS,
    API_BASE_URL,
    AQ_BASE_URL,
)

__all__ = [
    "settings",
    "PROVINCES",
    "KAFKA_TOPICS",
    "API_BASE_URL",
    "AQ_BASE_URL",
]
