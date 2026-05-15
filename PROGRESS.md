# REIS — Project Progress

> **Last updated:** 2026-05-14
> **Session context:** Compacts được lưu tại `~/.claude/projects/*/sessions/`

---

## 📊 Overall Status

```
Stage 1: Data Pipeline        ████████████████░░  ~88%  ✅ Integration + backfill script
Stage 2A: ML Models           ████████████████░░  ~85%  ✅ Core models + tests
Stage 2B: Insights (LLM)      ███████████████░░░  ~80%  ✅ Prompt/cache/client + API route
Stage 2C: API & WebSocket     ████████████████░░  ~82%  ✅ Contract cleanup + inference cache
Stage 2D: Frontend             █████████████████░  ~88%  ✅ Demo-ready UX cleanup
Stage 2E: Airflow MLOps       ██░░░░░░░░░░░░░░░░  ~10%  📝 Skeleton docs ready
Stage 2F: Notebooks (EDA)     █████████████████░  ~90%  ✅ EDA notebooks completed
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
| `backend/scripts/backfill_historical_data.py` | ✅ Done | Backfill lịch sử Open-Meteo idempotent, default 50 ngày / 63 tỉnh |
| `backend/scripts/init-db.sql` | ✅ Done | SQL schema reference |
| `backend/notebooks/01_api_exploration.ipynb` | ✅ Done | Explore Open-Meteo API structure |
| `backend/notebooks/03_backfill_historical_data.ipynb` | ✅ Done | Cào 50 ngày data lịch sử |

### Integration tests đã chạy

```
2026-05-14 — Full Kafka pipeline smoke test:
✅ docker-compose infra tối thiểu: zookeeper/kafka/redis/timescaledb/kafka-ui healthy
✅ Open-Meteo collector → Kafka producer: 63/63 records published, DLQ=0
✅ Kafka consumer → TimescaleDB: `Flushed 63 records`, lag=0
✅ TimescaleDB `env_readings`: row count 47,352 → 47,415, đủ 63 records tại `2026-05-14 18:45:00+00`
✅ FastAPI `/api/provinces`: 63/63 provinces có `current`
✅ FastAPI `/api/province/1`: có `current` và `history`
✅ FastAPI `/api/anomalies`: trả anomaly list từ DB

2026-05-14 — Historical backfill script smoke:
✅ `backend/scripts/backfill_historical_data.py --days 50 --sleep-between 0.2`
✅ Open-Meteo historical backfill: 63/63 tỉnh success, fetched 77,112 hourly rows
✅ TimescaleDB insert idempotent: inserted thêm 29,439 rows sau khi fix timezone UTC, không duplicate nhờ unique index `(province_id, time)`
✅ `env_readings`: total 77,099 rows, 63 provinces, min per province 1,225 rows, max 1,338 rows
✅ Time coverage: `2026-03-20 00:00:00+00` → `2026-05-14 13:00:00+00`, `future_rows=0`

2026-04-12 — Pipeline integration:
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

✅ consumer.py: Batch timeout chỉ flush khi có message mới
   → Đổi consumer loop sang `getmany(timeout_ms=1000)` để batch tự flush dù Kafka im lặng
   → Ctrl+C entrypoint thoát sạch hơn, không in traceback dev UX

✅ scheduler.py: Import paths sai (backend.ingestion → ingestion)
   → Fixed sys.path: parents[2] → parents[1]
