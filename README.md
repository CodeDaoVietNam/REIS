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
cp .env.example .env
# Chỉnh sửa .env: thêm GEMINI_API_KEY hoặc OPENAI_API_KEY
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
python processing/consumer.py

# Terminal 2: Start data collector (poll mỗi 15 phút)
python ingestion/scheduler.py

# Terminal 3: Start API server
uvicorn api.main:app --reload --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
# Mở http://localhost:3000
```

### 6. One-click Demo (tất cả trong 1 lệnh)

```bash
docker-compose --profile full up -d
# Dashboard tại http://localhost:3000
# API docs tại http://localhost:8000/docs
# Airflow UI tại http://localhost:8080
# MLflow UI tại http://localhost:5000
```

---

## 🔧 Environment Variables

```env
# LLM (bắt buộc 1 trong 2)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here       # Alternative

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
INSIGHT_CACHE_TTL=3600             # seconds (1 hour)
ANOMALY_THRESHOLD=0.70             # Isolation Forest score
CRITICAL_THRESHOLD=0.85            # Trigger alert
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
│   ├── insights/
│   │   ├── prompt_builder.py     # Context assembly
│   │   ├── llm_client.py         # Gemini/OpenAI wrapper
│   │   └── insight_cache.py      # Redis TTL cache
│   ├── api/
│   │   ├── main.py               # FastAPI app
│   │   ├── routes/               # REST endpoints
│   │   ├── websocket.py          # WS broadcaster
│   │   └── alert_manager.py      # Telegram + Email
│   ├── airflow/
│   │   └── dags/weekly_retrain.py
│   ├── tests/
│   ├── notebooks/                # EDA & model development
│   └── scripts/
│       └── setup_db.py
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
- **Input:** 48-hour rolling window, multivariate (AQI, PM2.5, temperature, wind, humidity)
- **Output:** 12-step ahead forecast với confidence intervals
- **Retrain:** Tự động mỗi Chủ Nhật 2:00 AM qua Airflow

### Anomaly Detection (Isolation Forest)
- **Input:** 7-feature vector `[pm2_5, pm10, aqi, no2, o3, temperature, wind_speed]`
- **Scores:** `> 0.70` → ANOMALY, `> 0.85` → CRITICAL + Alert
- **Latency:** < 100ms per inference

### Insight Engine (LLM)
- **Provider:** Google Gemini 1.5 Flash (mặc định) hoặc GPT-4o-mini
- **Cache:** Redis TTL 1 giờ — tiết kiệm ~80% API calls
- **Output:** Đánh giá + Nguyên nhân + Dự báo + Khuyến nghị (< 150 từ)

---

## 🧪 Testing

```bash
# Chạy toàn bộ test suite
cd backend
pytest tests/ -v

# Test riêng từng module
pytest tests/test_validator.py -v
pytest tests/test_isolation_forest.py -v
pytest tests/test_forecast.py -v

# Coverage report
pytest tests/ --cov=. --cov-report=html
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
- [x] MLOps auto-retraining
- [x] Real-time dashboard

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
