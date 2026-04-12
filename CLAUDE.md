# CLAUDE.md — Instructions for Claude Code

> This file is read automatically by Claude Code before any action.
> It contains project conventions, commands, constraints, and architecture decisions.

---

## PROJECT OVERVIEW

**Name:** Realtime Environmental Intelligence System (REIS)
**Purpose:** Real-time air quality monitoring for 63 Vietnamese provinces using Streaming Data + Predictive AI + Generative AI.
**Stack:** Python 3.11 (backend) · TypeScript/React 18 (frontend) · Docker Compose (infra)

---

## CRITICAL RULES — READ BEFORE ANY ACTION

1. **NEVER run `docker-compose down -v`** — this destroys all data volumes including trained models.
2. **NEVER commit `.env` files** — use `.env.example` as template only.
3. **NEVER call the LLM API directly in tests** — mock `llm_client.py` with fixtures.
4. **NEVER modify `airflow/dags/weekly_retrain.py`** without running `pytest tests/test_dag.py` first.
5. **NEVER use `SELECT *` on `env_readings`** — it has millions of rows. Always add time bounds.
6. **ALWAYS use async/await** in FastAPI route handlers — no sync blocking calls.
7. **ALWAYS go through Kafka** for data writes — never write directly to TimescaleDB from the collector.

---

## ESSENTIAL COMMANDS

### Development
```bash
# Start all infrastructure
docker-compose up -d

# Check all services are healthy
docker-compose ps

# View logs for a specific service
docker-compose logs -f fastapi
docker-compose logs -f kafka

# Start backend pipeline (3 separate terminals)
python backend/ingestion/scheduler.py        # Data collector
python backend/processing/consumer.py        # Kafka consumer
uvicorn backend.api.main:app --reload --port 8000  # API server

# Start frontend
cd frontend && npm run dev

# Reset demo state (clear simulator injections)
python tools/simulator.py --reset
```

### Testing
```bash
# Run all tests (from backend/ directory)
cd backend && pytest tests/ -v

# Run specific test files
pytest tests/test_validator.py -v
pytest tests/test_isolation_forest.py -v
pytest tests/test_forecast.py -v
pytest tests/test_prompt_builder.py -v
pytest tests/test_api_routes.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Type checking
mypy backend/ --ignore-missing-imports

# Lint
ruff check backend/
```

### Database
```bash
# Connect to TimescaleDB
docker exec -it reis-timescaledb psql -U reis -d reis_db

# Useful queries (always use time bounds!)
# Last 1 hour data for HCMC (province_id=48)
SELECT time, pm2_5, aqi, anomaly_score
FROM env_readings
WHERE province_id = 48 AND time > NOW() - INTERVAL '1 hour'
ORDER BY time DESC;

# Check data freshness
SELECT province_id, MAX(time) as last_seen
FROM env_readings
GROUP BY province_id
ORDER BY last_seen DESC;
```

### Demo
```bash
# Inject PM2.5 spike into HCMC (for live demo)
python tools/simulator.py --province hcm --pm25 350 --duration 600

# Inject spike into Hanoi
python tools/simulator.py --province hanoi --aqi 280

# Inject multi-province event
python tools/simulator.py --province hcm,hanoi --pm25 300 --duration 300
```

### MLflow & Airflow
```bash
# Manually trigger retraining DAG
airflow dags trigger weekly_retrain

# List registered models in MLflow
mlflow models list

# Compare experiment runs
# Open http://localhost:5000 → Experiments → weekly_retrain
```

---

## ARCHITECTURE — DATA FLOW

```
Open-Meteo API (batch 63 provinces)
    │
    ▼
APScheduler (every 15 min)
    │
    ▼
Pydantic Validator → [INVALID] → Redis Dead Letter Queue
    │ [VALID]
    ▼
Kafka Topic: env.readings.raw
    │
    ▼
Kafka Consumer → Feature Engineering → TimescaleDB (hypertable: env_readings)
                                                │
                        ┌───────────────────────┼───────────────────────┐
                        ▼                       ▼                       ▼
              Isolation Forest           LSTM/Prophet              Redis Cache
              (anomaly_score)           (12h forecast)         (LLM insight TTL=1h)
                        │                       │                       │
                        └───────────────────────┼───────────────────────┘
                                                ▼
                                         FastAPI + WebSocket
                                                │
                                    ┌───────────┴───────────┐
                                    ▼                       ▼
                             React Dashboard         Alert Manager
                             (real-time map)     (Telegram if score>0.85)
```

