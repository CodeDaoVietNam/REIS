# Airflow MLOps Skeleton — Weekly Retrain DAG

> Status: Documentation skeleton only.  
> Purpose: dùng để nộp/thuyết trình và làm handoff cho thành viên DevOps/ML nếu còn thời gian implement sau deadline.

---

## 1. Mục Tiêu

Mục tiêu của Stage 2E là thiết kế pipeline MLOps giúp REIS không phải retrain model thủ công mãi mãi.

Ở trạng thái production lý tưởng, hệ thống sẽ:

1. Lấy dữ liệu mới từ TimescaleDB.
2. Tạo feature engineering giống pipeline inference.
3. Train lại forecast/anomaly model theo lịch.
4. Evaluate model mới trên holdout set.
5. So sánh model mới với model production hiện tại.
6. Chỉ promote model mới nếu chất lượng tốt hơn đủ rõ ràng.
7. Log toàn bộ params/metrics/artifacts vào MLflow.
8. Gửi report sau mỗi lần retrain.

Trong deadline hiện tại, nhóm **không cố implement full DAG**, mà chốt skeleton design để:

- Thầy thấy nhóm hiểu MLOps cần gì.
- Roadmap rõ ràng, không nói quá trạng thái hiện tại.
- Người khác có thể implement tiếp mà không phải thiết kế lại từ đầu.

---

## 2. Trạng Thái Hiện Tại

Đã có:

- Data pipeline: collector -> Kafka -> consumer -> TimescaleDB.
- Historical backfill 50 ngày.
- Feature engineering module.
- Model training script `backend/scripts/train_models.py`.
- Model artifacts cho Isolation Forest, LSTM, Prophet.
- Prediction interface trong `backend/models/predict.py`.
- FastAPI routes dùng inference với fallback.

Chưa có:

- `backend/airflow/dags/weekly_retrain.py`.
- DAG chạy thật trong Airflow.
- MLflow experiment tracking đầy đủ cho retrain cycle.
- Model registry promotion/hotswap tự động.
- Alert/report sau retrain.

Kết luận nên nói khi thuyết trình:

> MLOps hiện là roadmap/skeleton, chưa phải phần đã chạy production. Nhóm đã hoàn thiện pipeline dữ liệu, model artifacts và API inference; bước tiếp theo là tự động hóa retrain bằng Airflow và quản lý model bằng MLflow.

---

## 3. Vì Sao Cần MLOps?

Model môi trường dễ bị giảm chất lượng theo thời gian vì:

- Dữ liệu mùa nóng/mùa mưa khác nhau.
- Hành vi giao thông thay đổi theo ngày/giờ.
- Nguồn Open-Meteo có thể thay đổi độ phủ hoặc chất lượng.
- AQI distribution có thể drift.
- Model train trên 50 ngày đầu chưa chắc tốt cho các tháng sau.

Nếu không có MLOps:

- Model retrain thủ công.
- Khó biết model mới có thật sự tốt hơn không.
- Dễ overwrite artifact tốt bằng artifact kém.
- Không có audit trail cho model version.

Vì vậy Airflow + MLflow được dùng theo vai trò:

| Thành phần | Vai trò |
|---|---|
| Airflow | Orchestrate retrain workflow theo lịch |
| TimescaleDB | Source dữ liệu training/evaluation |
| Feature engineering | Đảm bảo train và inference dùng cùng logic |
| MLflow Tracking | Log params, metrics, artifacts |
| MLflow Registry | Quản lý model version và stage |
| FastAPI inference | Load production artifact để phục vụ app |

---

## 4. DAG Tổng Quan

Tên DAG đề xuất:

```text
weekly_retrain
```

Schedule đề xuất:

```text
Every Sunday 02:00 Asia/Ho_Chi_Minh
```

Lý do:

- Chủ Nhật 2 giờ sáng là thời điểm ít người dùng.
- Có đủ dữ liệu của tuần vừa rồi.
- Nếu retrain lỗi thì còn thời gian xử lý trước giờ cao điểm.

Luồng tổng quát:

