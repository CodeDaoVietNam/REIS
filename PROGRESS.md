# REIS — Project Progress

> **Last updated:** 2026-04-12
> **Session context:** Compacts được lưu tại `~/.claude/projects/*/sessions/`

---

## 📊 Overall Status

```
Stage 1: Data Pipeline        ████████████████░░  ~85%  ✅ Integration Testing
Stage 2A: ML Models           ░░░░░░░░░░░░░░░░░░  0%   ⏸️  Pending
Stage 2B: Insights (LLM)      ░░░░░░░░░░░░░░░░░░  0%   ⏸️  Pending
Stage 2C: API & WebSocket     ░░░░░░░░░░░░░░░░░░  0%   ⏸️  Pending
Stage 2D: Frontend             ░░░░░░░░░░░░░░░░░░  0%   ⏸️  Pending
Stage 2E: Airflow MLOps       ░░░░░░░░░░░░░░░░░░  0%   ⏸️  Pending
Stage 2F: Notebooks (EDA)     ████░░░░░░░░░░░░░░░  15%  ⏳ In Progress
Stage 2G: Tools (Simulator)   ░░░░░░░░░░░░░░░░░░  0%   ⏸️  Pending
```

---

## ✅ STAGE 1 — Data Pipeline (ĐÃ HOÀN THÀNH ✅)

### Files đã implement

| File | Status | Mô tả |
|------|--------|-------|
| `backend/config/constants.py` | ✅ Done | 63 tỉnh VN (coords, names, regions), Kafka topics, API URLs |
| `backend/config/settings.py` | ✅ Done | Pydantic BaseSettings, load from `.env` |
| `backend/config/__init__.py` | ✅ Done | Package exports |
| `backend/ingestion/collector.py` | ✅ Done | Async batch fetch từ Open-Meteo Weather + AQ API |
| `backend/ingestion/validator.py` | ✅ Done | Pydantic v2 EnvironmentReading, range validation |
| `backend/ingestion/producer.py` | ✅ Done | Kafka producer (aiokafka) + Redis DLQ |
| `backend/ingestion/scheduler.py` | ✅ Done | APScheduler, immediate first cycle, graceful shutdown |
| `backend/processing/consumer.py` | ✅ Done | Kafka → TimescaleDB batch insert, manual commit |
| `backend/processing/feature_engineer.py` | ✅ Done | Build 13-feature vectors, lag + rolling stats |
| `backend/scripts/setup_db.py` | ✅ Done | Tạo tables + hypertable + indexes |
| `backend/scripts/init-db.sql` | ✅ Done | SQL schema reference |
| `backend/notebooks/01_api_exploration.ipynb` | ✅ Done | Explore Open-Meteo API structure |
| `backend/notebooks/03_backfill_historical_data.ipynb` | ✅ Done | Cào 50 ngày data lịch sử |

### Integration tests đã chạy (2026-04-12)

```
✅ collector → Kafka: 63 provinces fetched + published successfully
✅ Kafka consumer → TimescaleDB: batch insert working, offset committed
✅ Redis DLQ: routing on Kafka failures working
✅ Scheduler: immediate first cycle + 15-min interval confirmed
```

### Bugs đã fix

```
2026-04-12 — Pipeline integration fixes:
✅ collector.py: Đã xóa PROVINCE_COORDS hardcode (có id=64 sai)
   → Dùng PROVINCES_COORDS từ constants.py (single source of truth)
   → Chỉ collect đúng 63 tỉnh (province_id 1-63)

✅ producer.py: Kafka value_serializer double-encoding (escaped JSON strings)
   → Fix: send dict objects (không string/bytes), để value_serializer encode
   → Producer gửi dict → aiokafka encode JSON bytes → Kafka store

✅ producer.py: aiokafka `retries` parameter không supported
   → Removed retries=, retry_max_timeout_ms= (not in AIOKafkaProducer)

✅ consumer.py: KAFKA_BOOTSTRAP undefined → KAFKA_BOOTSTRAP_SERVERS

✅ consumer.py: UnboundLocalError với _pool (global declaration missing)
   → Moved _pool = None before _get_pool(), added global _pool

✅ consumer.py: TypeError datetime string → datetime object conversion
   → Added _parse_time() với datetime.fromisoformat() cho ISO 8601 strings

✅ scheduler.py: Import paths sai (backend.ingestion → ingestion)
   → Fixed sys.path: parents[2] → parents[1]
```