---

## DATABASE SCHEMA

### Main table: `env_readings` (TimescaleDB hypertable)

```sql
CREATE TABLE env_readings (
    time              TIMESTAMPTZ NOT NULL,
    province_id       INT NOT NULL,           -- FK → provinces(id)
    temperature       FLOAT4,                 -- °C, range: -20 to 60
    humidity          FLOAT4,                 -- %, range: 0 to 100
    wind_speed        FLOAT4,                 -- km/h, >= 0
    precipitation     FLOAT4,                 -- mm, >= 0
    pm2_5             FLOAT4,                 -- µg/m³, range: 0 to 1000
    pm10              FLOAT4,                 -- µg/m³, range: 0 to 1000
    aqi               INT,                    -- US EPA AQI, range: 0 to 500
    no2               FLOAT4,                 -- µg/m³
    ozone             FLOAT4,                 -- µg/m³
    uv_index          FLOAT4,                 -- 0 to 20
    anomaly_score     FLOAT4,                 -- Isolation Forest: 0.0 to 1.0
    is_anomaly        BOOLEAN DEFAULT FALSE,
    raw_json          JSONB                   -- original API payload
);
SELECT create_hypertable('env_readings', 'time');
```

### Key indexes
```sql
CREATE INDEX ON env_readings (province_id, time DESC);
CREATE INDEX ON env_readings (is_anomaly, time DESC) WHERE is_anomaly = TRUE;
```

### Lookup table: `provinces`
```sql
-- province_id 1-63, includes name_vi, name_en, lat, lon, region (Bắc/Trung/Nam)
```

---

## MODULE CONTRACTS (public interfaces)

### `backend/models/predict.py`
```python
# ONLY interface to ML models — do NOT import lstm_model or prophet_model directly
from models.predict import predict_forecast, predict_anomaly

forecast: ForecastResult = await predict_forecast(
    province_id=48,
    history_hours=48
)
# Returns: ForecastResult(values=[...12 floats], lower=[...], upper=[...], model_used="lstm")

anomaly: AnomalyResult = await predict_anomaly(feature_vector=np.array([...7 floats...]))
# Returns: AnomalyResult(score=0.73, label="ANOMALY", is_critical=False)
```

### `backend/insights/llm_client.py`
```python
# Always go through insight_cache.py — never call llm_client directly in routes
from insights.insight_cache import get_or_generate_insight

insight: InsightResult = await get_or_generate_insight(
    province_id=48,
    current_data=CurrentData(...),
    forecast=ForecastResult(...),
    anomaly=AnomalyResult(...)
)
# Returns from Redis cache if available (TTL=1h), otherwise calls LLM
```

### `backend/ingestion/validator.py`
```python
# Pydantic v2 models
class EnvironmentReading(BaseModel):
    province_id: int
    time: datetime
    temperature: confloat(ge=-20, le=60)    # type: ignore
    humidity: confloat(ge=0, le=100)
    pm2_5: confloat(ge=0, le=1000)
    pm10: confloat(ge=0, le=1000)
    aqi: conint(ge=0, le=500)
    # ... other fields
```

---

## PYTHON CONVENTIONS

### File naming
- snake_case for all Python files: `feature_engineer.py`, `llm_client.py`
- Prefix test files with `test_`: `test_validator.py`
- Constants file: `backend/config/constants.py`

### Import order (ruff enforces this)
```python
# 1. Standard library
import asyncio
from datetime import datetime

# 2. Third-party
import numpy as np
from fastapi import FastAPI

# 3. Local (absolute from backend/)
from models.predict import predict_forecast
from insights.insight_cache import get_or_generate_insight
```

### Async patterns
```python
# CORRECT — use asyncio.gather for parallel AI inference
forecast, anomaly = await asyncio.gather(
    predict_forecast(province_id, history_hours=48),
    predict_anomaly(feature_vector)
)

# WRONG — sequential, slow
forecast = await predict_forecast(...)
anomaly = await predict_anomaly(...)  # waits for forecast unnecessarily
```

