# REIS — Realtime Environmental Intelligence System

> REIS turns raw environmental signals into real-time monitoring, short-term forecasts, anomaly detection, natural-language insights, and exportable PDF reports for Vietnam's 63 provinces.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)](https://vitejs.dev)
[![Kafka](https://img.shields.io/badge/Kafka-Streaming-black?logo=apache-kafka)](https://kafka.apache.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-Time--Series-fdb515)](https://www.timescale.com)

---

## Table Of Contents

- [1. Product Story](#1-product-story)
- [2. What Is Working Now](#2-what-is-working-now)
- [3. Architecture](#3-architecture)
- [4. Feature Overview](#4-feature-overview)
- [5. Repository Structure](#5-repository-structure)
- [6. Quick Start](#6-quick-start)
- [7. Realtime Data Pipeline](#7-realtime-data-pipeline)
- [8. API Reference](#8-api-reference)
- [9. Frontend Pages](#9-frontend-pages)
- [10. AI And Insight Layer](#10-ai-and-insight-layer)
- [11. PDF Reports](#11-pdf-reports)
- [12. Testing And Verification](#12-testing-and-verification)
- [13. Docker Services](#13-docker-services)
- [14. Environment Variables](#14-environment-variables)
- [15. Troubleshooting](#15-troubleshooting)
- [16. Current Limitations](#16-current-limitations)
- [17. Suggested Demo Narrative](#17-suggested-demo-narrative)

---

## 1. Product Story

Most air-quality dashboards answer only one question: **what is the AQI right now?**

That is useful, but not enough. A realistic environmental intelligence system should also answer:

- Is the current reading normal or suspicious?
- Which provinces are becoming unhealthy?
- What may happen in the next 12 hours?
- What should a user or operator do next?
- Can the system produce a report instead of only showing a dashboard?

REIS is built around that loop:

```text
Observe -> Validate -> Stream -> Store -> Analyze -> Explain -> Act
```

The system collects weather and air-quality signals, streams them through Kafka, stores them in TimescaleDB, runs ML inference, generates LLM/template insights, serves everything through FastAPI/WebSocket, renders a React dashboard, and exports PDF reports.

---

## 2. What Is Working Now

### Demo-ready core

- Real data pipeline for 63 Vietnam provinces.
- Open-Meteo collector and Kafka producer.
- Kafka consumer writing to TimescaleDB `env_readings`.
- Historical backfill script, default 50 days.
- FastAPI REST routes and WebSocket live route.
- React/Vite frontend with Dashboard, Analytics, Compare, Map, Alerts, About.
- AQI warnings and AI anomalies are separated semantically.
- EDA-backed Key Findings answer the course insight/interpretation rubric directly.
- LSTM/Prophet-style forecast interface with confidence band.
- Isolation Forest anomaly scoring through model artifacts.
- Insight generation through Gemini/OpenAI when keys exist, with template fallback.
- Redis-backed insight cache path.
- PDF export for one province and multi-province comparison.
- Backend and frontend tests/build commands are passing.

### Still intentionally scoped

- Airflow/MLOps is documented as a skeleton, not production-finished.
- Telegram/email alert manager is planned, not part of the current demo-ready path.
- `tools/simulator.py` is documented as a task, not fully implemented.
- Authentication and production observability are not implemented.

---

## 3. Architecture

```text
                                  External Data Sources
                      Open-Meteo Forecast API + Air Quality API
                                             |
                                             v
┌────────────────────────────────────────────────────────────────────────────┐
│ L1. Ingestion                                                              │
│ collector.py -> validator.py -> producer.py -> scheduler.py                │
└────────────────────────────────────────────────────────────────────────────┘
                                             |
                                             v
┌────────────────────────────────────────────────────────────────────────────┐
│ L2. Streaming                                                              │
│ Kafka topic: env.readings.raw                                               │
│ Redis: DLQ/cache helpers                                                    │
└────────────────────────────────────────────────────────────────────────────┘
                                             |
                                             v
┌────────────────────────────────────────────────────────────────────────────┐
│ L3. Storage                                                                │
│ TimescaleDB hypertable: env_readings                                        │
│ Unique key: province_id + time                                              │
└────────────────────────────────────────────────────────────────────────────┘
                                             |
                                             v
┌────────────────────────────────────────────────────────────────────────────┐
│ L4. Intelligence                                                           │
│ Isolation Forest anomaly score                                              │
│ LSTM/Prophet forecast interface                                             │
│ Gemini/OpenAI/template insight engine                                       │
│ Inference cache + insight cache                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                             |
                                             v
┌────────────────────────────────────────────────────────────────────────────┐
│ L5. Delivery                                                               │
│ FastAPI REST + WebSocket + PDF reports                                      │
│ React frontend: Dashboard, Analytics, Compare, Map, Alerts, About          │
└────────────────────────────────────────────────────────────────────────────┘
```

### Input -> Process -> Output

| Stage | Input | Process | Output |
|---|---|---|---|
| Ingestion | Open-Meteo weather/AQ responses | Async fetch, normalize, validate | Valid environmental readings |
| Streaming | Valid readings | Kafka publish, DLQ on failure | Durable streaming messages |
| Processing | Kafka messages | Batch consume, parse time, insert | TimescaleDB rows |
| ML | Latest/history readings | Feature engineering, anomaly/forecast inference | Score, label, forecast values |
| Insight | Current reading + anomaly + forecast | Gemini/OpenAI/template + cache | Human-readable advice |
| API | DB + model/cache | FastAPI routes, WebSocket broadcast, PDF generation | JSON, WS payloads, PDF |
| Frontend | API/WS data | UI state, charts, map, fallback handling | Demo-ready dashboard |

---

## 4. Feature Overview

| Area | Status | Notes |
|---|---:|---|
| 63-province metadata | Done | Source of truth in `backend/config/constants.py` |
| Open-Meteo collection | Done | Weather + air quality |
| Kafka producer/consumer | Done | Consumer writes to TimescaleDB |
| Historical backfill | Done | Idempotent 50-day default |
| FastAPI health/docs | Done | `/api/health`, `/docs` |
| Province/summary APIs | Done | `/api/provinces`, `/api/province/{id}`, `/api/summary` |
| Forecast API | Done | `/api/forecast/{id}` |
| Insight API | Done | `/api/insights/{id}` |
| Alerts API | Done | `/api/anomalies` with `event_type`, `severity`, `reason` |
| Compare API | Done | `/api/compare` |
| PDF reports | Done | Province PDF + compare PDF |
| WebSocket | Done | `/ws/live`, shared broadcast manager |
| Frontend dashboard | Done | KPI, map, gauge, forecast, insight |
| Analytics page | Done | Province/range/metric filters, PDF export |
| Compare page | Done | Multi-province comparison, PDF export |
| Alert Center | Done | AQI warnings vs AI anomalies |
| MLOps/Airflow | Skeleton | Documentation only for deadline scope |
| Simulator tool | Planned | See `docs/simulator_task.md` |

---

## 5. Repository Structure

```text
reis/
├── backend/
│   ├── api/
│   │   ├── main.py                  # FastAPI app, CORS, lifespan
│   │   ├── db.py                    # asyncpg pool helper
│   │   ├── inference_cache.py       # short TTL inference cache
│   │   ├── rate_limit.py            # simple API rate limiter
│   │   ├── websocket.py             # WS route
│   │   ├── ws_manager.py            # shared WS broadcast loop
│   │   └── routes/
│   │       ├── provinces.py         # summary/provinces/detail/compare
│   │       ├── forecast.py          # forecast endpoint
│   │       ├── insights.py          # insights + anomalies
│   │       └── reports.py           # PDF report endpoints
│   ├── config/
│   │   ├── constants.py             # 63 provinces, thresholds, features
│   │   ├── settings.py              # env-driven settings
│   │   └── logging_config.py        # text/JSON logging setup
│   ├── ingestion/
│   │   ├── collector.py             # Open-Meteo fetcher
│   │   ├── validator.py             # Pydantic validation
│   │   ├── producer.py              # Kafka producer + Redis DLQ path
│   │   └── scheduler.py             # collection scheduler
│   ├── processing/
│   │   ├── consumer.py              # Kafka -> TimescaleDB
│   │   └── feature_engineer.py      # lag/rolling/time features
│   ├── models/
│   │   ├── isolation_forest.py      # anomaly scoring
│   │   ├── lstm_model.py            # LSTM forecast wrapper
│   │   ├── prophet_model.py         # Prophet fallback wrapper
│   │   ├── predict.py               # unified async inference
│   │   └── artifacts/               # trained model artifacts
│   ├── insights/
│   │   ├── prompt_builder.py        # prompt construction
│   │   ├── llm_client.py            # Gemini/OpenAI/template fallback
│   │   └── insight_cache.py         # Redis cache for insight text
│   ├── scripts/
│   │   ├── setup_db.py              # schema/hypertable setup
│   │   ├── backfill_historical_data.py
│   │   ├── train_models.py
│   │   └── test_insight_generation.py
│   ├── notebooks/                   # EDA, backfill, model comparison
│   └── tests/                       # backend tests
├── frontend/
│   ├── src/
│   │   ├── components/              # cards, charts, map, insight UI
│   │   ├── hooks/                   # useAQIData, useWebSocket
│   │   ├── pages/                   # Dashboard, Analytics, Compare, Map, Alerts
│   │   ├── services/apiClient.ts    # REST URL helpers
│   │   └── types.ts                 # API/frontend contracts
│   └── package.json
├── docs/
│   ├── adr/                         # architecture decisions
│   ├── presentation_script.md       # presentation script
│   ├── mlops_airflow_skeleton.md
│   └── simulator_task.md
├── docker-compose.yml
├── PROGRESS.md
└── README.md
```

---

## 6. Quick Start

The commands below assume the local conda env used during development:

```bash
/home/ductien/miniconda3/envs/reis/bin/python
```

If your Python path is different, replace it with your own `python`.

### 6.1. Clone

```bash
git clone https://github.com/CodeDaoVietNam/REIS.git
cd REIS
```

### 6.2. Install backend dependencies

```bash
cd /home/ductien/Documents/reis
/home/ductien/miniconda3/envs/reis/bin/python -m pip install -r backend/requirements.txt
```

### 6.3. Install frontend dependencies

```bash
cd /home/ductien/Documents/reis/frontend
npm install
```

### 6.4. Start minimal infrastructure

```bash
cd /home/ductien/Documents/reis
docker compose up -d zookeeper kafka redis timescaledb
docker compose ps
```

Optional UI tools:

```bash
docker compose up -d kafka-ui pgadmin
```

If `kafka-ui` is unhealthy but Kafka itself is healthy, the core pipeline can still run. Kafka UI is only an optional visual tool.

### 6.5. Setup database schema

```bash
cd /home/ductien/Documents/reis/backend
/home/ductien/miniconda3/envs/reis/bin/python scripts/setup_db.py
```

Verify tables:

```bash
cd /home/ductien/Documents/reis
docker compose exec timescaledb psql -U reis -d reis_db -c "\dt"
docker compose exec timescaledb psql -U reis -d reis_db -c "select count(*) from env_readings;"
```

### 6.6. Backfill historical data

Recommended before demo because charts, forecast, anomaly, and insights need enough history:

```bash
cd /home/ductien/Documents/reis/backend
/home/ductien/miniconda3/envs/reis/bin/python scripts/backfill_historical_data.py --days 50
```

Verify coverage:

```bash
cd /home/ductien/Documents/reis
docker compose exec timescaledb psql -U reis -d reis_db -c "
select province_id, count(*), min(time), max(time)
from env_readings
group by province_id
order by province_id;
"
```

### 6.7. Start realtime consumer

Open Terminal 1:

```bash
cd /home/ductien/Documents/reis/backend
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
DB_HOST=localhost DB_PORT=5432 DB_USER=reis DB_PASSWORD=reis_secret DB_NAME=reis_db \
/home/ductien/miniconda3/envs/reis/bin/python processing/consumer.py
```

### 6.8. Publish one realtime collection cycle

Open Terminal 2:

```bash
cd /home/ductien/Documents/reis/backend
KAFKA_BOOTSTRAP_SERVERS=localhost:9092 REDIS_HOST=localhost REDIS_PORT=6379 \
/home/ductien/miniconda3/envs/reis/bin/python - <<'PY'
import asyncio
from ingestion.scheduler import collect_and_publish
from ingestion.producer import close as close_producer

async def main():
    await collect_and_publish()
    await close_producer()

asyncio.run(main())
PY
```

Verify latest rows:

```bash
cd /home/ductien/Documents/reis
docker compose exec timescaledb psql -U reis -d reis_db -c "
select count(*) as total_rows, max(time) as latest_time
from env_readings;
"
docker compose exec timescaledb psql -U reis -d reis_db -c "
select province_id, aqi, pm2_5, temperature, time
from env_readings
order by time desc
limit 10;
"
```

### 6.9. Start FastAPI

Open Terminal 3:

```bash
cd /home/ductien/Documents/reis/backend
/home/ductien/miniconda3/envs/reis/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Smoke test:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/summary
curl "http://localhost:8000/api/province/1?hours=168"
curl "http://localhost:8000/api/compare?province_ids=1,2,4&days=7&metric=aqi"
curl http://localhost:8000/api/anomalies
```

Swagger:

```text
http://localhost:8000/docs
```

### 6.10. Start frontend

Open Terminal 4:

```bash
cd /home/ductien/Documents/reis/frontend
VITE_API_URL=http://localhost:8000 \
VITE_WS_URL=ws://localhost:8000/ws/live \
npm run dev -- --host 0.0.0.0 --port 3000
```

Open:

```text
http://localhost:3000
```

---

## 7. Realtime Data Pipeline

### Normal flow

```text
Open-Meteo
  -> collector.py
  -> validator.py
  -> producer.py
  -> Kafka
  -> consumer.py
  -> TimescaleDB env_readings
  -> FastAPI
  -> React dashboard
```

### Why Kafka?

Kafka decouples data collection from database writing. If TimescaleDB is temporarily slow, producer-side collection can still publish messages and consumer-side processing can catch up later.

### Why TimescaleDB?

Environmental readings are time-series data. TimescaleDB gives PostgreSQL compatibility plus hypertables, indexes, and efficient time-window queries.

### Why Redis?

Redis is used for cache-oriented paths such as insight caching and DLQ/helper flows. It keeps expensive LLM calls and repeated inference paths under control.

---

## 8. API Reference

Interactive docs:

```text
http://localhost:8000/docs
```

### Core REST

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Lightweight health check |
| `GET` | `/api/summary` | National KPI summary |
| `GET` | `/api/provinces` | 63 provinces with latest readings |
| `GET` | `/api/province/{id}?hours=168` | Province detail, current, history, anomaly, forecast |
| `GET` | `/api/forecast/{id}` | Forecast payload |
| `GET` | `/api/insights/{id}` | Natural-language insight |
| `GET` | `/api/insight-summary` | EDA-backed national Key Findings |
| `GET` | `/api/anomalies` | Alert Center events |
| `GET` | `/api/compare?province_ids=1,2,4&days=7&metric=aqi` | Multi-province comparison |

### PDF reports

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/report/province/{id}.pdf?hours=48` | Export one-province report |
| `GET` | `/api/report/compare.pdf?province_ids=1,2,4&days=7&metric=aqi` | Export multi-province comparison report |
| `GET` | `/api/report/insights.pdf` | Export national Insight & Interpretation report |

### WebSocket

| Protocol | Endpoint | Purpose |
|---|---|---|
| `WS` | `/ws/live` | Live province summary updates |

### Important response semantics

`AQI warnings` and `AI anomalies` are intentionally different:

- `AQI warning`: health threshold event, generally `AQI >= 150`.
- `AI anomaly`: model-detected unusual pattern based on anomaly score/label.
- `combined`: both AQI health threshold and AI anomaly are true.

`/api/anomalies` returns alert records with:

```json
{
  "province": {},
  "reading": {},
  "event_type": "aqi_warning | ai_anomaly | combined",
  "severity": "moderate | high | critical",
  "reason": "...",
  "recommendations": ["..."]
}
```

---

## 9. Frontend Pages

| Page | Route | Purpose |
|---|---|---|
| Landing | `/` | Product overview and entry point |
| Dashboard | `/dashboard` | National command center with KPI, map, gauge, forecast, insights |
| Analytics | `/analytics` | Single-province analysis with filters and PDF export |
| Compare | `/compare` | Multi-province comparison and PDF export |
| Map | `/map` | National live AQI map |
| Alerts | `/alerts` | Alert Center: AQI warnings vs AI anomalies |
| About | `/about` | Architecture, tech stack, and system explanation |

### Header interactions

- Search supports page/province lookup.
- `Ctrl+K` focuses search.
- Bell icon opens Alert Center.
- Settings icon opens quick settings and system info.
- Dashboard KPI cards for `AQI warnings` and `AI anomalies` are clickable drill-downs.
- Dashboard includes `Key Findings`, a rubric-focused interpretation layer derived from EDA and live DB context.

### Source labels

The frontend explicitly labels data source:

- `LIVE API`: REST data is available.
- `LIVE WS/API`: WebSocket payload is active.
- `MOCK FALLBACK`: backend unavailable, UI is using deterministic fallback data.

This is important for demo honesty: fallback data keeps UI stable but must not be mistaken for realtime operational data.

---

## 10. AI And Insight Layer

### Anomaly detection

- Main model: Isolation Forest.
- Input: engineered AQI, pollutant, weather, lag, rolling, and delta features.
- Output: normalized anomaly score and label.
- UI displays `N/A` only when no model/inference score is available.
- API enriches latest province readings with cached anomaly inference for consistent Dashboard/Alerts behavior.

### Forecast

- Forecast interface returns:

```json
{
  "values": [],
  "lower": [],
  "upper": [],
  "model_family": "..."
}
```

- The frontend renders forecast confidence bands.
- `lower` and `upper` should be interpreted as demo uncertainty bands unless replaced by a calibrated uncertainty method.

### Insight generation

Provider order:

1. Gemini, if `GEMINI_API_KEY` exists.
2. OpenAI fallback, if `OPENAI_API_KEY` exists.
3. Template fallback, always available.

Insight cache:

- `INSIGHT_CACHE_TTL_SECONDS=3600` by default.
- Helps avoid repeated paid LLM calls.
- Good enough for demo where AQI changes at minute/hour cadence, not second cadence.

### Key Findings from EDA

REIS includes a separate `Key Findings` layer because the course rubric requires interpretation, not only visualization.

It answers four questions explicitly:

- `Main trend`: AQI has a daily/weekly rhythm and often increases around the evening window.
- `Notable pattern`: the North, especially Hanoi and nearby provinces, forms a stronger pollution cluster than the South.
- `Forecast / explanation`: AQI has temporal memory through lag features, so short-term forecasting is technically justified.
- `Practical value`: users can plan outdoor activity, operators can prioritize regional warnings, and reports can explain why a chart matters.

The API endpoint is:

```bash
curl "http://localhost:8000/api/insight-summary"
```

The response is hybrid:

- `eda_live_hybrid`: EDA baseline enriched with current TimescaleDB metrics.
- `eda_baseline`: safe fallback when DB is unavailable.

---

## 11. PDF Reports

REIS can export three report types from the backend.

### One-province report

Endpoint:

```bash
curl -o hanoi-report.pdf "http://localhost:8000/api/report/province/1.pdf?hours=168"
```

Frontend:

```text
Analytics -> Export province PDF
```

Included sections:

- Executive Summary
- AQI history chart
- Current Reading
- AI Anomaly Analysis
- Forecast 12h
- Province LLM/template insight
- Insight & Interpretation
- Historical Table

### Multi-province compare report

Endpoint:

```bash
curl -o compare-report.pdf "http://localhost:8000/api/report/compare.pdf?province_ids=1,2,4&days=7&metric=aqi"
```

Frontend:

```text
Compare -> Export compare PDF
```

Included sections:

- Executive Comparison
- Current AQI comparison chart
- AQI/PM2.5/temperature/wind/anomaly score table
- Radar metrics
- Insight & Interpretation
- Historical samples for each selected province

### National insight report

Endpoint:

```bash
curl -o national-insights.pdf "http://localhost:8000/api/report/insights.pdf"
```

Frontend:

```text
Dashboard -> Key Findings -> Export insight PDF
```

Included sections:

- Executive Interpretation
- Key Findings from EDA
- Regional AQI chart when live DB is available
- Top polluted provinces chart when live DB is available
- Rubric answer: Main Trend, Notable Pattern, Forecast / Explanation, Practical Value, Limitations

### Implementation detail

PDF generation uses `reportlab`, including backend-generated charts. It is intentionally backend-side so the frontend does not need to capture screenshots or expose report logic in the browser.

---

## 12. Testing And Verification

### Backend route/API tests

```bash
cd /home/ductien/Documents/reis
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/test_api_routes.py -v
```

### Core pipeline/model tests

```bash
cd /home/ductien/Documents/reis
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/test_consumer.py backend/tests/test_isolation_forest.py -v
```

### Full backend test suite

```bash
cd /home/ductien/Documents/reis
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/ -v
```

### Frontend checks

```bash
cd /home/ductien/Documents/reis/frontend
npm run lint
npm run build
```

### Current verified commands

The following have been verified during the latest implementation cycle:

```bash
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/test_api_routes.py -v
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/test_consumer.py backend/tests/test_isolation_forest.py -v
cd frontend && npm run lint
cd frontend && npm run build
```

---

## 13. Docker Services

### Minimal infra

```bash
docker compose up -d zookeeper kafka redis timescaledb
```

### Optional tools

```bash
docker compose up -d kafka-ui pgadmin
```

| Service | Port | Purpose |
|---|---:|---|
| Kafka | `9092` | Local broker |
| Zookeeper | `2181` | Kafka coordination |
| TimescaleDB | `5432` | Time-series database |
| Redis | `6379` | Cache/DLQ helpers |
| Kafka UI | `8090` | Optional Kafka browser |
| pgAdmin | `5050` | Optional DB UI |
| FastAPI | `8000` | API service |
| Frontend | `3000` | Vite dev server |

### App services through Compose

The compose file includes `fastapi` and `frontend` services, but during development the recommended workflow is:

- Docker Compose for infrastructure.
- Local conda Python for backend.
- Local npm/Vite for frontend.

This keeps logs readable and reload behavior predictable.

---

## 14. Environment Variables

Copy `.env.example` if needed:

```bash
cp .env.example .env
```

Important variables:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=reis
DB_PASSWORD=reis_secret
DB_NAME=reis_db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=reis-consumer-group

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Cache
INSIGHT_CACHE_TTL_SECONDS=3600
INFERENCE_CACHE_TTL_SECONDS=600

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:5173
LOG_LEVEL=INFO
LOG_JSON=false

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/live
```

Security note:

- Do not commit real API keys.
- Do not use `reis_secret` in production.
- Frontend must not call Gemini/OpenAI directly with secret keys; LLM calls should go through backend routes.

---

## 15. Troubleshooting

### Frontend says API fallback is active

Usually FastAPI is not running or CORS/port is wrong.

Check:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/provinces
```

Then restart frontend with:

```bash
cd frontend
VITE_API_URL=http://localhost:8000 VITE_WS_URL=ws://localhost:8000/ws/live npm run dev -- --host 0.0.0.0 --port 3000
```

### `AI anomalies = 6/63` but list is empty

This used to happen when summary counted model inference but province list read only DB `anomaly_score`, which was often `NULL`.

Current fix:

- `/api/provinces` enriches latest readings with cached anomaly inference.
- `/api/anomalies` uses the same enriched anomaly score.
- Restart FastAPI after pulling latest code.

### Most AI scores are `N/A`

Possible causes:

- API is using fallback/mock.
- Model artifacts are missing.
- FastAPI has not been restarted after code changes.
- Inference failed and route fell back to default.

Check:

```bash
curl "http://localhost:8000/api/province/1?hours=48"
curl http://localhost:8000/api/anomalies
```

Look for:

```json
"inference_source": "model | cache"
```

### Kafka UI is unhealthy

Kafka UI is optional. If core services are healthy, continue without it:

```bash
docker compose up -d zookeeper kafka redis timescaledb
```

Verify Kafka itself:

```bash
docker compose ps kafka
docker compose logs kafka --tail=100
```

### Duplicate DB rows

Backfill is designed to be idempotent when the schema has a unique key on `(province_id, time)`.

Check duplicates:

```bash
docker compose exec timescaledb psql -U reis -d reis_db -c "
select province_id, time, count(*)
from env_readings
group by province_id, time
having count(*) > 1
limit 20;
"
```

### TensorFlow CUDA/TensorRT warnings

On CPU-only machines, warnings such as `CUDA_ERROR_NO_DEVICE` or missing TensorRT are expected. They are noisy but not fatal for local demo.

### PDF route is not found

Restart FastAPI after pulling latest code:

```bash
cd backend
/home/ductien/miniconda3/envs/reis/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Then try:

```bash
curl -I "http://localhost:8000/api/report/province/1.pdf"
```

---

## 16. Current Limitations

This project is demo-ready, not production-complete.

Known limitations:

- No authentication or user roles.
- No production monitoring stack.
- No real Telegram/email alert dispatch in the current demo path.
- Airflow/MLOps is a skeleton/documentation task, not fully operational.
- Simulator spike tool is planned but not fully implemented.
- Forecast confidence bands are demo-oriented and should be calibrated before production use.
- Frontend has lint/build checks but no dedicated component test suite yet.
- PDF charts are backend-generated ReportLab charts, not full frontend screenshots.

---

## 17. Suggested Demo Narrative

If presenting REIS, use this story:

1. Start with the problem: current AQI alone is reactive.
2. Show the pipeline: Open-Meteo -> Kafka -> TimescaleDB.
3. Show Dashboard: national status, map, AQI warnings, AI anomalies.
4. Explain the difference between AQI warning and AI anomaly.
5. Show Analytics: one province, history, forecast confidence band.
6. Show Compare: multiple provinces side by side.
7. Show Alerts: explain event type, severity, reason, recommendations.
8. Export PDF report: prove the system can produce shareable output.
9. Close with limitations: MLOps, simulator, production alerting are next steps.

One-line summary:

```text
REIS is not only a dashboard; it is an environmental intelligence loop: observe, forecast, explain, alert, and report.
```

---

## Documentation

- Project progress: [PROGRESS.md](PROGRESS.md)
- Presentation script: [docs/presentation_script.md](docs/presentation_script.md)
- Architecture notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Data sources: [docs/data-sources.md](docs/data-sources.md)
- ML models: [docs/ml-models.md](docs/ml-models.md)
- MLOps skeleton: [docs/mlops_airflow_skeleton.md](docs/mlops_airflow_skeleton.md)
- Simulator task: [docs/simulator_task.md](docs/simulator_task.md)
- ADR Kafka vs RabbitMQ: [docs/adr/001-kafka-vs-rabbitmq.md](docs/adr/001-kafka-vs-rabbitmq.md)
- ADR TimescaleDB vs InfluxDB: [docs/adr/002-timescaledb-vs-influxdb.md](docs/adr/002-timescaledb-vs-influxdb.md)
- ADR Gemini vs GPT: [docs/adr/003-gemini-vs-gpt4.md](docs/adr/003-gemini-vs-gpt4.md)

---

## License

This repository is intended for academic/demo use. Add or update a formal license file before public production distribution.