### Tests đã viết

| File | Test cases | Lines |
|------|-----------|-------|
| `tests/test_validator.py` | 12 cases | 265 |
| `tests/test_producer.py` | 5 cases | 200 |
| `tests/test_scheduler.py` | 6 cases | 143 |
| `tests/test_consumer.py` | 7 cases | 187 |
| `tests/test_collector.py` | 5 cases | 154 |
| `tests/test_integration.py` | 7 cases | 311 |

**Tổng: 42+ test cases, ~1260 lines**

---

## ⏳ STAGE 2A — ML Models (CHƯA LÀM)

### Cần implement

| File | Mô tả | Priority |
|------|--------|----------|
| `backend/models/isolation_forest.py` | sklearn IsolationForest, score inversion 0-1 | 🔴 Cao |
| `backend/models/lstm_model.py` | Keras LSTM architecture + train/predict | 🔴 Cao |
| `backend/models/prophet_model.py` | Prophet wrapper, timezone-naive handling | 🟡 Trung |
| `backend/models/predict.py` | Unified interface: `predict_forecast()` + `predict_anomaly()` | 🔴 Cao |
| `backend/models/artifacts/` | Thư mục chứa trained models (.gitkeep) | 🟡 Trung |

### Test cần viết

- `tests/test_isolation_forest.py`
- `tests/test_lstm_model.py`
- `tests/test_prophet_model.py`
- `tests/test_predict.py`

---

## ⏳ STAGE 2B — Insights Layer (LLM) (CHƯA LÀM)

### Cần implement

| File | Mô tả | Priority |
|------|--------|----------|
| `backend/insights/prompt_builder.py` | Assemble context: province + timestamp + current + anomaly + forecast | 🔴 Cao |
| `backend/insights/llm_client.py` | Gemini/OpenAI wrapper, retry logic, timeout 10s | 🔴 Cao |
| `backend/insights/insight_cache.py` | Redis TTL cache với AQI bucketing | 🔴 Cao |

### Test cần viết

- `tests/test_prompt_builder.py`
- `tests/test_llm_client.py` (mock API calls)

---

## ⏳ STAGE 2C — API & WebSocket (CHƯA LÀM)

### Cần implement

| File | Mô tả | Priority |
|------|--------|----------|
| `backend/api/main.py` | FastAPI app, CORS, lifespan, WebSocket setup | 🔴 Cao |
| `backend/api/routes/provinces.py` | GET /api/provinces, GET /api/province/{id} | 🔴 Cao |
| `backend/api/routes/forecast.py` | GET /api/forecast/{id} | 🟡 Trung |
| `backend/api/routes/insights.py` | GET /api/insights/{id} | 🟡 Trung |
| `backend/api/websocket.py` | WS broadcaster sau mỗi collection cycle | 🟡 Trung |
| `backend/api/alert_manager.py` | Telegram Bot + Email SMTP alerts | 🟡 Trung |

### Test cần viết

- `tests/test_api_routes.py`

---

## ⏳ STAGE 2D — Frontend (CHƯA LÀM)

### Cần implement

```
frontend/src/
├── components/
│   ├── AQIMap.tsx           ← Leaflet map + AQI heatmap
│   ├── ForecastChart.tsx     ← Recharts line chart + CI bands
│   ├── InsightCard.tsx       ← LLM text + anomaly badge
│   └── AlertTicker.tsx      ← Scrolling alert feed
├── hooks/
│   ├── useWebSocket.ts       ← Auto-reconnect hook
│   └── useAQIData.ts         ← Data fetching + state
├── pages/
│   ├── Dashboard.tsx         ← Main view
│   ├── Analytics.tsx         ← Historical charts
│   └── Alerts.tsx            ← Alert history
├── utils/
│   ├── aqiScale.ts           ← AQI → color/label (US EPA)
│   └── formatters.ts         ← Date/number formatters
├── App.tsx
├── main.tsx
└── vite.config.ts
```

