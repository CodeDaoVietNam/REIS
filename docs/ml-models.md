# ML Models

Tài liệu này mô tả chi tiết ba mô hình ML trong REIS: Isolation Forest (phát hiện bất thường), LSTM và Prophet (dự báo AQI). Bao gồm feature engineering, architecture, evaluation methodology, và kết quả benchmark.

---

## Tổng quan

REIS sử dụng hai nhóm model hoạt động **song song** tại mỗi inference cycle:

```
┌─────────────────────────────────────────────────────────┐
│  asyncio.gather() — chạy đồng thời, không chờ nhau      │
├──────────────────────────┬──────────────────────────────┤
│  Nhánh A                 │  Nhánh B                     │
│  Isolation Forest        │  LSTM / Prophet               │
│  "Đây có bất thường?"    │  "12 giờ tới sẽ thế nào?"    │
│  Input: 7 features       │  Input: 48h × 12 features    │
│  Output: score 0.0–1.0   │  Output: forecast[12]        │
│  Latency: < 100ms        │  Latency: < 500ms            │
└──────────────────────────┴──────────────────────────────┘
```

---

## Feature Engineering

Mọi model đều dùng chung **feature pipeline** trong `backend/processing/feature_engineer.py`.

### Raw features (từ DB)

```python
RAW_FEATURES = [
    "pm2_5",         # Bụi mịn µg/m³
    "pm10",          # Bụi thô µg/m³
    "aqi",           # US AQI tổng hợp
    "no2",           # Nitrogen dioxide µg/m³
    "ozone",         # Ozone µg/m³
    "temperature",   # Nhiệt độ °C
    "humidity",      # Độ ẩm %
    "wind_speed",    # Tốc độ gió km/h
]
```

### Engineered features (tạo thêm)

```python
# Lag features — giúp model biết "xu hướng đang đi lên hay xuống"
"pm2_5_lag_1h"          # PM2.5 tại t-1h
"pm2_5_lag_3h"          # PM2.5 tại t-3h
"pm2_5_lag_6h"          # PM2.5 tại t-6h
"pm2_5_lag_24h"         # PM2.5 cùng giờ hôm qua

# Rolling statistics — "mức bình thường" của tỉnh này
"aqi_rolling_mean_3h"   # Trung bình AQI 3 giờ gần nhất
"aqi_rolling_mean_6h"   # Trung bình AQI 6 giờ
"aqi_rolling_std_6h"    # Độ lệch chuẩn AQI 6 giờ (đo biến động)

# Time features — patterns theo giờ/ngày/mùa
"hour_of_day"           # 0–23
"day_of_week"           # 0=Monday, 6=Sunday
"month"                 # 1–12
"is_weekend"            # 0 hoặc 1
"is_rush_hour"          # 1 nếu 7-9h hoặc 17-19h
```

### FEATURE_COLUMNS cho LSTM (thứ tự quan trọng — không được thay đổi)

```python
# backend/config/constants.py
FEATURE_COLUMNS = [
    # Raw air quality (5)
    "pm2_5", "pm10", "aqi", "no2", "ozone",
    # Raw weather (3)
    "temperature", "humidity", "wind_speed",
    # Lag features (4)
    "pm2_5_lag_1h", "pm2_5_lag_3h", "pm2_5_lag_6h", "aqi_rolling_mean_3h",
]
# Tổng: 12 features

TARGET_COLUMN    = "aqi"
FORECAST_HORIZON = 12   # Dự báo 12 giờ tới
HISTORY_WINDOW   = 48   # Dùng 48 giờ lịch sử làm input
```

> **Cảnh báo:** LSTM model nhạy cảm với thứ tự features. Phải luôn dùng `FEATURE_COLUMNS` từ `constants.py` — không hardcode danh sách riêng ở bất kỳ đâu.

### Normalization

```python
from sklearn.preprocessing import MinMaxScaler

# Fit scaler trên training data, save cùng model
scaler = MinMaxScaler(feature_range=(0, 1))
X_train_scaled = scaler.fit_transform(X_train)

# Khi inference, dùng scaler đã fit (không fit lại)
X_input_scaled = scaler.transform(X_input)
```

Tại sao cần normalize: AQI (0–500) >> wind_speed (0–50) → không normalize thì model bị bias về AQI, bỏ qua wind_speed. Normalize về [0,1] cho tất cả features trọng số bình đẳng.

---

## Model 1: Isolation Forest — Anomaly Detection

### Mục đích

Phát hiện spike ô nhiễm bất thường trong < 100ms, không cần dữ liệu có label.

