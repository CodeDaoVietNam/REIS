# 🌿 Realtime Environmental Intelligence System (REIS)

> **Biến dữ liệu môi trường thô thành hành động tức thì** — kết hợp Streaming Data Pipeline, Predictive AI và Generative AI để giám sát chất lượng không khí 63 tỉnh thành Việt Nam theo thời gian thực.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-3.6-black?logo=apache-kafka)](https://kafka.apache.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Vấn Đề & Giải Pháp

**Vấn đề:** Các hệ thống giám sát môi trường hiện tại (AirVisual, CAQM...) chỉ hiển thị số liệu tại thời điểm hiện tại — bị động, không dự báo, không giải thích.

**Giải pháp REIS:**
- 📡 **Real-time streaming** — dữ liệu 63 tỉnh cập nhật mỗi 15 phút qua Kafka pipeline
- 🤖 **Predictive AI** — LSTM/Prophet dự báo AQI và PM2.5 trong 3–12 giờ tới
- 💬 **Generative AI** — LLM tự động sinh lời khuyên bằng ngôn ngữ tự nhiên
- 🔄 **MLOps** — Airflow tự động retrain mô hình hàng tuần, chống Data Drift

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                    REIS — 5-Layer Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  L1: DATA INGESTION                                               │
│  Open-Meteo API ──► APScheduler ──► Pydantic Validator           │
│                                          │                        │
│                                    ┌─────▼──────┐                │
│  L2: STORAGE                       │   Kafka    │                │
│                                    └─────┬──────┘                │
│                              ┌───────────▼──────────┐            │
│                              │  TimescaleDB + Redis  │            │
│                              └───────────┬──────────┘            │
│                                          │                        │
│  L3: AI INFERENCE          ┌─────────────▼──────────────┐        │
│                            │  Isolation Forest (Anomaly) │        │
│                            │  LSTM / Prophet (Forecast)  │        │
│                            │  Gemini / GPT-4 (Insights)  │        │
│                            └─────────────┬──────────────┘        │
│                                          │                        │
│  L4: DELIVERY              ┌─────────────▼──────────────┐        │
│                            │  FastAPI + WebSocket        │        │
│                            │  React Dashboard + Map      │        │
│                            │  Alert Manager (Telegram)   │        │
│                            └────────────────────────────┘        │
│                                                                   │
│  L5: MLOPS (background)                                           │
│  Airflow DAG ──► Retrain ──► MLflow Registry ──► Hot-swap        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Prerequisites

- Docker Desktop (≥ 25.0) + Docker Compose (≥ 2.24)
- Python 3.11+
- Node.js 20+
- 8GB RAM khuyến nghị

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/reis.git
cd reis
# Chỉnh sửa .env: thêm GEMINI_API_KEY nếu muốn test insight thật
```

### 2. Start Infrastructure

```bash
docker-compose up -d
# Đợi ~60 giây cho Kafka và TimescaleDB khởi động
docker-compose ps  # Kiểm tra tất cả services healthy
```

### 3. Setup Database

```bash
cd backend
pip install -r requirements.txt
python scripts/setup_db.py  # Tạo tables và hypertables
```

### 4. Start Data Pipeline

```bash
# Terminal 1: Start Kafka consumer
python backend/processing/consumer.py

# Terminal 2: Start data collector (poll mỗi 15 phút)
python backend/ingestion/scheduler.py
```

### 5. Backfill + Train Models

```bash
# Backfill dữ liệu lịch sử trước bằng notebook
# backend/notebooks/03_backfill_historical_data.ipynb

# Train và export toàn bộ model từ DB
cd ..
python backend/scripts/train_models.py --model all
```

### 6. Test Insight Generation

```bash
# Smoke test LLM insight với payload mẫu
python backend/scripts/test_insight_generation.py

# Test qua Redis cache
python backend/scripts/test_insight_generation.py --use-cache

# Test với dữ liệu thật từ DB + model inference
python backend/scripts/test_insight_generation.py --use-db
```

### 7. Start Frontend / API

> Hiện tại frontend và FastAPI route layer vẫn đang được triển khai dần.
> Core inference và insight engine đã sẵn sàng, nhưng `api.main` và dashboard chưa hoàn tất end-to-end.

```bash
cd frontend
npm install
npm run dev
```

### 8. One-click Infra Demo

```bash
docker-compose --profile full up -d
# Airflow UI tại http://localhost:8080
# MLflow UI tại http://localhost:5000
# pgAdmin tại http://localhost:5050
# Kafka UI tại http://localhost:8090
```

---

## 🔧 Environment Variables

```env
# LLM
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
OPENAI_API_KEY=your_key_here       # Optional fallback
OPENAI_MODEL=gpt-4o-mini

# Database
DATABASE_URL=postgresql://reis:reis@localhost:5432/reis_db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379

# Alerts (tùy chọn)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
ALERT_EMAIL=your@email.com

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# App
ENV=development                    # development | production
LOG_LEVEL=INFO
INSIGHT_CACHE_TTL_SECONDS=3600     # seconds (1 hour)
```

---

## 📁 Project Structure

```
reis/
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── ingestion/
│   │   ├── collector.py          # Open-Meteo API fetcher
│   │   ├── validator.py          # Pydantic schema validation
│   │   ├── producer.py           # Kafka producer
│   │   └── scheduler.py          # APScheduler entry point
│   ├── processing/
│   │   ├── consumer.py           # Kafka → TimescaleDB
│   │   └── feature_engineer.py  # Lag, rolling, time features
│   ├── models/
│   │   ├── lstm_model.py         # LSTM (Keras/TF)
│   │   ├── prophet_model.py      # Prophet wrapper
│   │   ├── isolation_forest.py  # Anomaly detector
│   │   └── predict.py            # Unified inference interface
│   │   └── artifacts/            # Exported model artifacts
│   ├── insights/
│   │   ├── prompt_builder.py     # Prompt + template fallback
│   │   ├── llm_client.py         # Gemini/OpenAI wrapper
│   │   └── insight_cache.py      # Redis TTL cache
│   ├── api/                      # API layer planned
│   │   ├── routes/               # REST endpoints planned
│   │   ├── websocket.py          # WS broadcaster planned
│   │   └── alert_manager.py      # Telegram + Email planned
│   ├── airflow/
│   │   └── dags/weekly_retrain.py
│   ├── tests/
│   ├── notebooks/                # EDA & model development
│   └── scripts/
│       ├── setup_db.py
│       ├── train_models.py
│       └── test_insight_generation.py
│
├── frontend/
│   ├── src/
│   │   ├── components/           # AQIMap, ForecastChart, InsightCard
│   │   ├── hooks/                # useWebSocket, useAQIData
│   │   ├── pages/                # Dashboard, Alerts, Analytics
│   │   └── utils/                # AQI color scale, formatters
│   └── vite.config.ts
│
└── tools/
    └── simulator.py              # Demo spike injector
```

---

## 🗺️ API Reference

> Planned interface. Một phần endpoint vẫn chưa được implement trong repo hiện tại.

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `GET` | `/api/provinces` | Danh sách 63 tỉnh + AQI hiện tại |
| `GET` | `/api/province/{id}` | Chi tiết 1 tỉnh: current + 48h history + forecast |
| `GET` | `/api/forecast/{id}` | Dự báo 12h tới với confidence interval |
| `GET` | `/api/anomalies` | Anomalies trong 24h qua |
| `GET` | `/api/insights/{id}` | LLM insight (cached) |
| `WS` | `/ws/live` | Real-time WebSocket stream |
| `POST` | `/api/simulator/spike` | **DEMO ONLY** — inject PM2.5 spike |

📖 Interactive docs: `http://localhost:8000/docs`

---

## 🤖 AI Components

### Forecasting (LSTM + Prophet)
- **Input:** 12-hour lookback window, multivariate engineered features
- **Output:** 12-step ahead forecast với confidence intervals
- **Champion config:** stacked LSTM `128 -> 64`, `dropout=0.2`, `Adam(1e-3)`, `Huber loss`, sample weighting cho spike
- **Fallback:** Prophet nếu LSTM unavailable

### Anomaly Detection (Isolation Forest)
- **Input:** engineered feature set gồm AQI/PM + lag + rolling + delta
- **Direction:** ưu tiên ranking / top suspicious events
- **Threshold dùng trong code hiện tại:** `0.55` cho strict alert gating
- **Latency:** < 100ms per inference

### Insight Engine (LLM)
- **Provider:** Google Gemini 2.5 Flash (mặc định) hoặc GPT-4o-mini fallback
- **Cache:** Redis TTL 1 giờ — tiết kiệm ~80% API calls
- **Output:** Đánh giá + Nguyên nhân + Dự báo + Khuyến nghị (< 150 từ)
- **Fallback:** template text nếu provider lỗi / timeout / thiếu key

---

## 🧪 Testing

```bash
# Chạy test core ML + insight
python -m pytest backend/tests/test_lstm_model.py -q
python -m pytest backend/tests/test_prophet_model.py -q
python -m pytest backend/tests/test_predict.py -q
python -m pytest backend/tests/test_prompt_builder.py backend/tests/test_llm_client.py backend/tests/test_insight_cache.py -q

# Chạy toàn bộ test backend
python -m pytest backend/tests/ -v

# Coverage report
python -m pytest backend/tests/ --cov=backend --cov-report=html
```

---

## 🎬 Demo — Spike Simulation

```bash
# Giả lập spike PM2.5 cực cao tại TP.HCM
python tools/simulator.py --province hcm --pm25 350 --duration 600

# Giả lập spike cho Hà Nội
python tools/simulator.py --province hanoi --aqi 280

# Reset về dữ liệu thật
python tools/simulator.py --reset
```

Sau khi inject: Dashboard đỏ lên → Isolation Forest alert → LLM sinh cảnh báo → Telegram notification — tất cả trong < 5 giây.

---

## 📊 Data Sources

| Nguồn | API | Chỉ số | Tần suất |
|-------|-----|--------|----------|
| Open-Meteo Weather | `/v1/forecast` | temperature, humidity, wind, precipitation | 15 phút |
| Open-Meteo Air Quality | `/v1/air-quality` | PM2.5, PM10, AQI, NO₂, O₃, UV | 1 giờ |

**Coverage:** 63 tỉnh thành Việt Nam — 1 batch request (không cần API key).

---

## 🔄 MLOps Pipeline

```
Every Sunday 2:00 AM (Airflow DAG: weekly_retrain)
│
├── 1. Extract: Query last 30 days from TimescaleDB
├── 2. Feature Engineering: lag, rolling, time features
├── 3. Train: LSTM + Prophet (parallel)
├── 4. Evaluate: MAE, RMSE, MAPE on holdout set
├── 5. Compare: New model vs Production model
│
├── If MAE improved:
│   ├── 6a. Register artifact in MLflow
│   ├── 7a. Hot-swap model (zero downtime)
│   └── 8a. Send success report
│
└── If MAE degraded:
    ├── 6b. Keep current model
    ├── 7b. Log drift report
    └── 8b. Send warning report
```

MLflow UI: `http://localhost:5000`

---

## 🚀 Roadmap

### Phase 1 (Current) — Việt Nam
- [x] 5-layer streaming architecture
- [x] Dual-AI inference (Predictive + Generative)
- [x] Train/export script cho model artifacts
- [x] Insight engine với Gemini + Redis cache
- [ ] FastAPI route layer hoàn chỉnh
- [ ] Real-time dashboard hoàn chỉnh
- [ ] Airflow retrain pipeline hoàn chỉnh

### Phase 2 — Enhancements
- [ ] Graph Neural Network (Spatio-temporal forecasting)
- [ ] Global scale: 50 cities worldwide
- [ ] Multi-language insights (EN/VI/JP)
- [ ] Health Risk Calculator
- [ ] Mobile PWA

---

## 📚 References

- [Open-Meteo API](https://open-meteo.com/en/docs)
- [TimescaleDB Docs](https://docs.timescale.com)
- [Meta Prophet](https://facebook.github.io/prophet/)
- [MLflow Tracking](https://mlflow.org/docs/latest/tracking.html)
- [WorldMonitor](https://github.com/koala73/worldmonitor) — inspiration

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