```text
extract_training_data
  -> validate_training_data
  -> build_features
  -> train_isolation_forest
  -> train_lstm
  -> train_prophet
  -> evaluate_models
  -> compare_with_production
  -> register_or_keep_current
  -> write_retrain_report
```

Ghi chú:

- `train_isolation_forest`, `train_lstm`, `train_prophet` có thể chạy song song sau `build_features`.
- V1 có thể dùng `backend/scripts/train_models.py --model all` để giảm công.
- Full version nên tách rõ từng task để dễ debug và log metrics.

---

## 5. Input -> Process -> Output Của MLOps Pipeline

### 5.1 Input

Input chính:

- Bảng `env_readings` trong TimescaleDB.
- Model artifacts production hiện tại.
- Feature list trong `backend/config/constants.py`.
- Training configuration.

Dữ liệu cần query:

```sql
SELECT *
FROM env_readings
WHERE time >= NOW() - INTERVAL '60 days'
ORDER BY province_id, time;
```

Mặc định đề xuất:

- Training window: 60 ngày nếu có đủ dữ liệu.
- Minimum data threshold: ít nhất 30 ngày.
- Province coverage: ít nhất 80% tỉnh có dữ liệu đủ.

Nếu không đủ dữ liệu:

- DAG không retrain.
- Ghi report `SKIPPED_NOT_ENOUGH_DATA`.
- Giữ production model hiện tại.

### 5.2 Process

Các bước xử lý:

1. Extract dữ liệu từ TimescaleDB.
2. Kiểm tra completeness/missing values.
3. Tạo lag/rolling/time features.
4. Split theo thời gian, không split random.
5. Train model mới.
6. Evaluate trên holdout set.
7. So sánh với model production.
8. Nếu tốt hơn, register/promote.
9. Nếu không tốt hơn, giữ model cũ.

Reasoning:

> Với time-series, random split có thể leak tương lai vào training set. Vì vậy train/validation/test phải split theo thời gian.

### 5.3 Output

Output của pipeline:

- New model artifacts nếu retrain thành công.
- Metrics: MAE, RMSE, MAPE cho forecast; anomaly score distribution cho Isolation Forest.
- MLflow run.
- Decision report:
  - `PROMOTED`
  - `REJECTED_NO_IMPROVEMENT`
  - `SKIPPED_NOT_ENOUGH_DATA`
  - `FAILED`

---

## 6. Task Contract Chi Tiết

### Task 1 — `extract_training_data`

Input:

- DB connection settings.
- Training window days.

Process:

- Query `env_readings`.
- Sort by `province_id`, `time`.
- Export intermediate dataset path hoặc push XCom metadata.

Output:

```json
{
  "rows": 77099,
  "province_count": 63,
  "min_time": "...",
  "max_time": "...",
  "dataset_path": "/tmp/reis_retrain/raw.parquet"
}
```

Failure handling:

- Nếu DB lỗi: fail task.
- Nếu rows quá ít: raise controlled skip.

### Task 2 — `validate_training_data`

Input:

- Raw dataset.

Process:

- Check missing columns.
- Check duplicate `(province_id, time)`.
- Check province coverage.
- Check future rows.
- Check missing ratio.

Output:

```json
{
  "valid": true,
  "duplicate_rows": 0,
  "future_rows": 0,
  "coverage_ratio": 1.0,
  "missing_ratio": 0.03
}
```

Acceptance:

- `future_rows = 0`.
- `coverage_ratio >= 0.8`.
- Không có duplicate nghiêm trọng.

### Task 3 — `build_features`

Input:

- Raw dataset.
- Feature definitions.

Process:

- Tạo lag features.
- Tạo rolling features.
- Tạo time features.
- Drop hoặc impute rows không đủ lag.

Output:

```json
{
  "feature_rows": 72000,
  "feature_count": 32,
  "feature_path": "/tmp/reis_retrain/features.parquet"
}
```

Important rule:

- Train pipeline phải dùng cùng feature logic với inference pipeline để tránh training-serving skew.

### Task 4 — `train_isolation_forest`

Input:

- Feature dataset.

Process:

- Fit Isolation Forest.
- Save model + scaler.
- Log params vào MLflow.

Output:

- `isolation_forest.joblib`
- `anomaly_scaler.joblib`
- Metadata JSON.

Metrics đề xuất:

- Score distribution.
- Percent records above strict threshold.
- Top suspicious provinces.

### Task 5 — `train_lstm`

Input:

- Feature dataset theo sequence.

Process:

- Build windows.
- Split train/val/test theo thời gian.
- Train LSTM.
- Save Keras model + scalers.
- Log loss curve và metrics.

Output:

- `lstm_aqi.keras`
- `lstm_feature_scaler.joblib`
- `lstm_target_scaler.joblib`
- Metadata JSON.

Metrics:

- MAE.
- RMSE.
- MAPE.
- Validation loss.

### Task 6 — `train_prophet`

Input:

- Time-series AQI per province hoặc aggregate strategy.

Process:

- Convert timestamp timezone-aware -> timezone-naive nếu cần.
- Train Prophet model.
- Log metrics.

Output:

- `prophet_aqi.json`
- Metadata JSON.

Metrics:

- MAE.
- RMSE.
- MAPE.

### Task 7 — `evaluate_models`

Input:

- LSTM result.
- Prophet result.
- Isolation Forest summary.

Process:

- So sánh forecast models trên cùng holdout set.
- Chọn champion forecast model.
- Tổng hợp anomaly model report.

Output:

```json
{
  "champion_forecast": "lstm",
  "new_mae": 12.4,
  "new_rmse": 18.7,
  "new_mape": 0.13
}
```

### Task 8 — `compare_with_production`

Input:

- New champion metrics.
- Current production metrics từ MLflow hoặc metadata.

Process:

- So sánh improvement.
- Rule đề xuất:

```text
promote nếu new_mae <= production_mae * 0.95
```

Reasoning:

> Yêu cầu cải thiện ít nhất 5% giúp tránh promote model mới chỉ vì noise nhỏ.

Output:

```json
{
  "decision": "PROMOTE",
  "reason": "MAE improved by 7.2%"
}
```

### Task 9 — `register_or_keep_current`

Input:

- Decision từ compare task.
- New artifacts.

Process:

- Nếu promote:
  - Register artifact vào MLflow.
  - Transition model stage sang Staging/Production.
  - Optionally copy artifacts sang production artifacts dir.
- Nếu reject:
  - Không thay production artifact.
  - Log reason.

Output:

- Production model unchanged hoặc new version promoted.

### Task 10 — `write_retrain_report`

Input:

- Tất cả task metadata.

Process:

- Tạo Markdown/JSON report.
- Optionally gửi email/Slack/Telegram sau này.

Output:

```text
reports/retrain_YYYYMMDD.md
```

---

## 7. Pseudocode DAG

Đây là skeleton logic, không phải code final:

```python
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    dag_id="weekly_retrain",
    schedule="0 2 * * 0",
    start_date=datetime(2026, 5, 1, tz="Asia/Ho_Chi_Minh"),
    catchup=False,
    tags=["reis", "mlops", "retrain"],
)
def weekly_retrain():
    @task
    def extract_training_data():
        ...

    @task
    def validate_training_data(dataset_meta):
        ...

    @task
    def build_features(dataset_meta):
        ...

    @task
    def train_isolation_forest(feature_meta):
        ...

    @task
    def train_lstm(feature_meta):
        ...

    @task
    def train_prophet(feature_meta):
        ...

    @task
    def evaluate_models(lstm_meta, prophet_meta, anomaly_meta):
        ...

    @task
    def compare_with_production(eval_meta):
        ...

    @task
    def register_or_keep_current(decision_meta):
        ...

    @task(trigger_rule="all_done")
    def write_retrain_report(*metas):
        ...

    raw = extract_training_data()
    valid = validate_training_data(raw)
    features = build_features(valid)

    anomaly = train_isolation_forest(features)
    lstm = train_lstm(features)
    prophet = train_prophet(features)

    evaluation = evaluate_models(lstm, prophet, anomaly)
    decision = compare_with_production(evaluation)
    deployment = register_or_keep_current(decision)
    write_retrain_report(raw, valid, features, anomaly, lstm, prophet, evaluation, decision, deployment)

weekly_retrain()
```