### Cơ chế hoạt động

```
Điểm bình thường: cần nhiều "câu hỏi" để tách riêng → path dài
Điểm bất thường: chỉ cần vài "câu hỏi" → path ngắn → score cao

Score = 1 - (avg_path_length / expected_path_length)
```

### Hyperparameters

```python
from sklearn.ensemble import IsolationForest

model = IsolationForest(
    n_estimators=200,      # 200 cây — đủ ổn định, không quá nặng
    contamination=0.05,    # Ước tính 5% data là bất thường
    max_samples="auto",    # min(256, n_samples)
    random_state=42,       # Reproducible
    n_jobs=-1,             # Dùng tất cả CPU cores
)
```

### Input

```python
# 7 features: chỉ raw environmental values, không dùng lag/rolling
ANOMALY_FEATURES = ["pm2_5", "pm10", "aqi", "no2", "ozone", "temperature", "wind_speed"]

# Input shape: (1, 7) — 1 điểm dữ liệu, 7 features
feature_vector = np.array([[pm2_5, pm10, aqi, no2, ozone, temp, wind]])
feature_vector_scaled = scaler.transform(feature_vector)
```

### Score inversion

```python
# sklearn trả về score âm: gần -1 = bất thường nhất (confusing!)
raw_score = model.decision_function(feature_vector_scaled)[0]
# raw_score range: khoảng (-0.5, 0.5)

# REIS đảo về 0.0–1.0: cao = bất thường (intuitive)
anomaly_score = float(np.clip(0.5 - raw_score, 0, 1))

# Thresholds
is_anomaly  = anomaly_score > 0.70   # Ghi vào DB, hiển thị trên UI
is_critical = anomaly_score > 0.85   # Trigger Alert Manager → Telegram
```

### Training

```python
# Train offline, trên 30 ngày lịch sử
# Isolation Forest không cần nhiều data như LSTM
X_train = historical_df[ANOMALY_FEATURES].dropna().values
model.fit(X_train)

# Save với joblib (nhỏ gọn hơn pickle cho sklearn models)
import joblib
joblib.dump(model, "artifacts/isolation_forest.joblib")
joblib.dump(scaler, "artifacts/anomaly_scaler.joblib")
```

---

## Model 2: LSTM — Time-series Forecasting

### Mục đích

Dự báo AQI trong 12 giờ tới dựa trên 48 giờ lịch sử, sử dụng 12 features multivariate.

### Tại sao LSTM cho bài toán này

| Yêu cầu | ARIMA | Prophet | LSTM |
|---------|-------|---------|------|
| Multivariate (nhiều biến input) | ❌ | ❌ | ✅ |
| Học patterns phi tuyến | ❌ | Một phần | ✅ |
| Long-range dependencies (24h+) | Khó | Tốt | ✅ |
| Xử lý missing values | Cần xử lý | Tốt | Cần xử lý |
| Giải thích được | ✅ | ✅ | ❌ |
| Cần nhiều data | ❌ | ❌ | ✅ (cần >30 ngày) |

### Architecture

```
Input shape: (batch_size=32, time_steps=48, features=12)

Layer 1:  LSTM(units=64, return_sequences=True)
          → Output shape: (32, 48, 64)
          → "Nhớ patterns ngắn hạn trong 48 giờ"

Layer 2:  Dropout(rate=0.2)
          → Ngăn overfitting bằng cách random drop 20% neurons

Layer 3:  LSTM(units=32, return_sequences=False)
          → Output shape: (32, 32)
          → "Tóm tắt thành biểu diễn compact 32 chiều"

Layer 4:  Dropout(rate=0.2)

Layer 5:  Dense(units=12)
          → Output shape: (32, 12)
          → Dự báo 12 bước thời gian (T+1h đến T+12h)
```

```python
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(48, 12)),
    Dropout(0.2),
    LSTM(32),
    Dropout(0.2),
    Dense(12),
])

model.compile(
    optimizer="adam",
    loss="mse",          # Mean Squared Error — phạt nặng outlier predictions
    metrics=["mae"],     # Mean Absolute Error — dễ interpret
)
```

### Training config

```python
callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=10,         # Dừng nếu val_loss không giảm sau 10 epoch
        restore_best_weights=True,
    ),
    ModelCheckpoint(
        filepath="artifacts/lstm_best.keras",
        save_best_only=True,
        monitor="val_loss",
    ),
]

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32,
    callbacks=callbacks,
    verbose=1,
)
```

### Data preparation

