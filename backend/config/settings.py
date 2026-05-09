"""
settings.py — Load environment variables via pydantic-settings.

Dùng settings.xxx thay vì os.getenv() để:
  - Type-safe (int → int, không phải string)
  - Validation lúc startup (fail early nếu thiếu biến bắt buộc)
  - IDE autocomplete

Usage:
    from config.settings import settings
    print(settings.DB_HOST)
"""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Tất cả env vars cho REIS. Default values phù hợp cho local dev.

    Override bằng .env file hoặc environment variables thật:
        export DB_HOST=production-db.example.com
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",         # Ignore unexpected env vars
        case_sensitive=False,   # DB_HOST = db_host = Db_Host
    )

    # ── Database ────────────────────────────────────────────────────────────
    DB_HOST:     str = "localhost"
    DB_PORT:     int = 5432
    DB_USER:     str = "reis"
    DB_PASSWORD: str = "reis_secret"
    DB_NAME:     str = "reis_db"

    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL connection string dạng: postgresql://user:pass@host:port/db"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ── Redis ───────────────────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL: redis://host:port"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    # ── Kafka ────────────────────────────────────────────────────────────────
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP:    str = "reis-consumer-group"

    # ── Open-Meteo API ──────────────────────────────────────────────────────
    OPEN_METEO_TIMEOUT: int = 30   # seconds

    # ── Collection ───────────────────────────────────────────────────────────
    COLLECTION_INTERVAL_MINUTES: int = 15   # Chạy mỗi 15 phút

    # ── LLM (Generative AI) ────────────────────────────────────────────────
    LLM_API_KEY:    str = ""   # Backward-compatible Gemini key fallback
    LLM_MODEL:      str = "gemini-2.0-flash"
    LLM_TIMEOUT:    int = 10   # seconds
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL:   str = "gemini-2.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL:   str = "gpt-4o-mini"
    INSIGHT_CACHE_TTL_SECONDS: int = 3600

    # ── Alert ───────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID:    str = ""

    # ── MLflow ──────────────────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"


# ── Singleton instance ────────────────────────────────────────────────────────
# Import ở bất kỳ đâu → cùng một object, không tạo lại
settings = Settings()