---

## 8. V1 Skeleton Nếu Có Thời Gian Code Nhanh

Nếu gần deadline nhưng vẫn muốn có file DAG skeleton, chỉ nên implement tối thiểu:

```text
backend/airflow/dags/weekly_retrain.py
```

V1 code scope:

- DAG import được.
- Có 5 Python tasks dummy/logging:
  - `extract_training_data`
  - `build_features`
  - `train_models`
  - `evaluate_models`
  - `write_report`
- Mỗi task log rõ `TODO`.
- Không chạy training thật.
- Không mutate model artifacts.

Acceptance:

- Airflow parse DAG không lỗi.
- `airflow dags list` thấy `weekly_retrain`.
- Docs nói rõ đây là skeleton.

Không nên làm gần deadline:

- Hot-swap model thật.
- MLflow registry promotion thật.
- Email/Telegram thật.
- Full train LSTM trong Airflow container nếu chưa kiểm soát resource.

---

## 9. Acceptance Criteria Cho Stage 2E Skeleton

Skeleton docs được coi là hoàn thành khi có:

- Tài liệu này tồn tại.
- Có luồng DAG rõ ràng.
- Có Input -> Process -> Output.
- Có task contract cho từng bước.
- Có acceptance criteria nếu implement sau.
- Presentation script nói rõ MLOps là roadmap, chưa production.

Không được claim:

- Airflow retrain đã chạy production.
- MLflow registry đã tự promote model.
- Model tự hot-swap thành công.

---

## 10. Cách Nói Khi Thuyết Trình

Nói ngắn:

> Với MLOps, nhóm em đã thiết kế skeleton pipeline weekly retrain. Pipeline này sẽ lấy dữ liệu mới từ TimescaleDB, build features, train lại model, evaluate trên holdout set, log vào MLflow và chỉ promote model mới nếu tốt hơn ít nhất 5%. Do deadline, phần này hiện là roadmap/skeleton, chưa phải DAG production hoàn chỉnh.

Nếu thầy hỏi vì sao chưa làm full:

> Vì full MLOps có nhiều rủi ro: Airflow container, MLflow registry, artifact promotion, resource khi train LSTM và rollback model. Nhóm ưu tiên hoàn thiện pipeline dữ liệu, API, frontend và demo-ready trước; MLOps được thiết kế rõ để triển khai tiếp.

Nếu thầy hỏi vì sao vẫn đưa vào kiến trúc:

> Vì với hệ thống AI realtime, retraining và model governance là yêu cầu dài hạn. Dù chưa full implement, thiết kế này cho thấy hệ thống có đường phát triển từ demo-ready lên production-ready.

---

## 11. Task Handoff Cho Thành Viên DevOps/ML

Nếu giao cho một thành viên làm tiếp, giao như sau:

Task title:

```text
Implement Airflow weekly_retrain DAG skeleton
```

Scope:

- Tạo `backend/airflow/dags/weekly_retrain.py`.
- DAG parse được trong Airflow.
- Các tasks chỉ log và return metadata giả.
- Không train model thật.
- Không overwrite artifacts.

Test:

```bash
docker-compose up -d postgres-airflow airflow-webserver
docker-compose exec airflow-webserver airflow dags list | grep weekly_retrain
```

Deliverables:

- DAG skeleton file.
- Screenshot/log Airflow DAG list.
- Update `PROGRESS.md`.

---

## 12. Roadmap Sau Deadline

Sau khi nộp/thuyết trình, có thể nâng cấp theo thứ tự:

1. DAG skeleton parse được.
2. Extract training data thật từ TimescaleDB.
3. Build features thật và lưu parquet.
4. Train Prophet trước vì nhẹ hơn LSTM.
5. Log metrics vào MLflow.
6. Train LSTM trong controlled environment.
7. Compare champion/challenger.
8. Register model vào MLflow.
9. Add report notification.
10. Add model rollback strategy.