```

### Tests đã viết

| File | Test cases | Lines |
|------|-----------|-------|
| `backend/tests/test_validator.py` | 12 cases | 265 |
| `backend/tests/test_producer.py` | 5 cases | 200 |
| `backend/tests/test_scheduler.py` | 6 cases | 143 |
| `backend/tests/test_consumer.py` | 7 cases | 187 |
| `backend/tests/test_collector.py` | 5 cases | 154 |
| `backend/tests/test_integration.py` | 7 cases | 311 |

**Tổng: 42+ test cases, ~1260 lines**

---

## ✅ STAGE 2A — ML Models (CORE ĐÃ XONG)

### Files đã implement

| File | Mô tả | Priority |
|------|--------|----------|
| `backend/models/isolation_forest.py` | Isolation Forest anomaly scoring, score [0,1], strict alert rules | ✅ |
| `backend/models/lstm_model.py` | Tuned LSTM forecast model, Huber + sample weighting, scaler save/load | ✅ |
| `backend/models/prophet_model.py` | Prophet fallback model, timezone-naive handling, JSON export | ✅ |
| `backend/models/predict.py` | Unified async inference: anomaly + forecast, LSTM fallback Prophet | ✅ |
| `backend/scripts/train_models.py` | Train/export script from TimescaleDB | ✅ |
| `backend/models/artifacts/` | Exported artifacts for Isolation Forest, LSTM, Prophet | ✅ |

### Notebooks and tuning status

- `backend/notebooks/06_model_comparison.ipynb` đã hoàn thành baseline comparison.
- `backend/notebooks/06_model_comparison_copy.ipynb` đã hoàn thành tuning vòng 2.
- Champion anomaly direction:
  - Isolation Forest với feature động mở rộng
  - ưu tiên ranking / top suspicious events
  - threshold binary thực dụng: `0.55`
- Champion forecast direction:
  - `lookback=12h`
  - stacked LSTM `128 -> 64`
  - `dropout=0.2`
  - `Adam(1e-3)`
  - `Huber loss`
  - sample weighting cho spike

### Tests đã có

- `backend/tests/test_lstm_model.py`
- `backend/tests/test_prophet_model.py`
- `backend/tests/test_predict.py`

### Trạng thái hiện tại

```
✅ train/export model từ DB bằng script
✅ artifact đã sinh cho Isolation Forest / LSTM / Prophet
✅ predict.py đã test pass với fallback logic
✅ `backend/tests/test_isolation_forest.py` đã bổ sung
✅ API layer đã có route gọi inference/forecast với fallback có kiểm soát
```

---

## ✅ STAGE 2B — Insights Layer (LLM) (CORE ĐÃ XONG)

### Files đã implement

| File | Mô tả | Priority |
|------|--------|----------|
| `backend/insights/prompt_builder.py` | Build prompt tiếng Việt + template fallback dưới 150 từ | ✅ |
| `backend/insights/llm_client.py` | Gemini primary, OpenAI fallback, retry + timeout + template fallback | ✅ |
| `backend/insights/insight_cache.py` | Redis cache theo `province_id + aqi_bucket`, TTL 1 giờ | ✅ |
| `backend/scripts/test_insight_generation.py` | Smoke test script cho Gemini/template/cache/DB flow | ✅ |

### Tests đã có

- `backend/tests/test_prompt_builder.py`
- `backend/tests/test_llm_client.py`
- `backend/tests/test_insight_cache.py`

### Runtime status

```
✅ Block 3 unit tests pass trong env `reis`
✅ Gemini model config đã chuyển sang `gemini-2.5-flash`
✅ Smoke test sinh insight thật qua Gemini thành công
✅ Fallback template hoạt động khi provider lỗi hoặc thiếu API key
✅ API route `/api/insights/{id}` đã implement, gọi `get_or_create_insight`
⏳ Redis cache đã gắn vào API nhưng chưa smoke test end-to-end với Redis thật trong session này
```

---

## ✅ STAGE 2C — API & WebSocket (CORE ĐÃ XONG)

### Đã implement

| File | Mô tả | Status |
|------|------|--------|
| `backend/api/main.py` | FastAPI app, CORS local dev, lifespan gắn DB pool best-effort, mount routes | ✅ Done |
| `backend/api/db.py` | `asyncpg.create_pool` helper, DB lỗi thì API tự fallback | ✅ Done |
| `backend/api/inference_cache.py` | TTL cache chia sẻ cho province/forecast/insights để giảm inference lặp | ✅ Done |
| `backend/api/routes/provinces.py` | `GET /api/provinces`, `GET /api/province/{id}?hours=...`, `GET /api/summary`, `GET /api/compare`; 63 tỉnh từ constants | ✅ Done |
| `backend/api/routes/forecast.py` | `GET /api/forecast/{id}` gọi `predict_forecast`, fallback không crash | ✅ Done |
| `backend/api/routes/insights.py` | `GET /api/insights/{id}`, `GET /api/anomalies`; fallback khi DB/LLM lỗi | ✅ Done |
| `backend/api/websocket.py` | Re-export WebSocket router cho `/ws/live` | ✅ Done |
| `backend/api/routes/websocket.py` | WebSocket live update polling 15s, fallback payload khi DB lỗi | ✅ Done |
| `backend/tests/test_api_routes.py` | Health/docs/provinces/detail/forecast/insights/anomalies/404 tests | ✅ Done |
| `backend/tests/test_isolation_forest.py` | Isolation Forest score/classify/strict-alert tests | ✅ Done |

### Verification

```bash
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/test_api_routes.py backend/tests/test_isolation_forest.py backend/tests/test_consumer.py -v
# 24 passed