```python
def create_sequences(df, window=48, horizon=12):
    """
    Tạo sequences cho LSTM từ DataFrame time-series.
    
    Args:
        df: DataFrame đã sorted theo time, đã có tất cả features
        window: số giờ lịch sử làm input
        horizon: số giờ cần dự báo
    
    Returns:
        X: shape (n_samples, window, n_features)
        y: shape (n_samples, horizon) — chỉ target AQI
    """
    X, y = [], []
    data = df[FEATURE_COLUMNS].values
    target = df[TARGET_COLUMN].values

    for i in range(len(data) - window - horizon + 1):
        X.append(data[i : i + window])          # 48 giờ input
        y.append(target[i + window : i + window + horizon])  # 12 giờ target
    
    return np.array(X), np.array(y)

# Split: 70% train, 15% val, 15% test
# Không dùng random shuffle — phải giữ thứ tự thời gian!
n = len(X)
X_train, y_train = X[:int(n*0.7)], y[:int(n*0.7)]
X_val,   y_val   = X[int(n*0.7):int(n*0.85)], y[int(n*0.7):int(n*0.85)]
X_test,  y_test  = X[int(n*0.85):], y[int(n*0.85):]
```

### Inference

```python
async def predict_forecast(province_id: int, history_hours: int = 48) -> ForecastResult:
    # Lấy lịch sử từ DB
    history_df = await db.fetch_history(province_id, hours=history_hours)
    
    # Feature engineering
    history_df = feature_engineer(history_df)
    
    # Normalize
    X = scaler.transform(history_df[FEATURE_COLUMNS].values)
    X = X.reshape(1, 48, 12)  # (1 sample, 48 timesteps, 12 features)
    
    # Predict
    y_pred_scaled = model.predict(X, verbose=0)[0]  # shape: (12,)
    
    # Inverse transform chỉ target column
    y_pred = inverse_transform_target(y_pred_scaled)
    
    # Tính confidence interval (empirical từ validation set)
    mae = get_model_mae()
    lower = y_pred - 1.5 * mae
    upper = y_pred + 1.5 * mae
    
    return ForecastResult(
        values=y_pred.tolist(),
        lower=lower.tolist(),
        upper=upper.tolist(),
        model_used="lstm",
    )
```

---

## Model 3: Prophet — Seasonal Forecasting

### Mục đích

Dự báo univariate (chỉ AQI) với khả năng handle seasonality tự động. Dùng làm **challenger** để so sánh với LSTM, và **fallback** khi LSTM không đủ data.

### Ưu điểm so với LSTM

- Không cần nhiều data (30 ngày là đủ vs LSTM cần 60+)
- Giải thích được: tách rõ trend + weekly seasonality + daily seasonality
- Xử lý missing values tốt hơn
- Không cần normalize

### Nhược điểm

- Chỉ univariate — không học được quan hệ giữa PM2.5, wind, temperature
- Không capture được patterns phi tuyến phức tạp

### Implementation

```python
from prophet import Prophet
import pandas as pd

def train_prophet(df: pd.DataFrame) -> Prophet:
    """
    df phải có 2 cột: 'ds' (datetime) và 'y' (AQI value)
    """
    # Prophet yêu cầu timezone-naive!
    df["ds"] = df["time"].dt.tz_localize(None)
    df["y"]  = df["aqi"]
    
    model = Prophet(
        daily_seasonality=True,    # AQI cao vào giờ cao điểm sáng/chiều
        weekly_seasonality=True,   # Cuối tuần ít xe → AQI thấp hơn
        yearly_seasonality=False,  # Không đủ 1 năm data để học
        changepoint_prior_scale=0.05,   # Độ nhạy với trend changes
        seasonality_prior_scale=10.0,   # Độ mạnh của seasonality
    )
    model.fit(df[["ds", "y"]])
    return model

def predict_prophet(model: Prophet, horizon: int = 12) -> pd.DataFrame:
    future = model.make_future_dataframe(periods=horizon, freq="H")
    forecast = model.predict(future)
    
    # Lấy 12 giờ cuối (forecast, không phải in-sample)
    result = forecast.tail(horizon)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    return result
```

---

## Evaluation Methodology

### Metrics

| Metric | Công thức | Target | Ý nghĩa thực tế |
|--------|-----------|--------|-----------------|
| **MAE** | `mean(|y - ŷ|)` | < 15 AQI | Sai số trung bình. MAE=10 → dự báo lệch TB 10 units |
| **RMSE** | `sqrt(mean((y-ŷ)²))` | < 25 AQI | Phạt nặng outlier predictions. RMSE >> MAE = nhiều spike lớn |
| **MAPE** | `mean(|y-ŷ|/y) × 100` | < 20% | Tỉ lệ % sai số. Dễ communicate với non-technical |
| **CI Coverage** | `% actual ∈ [lower, upper]` | > 90% | Confidence interval có đáng tin không |