---

## ⏳ STAGE 2E — Airflow MLOps (CHƯA LÀM)

| File | Mô tả |
|------|-------|
| `backend/airflow/dags/weekly_retrain.py` | DAG: extract → feature → train → evaluate → compare → hotswap |

---

## ⏳ STAGE 2F — Notebooks EDA (ĐANG LÀM)

| Notebook | Status | Mô tả |
|----------|--------|-------|
| `01_api_exploration.ipynb` | ✅ Done | Explore Open-Meteo API structure |
| `02_data_quality.ipynb` | 🔲 Pending | Missing values, duplicates, validation errors |
| `03_backfill_historical_data.ipynb` | ✅ Done | Cào 50 ngày data lịch sử |

---

## ⏳ STAGE 2G — Tools (CHƯA LÀM)

| File | Mô tả |
|------|-------|
| `tools/simulator.py` | Inject PM2.5 spike để demo anomaly detection |

---

## 🧪 Testing Strategy cho REIS

### 1. Automation Tests (CI/CD)

```bash
# Chạy mỗi lần push code
pytest backend/tests/ -v --cov=backend

# Type check
mypy backend/ --ignore-missing-imports

# Lint
ruff check backend/
```

### 2. Manual Testing Checklist

```
TRƯỚC KHI PUSH CODE:
[ ] pytest tests/ -v  → Tất cả PASS
[ ] ruff check backend/ → 0 errors
[ ] mypy backend/ --ignore-missing-imports → 0 errors

TRƯỚC KHI MERGE STAGE:
[ ] Docker infra: docker-compose ps → Tất cả running
[ ] Pipeline E2E: scheduler + consumer chạy không lỗi
[ ] DB check: SELECT COUNT(*) FROM env_readings > 0
[ ] API check: curl http://localhost:8000/docs → Swagger OK
[ ] Frontend: http://localhost:3000 → Dashboard load được
[ ] No print() statements (dùng logger.*)
[ ] Không hardcode credentials (dùng .env)
```

### 3. Test Pyramid

```
        ┌─────────────────────┐
        │  E2E / Integration  │  ← ít nhất, chậm nhất
        │  (test_integration) │     ~7 test cases
        ├─────────────────────┤
        │  Integration        │  ← vừa
        │  (producer+scheduler│     ~20 test cases
        │   + consumer)       │
        ├─────────────────────┤
        │  Unit Tests         │  ← nhiều nhất, nhanh nhất
        │  (validator, model)  │     ~30+ test cases
        └─────────────────────┘
```

### 4. Test Data Strategy

```
pytest fixtures:
├── Mock Open-Meteo API response    → test_collector.py
├── Mock Kafka messages              → test_producer.py, test_consumer.py
├── Mock Redis DLQ                   → test_producer.py
├── Valid EnvironmentReading         → test_validator.py
├── Invalid records (edge cases)     → test_validator.py
└── 63-province full batch           → test_integration.py

⚠️  KHÔNG bao giờ gọi LLM API thật trong tests
⚠️  KHÔNG gọi Open-Meteo thật trong tests (mock response)
```

### 5. Gate Conditions (Docs spec)

```
Stage 1 Gate → Qua Stage 2 khi:
  ✅ pytest tests/ -v → Tất cả PASS
  ✅ 63 tỉnh × 3 cycles → Data vào DB không lỗi
  ✅ DLQ empty sau 3 cycles
  ✅ Manual offset commit hoạt động

Stage 2A Gate → Qua Stage 2B khi:
  ✅ isolation_forest: score inversion đúng (0.0-1.0)
  ✅ LSTM: 12h forecast output shape đúng
  ✅ Prophet: timezone-naive datetime đúng
  ✅ predict.py: unified interface hoạt động

Stage 2C Gate → Qua Frontend khi:
  ✅ All REST endpoints return đúng schema
  ✅ WebSocket broadcast sau mỗi cycle
  ✅ Redis cache hit/miss hoạt động
```