cd backend
/home/ductien/miniconda3/envs/reis/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# /api/health   -> 200
# /docs         -> 200
# /api/provinces -> 200, 63 records
# /api/province/1 -> current + history from DB after smoke test
# /api/summary -> KPI toàn quốc
# /api/compare?province_ids=1,2,4&days=7&metric=aqi -> compare contract

2026-05-14 API smoke sau backfill:
# /api/summary -> {"aqi_avg":104.0,"pm25_avg":27.5,"aqi_warning_count":12,"ai_anomaly_count":0,...}
# /api/province/1?hours=168 -> current=True, history=169
# /api/compare?province_ids=1,2,4&days=7&metric=aqi -> provinces=3, histories=[169,169,169]

2026-05-14 demo-ready contract cleanup:
✅ `/api/summary` phân biệt rõ `aqi_warning_count` và `ai_anomaly_count`
✅ `/api/province/{id}` trả thêm `data_source`, `inference_source`, `updated_at`
✅ `/api/forecast`, `/api/province`, `/api/insights`, `/api/compare` dùng chung inference cache TTL
✅ CORS đọc từ `CORS_ORIGINS`, default gồm ports `3000`, `3001`, `5173`
✅ Docker Compose frontend chuyển sang Vite `VITE_API_URL`/`VITE_WS_URL`
✅ `backend/Dockerfile` và `frontend/Dockerfile` đã thêm cho app services
```

### Còn thiếu / cần làm tiếp

| File | Mô tả | Priority |
|------|--------|----------|
| `backend/api/alert_manager.py` | Telegram Bot + Email SMTP alerts | 🟡 Trung |
| Docker runtime | Thêm/verify Dockerfile backend/frontend và compose commands | 🟡 Trung |
| ML inference data quality | Forecast/anomaly hiện fallback khi feature frame có NaN hoặc thiếu history đủ dài | 🟡 Trung |

### Ghi chú kỹ thuật

- `/api/health` vẫn không phụ thuộc DB.
- Nếu DB/model/LLM/Redis lỗi, route trả fallback thay vì crash app.
- Invalid province id ngoài `1..63` trả `404`.

---

## ✅ STAGE 2D — Frontend (API-INTEGRATED UI)

### Đã implement

| File / Area | Mô tả | Status |
|-------------|------|--------|
| `frontend/package.json` | Vite + React + TypeScript app scripts (`dev`, `build`, `lint`, `preview`) | ✅ Done |
| `frontend/src/App.tsx` | React Router: `/`, `/dashboard`, `/analytics`, `/compare`, `/map`, `/alerts` | ✅ Done |
| `frontend/src/components/Navigation.tsx` | Navbar desktop + bottom nav mobile, theme toggle, Compare nav | ✅ Done |
| `frontend/src/contexts/ThemeContext.tsx` | Tách hook `useTheme` để pass `react-refresh/only-export-components` | ✅ Done |
| `frontend/src/pages/LandingPage.tsx` | Landing page marketing/hero cho REIS/AeroSense | ✅ Done |
| `frontend/src/pages/Dashboard.tsx` | Dashboard V2: KPI row, Vietnam live map, AQI gauge, forecast band, insight panel | ✅ API + fallback |
| `frontend/src/pages/Analytics.tsx` | Analytics V2: filter Province/Range/Metric, forecast confidence band, calendar/top/radar/distribution | ✅ API + fallback |
| `frontend/src/pages/Compare.tsx` | Compare page: multi-line trend, 3 province cards, radar/gauge, heatmap table | ✅ API + fallback |
| `frontend/src/pages/NationPage.tsx` | Vietnam map dùng chung `VietnamLiveMap`, marker đồng bộ Dashboard | ✅ API + fallback |
| `frontend/src/pages/HealthAlert.tsx` | Tách AQI Health Alerts / AI Anomaly Events, không giả lập event khi API rỗng | ✅ API + fallback |
| `frontend/src/pages/LandingPage.tsx` | Bỏ hardcode fake KPI, dùng `/api/summary` hoặc nhãn fallback rõ | ✅ API + fallback |
| `frontend/src/pages/HealthAlert.tsx` | Alert center dùng `/api/anomalies`, fallback rõ ràng khi API down | ✅ API + fallback |
| `frontend/src/types.ts` | Chỉ chứa interfaces/types frontend + API contracts | ✅ Done |
| `frontend/src/mocks/mockData.ts` | 63 provinces + mock deterministic, không `Math.random()` trong render path | ✅ Done |
| `frontend/src/services/apiClient.ts` | REST client dùng `VITE_API_URL`, fallback default `http://localhost:8000` | ✅ Done |
| `frontend/src/hooks/useAQIData.ts` | Hooks fetch provinces/detail/summary/compare/insights/anomalies + normalize + mock fallback | ✅ Done |
| `frontend/src/hooks/useWebSocket.ts` | WebSocket hook dùng `VITE_WS_URL`, auto reconnect 1s/2s/4s/max 30s | ✅ Done |
| `frontend/src/services/geminiService.ts` | Typed mock AI advice service, giữ làm fallback/dev utility | ✅ Done |
| `frontend/src/components/KpiCard.tsx` | Reusable KPI card cho dashboard/analytics | ✅ Done |
| `frontend/src/components/AqiGauge.tsx` | Reusable AQI gauge | ✅ Done |
| `frontend/src/components/ForecastBandChart.tsx` | History + forecast lower/upper/value confidence band | ✅ Done |
| `frontend/src/components/InsightCard.tsx` | Insight card có source/cache/risk/timestamp metadata | ✅ Done |
| `frontend/src/components/VietnamLiveMap.tsx` | Reusable Vietnam live map dùng `/api/provinces`/WS summaries | ✅ Done |
| `frontend/src/components/ProvinceCompareCard.tsx` | Compare card với gauge + anomaly badge + radar | ✅ Done |

