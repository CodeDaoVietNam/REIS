# REIS — System Architecture

> **Realtime Environmental Intelligence System**  
> Hệ thống giám sát môi trường thế hệ mới: Streaming Data × Predictive AI × Generative AI

---

## Table of Contents

- [Overview](#overview)
- [System Architecture — 5 Layers](#system-architecture--5-layers)
- [Data Flow](#data-flow)
- [Layer Details](#layer-details)
  - [Layer 1: Data Ingestion](#layer-1-data-ingestion)
  - [Layer 2: Message Broker & Storage](#layer-2-message-broker--storage)
  - [Layer 3: Dual-AI Inference Engine](#layer-3-dual-ai-inference-engine)
  - [Layer 4: Delivery & Alerting](#layer-4-delivery--alerting)
  - [Layer 5: MLOps & Auto-Retraining](#layer-5-mlops--auto-retraining)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Infrastructure — Docker Services](#infrastructure--docker-services)
- [Directory Structure](#directory-structure)
- [Key Design Decisions](#key-design-decisions)
- [Data Lifecycle](#data-lifecycle)
- [MLOps Pipeline](#mlops-pipeline)
- [Sequence — One Collection Cycle](#sequence--one-collection-cycle)

---

## Overview

REIS giải quyết vấn đề cốt lõi của các hệ thống giám sát môi trường hiện tại: **bị động**. Chúng chỉ hiển thị số liệu tại thời điểm hiện tại mà không dự báo, không phát hiện bất thường, không giải thích.

```
Vấn đề                          Giải pháp REIS
─────────────────────────────   ─────────────────────────────────────────
Chỉ hiển thị số liệu thô    →   Sinh insight bằng ngôn ngữ tự nhiên (LLM)
Không dự báo tương lai       →   LSTM / Prophet forecast 3–12h tới
Không phát hiện bất thường   →   Isolation Forest real-time anomaly scoring
Phải train lại thủ công      →   Airflow DAG auto-retrain mỗi Chủ Nhật
```

**Phạm vi:** 63 tỉnh thành Việt Nam · Cập nhật mỗi 15 phút · Dữ liệu lịch sử 90 ngày

---

## System Architecture — 5 Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REIS — 5-Layer Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  LAYER 1 — DATA INGESTION                                            │    │
│  │  Open-Meteo API ──► APScheduler (15min) ──► Pydantic Validator       │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                  │ valid                  │ invalid           │
│                          ┌───────▼────────┐      ┌────────▼────────┐        │
│  LAYER 2 — STORAGE       │  Apache Kafka  │      │   Redis DLQ     │        │
│                          │  Message Broker│      │  dead-letter    │        │
│                          └───────┬────────┘      └─────────────────┘        │
│                                  │                                            │
│                          ┌───────▼────────────────────────┐                 │
│                          │  TimescaleDB  │  Redis Cache    │                 │
│                          │  (hypertable) │  (LLM TTL 1h)  │                 │
│                          └───────┬───────────────┬─────────┘                 │
│                                  │               │                            │
│  ┌───────────────────────────────▼───────────────▼───────────────────┐      │
│  │  LAYER 3 — DUAL-AI INFERENCE ENGINE              [asyncio.gather]  │      │
│  │                                                                     │      │
│  │  ┌──────────────────────┐    ┌────────────────────────────────┐    │      │
│  │  │  Isolation Forest    │    │  LSTM / Prophet Forecasting    │    │      │
│  │  │  anomaly_score 0–1.0 │    │  AQI T+3h → T+12h forecast     │    │      │
│  │  └──────────┬───────────┘    └────────────────┬───────────────┘    │      │
│  │             │                                  │                     │      │
│  │             └──────────────┬───────────────────┘                    │      │
│  │                            ▼                                         │      │
│  │              ┌─────────────────────────┐                            │      │
│  │              │  LLM Insight Engine     │                            │      │
│  │              │  Gemini / GPT-4o-mini   │                            │      │
│  │              │  Redis Cache (TTL 1h)   │                            │      │
│  │              └─────────────────────────┘                            │      │
│  └───────────────────────────┬───────────────────────────────────────┘      │
│                               │                                               │
│  ┌────────────────────────────▼──────────────────────────────────────┐      │
│  │  LAYER 4 — DELIVERY & ALERTING                                     │      │
│  │  FastAPI (REST + WebSocket) ──► React Dashboard                    │      │
│  │                             ──► Alert Manager → Telegram / Email   │      │
│  └────────────────────────────────────────────────────────────────────┘      │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────── ┐     │
│  │  LAYER 5 — MLOPS & AUTO-RETRAINING               [background]      │     │
│  │  Airflow DAG (weekly) ──► Retrain ──► MLflow Registry ──► Hotswap  │     │
│  └─────────────────────────────────────────────────────────────────── ┘     │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
Open-Meteo API (batch 63 provinces)
         │
         │  HTTP GET — 1 request / 15 min
         ▼
   APScheduler
         │
         │  raw JSON payload
         ▼
  Pydantic Validator ──── invalid ──────► Redis Dead Letter Queue
         │
         │  validated EnvironmentReading
         ▼
   Kafka Producer
         │  topic: env.readings.raw
         │  key: province_id (same province → same partition → ordered)
         ▼
   Kafka Consumer
         │
         │  batch insert
         ▼
   TimescaleDB (hypertable: env_readings)
         │
         ├──────────────────────────────────────────┐
         │                                           │
         │  latest readings                          │  48h history
         ▼                                           ▼
  Isolation Forest                           LSTM / Prophet
  anomaly_score (0.0 – 1.0)                 forecast[T+1h..T+12h]
         │                                           │
         └──────────────────┬────────────────────────┘
                            │
                     Prompt Builder
                    (context assembly)
                            │
                            ▼
                   Redis Cache ──HIT──► FastAPI WS
                            │ MISS
                            ▼
                      Gemini LLM
                            │
                            ▼
                   Redis (store TTL=1h)
                            │
                            ▼
                       FastAPI WS
                    ╱              ╲
           React Dashboard      Alert Manager
           (map + charts)       (if score > 0.85)
                                      │
                              Telegram / Email
```

---

## Layer Details

### Layer 1: Data Ingestion

**Mục đích:** Thu thập dữ liệu thời tiết và chất lượng không khí cho 63 tỉnh theo lịch định kỳ.

**Thành phần:**

| Component | File | Vai trò |
|-----------|------|---------|
| `APScheduler` | `scheduler.py` | Trigger collection mỗi 15 phút |
| `Collector` | `collector.py` | Batch fetch từ Open-Meteo API |
| `Validator` | `validator.py` | Pydantic schema + range validation |
| `Producer` | `producer.py` | Publish vào Kafka topic |

**Chiến lược Batching:**

```
❌ Naive approach:  63 requests × 200ms = 12.6 giây, gần rate limit
✅ Batch approach:  1 request  × 400ms = 0.4  giây, dùng 1/63 quota
```

63 tọa độ gộp vào 1 URL duy nhất bằng cách join bằng dấu phẩy. Open-Meteo trả về `list` khi nhận nhiều tọa độ.

**Validation Rules:**

```
temperature:   -20°C  ≤ value ≤  60°C
humidity:        0%   ≤ value ≤ 100%
wind_speed:      0    ≤ value ≤ 200 km/h
pm2_5:           0    ≤ value ≤ 1000 µg/m³
pm10:            0    ≤ value ≤ 1000 µg/m³
aqi:             0    ≤ value ≤  500 (US EPA scale)
province_id:     1    ≤ value ≤   63
```

Data không pass → Dead Letter Queue trên Redis (key: `dead_letter_queue`).

**Data Sources:**

| API | Endpoint | Variables | Interval |
|-----|----------|-----------|----------|
| Open-Meteo Weather | `/v1/forecast` | temperature_2m, wind_speed_10m, relative_humidity_2m, precipitation | 15 min |
| Open-Meteo Air Quality | `/v1/air-quality` | pm10, pm2_5, carbon_monoxide, nitrogen_dioxide, ozone, uv_index, us_aqi | 1 hour |
| Open-Meteo Archive | `/v1/archive` | Tất cả biến trên dạng hourly | One-time historical fetch |

---

### Layer 2: Message Broker & Storage

**Kafka Topics:**

| Topic | Producer | Consumer | Retention | Partitions |
|-------|----------|----------|-----------|------------|
| `env.readings.raw` | `producer.py` | `consumer.py` | 24h | 3 |
| `env.dead-letter` | `validator.py` | Manual review | 30d | 1 |

**Partition Strategy:** Message key = `province_id`. Đảm bảo tất cả data của cùng 1 tỉnh vào cùng partition → consumer đọc theo đúng thứ tự thời gian.

**Commit Strategy:** Manual commit (`enable.auto.commit: false`). Consumer chỉ commit offset **sau khi** insert vào DB thành công. Nếu DB lỗi → không commit → đọc lại lần sau. Đảm bảo at-least-once delivery.

**Redis Roles:**

```
Role 1: LLM Insight Cache
  Key format:  insight:{province_id}:{aqi_bucket}:{is_critical}
  TTL:         3600 seconds (1 hour)
  Hit rate:    ~80% (AQI thay đổi chậm trong 1 giờ)

Role 2: Dead Letter Queue
  Key:         dead_letter_queue (list)
  Max size:    10,000 entries (ltrim enforced)

Role 3: Temporal Baseline (future)
  Key format:  baseline:{province_id}:{hour_of_day}:{day_of_week}
  Algorithm:   Welford's online mean/variance
```

**TimescaleDB:**

Hypertable `env_readings` được chunk theo 7 ngày. Query với time bound chỉ scan chunk cần thiết — không full table scan dù bảng có hàng triệu rows.

```sql
-- Tạo hypertable
SELECT create_hypertable('env_readings', 'time');

-- Chunk interval mặc định: 7 ngày
-- Sau 6 tháng: ~26 chunks, mỗi chunk ~270,000 rows (63 tỉnh × 24h × 7d)
```

---

### Layer 3: Dual-AI Inference Engine

Hai nhánh chạy **song song** qua `asyncio.gather()`.

**Nhánh A — Anomaly Detection (Isolation Forest):**

```
Input:   feature vector (7 dims): [pm2_5, pm10, aqi, no2, ozone, temperature, wind_speed]
         → normalized to [0, 1]

Process: 200 random decision trees
         Path length ↑ = normal point
         Path length ↓ = anomaly (easy to isolate)

Output:  anomaly_score: float [0.0, 1.0]
         0.00 – 0.69  → NORMAL
         0.70 – 0.84  → ANOMALY    → flag in DB
         0.85 – 1.00  → CRITICAL   → trigger Alert Manager

Latency: < 100ms per inference
```

**Nhánh B — Forecasting (LSTM + Prophet):**

```
Input:   48-hour history window × 12 features per timestep
         Features: pm2_5, pm10, aqi, no2, ozone, temperature,
                   humidity, wind_speed,
                   pm2_5_lag_1h, pm2_5_lag_3h, pm2_5_lag_6h,
                   aqi_rolling_mean_3h

LSTM Architecture:
  LSTM(64, return_sequences=True)
  Dropout(0.2)
  LSTM(32)
  Dropout(0.2)
  Dense(12)   ← 12-step forecast output

Output:  forecast[T+1h .. T+12h] with confidence interval
         {values: [float × 12], lower: [float × 12], upper: [float × 12]}

Prophet: univariate fallback, handles daily/weekly seasonality automatically
Champion: selected by MAE on holdout set, managed via MLflow
```

**LLM Insight Engine:**

```
System:  Domain expert in Vietnamese air quality
         Output language: Vietnamese, < 150 words
         Format: (1) Current state, (2) Cause, (3) Forecast, (4) Recommendation

Context: province_name + timestamp
       + current: AQI, PM2.5, PM10, temp, wind
       + anomaly: label + score
       + forecast: T+3h, T+6h, T+12h values

Cache:   Redis key = hash(province_id + aqi_bucket + anomaly_flag)
         aqi_bucket = (aqi // 20) * 20   ← AQI 121 và 125 → same bucket
         TTL = 3600s, hit rate ~80%

Provider: Gemini 1.5 Flash (primary), GPT-4o-mini (fallback)
Timeout:  10s → fallback to template message if exceeded
```

---

### Layer 4: Delivery & Alerting

**FastAPI Endpoints:**

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | `/api/provinces` | All 63 provinces, latest AQI | — |
| `GET` | `/api/province/{id}` | Detail: current + 48h history + forecast + insight | — |
| `GET` | `/api/forecast/{id}` | 12h forecast with CI bands | — |
| `GET` | `/api/anomalies` | Anomalies in last 24h | — |
| `GET` | `/api/insights/{id}` | LLM insight (from cache) | — |
| `WS` | `/ws/live` | Real-time push stream | — |
| `POST` | `/api/simulator/spike` | **DEMO ONLY** — inject PM2.5 spike | Internal |

**WebSocket Broadcast Flow:**

```
After each collection cycle:
  Scheduler → Consumer writes DB → Inference runs → LLM insight cached
    → FastAPI broadcasts JSON to all connected WebSocket clients
    → React Dashboard re-renders: map markers, charts, insight card

Client-side: useWebSocket hook with auto-reconnect (exponential backoff: 1s → 2s → 4s → max 30s)
Latency target: < 5 seconds from data collection to UI update
```

**Alert Manager:**

```
Trigger condition: anomaly_score > 0.85

Channels:
  Telegram Bot:  Instant push notification with province name, AQI, PM2.5
  Email (SMTP):  Detailed report with forecast trend

Rate limiting: 1 alert per province per 30 minutes (prevent alert fatigue)
```

---

### Layer 5: MLOps & Auto-Retraining

**Airflow DAG:** `weekly_retrain`  
**Schedule:** `0 2 * * 0` — Every Sunday at 2:00 AM

```
Task Graph:

extract_data ──► feature_engineering ──► train_lstm ──┐
                                         train_prophet ─┤
                                                        ▼
                                              evaluate_models
                                                        │
                              ┌─────────────────────────┤
                              │                         │
                         MAE improved              MAE not improved
                              │                         │
                    register_mlflow             keep_current_model
                              │                         │
                       hotswap_model             log_drift_report
                              │                         │
                       send_success              send_warning
```

**MLflow Model Registry:**

```
Experiment:  reis_weekly_retrain
Model name:  reis_aqi_forecaster

Stages:
  None      → newly trained, not yet evaluated
  Staging   → passed evaluation, waiting for comparison
  Production → currently serving (only 1 at a time)
  Archived  → replaced by newer model

Hotswap strategy (zero-downtime):
  1. Load new model into memory
  2. Run 5 inference samples as smoke test
  3. Swap pointer: inference module uses new model
  4. Unload old model
  5. User sees no interruption
```

**Evaluation Metrics:**

| Metric | Target | Description |
|--------|--------|-------------|
| MAE | < 15 AQI units | Mean Absolute Error |
| RMSE | < 25 AQI units | Root Mean Square Error |
| MAPE | < 20% | Mean Absolute Percentage Error |
| CI Coverage | > 90% | % actual values within confidence interval |
| Anomaly Precision | > 0.85 | True positive rate for spike detection |
| Anomaly Recall | > 0.80 | Recall on genuine spikes |

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Data Collection | Python requests + aiohttp | 3.11 | Async HTTP batch fetch |
| Scheduling | APScheduler | 3.10 | 15-min interval trigger |
| Validation | Pydantic v2 | 2.x | Schema validation + range check |
| Message Broker | Apache Kafka | 3.6 | At-least-once message delivery |
| Time-series DB | TimescaleDB | 2.13 (PG15) | Hypertable storage |
| Cache | Redis | 7.2 | LLM cache + Dead Letter Queue |
| ML Baseline | statsmodels ARIMA | 0.14 | Baseline comparison |
| ML Seasonal | Meta Prophet | 1.1.5 | Seasonality-aware forecasting |
| ML Deep Learning | TensorFlow/Keras LSTM | 2.14 | Multivariate time-series |
| Anomaly Detection | scikit-learn IsolationForest | 1.3 | Unsupervised spike detection |
| Model Registry | MLflow | 2.9 | Experiment tracking + versioning |
| Orchestration | Apache Airflow | 2.8 | Weekly retrain DAG |
| Backend API | FastAPI + Uvicorn | 0.104 | REST + WebSocket server |
| Frontend | React + Vite | 18 / 5.x | Real-time SPA dashboard |
| Maps | React Leaflet | 4.x | AQI heatmap visualization |
| Charts | Recharts | 2.x | Time-series + forecast charts |
| LLM | Gemini 1.5 Flash | API | Insight generation |
| Containerization | Docker Compose | 2.24 | Full infra in one command |

---

## Database Schema

### `provinces` (lookup table)

```sql
CREATE TABLE provinces (
    id          INT PRIMARY KEY,          -- 1–63
    name_vi     VARCHAR(100) NOT NULL,    -- Tên tiếng Việt
    name_en     VARCHAR(100),
    latitude    FLOAT NOT NULL,
    longitude   FLOAT NOT NULL,
    region      VARCHAR(10)               -- Bắc / Trung / Nam
);
```

### `env_readings` (hypertable — main data store)

```sql
CREATE TABLE env_readings (
    time            TIMESTAMPTZ NOT NULL,
    province_id     INT         NOT NULL REFERENCES provinces(id),

    -- Weather metrics
    temperature     FLOAT4,          -- °C, range: -20 to 60
    humidity        FLOAT4,          -- %, range: 0 to 100
    wind_speed      FLOAT4,          -- km/h, >= 0
    precipitation   FLOAT4,          -- mm, >= 0

    -- Air quality metrics
    pm2_5           FLOAT4,          -- µg/m³, range: 0 to 1000
    pm10            FLOAT4,          -- µg/m³, range: 0 to 1000
    aqi             INT,             -- US EPA scale: 0 to 500
    no2             FLOAT4,          -- µg/m³, >= 0
    ozone           FLOAT4,          -- µg/m³, >= 0
    uv_index        FLOAT4,          -- range: 0 to 20

    -- AI inference outputs
    anomaly_score   FLOAT4,          -- Isolation Forest: 0.0 to 1.0
    is_anomaly      BOOLEAN DEFAULT FALSE,

    -- Debug
    raw_json        JSONB            -- original API payload
);

-- Convert to hypertable (auto-chunk by 7 days)
SELECT create_hypertable('env_readings', 'time');

-- Indexes
CREATE INDEX idx_readings_province_time
    ON env_readings (province_id, time DESC);

CREATE INDEX idx_readings_anomaly
    ON env_readings (is_anomaly, time DESC)
    WHERE is_anomaly = TRUE;
```

**Estimated storage:**
```
63 provinces × 4 readings/hour × 24h × 365d
= ~2.2M rows/year
= ~1.5 GB/year (with JSONB)
= ~400 MB/year (without raw_json)
```

---

## API Reference

### REST Endpoints

**`GET /api/provinces`**
```json
[
  {
    "province_id": 48,
    "name_vi": "TP. Hồ Chí Minh",
    "lat": 10.7769,
    "lon": 106.7009,
    "aqi": 120,
    "pm2_5": 45.2,
    "temperature": 32.4,
    "anomaly_score": 0.12,
    "status": "NORMAL",
    "updated_at": "2024-01-15T08:00:00Z"
  }
]
```

**`GET /api/province/{id}`**
```json
{
  "current": { "aqi": 120, "pm2_5": 45.2, ... },
  "history": [ { "time": "...", "aqi": 115 }, ... ],
  "forecast": {
    "values":  [122, 125, 130, 128, 125, 120, 118, 115, 112, 110, 108, 105],
    "lower":   [100, 102, 105, 104, 101,  97,  95,  93,  90,  88,  86,  84],
    "upper":   [144, 148, 155, 152, 149, 143, 141, 137, 134, 132, 130, 126],
    "horizon": "T+1h to T+12h",
    "model":   "lstm"
  },
  "insight": {
    "text": "⚠️ CẢNH BÁO: PM2.5 tăng bất thường...",
    "generated_at": "2024-01-15T08:00:00Z",
    "cached": true
  }
}
```

**`WS /ws/live`** — Server-push JSON every collection cycle:
```json
{
  "event": "data_update",
  "timestamp": "2024-01-15T08:00:00Z",
  "provinces": [ { "province_id": 48, "aqi": 120, "anomaly_score": 0.12 } ],
  "alerts": [ { "province_id": 48, "score": 0.91, "level": "CRITICAL" } ]
}
```

---

## Infrastructure — Docker Services

```
┌─────────────────────────────────────────────────────────────┐
│  docker-compose up -d                                        │
├─────────────┬─────────────────────────────┬─────────────────┤
│  Service    │  Image                      │  Port / Volume  │
├─────────────┼─────────────────────────────┼─────────────────┤
│  zookeeper  │  confluentinc/cp-zookeeper  │  :2181          │
│  kafka      │  confluentinc/cp-kafka      │  :9092          │
│  kafka-ui   │  provectuslabs/kafka-ui     │  :8090          │
│  timescaledb│  timescale/timescaledb      │  :5432  pgdata⚠ │
│  redis      │  redis:alpine               │  :6379          │
│  airflow    │  apache/airflow             │  :8080          │
│  mlflow     │  mlflow/mlflow              │  :5000  models⚠ │
│  fastapi    │  python:3.11 (custom)       │  :8000          │
│  react-app  │  node:20 (custom)           │  :3000          │
└─────────────┴─────────────────────────────┴─────────────────┘

⚠️ = Critical volumes — NEVER run `docker-compose down -v`
```

**Startup order:**
```
zookeeper → kafka → timescaledb → redis → airflow → mlflow → fastapi → react-app
```

**Health checks:** All services have Docker healthcheck configured.  
After `docker-compose up -d`, wait ~60 seconds then verify: `docker-compose ps`

---

## Directory Structure

```
reis/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── ARCHITECTURE.md           ← this file
├── CLAUDE.md                 ← AI agent instructions
├── README.md
│
├── backend/
│   ├── requirements.txt
│   ├── config/
│   │   ├── constants.py      ← PROVINCES_COORDS (63 entries), Kafka topics, thresholds
│   │   └── settings.py       ← Load from .env via pydantic-settings
│   │
│   ├── ingestion/            ← Layer 1: Data collection
│   │   ├── collector.py      ← Async batch fetch from Open-Meteo
│   │   ├── validator.py      ← Pydantic EnvironmentReading model
│   │   ├── producer.py       ← Kafka producer + Redis DLQ
│   │   └── scheduler.py      ← APScheduler entry point
│   │
│   ├── processing/           ← Layer 2: Consumer & feature engineering
│   │   ├── consumer.py       ← Kafka consumer → TimescaleDB batch insert
│   │   └── feature_engineer.py  ← Lag, rolling, time features for ML
│   │
│   ├── models/               ← Layer 3: AI inference
│   │   ├── lstm_model.py     ← Keras LSTM: architecture, train, predict
│   │   ├── prophet_model.py  ← Prophet wrapper with timezone handling
│   │   ├── isolation_forest.py  ← Anomaly scoring (score inversion to 0–1)
│   │   ├── predict.py        ← Unified inference interface (use this, not internals)
│   │   └── artifacts/        ← MLflow-managed model files (gitignored)
│   │       └── .gitkeep
│   │
│   ├── insights/             ← Layer 3: LLM pipeline
│   │   ├── prompt_builder.py ← Assemble context from data + forecast + anomaly
│   │   ├── llm_client.py     ← Gemini/OpenAI API wrapper with retry
│   │   └── insight_cache.py  ← Redis cache with AQI bucketing
│   │
│   ├── api/                  ← Layer 4: Delivery
│   │   ├── main.py           ← FastAPI app, CORS, lifespan
│   │   ├── routes/
│   │   │   ├── provinces.py
│   │   │   ├── forecast.py
│   │   │   └── insights.py
│   │   ├── websocket.py      ← WebSocket broadcaster
│   │   └── alert_manager.py  ← Telegram Bot + Email SMTP
│   │
│   ├── airflow/              ← Layer 5: MLOps
│   │   └── dags/
│   │       └── weekly_retrain.py  ← Full retrain DAG
│   │
│   ├── scripts/
│   │   ├── setup_db.py       ← Create tables + hypertable + indexes
│   │   └── fetch_historical.py  ← One-time 90-day historical data fetch
│   │
│   └── tests/
│       ├── test_collector.py
│       ├── test_validator.py     ← 8 cases: valid, range errors, nulls, edge
│       ├── test_producer.py
│       ├── test_consumer.py
│       ├── test_forecast.py
│       ├── test_isolation_forest.py
│       └── test_integration.py   ← Gate test: 63 provinces × 3 cycles
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AQIMap.tsx        ← Leaflet map + heatmap overlay
│   │   │   ├── ForecastChart.tsx ← Recharts line chart + CI shading
│   │   │   ├── InsightCard.tsx   ← LLM text card + anomaly badge
│   │   │   └── AlertTicker.tsx   ← Real-time scrolling alert feed
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts   ← Auto-reconnect WS hook
│   │   │   └── useAQIData.ts     ← Data fetching + state management
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx     ← Main view
│   │   │   ├── Analytics.tsx     ← Historical charts
│   │   │   └── Alerts.tsx        ← Alert history
│   │   └── utils/
│   │       ├── aqiScale.ts       ← AQI → color/label mapping (US EPA)
│   │       └── formatters.ts     ← Date, number formatters
│   └── vite.config.ts
│
├── notebooks/
│   ├── 01_api_exploration.ipynb     ← ✅ Done: understand API structure
│   ├── 02_historical_fetch.ipynb    ← Fetch 90-day history for ML training
│   ├── 03_eda_and_features.ipynb    ← EDA: distributions, correlations, seasonality
│   ├── 04_model_comparison.ipynb    ← ARIMA vs Prophet vs LSTM benchmarks
│   └── 05_data_quality.ipynb        ← Post-pipeline data quality verification
│
└── tools/
    └── simulator.py                  ← DEMO: inject PM2.5 spike for live demo
```

---

## Key Design Decisions

### 1. Kafka over direct DB writes

**Decision:** Collector → Kafka → Consumer → DB (not Collector → DB directly)

**Rationale:**
- If DB is slow or under maintenance, messages wait in Kafka — no data loss
- Decouples producer and consumer speeds
- Multiple consumers (ML inference, monitoring, backup) can read same topic independently
- Replay capability: re-process historical messages if consumer logic changes

### 2. Manual Kafka commit

**Decision:** `enable.auto.commit: false` — commit only after successful DB insert

**Rationale:** Auto-commit can acknowledge messages before they're persisted. If DB insert fails after auto-commit, that data is permanently lost. Manual commit guarantees at-least-once delivery.

### 3. Redis LLM cache with AQI bucketing

**Decision:** Cache key uses `(aqi // 20) * 20` instead of exact AQI

**Rationale:** AQI 121 and AQI 125 would generate nearly identical insight text. Bucketing by 20 increases cache hit rate from ~15% to ~80%, reducing Gemini API calls and cost by ~5×.

### 4. asyncio.gather for parallel AI inference

**Decision:** Run Isolation Forest and LSTM inference concurrently

**Rationale:** Both are I/O-bound (read from DB) and CPU-independent. Sequential execution takes ~600ms; parallel takes ~350ms. At 63 provinces × 4 cycles/hour = 252 inference pairs/hour, this saves ~62 seconds of latency per hour.

### 5. Province_id as Kafka partition key

**Decision:** Use `province_id` as message key

**Rationale:** Kafka guarantees ordering within a partition. Using province_id as key ensures all messages for province 48 land in the same partition → consumer processes them in chronological order → no out-of-order time-series data in DB.

### 6. MLflow champion/challenger model management

**Decision:** New model deployed only if MAE improves by ≥ 5% over production model

**Rationale:** Small MAE improvements may be noise. Requiring ≥ 5% improvement prevents unnecessary model churn. MLflow stages (Staging → Production → Archived) provide full audit trail and one-click rollback.

---

## Data Lifecycle

```
Collection cycle (every 15 minutes):
  T+0:00  APScheduler triggers collect_and_publish()
  T+0:01  aiohttp sends batch request to Open-Meteo Weather API
  T+0:02  aiohttp sends batch request to Open-Meteo Air Quality API (parallel)
  T+0:04  Pydantic validates all 63 records
  T+0:05  Valid records published to Kafka
  T+0:06  Kafka consumer reads and inserts to TimescaleDB
  T+0:08  Feature engineering runs on new records
  T+0:09  asyncio.gather → Isolation Forest + LSTM (parallel)
  T+0:11  Prompt builder assembles context
  T+0:11  Redis cache lookup
  T+0:11  Cache HIT → serve cached insight (< 100ms)
         OR
  T+0:14  Cache MISS → Gemini API call (~3s) → store in Redis
  T+0:15  FastAPI broadcasts to all WebSocket clients
  T+0:15  React Dashboard re-renders
          └── if anomaly_score > 0.85: Alert Manager fires Telegram

Historical data (one-time, Week 1):
  fetch_historical.py → /v1/archive API → 90 days × 63 provinces
  → ~135,000 rows → TimescaleDB seed data → ready for ML training (Week 2)
```

---

## MLOps Pipeline

```
Every Sunday 02:00 AM (Airflow DAG: weekly_retrain)
│
├── Task 1: extract_training_data
│   └── Query last 30 days from TimescaleDB
│       WHERE time > NOW() - INTERVAL '30 days'
│
├── Task 2: feature_engineering
│   └── Add lag features, rolling stats, time features
│       Train/val/test split: 70% / 15% / 15%
│
├── Task 3: train_lstm  (parallel with Task 4)
│   └── Retrain LSTM with new data
│       Log: params, loss curve, final metrics to MLflow
│
├── Task 4: train_prophet  (parallel with Task 3)
│   └── Retrain Prophet with new data
│       Log: params, cross-validation MAE to MLflow
│
├── Task 5: evaluate_models
│   └── Compute MAE, RMSE, MAPE on holdout test set
│       Select champion between LSTM and Prophet
│
├── Task 6: compare_with_production
│   └── Load current Production model MAE from MLflow
│       Compare: new_mae vs prod_mae
│
├── [If new_mae < prod_mae × 0.95]
│   ├── Task 7a: register_in_mlflow
│   │   └── Transition new model to Staging, then Production
│   ├── Task 7b: hotswap_model
│   │   └── Zero-downtime in-memory model swap
│   └── Task 7c: send_success_report
│       └── Slack/Email: "New model deployed. MAE: X → Y"
│
└── [If new_mae >= prod_mae × 0.95]
    ├── Task 7d: keep_current_model
    └── Task 7e: send_drift_report
        └── Slack/Email: "Model unchanged. Possible data drift."
```

---

## Sequence — One Collection Cycle

```
APScheduler    Open-Meteo     Validator     Kafka      TimescaleDB   Isolation    LSTM        Gemini       Redis       FastAPI     Dashboard
     │               │              │          │              │          Forest        │            │             │            │            │
     │──trigger──────►              │          │              │              │          │            │             │            │            │
     │◄──batch(63 tỉnh)────────────│          │              │              │          │            │             │            │            │
     │──validate──────────────────►│          │              │              │          │            │             │            │            │
     │               │         valid│──publish─►              │              │          │            │             │            │            │
     │               │       invalid│───────────────────────────────────────────────────────────────────────────► Redis DLQ   │            │
     │               │              │          │──consume─────►              │          │            │             │            │            │
     │               │              │          │              │──stream──────►          │            │             │            │            │
     │               │              │          │              │              │──score───│            │             │            │            │
     │               │              │          │              │──query 48h───────────────►           │             │            │            │
     │               │              │          │              │              │          │──forecast──│             │            │            │
     │               │              │          │              │──current vals + score + forecast─────────────────►│            │            │
     │               │              │          │              │              │          │            │──store TTL──►            │            │
     │               │              │          │              │              │          │            │             │──insight───►            │
     │               │              │          │              │              │──anomaly flag──────────────────────────────────►            │
     │               │              │          │              │              │          │──forecast──────────────────────────────────────► │
     │               │              │          │              │              │          │            │             │            │──push WS──►│
     │               │              │          │              │              │          │            │             │            │            │◄render
```

---

*Last updated: 2025 · REIS v1.0*