### Error handling
```python
# ALWAYS handle LLM API failures gracefully
try:
    insight = await llm_client.generate(prompt)
except (APITimeoutError, RateLimitError) as e:
    logger.warning(f"LLM API failed: {e}, using fallback template")
    insight = build_fallback_insight(current_data, anomaly)
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)  # module-level, never root logger

# Structured logging for data pipeline events
logger.info("Collected data", extra={"provinces": 63, "duration_ms": 450})
logger.warning("Anomaly detected", extra={"province_id": 48, "score": 0.87})
```

---

## TYPESCRIPT/REACT CONVENTIONS

### WebSocket hook pattern
```typescript
// Use the custom hook — never create raw WebSocket connections in components
import { useAQIStream } from '@/hooks/useWebSocket';

const { data, isConnected, lastUpdate } = useAQIStream();
// Hook handles: auto-reconnect, exponential backoff, cleanup on unmount
```

### AQI Color Scale
```typescript
// Always use this helper — never hardcode colors
import { getAQIColor, getAQILabel } from '@/utils/aqiScale';

// Returns: { bg: '#92d14f', text: '#2d6a0a', label: 'Tốt' }
const { bg, text, label } = getAQIColor(aqi);
```

### Component naming
- PascalCase components: `AQIMap.tsx`, `ForecastChart.tsx`, `InsightCard.tsx`
- camelCase hooks: `useWebSocket.ts`, `useAQIData.ts`
- SCREAMING_SNAKE for constants: `MAX_RECONNECT_ATTEMPTS`

---

## KAFKA TOPICS

| Topic | Producer | Consumer | Retention |
|-------|----------|----------|-----------|
| `env.readings.raw` | `ingestion/producer.py` | `processing/consumer.py` | 24h |
| `env.anomalies` | Isolation Forest service | Alert Manager | 7 days |
| `env.dead-letter` | `ingestion/validator.py` | Manual review | 30 days |

**Partition key:** `province_id` — ensures ordering per province.

---

## ML MODEL DETAILS

### LSTM Architecture
```
Input: (batch, 48, 12)  ← 48 hours, 12 features
LSTM(64, return_sequences=True)
Dropout(0.2)
LSTM(32)
Dropout(0.2)
Dense(12)  ← 12-hour forecast output
```
- **Loss:** MSE
- **Optimizer:** Adam, lr=0.001
- **Training:** 50 epochs, early stopping patience=10
- **Saved as:** `backend/models/artifacts/lstm_champion.pkl` (MLflow managed)

### Feature Engineering Order (must match training!)
```python
FEATURE_COLUMNS = [
    'pm2_5', 'pm10', 'aqi', 'no2', 'ozone',          # Air quality
    'temperature', 'humidity', 'wind_speed',            # Weather
    'pm2_5_lag_1h', 'pm2_5_lag_3h', 'pm2_5_lag_6h',   # Lag features
    'aqi_rolling_mean_3h', 'aqi_rolling_std_6h',        # Rolling stats
]
TARGET_COLUMN = 'aqi'
FORECAST_HORIZON = 12  # hours
HISTORY_WINDOW = 48    # hours
```

### Isolation Forest Config
```python
IsolationForest(
    contamination=0.05,    # ~5% of data expected as anomalies
    n_estimators=200,
    random_state=42
)
# Score > 0.70 → is_anomaly = True
# Score > 0.85 → trigger Alert Manager
```

---

## LLM PROMPT TEMPLATE

```python
SYSTEM_PROMPT = """Bạn là chuyên gia phân tích chất lượng không khí tại Việt Nam.
Trả lời LUÔN bằng tiếng Việt, ngắn gọn, dưới 150 từ.
Cấu trúc bắt buộc: (1) Hiện trạng, (2) Nguyên nhân có thể, (3) Dự báo, (4) Khuyến nghị.
Nếu is_critical=True, bắt đầu bằng '⚠️ CẢNH BÁO:'."""

USER_PROMPT_TEMPLATE = """
Tỉnh/Thành phố: {province_name}
Thời điểm: {timestamp}

CHỈ SỐ HIỆN TẠI:
- AQI: {aqi} ({aqi_category})
- PM2.5: {pm2_5} µg/m³
- PM10: {pm10} µg/m³
- Nhiệt độ: {temperature}°C, Gió: {wind_speed} km/h

PHÁT HIỆN BẤT THƯỜNG: {anomaly_label} (score: {anomaly_score:.2f})

DỰ BÁO 3-12 GIỜ TỚI:
- T+3h: AQI {forecast_3h}
- T+6h: AQI {forecast_6h}
- T+12h: AQI {forecast_12h}
"""
```