### Frontend verification (2026-05-14)

```bash
cd frontend
npm install
npm run lint
# pass
npm run build
# build pass, Vite warning bundle ~948 KB

npm run dev -- --host 0.0.0.0 --port 3000
curl -I http://localhost:3000/
# HTTP/1.1 200 OK
```

### Vấn đề còn tồn tại / cần làm tiếp

1. Build warning: bundle JS ~954 KB, nên code-split routes/recharts/map sau nếu muốn production polish.
2. Smoke test browser nên kiểm tra thêm Dashboard V2, Analytics filters và Compare page với API thật.
3. Dữ liệu đã dày hơn, nhưng anomaly/forecast model vẫn nên retrain/validate lại sau backfill để tận dụng lịch sử mới.

---

## 📝 STAGE 2E — Airflow MLOps (SKELETON DOCS)

| File | Mô tả |
|------|-------|
| `backend/airflow/dags/weekly_retrain.py` | DAG: extract → feature → train → evaluate → compare → hotswap |
| `docs/mlops_airflow_skeleton.md` | Skeleton design: DAG tasks, Input → Process → Output, contracts, acceptance criteria |

### Trạng thái hiện tại

```
✅ Đã có skeleton docs để thuyết trình/giao việc
✅ Đã xác định DAG contract: extract → validate → feature → train → evaluate → compare → report
⏳ Chưa implement `weekly_retrain.py`
⏳ Chưa chạy Airflow DAG thật
⏳ Chưa có MLflow registry promotion/hotswap tự động
```

---

## ⏳ STAGE 2F — Notebooks EDA (ĐANG LÀM)

| Notebook | Status | Mô tả |
|----------|--------|-------|
| `01_api_exploration.ipynb` | ✅ Done | Explore Open-Meteo API structure |
| `02_data_quality.ipynb` | ✅ Done | Data quality: missing values, duplicates, completeness, outliers, correlation |
| `03_backfill_historical_data.ipynb` | ✅ Done | Cào 50 ngày data lịch sử |
| `04_eda_air_quality.ipynb` | ✅ Done | AQI / PM distribution, correlation, seasonality, regional/spatial analysis, anomaly insights |
| `05-feature-engineering.ipynb` | ✅ Done | Feature experiments and final feature shortlist |
| `06_model_comparison.ipynb` | ✅ Done | Baseline model comparison |
| `06_model_comparison_copy.ipynb` | ✅ Done | Tuning vòng 2 cho LSTM + anomaly |

### Notebook verification (2026-05-14)

```
✅ 02_data_quality.ipynb: 15 cells, 7/7 code cells executed
✅ 04_eda_air_quality.ipynb: 84 cells, 27/30 code cells executed
✅ 05-feature-engineering.ipynb: 14 cells, 6/6 code cells executed
```