---

## 📁 Docs & Architecture

| File | Mô tả |
|------|-------|
| `docs/ARCHITECTURE.md` | System architecture đầy đủ (5 layers) |
| `docs/ml-models.md` | ML model details |
| `docs/data-sources.md` | Open-Meteo API documentation |
| `docs/adr/001-kafka-vs-rabbitmq.md` | ADR: Kafka decision |
| `docs/adr/002-timescaledb-vs-influxdb.md` | ADR: TimescaleDB decision |
| `docs/adr/003-gemini-vs-gpt4.md` | ADR: Gemini decision |
| `REIS_Stage1_2_Docs.docx` | Original spec document |

---

## 🔧 Cấu hình Infrastructure

### Docker Services đã define

```
docker-compose.yml (234 lines):
├── zookeeper  :2181
├── kafka      :9092  (kafka-data volume ⚠️)
├── kafka-ui   :8090
├── timescaledb:5432  (pgdata volume ⚠️)
├── redis      :6379
├── airflow    :8080
├── mlflow     :5000  (mlflow-artifacts volume ⚠️)
└── fastapi    :8000
```

### Environment Variables (.env)

```
DATABASE_URL, ASYNC_DATABASE_URL
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
KAFKA_BOOTSTRAP_SERVERS, KAFKA_BOOTSTRAP_SERVERS_INTERNAL
REDIS_URL
GEMINI_API_KEY / OPENAI_API_KEY
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
MLFLOW_TRACKING_URI
ENV, LOG_LEVEL, INSIGHT_CACHE_TTL, ANOMALY_THRESHOLD, CRITICAL_THRESHOLD
```

---

## 🚀 Next Steps

### Ngay lập tức (Stage 2A - ML Models)
1. Viết `backend/models/isolation_forest.py` + tests
2. Viết `backend/models/lstm_model.py` + tests
3. Viết `backend/models/prophet_model.py` + tests
4. Viết `backend/models/predict.py` + tests (unified interface)

### Sau đó (Stage 2B - Insights)
5. Viết `backend/insights/prompt_builder.py` + tests
6. Viết `backend/insights/llm_client.py` + tests (mock API)
7. Viết `backend/insights/insight_cache.py`

### Tiếp theo (Stage 2C - API)
8. Viết `backend/api/main.py` + routes + tests
9. Viết WebSocket broadcaster + alert manager

### Cuối cùng (Frontend)
10. React components + pages + hooks
11. `tools/simulator.py` cho demo

---

## ⚠️ Critical Rules (từ CLAUDE.md)

```
1. NEVER    docker-compose down -v         → MẤT HẾT DATA + MODELS
2. NEVER    commit .env files              → Dùng .env.example
3. NEVER    gọi LLM API trong tests       → Mock với fixtures
4. NEVER    SELECT * on env_readings       → Luôn thêm time bounds
5. ALWAYS   async/await trong FastAPI     → Không sync blocking
6. ALWAYS   qua Kafka cho data writes     → Không write trực tiếp vào DB
7. NEVER    modify airflow/dags/weekly_retrain.py → chạy pytest trước
```

---

## 📝 Session Notes

```
2026-04-11 — Session started
- Đã hoàn thành Stage 1 (data pipeline)
- Đã viết 6 test files (~1260 lines)
- Đã viết 2 notebooks (01_api_exploration, 03_backfill)
- Đã tạo PROGRESS.md này

2026-04-12 — Integration testing + pipeline fixes
- Đã fix Kafka double-encoding (producer gửi dict → serializer encode)
- Đã fix aiokafka retries parameter
- Đã fix consumer datetime parsing (_parse_time)
- Đã fix scheduler import paths
- Đã fix collector province_id=64 bug
- Đã chạy pipeline E2E: collector → Kafka → consumer → TimescaleDB ✅
- Stage 1 E2E verified: 63 provinces × cycles → data vào DB thành công
- PROGRESS.md updated + push lên GitHub
```