---

## DOCKER SERVICES

| Service | Container name | Port | Data volume |
|---------|---------------|------|-------------|
| Zookeeper | reis-zookeeper | 2181 | — |
| Kafka | reis-kafka | 9092 | `kafka-data` |
| TimescaleDB | reis-timescaledb | 5432 | `pgdata` ⚠️ |
| Redis | reis-redis | 6379 | `redis-data` |
| Airflow | reis-airflow | 8080 | `airflow-logs` |
| MLflow | reis-mlflow | 5000 | `mlflow-artifacts` ⚠️ |
| FastAPI | reis-fastapi | 8000 | — |
| React | reis-frontend | 3000 | — |

⚠️ = **Never delete these volumes** — contains trained models and historical data.

---

## AIRFLOW DAG: `weekly_retrain`

**Schedule:** `0 2 * * 0` (Every Sunday at 2:00 AM)

**Task sequence:**
```
extract_data → feature_engineering → train_lstm ──┐
                                    → train_prophet ──┤→ evaluate → compare
                                                              │
                                              ┌─────────────┴─────────────┐
                                         [improved]               [degraded]
                                              │                       │
                                    register_mlflow          keep_current
                                              │                       │
                                         hot_swap              log_drift
                                              │                       │
                                         send_success         send_warning
```

**MLflow experiment name:** `reis_weekly_retrain`
**Model registry name:** `reis_aqi_forecaster`
**Stages:** `Staging` → (if MAE improves) → `Production`

---

## TESTING CHECKLIST

Before submitting any code change, verify:

- [ ] `pytest tests/ -v` — all tests pass
- [ ] `ruff check backend/` — no lint errors
- [ ] `mypy backend/ --ignore-missing-imports` — no type errors
- [ ] LLM calls are mocked (not real API calls in tests)
- [ ] New DB queries have time bounds
- [ ] No `print()` statements (use `logger.*`)
- [ ] New async functions are awaited properly

---

## COMMON GOTCHAS

1. **TimescaleDB chunk interval:** Default is 7 days. For queries spanning >30 days, use `time_bucket()` for performance, not raw `GROUP BY time`.

2. **Kafka auto-offset reset:** Consumer is set to `latest` in production, `earliest` in tests. Don't change this without updating test fixtures.

3. **Prophet timezone:** Prophet expects timezone-naive datetimes. Strip timezone before feeding: `df['ds'] = df['time'].dt.tz_localize(None)`.

4. **Isolation Forest scoring:** `sklearn` returns negative scores where more negative = more anomalous. The wrapper in `isolation_forest.py` inverts this to `0.0–1.0` (higher = more anomalous). Don't use sklearn's raw output directly.

5. **React WebSocket reconnect:** The `useWebSocket` hook uses exponential backoff (1s → 2s → 4s → max 30s). Don't add additional retry logic in components.

6. **Gemini Flash token limit:** Max 8192 tokens per request. The prompt builder caps context to prevent overflow. Never bypass `prompt_builder.py`.

7. **Feature column order:** The LSTM model is sensitive to feature column order. Always use `FEATURE_COLUMNS` constant from `constants.py` — never hardcode column lists.

---

## FILE SIZE & PERFORMANCE LIMITS

- Single Kafka message: max 1MB (default)
- Redis insight value: max 10KB per key
- API response time target: p95 < 200ms
- WebSocket broadcast interval: 15 minutes (matches data collection)
- LLM response timeout: 10 seconds (then fallback template)
- LSTM inference timeout: 500ms per province

---

## WHEN ADDING NEW FEATURES

1. **New data source** → Add validator schema first, then producer, then consumer
2. **New ML model** → Add to `models/` directory, expose through `predict.py` interface, add MLflow logging
3. **New API endpoint** → Add route in `api/routes/`, add OpenAPI docstring, add test in `tests/test_api_routes.py`
4. **New React component** → Place in `frontend/src/components/`, add prop types with TypeScript interfaces
5. **New Airflow task** → Add to existing DAG if related, create new DAG only if independent schedule