### Train/Val/Test Split

```
Không dùng random shuffle — vi phạm tính liên tục của time series!

Timeline:
│──────── 70% train ────────│── 15% val ──│── 15% test ──│
T₀                          T₁            T₂             T₃

Train:  Học patterns
Val:    Tune hyperparameters, early stopping
Test:   Đánh giá cuối cùng, báo cáo metrics
```

### Benchmark kết quả (dự kiến)

| Model | MAE (AQI) | RMSE | MAPE | Training Time |
|-------|-----------|------|------|---------------|
| ARIMA (baseline) | ~22 | ~31 | ~28% | < 1 min |
| Prophet | ~17 | ~24 | ~21% | ~2 min |
| **LSTM** | **~13** | **~19** | **~16%** | ~15 min |

> Kết quả thực tế sẽ cập nhật sau khi chạy `notebooks/04_model_comparison.ipynb`.

### MLflow tracking

Mọi training run đều log tự động:

```python
import mlflow

with mlflow.start_run(experiment_id=experiment_id):
    # Log hyperparameters
    mlflow.log_params({
        "model_type": "lstm",
        "window_size": 48,
        "horizon": 12,
        "n_features": 12,
        "lstm_units_1": 64,
        "lstm_units_2": 32,
        "dropout": 0.2,
        "epochs_trained": len(history.history["loss"]),
    })
    
    # Log metrics
    mlflow.log_metrics({
        "train_mae": train_mae,
        "val_mae": val_mae,
        "test_mae": test_mae,
        "test_rmse": test_rmse,
        "test_mape": test_mape,
    })
    
    # Log model artifact
    mlflow.keras.log_model(model, artifact_path="lstm_model")
    
    # Log plots
    mlflow.log_figure(loss_plot, "training_loss.png")
    mlflow.log_figure(forecast_plot, "sample_forecast.png")
```

---

## Model Registry & Deployment

### Stages trong MLflow

```
Staging      → Vừa train xong, chưa so sánh với production
Production   → Đang serve real-time inference (chỉ 1 model tại 1 thời điểm)
Archived     → Đã bị thay thế, giữ lại để rollback nếu cần
```

### Champion/Challenger logic

```python
def should_deploy_new_model(new_mae: float, prod_mae: float) -> bool:
    """
    Deploy model mới chỉ khi cải thiện ít nhất 5%.
    Tránh deploy noise — cải thiện nhỏ có thể là statistical variance.
    """
    improvement = (prod_mae - new_mae) / prod_mae
    return improvement >= 0.05    # 5% improvement threshold

# Ví dụ:
# prod_mae = 15.0, new_mae = 13.5 → improvement = 10% → DEPLOY ✅
# prod_mae = 15.0, new_mae = 14.8 → improvement = 1.3% → KEEP ❌
```

### Zero-downtime hotswap

```python
# backend/models/predict.py
_current_model = None
_current_scaler = None
_model_lock = asyncio.Lock()

async def hotswap_model(new_model_uri: str):
    """Load model mới trước, swap sau — không downtime."""
    new_model  = mlflow.keras.load_model(new_model_uri)
    new_scaler = load_scaler(new_model_uri)
    
    # Smoke test trước khi swap
    test_input = np.zeros((1, 48, 12))
    test_output = new_model.predict(test_input)
    assert test_output.shape == (1, 12), "Model output shape mismatch!"
    
    async with _model_lock:     # Thread-safe swap
        global _current_model, _current_scaler
        _current_model  = new_model
        _current_scaler = new_scaler
    
    logger.info("Model hotswapped successfully", extra={"uri": new_model_uri})
```

---

## Liên quan

- `backend/models/lstm_model.py` — LSTM implementation
- `backend/models/prophet_model.py` — Prophet wrapper
- `backend/models/isolation_forest.py` — Anomaly detector
- `backend/models/predict.py` — Unified inference interface
- `backend/processing/feature_engineer.py` — Feature pipeline
- `backend/config/constants.py` — `FEATURE_COLUMNS`, thresholds
- `backend/airflow/dags/weekly_retrain.py` — Auto-retrain DAG
- `notebooks/03_eda_and_features.ipynb` — EDA và feature exploration
- `notebooks/04_model_comparison.ipynb` — Benchmark 3 models
