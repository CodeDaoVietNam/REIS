"""
backend.ingestion — Data ingestion package.

Modules:
    collector.py   — Fetch weather + AQ data from Open-Meteo API
    validator.py  — Pydantic v2 validation
    producer.py   — Kafka producer + Redis DLQ
    scheduler.py  — APScheduler orchestration
"""