Ghi chú nhỏ: `04_eda_air_quality.ipynb` còn 3 code cells chưa execute; trong đó có cell cài package/commented-out và một vài cell nên rerun lại trước khi nộp final. File feature engineering hiện đang tên `05-feature-engineering.ipynb`, khác tên trong task spec là `05_feature_engineering.ipynb`; nên cân nhắc rename cho đồng bộ.

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
[ ] pytest backend/tests/ -v  → Tất cả PASS
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
  ✅ pytest backend/tests/ -v → Tất cả PASS
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

### Ngay lập tức (Data + Demo Readiness)
1. Chạy API + frontend, kiểm tra Dashboard V2, Analytics filters và Compare page trên browser với dữ liệu backfill thật
2. Re-run training/inference validation để anomaly/forecast tận dụng thêm 50 ngày lịch sử
3. Chạy thêm một realtime cycle sau backfill để xác nhận dữ liệu mới tiếp tục nối vào timeline

### Polish còn thiếu
4. Code-split frontend routes/charts/map để giảm bundle warning
5. Thêm loading/error component dùng chung để UI nhất quán hơn
6. Rerun/finalize `04_eda_air_quality.ipynb` để toàn bộ code cells sạch output cuối
7. Cân nhắc rename `05-feature-engineering.ipynb` → `05_feature_engineering.ipynb` cho khớp `TASK_ASSIGNMENT.md`

### Cuối cùng (MLOps & Demo)
8. Viết `backend/airflow/dags/weekly_retrain.py`
9. Viết `tools/simulator.py` để demo anomaly spike

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

2026-05-14 — Progress sync after EDA notebooks
- Đã cập nhật trạng thái notebook: 02_data_quality, 04_eda_air_quality, 05-feature-engineering đều đã có nội dung và đã chạy phần lớn/toàn bộ code cells
- Stage 2F tăng từ ~65% lên ~90%
- Next Steps đã đổi trọng tâm sang API/WebSocket, Frontend, isolation_forest tests, MLOps và simulator

2026-05-14 — API shell + frontend mock UI sync
- Đã thêm FastAPI shell với `GET /api/health` và test route cơ bản pass 3/3
- Đã selective import `frontend/` từ nhánh `feat_fe` vào `develop`
- Frontend hiện có Vite React SPA, 5 routes, dashboard/map/analytics/alerts dùng mock data
- `npm run build` pass, dev server port 3000 trả HTTP 200
- Ghi chú lịch sử: lint từng còn lỗi, đã được xử lý ở các task frontend/API integration sau đó

2026-05-14 — Dashboard/Analytics V2 + historical backfill foundation
- Đã thêm `backend/scripts/backfill_historical_data.py`, dry-run 1 ngày / Hà Nội fetch được 48 hourly rows, không ghi DB khi `--dry-run`
- Đã chạy backfill thật `--days 50`: 63/63 tỉnh success, fetched 77,112 rows, inserted thêm 29,439 rows sau khi chuẩn hóa UTC
- Đã fix timezone cho backfill script và realtime collector: Open-Meteo timestamps được lưu UTC đúng, không còn future rows
- DB sau backfill: 77,099 rows, đủ 63 tỉnh, mỗi tỉnh tối thiểu 1,225 rows, latest `2026-05-14 13:00:00+00`
- Đã mở rộng API: `/api/province/{id}?hours=...`, `/api/summary`, `/api/compare`
- Đã thêm Dashboard V2: KPI row, Vietnam live map, AQI gauge, forecast band, insight metadata
- Đã thêm Analytics V2: Province/Range/Metric filters, forecast confidence band, calendar/top/radar/distribution
- Đã thêm Compare page `/compare`: multi-line chart, province compare cards, heatmap table
- Verification: backend selected tests 24 passed, frontend `npm run lint` pass, frontend `npm run build` pass, API smoke sau backfill pass

2026-05-14 — Demo-ready quality audit fixes
- Đã chuẩn hóa wording/contract: `AQI warnings` khác `AI anomalies`
- Đã thêm inference cache TTL cho API province/forecast/insights/compare để giảm gọi model lặp
- Đã sửa Alerts không dùng mock khi API trả empty list; pollen/allergy được gắn nhãn demo placeholder
- Map page dùng chung `VietnamLiveMap` với Dashboard, marker đồng nhất
- Landing page dùng `/api/summary` hoặc nhãn fallback, không còn hardcode `Hanoi 42 AQI`
- Docker Compose app services đã cập nhật Vite/FastAPI hiện tại, thêm `backend/Dockerfile` và `frontend/Dockerfile`
- Verification: backend selected tests 26 passed, frontend `npm run lint` pass, frontend `npm run build` pass
```
