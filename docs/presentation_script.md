# Kịch Bản Thuyết Trình REIS

> REIS - Realtime Environmental Intelligence System  
> Chủ đề thuyết trình: từ dữ liệu môi trường thô đến cảnh báo, dự báo và insight có thể hành động.

---

## 1. Cách Dùng File Này

File này không phải demo guide. Đây là kịch bản để bạn thuyết trình trước thầy theo hướng có chiều sâu:

- Có storytelling để bài nói không bị khô.
- Có reasoning cho từng kết luận kỹ thuật.
- Có luồng Input -> Process -> Output cho toàn hệ thống.
- Có phần trả lời khi thầy hỏi sâu.
- Có phiên bản nói 15 phút và phần mở rộng nếu thầy muốn hỏi kỹ.

Nếu thời gian đúng 15 phút, bạn ưu tiên các phần:

- Mở đầu vấn đề.
- Luồng end-to-end.
- Kiến trúc Input -> Process -> Output.
- 3 điểm kỹ thuật quan trọng: Kafka, TimescaleDB, AI inference.
- Hạn chế và hướng phát triển.

Nếu thầy hỏi sâu, bạn dùng phần Q&A và phần reasoning phía cuối.

---

## 2. One-Liner Mở Đầu

> REIS không chỉ trả lời câu hỏi "chất lượng không khí bây giờ là bao nhiêu", mà cố gắng trả lời câu hỏi quan trọng hơn: "sắp tới có rủi ro gì, vì sao xảy ra, và người dùng nên làm gì".

Đây là câu mở bài nên học thuộc. Nó định vị hệ thống ngay từ đầu:

- Không chỉ hiển thị AQI.
- Có dự báo.
- Có phát hiện bất thường.
- Có insight và khuyến nghị.
- Có pipeline realtime đứng phía sau.

---

## 3. Thông Điệp Trung Tâm Của Bài Thuyết Trình

Luận điểm chính:

> REIS là một hệ thống environmental intelligence end-to-end, biến dữ liệu môi trường thô thành một vòng lặp: quan sát -> lưu trữ -> phân tích -> dự báo -> giải thích -> hành động.

Tại sao luận điểm này quan trọng:

- Nếu chỉ có dashboard, hệ thống chỉ là nơi nhìn số liệu.
- Nếu chỉ có model, hệ thống chỉ là thí nghiệm ML.
- Nếu chỉ có API, hệ thống chưa giải quyết bài toán người dùng.
- REIS có giá trị vì nối đủ các lớp: data pipeline, storage, AI, API, frontend và fallback.

Bạn có thể nhấn mạnh:

> Điểm em muốn bảo vệ không phải là "một mô hình AI riêng lẻ", mà là cách nhóm em thiết kế một hệ thống dữ liệu realtime hoàn chỉnh, có khả năng chịu lỗi và có thể mở rộng.

---

## 4. Bài Toán Thực Tế

### 4.1 Vấn đề đời sống

Chất lượng không khí ảnh hưởng trực tiếp đến:

- Người có bệnh hô hấp.
- Trẻ em và người lớn tuổi.
- Người đi làm, đi học ngoài trời.
- Quyết định mở cửa, chạy máy lọc không khí, tập thể dục, di chuyển.

Nhưng người dùng thường gặp 3 vấn đề:

- Chỉ biết AQI hiện tại, không biết xu hướng sắp tới.
- Không biết một thay đổi là bình thường hay bất thường.
- Không biết nên hành động thế nào với con số AQI.

Lời thoại gợi ý:

> Khi người dùng thấy AQI là 150, câu hỏi tiếp theo không phải chỉ là "150 nghĩa là gì". Họ sẽ hỏi: "nó đang tăng hay giảm", "mấy giờ nữa có nguy hiểm hơn không", và "tôi nên làm gì". Đây là khoảng trống mà REIS muốn giải quyết.

### 4.2 Khoảng trống của các hệ thống hiện tại

Nhiều hệ thống hiện tại mạnh ở phần hiển thị số liệu, nhưng yếu ở phần intelligence:

| Nhu cầu | Hệ thống hiển thị AQI thông thường | REIS |
|---|---|---|
| Xem AQI hiện tại | Có | Có |
| Xem dữ liệu nhiều tỉnh | Có thể có | Có, 63 tỉnh |
| Realtime pipeline | Không phải trọng tâm | Có Kafka pipeline |
| Dự báo 12 giờ tới | Thường thiếu | Có forecast |
| Phát hiện bất thường | Thường thiếu | Có anomaly scoring |
| Giải thích bằng tiếng Việt | Thường thiếu | Có LLM/template insight |
| Fallback khi lỗi API/model | Không rõ | Có thiết kế fallback |

Kết luận:

> REIS không cạnh tranh bằng việc "có thêm một bản đồ AQI", mà bằng việc biến bản đồ AQI thành một hệ thống hỗ trợ quyết định.

---

## 5. Bức Tranh Tổng Quan: Input -> Process -> Output

### 5.1 Luồng tổng quát

```text
Input
  Open-Meteo weather + air-quality data
  63 tỉnh thành Việt Nam
  dữ liệu realtime + dữ liệu lịch sử backfill

Process
  Collector -> Validator -> Kafka Producer
  Kafka -> Consumer -> TimescaleDB
  Feature Engineering -> ML Inference
  Insight Generation -> API/WebSocket

Output
  Dashboard KPI
  Vietnam live map
  Forecast confidence band
  Analytics/Compare views
  Alerts
  Vietnamese insight
```

Lời thoại gợi ý:

> Nếu tóm tắt REIS bằng một dòng Input -> Process -> Output, thì input là dữ liệu môi trường thô, process là streaming pipeline kết hợp AI inference, và output là các màn hình giúp người dùng hiểu rủi ro môi trường.

### 5.2 Câu chuyện của một data point

Đây là cách rất hay để thuyết trình vì thầy dễ hình dung:

> Ta hãy theo dõi một data point của Hà Nội tại thời điểm hiện tại.

1. Open-Meteo trả về nhiệt độ, độ ẩm, gió, PM2.5, PM10, AQI.
2. Collector lấy record đó về.
3. Validator kiểm tra field và range.
4. Producer gửi record vào Kafka topic `env.readings.raw`.
5. Consumer đọc message từ Kafka.
6. Consumer ghi record vào TimescaleDB.
7. API lấy latest reading và 48h history của Hà Nội.
8. Model dùng history để dự báo và tính anomaly.
9. Insight engine sinh lời khuyên tiếng Việt.
10. Frontend hiển thị trên Dashboard, Map, Analytics hoặc Alerts.

Điểm cần nhấn:

> Một con số AQI trên dashboard không tự nhiên xuất hiện. Nó đi qua một chuỗi quyết định thiết kế: validate, stream, persist, infer, explain, deliver.

---

## 6. Kiến Trúc 5 Lớp Của REIS

```text
Layer 1: Data Ingestion
  Open-Meteo -> Collector -> Validator -> Producer

Layer 2: Streaming & Storage
  Kafka -> Consumer -> TimescaleDB
  Redis for cache/DLQ

Layer 3: AI Inference
  Feature engineering
  Isolation Forest
  LSTM / Prophet
  Gemini / OpenAI / template fallback

Layer 4: Delivery
  FastAPI REST
  WebSocket /ws/live
  React frontend

Layer 5: MLOps Roadmap
  Airflow retraining
  MLflow registry
  Monitoring and alerting
```

Lời thoại gợi ý:

> Em chia hệ thống thành 5 lớp để dễ kiểm soát trách nhiệm. Mỗi lớp có input, process và output rõ ràng. Khi lỗi xảy ra, mình cũng biết lỗi nằm ở thu thập, streaming, storage, model, API hay frontend.

Reasoning:

- Chia lớp giúp hệ thống dễ debug.
- Mỗi lớp có contract rõ.
- Có thể thay thế từng phần mà không phá toàn bộ hệ thống.
- Ví dụ sau này đổi nguồn data không nhất thiết đổi frontend.
- Ví dụ sau này thay model không nhất thiết đổi Kafka pipeline.

---

## 7. Layer 1 - Data Ingestion

### 7.1 Input

Nguồn dữ liệu chính:

- Open-Meteo Weather API.
- Open-Meteo Air Quality API.
- Open-Meteo Archive API cho dữ liệu lịch sử.

Các biến quan trọng:

| Nhóm | Field | Ý nghĩa |
|---|---|---|
| Thời tiết | `temperature` | Nhiệt độ |
| Thời tiết | `humidity` | Độ ẩm |
| Thời tiết | `wind_speed` | Gió, ảnh hưởng phân tán ô nhiễm |
| Thời tiết | `precipitation` | Mưa, có thể giảm bụi |
| Không khí | `pm2_5` | Bụi mịn, chỉ số rất quan trọng với sức khỏe |
| Không khí | `pm10` | Bụi thô |
| Không khí | `no2` | Khí từ giao thông, công nghiệp |
| Không khí | `ozone` | Ozone tầng thấp |
| Không khí | `uv_index` | Tia UV |
| Tổng hợp | `aqi` | US AQI |

### 7.2 Process

Luồng xử lý:

```text
Open-Meteo API
  -> collector.py batch fetch 63 tỉnh
  -> validator.py kiểm tra schema/range
  -> producer.py gửi Kafka
```

Tại sao batch 63 tỉnh:

- Nếu gọi từng tỉnh riêng lẻ, số request tăng rất nhanh.
- 63 tỉnh x 2 API x nhiều cycle mỗi ngày dễ chạm rate limit.
- Batch nhiều tọa độ trong một request giúp giảm số request.

Reasoning:

> Vì dữ liệu cần cập nhật định kỳ, tối ưu số request ngay từ đầu quan trọng hơn viết một collector đơn giản nhưng tốn quota.

### 7.3 Output

Output của layer này là `EnvironmentReading` đã validate, ví dụ về mặt logic:

```json
{
  "province_id": 1,
  "time": "2026-05-15T10:00:00+07:00",
  "temperature": 30.5,
  "humidity": 72,
  "wind_speed": 8.1,
  "precipitation": 0,
  "pm2_5": 45.2,
  "pm10": 68.0,
  "aqi": 120,
  "no2": 28.4,
  "ozone": 57.0,
  "uv_index": 6.0
}
```

Điểm cần nhấn:

> Dữ liệu sau layer 1 không còn là JSON thô tùy ý nữa. Nó đã trở thành một record có schema, có range hợp lệ và có thể đưa vào pipeline.

---

## 8. Layer 2 - Kafka Streaming Và TimescaleDB Storage

### 8.1 Input

Input là các `EnvironmentReading` đã validate.

### 8.2 Process

```text
Validated reading
  -> Kafka topic env.readings.raw
  -> Consumer poll messages
  -> Batch insert
  -> TimescaleDB env_readings
```

Consumer có các điểm đáng nói:

- Đọc Kafka message.
- Parse JSON.
- Convert timestamp ISO string thành datetime.
- Batch insert vào DB.
- Commit Kafka offset sau khi insert thành công.

Reasoning về manual commit:

> Nếu commit offset trước rồi DB insert fail, message có thể bị mất. Vì vậy consumer chỉ commit sau khi ghi DB thành công. Đây là tư duy at-least-once delivery.

Reasoning về `ON CONFLICT DO NOTHING`:

> Vì at-least-once có thể đọc lại message khi lỗi, DB cần chống duplicate. Unique key theo `(province_id, time)` và `ON CONFLICT DO NOTHING` giúp dữ liệu idempotent hơn.

### 8.3 Vì sao dùng Kafka?

Kết luận:

> Kafka không được dùng để làm hệ thống phức tạp cho vui. Kafka giải quyết bài toán tách producer và consumer trong pipeline realtime.

Reasoning:

- Collector không cần biết DB đang nhanh hay chậm.
- Có buffer nếu consumer tạm thời ngắt.
- Sau này có thể thêm consumer khác, ví dụ alert service hoặc monitoring service.
- Key theo `province_id` giúp giữ ordering theo tỉnh.

Nếu thầy hỏi "ghi thẳng DB được không":

> Ghi thẳng DB được ở bản nhỏ. Nhưng khi muốn realtime, chịu lỗi và mở rộng nhiều consumer, Kafka là lựa chọn hợp lý hơn.

### 8.4 Vì sao dùng TimescaleDB?

Kết luận:

> TimescaleDB phù hợp vì dữ liệu môi trường là time-series.

Reasoning:

- Mỗi record luôn có thời gian.
- Query phổ biến là latest reading, 48h history, 7 days, 30 days.
- Cần rolling/lag features.
- Hypertable giúp quản lý dữ liệu theo thời gian tốt hơn bảng PostgreSQL thường.

### 8.5 Output

Output là bảng `env_readings` có dữ liệu theo thời gian:

```text
time
province_id
temperature
humidity
wind_speed
precipitation
pm2_5
pm10
aqi
no2
ozone
uv_index
anomaly_score
is_anomaly
raw_json
inserted_at
```

Điểm cần nhấn:

> Từ đây, hệ thống đã có một source of truth cho cả API, ML và frontend.

---

## 9. Historical Backfill - Vì Sao Không Chỉ Dùng Realtime?

### 9.1 Input

Dữ liệu lịch sử từ Open-Meteo Archive API.

Trong project hiện tại:

- Backfill 50 ngày.
- 63 tỉnh.
- Hourly records.
- Ghi vào cùng bảng `env_readings`.

### 9.2 Process

```text
Archive API
  -> backfill_historical_data.py
  -> normalize timestamp UTC
  -> insert idempotent vào env_readings
```

### 9.3 Output

DB có dữ liệu đủ dày để:

- Vẽ chart 7 ngày/30 ngày.
- Tính lag features.
- Tính rolling statistics.
- Train và validate model.
- So sánh tỉnh theo thời gian.

Reasoning:

> Nếu chỉ có realtime từ lúc bật hệ thống, dữ liệu rất mỏng. Một dashboard có vài điểm dữ liệu không đủ thuyết phục, và model cũng thiếu lịch sử để học pattern.

Điểm cần nói:

> Backfill không thay thế realtime. Backfill tạo nền lịch sử, realtime cập nhật hiện tại.

---

## 10. Layer 3 - Feature Engineering

### 10.1 Input

Input là dữ liệu thô trong DB:

- AQI.
- PM2.5.
- PM10.
- NO2.
- Ozone.
- Temperature.
- Humidity.
- Wind speed.
- Timestamp.

### 10.2 Process

Feature engineering tạo thêm bối cảnh cho model:

| Feature group | Ví dụ | Reasoning |
|---|---|---|
| Raw features | `aqi`, `pm2_5`, `pm10` | Cho biết trạng thái hiện tại |
| Lag features | `pm2_5_lag_1h`, `aqi_lag_3h` | Cho biết xu hướng gần đây |
| Rolling features | `aqi_rolling_mean_6h`, `aqi_rolling_std_6h` | Cho biết baseline và biến động |
| Time features | hour, day of week | Ô nhiễm có pattern theo giờ/ngày |
| Delta features | `delta_aqi_1h` | Cho biết tốc độ thay đổi |

Reasoning:

> Model không chỉ cần biết AQI hiện tại là 150. Nó cần biết 150 này là đang tăng từ 80 lên, hay đang giảm từ 220 xuống. Hai trường hợp này có ý nghĩa rất khác nhau.

### 10.3 Output

Output là feature vector cho model:

```text
current reading + historical context -> feature matrix
```

Điểm cần nhấn:

> Feature engineering là cầu nối giữa dữ liệu thô và AI. Nếu feature yếu, model tốt cũng khó ra kết quả tốt.

---

## 11. Layer 3 - AI Inference

### 11.1 Tổng quan Input -> Process -> Output

```text
Input
  current reading
  recent history
  engineered features

Process
  Isolation Forest -> anomaly score
  LSTM / Prophet -> forecast
  Prompt Builder + LLM/template -> insight

Output
  anomaly payload
  forecast values/lower/upper
  Vietnamese insight
```

### 11.2 Anomaly Detection

Input:

- Feature vector của một tỉnh tại một thời điểm.
- Các chỉ số như PM2.5, PM10, AQI, NO2, ozone, temperature, wind speed.
- Có thể có thêm lag/rolling tùy model pipeline.

Process:

- Isolation Forest học pattern bình thường từ dữ liệu.
- Điểm dễ bị tách khỏi đám đông sẽ có anomaly score cao.

Output:

```json
{
  "score": 0.45,
  "label": "NORMAL",
  "strict_alert": false
}
```

Reasoning:

> Isolation Forest phù hợp vì bài toán anomaly thường thiếu label. Ta không có sẵn nhãn "bất thường" cho mọi thời điểm, nên dùng unsupervised learning là hợp lý.

Điểm rất quan trọng khi thuyết trình:

> AI anomaly không giống AQI warning.

Giải thích:

- `AQI warning`: rule theo ngưỡng sức khỏe, ví dụ AQI >= 150.
- `AI anomaly`: model thấy pattern bất thường so với dữ liệu/pattern.

Ví dụ:

- AQI 170 ở một đô thị thường xuyên ô nhiễm có thể là AQI warning nhưng chưa chắc là anomaly.
- AQI 95 nhưng tăng đột ngột từ 20 lên 95 trong thời gian ngắn có thể đáng chú ý về anomaly.

### 11.3 Forecast

Input:

- Lịch sử gần đây của tỉnh.
- Feature matrix theo thời gian.
- Mục tiêu dự báo thường là AQI.

Process:

- LSTM học chuỗi thời gian nhiều biến.
- Prophet đóng vai trò fallback hoặc baseline dễ giải thích hơn.

Output:

```json
{
  "values": [83, 86, 89, 92],
  "lower": [76, 78, 81, 84],
  "upper": [92, 96, 100, 105],
  "model_family": "lstm"
}
```

Reasoning:

> Forecast không nên chỉ trả một đường duy nhất. Lower và upper bound giúp frontend thể hiện mức bất định bằng confidence band.

Tại sao dùng LSTM:

- Chuỗi môi trường có pattern theo thời gian.
- AQI bị ảnh hưởng bởi nhiều biến: gió, độ ẩm, PM2.5, PM10.
- LSTM có thể học quan hệ phi tuyến và phụ thuộc thời gian.

Tại sao vẫn có Prophet:

- Prophet dễ làm baseline.
- Khi LSTM lỗi hoặc thiếu artifact, hệ thống vẫn có đường fallback.

### 11.4 Insight Generation

Input:

- Province metadata.
- Current reading.
- Anomaly result.
- Forecast result.

Process:

```text
current + anomaly + forecast
  -> prompt_builder.py
  -> Gemini/OpenAI if API key exists
  -> template fallback if provider missing/error
  -> Redis cache
```

Output:

Insight tiếng Việt dạng:

- Hiện trạng.
- Nguyên nhân có thể.
- Dự báo.
- Khuyến nghị.

Reasoning:

> Người dùng phổ thông không phải lúc nào cũng hiểu AQI, PM2.5 hay anomaly score. Insight biến số liệu kỹ thuật thành lời giải thích có thể hành động.

Vì sao cần fallback template:

- Không phải máy nào cũng có Gemini/OpenAI key.
- Provider có thể timeout.
- Demo không nên fail chỉ vì LLM không sẵn sàng.

Vì sao cần Redis cache:

- Insight không cần generate lại mỗi giây.
- LLM call chậm và có thể tốn chi phí.
- Cache theo tỉnh và AQI bucket giúp giữ insight ổn định trong một khoảng thời gian.

---

## 12. Layer 4 - API Và WebSocket

### 12.1 Input

API nhận request từ frontend:

- Dashboard cần summary và provinces.
- Province detail cần current, history, anomaly, forecast.
- Analytics cần history theo `hours`.
- Compare cần nhiều tỉnh.
- Alerts cần anomaly list.
- Insight card cần insight.

### 12.2 Process

FastAPI làm nhiệm vụ:

- Query TimescaleDB.
- Gọi inference cache.
- Gọi insight cache.
- Normalize response.
- Fallback nếu DB/model/LLM lỗi.

Các route quan trọng:

| Endpoint | Mục đích |
|---|---|
| `GET /api/health` | Health check nhẹ, không phụ thuộc DB |
| `GET /api/summary` | KPI toàn quốc |
| `GET /api/provinces` | 63 tỉnh + latest reading |
| `GET /api/province/{id}?hours=168` | Chi tiết một tỉnh |
| `GET /api/compare` | So sánh nhiều tỉnh |
| `GET /api/forecast/{id}` | Forecast |
| `GET /api/insights/{id}` | Insight |
| `GET /api/anomalies` | AQI warnings/anomaly records |
| `WS /ws/live` | Live updates cho frontend |

### 12.3 Output

Output là API contract ổn định cho frontend.

Ví dụ summary:

```json
{
  "aqi_avg": 104.0,
  "pm25_avg": 27.5,
  "aqi_warning_count": 12,
  "ai_anomaly_count": 0,
  "province_count": 63,
  "latest_time": "2026-05-14T13:00:00+00:00"
}
```

Reasoning:

> API không chỉ trả dữ liệu. API còn định nghĩa ngôn ngữ chung giữa backend và frontend. Ví dụ tách `aqi_warning_count` và `ai_anomaly_count` giúp UI không gây hiểu nhầm.

### 12.4 Vì sao cần WebSocket?

Kết luận:

> REST phù hợp lấy dữ liệu theo request. WebSocket phù hợp đẩy cập nhật live.

Reasoning:

- Dashboard muốn cảm giác realtime.
- Polling quá dày gây tốn request.
- WebSocket giúp frontend nhận payload mới khi server có cập nhật.

Ghi chú trung thực:

> WebSocket hiện là bản demo-friendly, có polling/broadcast đơn giản. Để production cần monitoring, backpressure và lifecycle management tốt hơn.

---

## 13. Layer 4 - Frontend Experience

### 13.1 Input

Frontend nhận:

- REST API payload.
- WebSocket live payload.
- Mock fallback nếu API down.

### 13.2 Process

Frontend xử lý:

- Normalize dữ liệu API.
- Hiển thị loading/error/fallback rõ ràng.
- Gắn source label: `LIVE API`, `LIVE WS/API`, `MOCK FALLBACK`.
- Vẽ chart/map/gauge/table.

### 13.3 Output theo page

| Page | Output | Ý nghĩa |
|---|---|---|
| Landing | Câu chuyện và live summary | Giới thiệu hệ thống |
| Dashboard | KPI, map, gauge, forecast, insight | Command center |
| Analytics | Filter theo tỉnh/range/metric | Phân tích xu hướng |
| Compare | So sánh nhiều tỉnh | Phân tích tương quan vùng |
| Map | Bản đồ live toàn quốc | Trực quan không gian |
| Alerts | AQI Health Alerts và AI events | Tập trung vào rủi ro |

Reasoning:

> Frontend không chỉ là lớp trang trí. Nó là nơi biến hệ thống kỹ thuật thành trải nghiệm mà người dùng hiểu được.

Điểm nên nói:

- Dashboard trả lời "toàn quốc đang thế nào".
- Analytics trả lời "một tỉnh thay đổi ra sao theo thời gian".
- Compare trả lời "tỉnh này khác tỉnh kia thế nào".
- Map trả lời "rủi ro phân bố ở đâu".
- Alerts trả lời "cần chú ý sự kiện nào".

---

## 14. Engineering Quality Và Fault Tolerance

### 14.1 Kết luận

> Hệ thống tốt không chỉ chạy được khi mọi thứ ổn, mà còn phải không sập vô nghĩa khi một thành phần lỗi.

### 14.2 Các thiết kế chịu lỗi

| Rủi ro | Thiết kế xử lý |
|---|---|
| DB chưa sẵn sàng | API fallback, health check không phụ thuộc DB |
| LLM thiếu API key | Template insight fallback |
| Model artifact lỗi | Default forecast/anomaly fallback |
| Frontend không gọi được API | Mock fallback có nhãn rõ |
| Kafka publish lỗi | Redis DLQ best-effort |
| Inference bị gọi lặp | Inference cache TTL |

Reasoning:

> Trong demo và cả production, lỗi không thể tránh hoàn toàn. Điều quan trọng là lỗi phải được cô lập, quan sát được và không làm toàn bộ trải nghiệm sập.

### 14.3 Testing

Các nhóm test hiện có:

- Validator tests.
- Producer tests.
- Scheduler tests.
- Consumer tests.
- Collector tests.
- Integration tests.
- ML model tests.
- Prompt/LLM/cache tests.
- API route tests.
- Frontend lint/build.

Điểm cần nói:

> Test ở nhiều lớp cho thấy nhóm không chỉ test UI cuối cùng, mà test các contract quan trọng trong pipeline.

---

## 15. Script Thuyết Trình 15 Phút Có Đào Sâu

### 0:00 - 1:00 | Hook

Lời thoại:

> Thưa thầy, nếu một ứng dụng nói với em rằng AQI hiện tại là 150, thông tin đó có ích nhưng chưa đủ. Vì câu hỏi thật sự của người dùng là: vài giờ tới có xấu hơn không, đây có phải biến động bất thường không, và tôi nên làm gì ngay bây giờ.
>
> Vì vậy nhóm em xây dựng REIS, một hệ thống realtime environmental intelligence. Hệ thống này không chỉ hiển thị dữ liệu, mà cố gắng tạo ra một vòng lặp: quan sát, dự báo, giải thích và hành động.

Reasoning cần nắm:

- Bắt đầu từ problem, không bắt đầu từ tech stack.
- Người nghe hiểu ngay hệ thống giải quyết nhu cầu gì.

### 1:00 - 2:30 | REIS Là Gì?

Lời thoại:

> REIS thu thập dữ liệu môi trường cho 63 tỉnh thành Việt Nam. Dữ liệu đi qua pipeline realtime, được lưu vào TimescaleDB, sau đó được AI phân tích để tạo forecast, anomaly score và insight tiếng Việt.
>
> Nếu xem theo Input -> Process -> Output, input là dữ liệu weather và air quality từ Open-Meteo. Process là Kafka pipeline, time-series storage, feature engineering và AI inference. Output là dashboard, bản đồ, biểu đồ, cảnh báo và lời khuyên.

Reasoning cần nắm:

- Nói rõ hệ thống end-to-end.
- Không để thầy hiểu nhầm đây chỉ là frontend.

### 2:30 - 5:00 | Data Pipeline

Lời thoại:

> Lớp đầu tiên là data ingestion. Collector gọi Open-Meteo theo chu kỳ 15 phút. Điểm quan trọng là nhóm fetch theo batch cho 63 tỉnh thay vì gọi từng tỉnh riêng lẻ, để giảm request và tránh rate limit.
>
> Sau khi lấy dữ liệu, validator kiểm tra schema và range. Ví dụ AQI phải nằm trong 0 đến 500, độ ẩm 0 đến 100, PM2.5 không âm. Điều này giúp chặn dữ liệu bất thường ngay từ đầu pipeline.
>
> Record hợp lệ được producer gửi vào Kafka topic `env.readings.raw`. Consumer đọc Kafka, batch insert vào TimescaleDB và chỉ commit offset sau khi ghi DB thành công.

Reasoning cần nắm:

- Batch fetch vì rate limit.
- Validator vì data quality.
- Kafka vì decoupling.
- Manual commit vì không muốn mất data.
- TimescaleDB vì time-series.

### 5:00 - 7:00 | Storage Và Historical Backfill

Lời thoại:

> TimescaleDB là source of truth cho hệ thống. Tất cả latest reading, history 48 giờ, history 7 ngày và compare đều xuất phát từ bảng `env_readings`.
>
> Ngoài dữ liệu realtime, nhóm backfill 50 ngày dữ liệu lịch sử. Lý do là nếu chỉ bật realtime từ hôm nay, chart sẽ rất mỏng và model không có đủ lịch sử để học pattern. Backfill tạo nền dữ liệu, còn realtime giữ hệ thống cập nhật.

Reasoning cần nắm:

- Realtime và historical data bổ sung cho nhau.
- Model cần context lịch sử.
- Dashboard cần history để có ý nghĩa.

### 7:00 - 10:30 | AI Layer

Lời thoại:

> AI layer gồm ba phần. Phần thứ nhất là anomaly detection bằng Isolation Forest. Vì dữ liệu môi trường thường không có label rõ ràng cho "bất thường", nên unsupervised learning là lựa chọn hợp lý.
>
> Phần thứ hai là forecast. LSTM dùng chuỗi lịch sử và nhiều biến môi trường để dự báo AQI tương lai. Prophet đóng vai trò fallback hoặc baseline. Output forecast gồm values, lower và upper để frontend vẽ vùng bất định.
>
> Phần thứ ba là insight generation. Hệ thống gom current reading, anomaly result và forecast vào prompt tiếng Việt. Nếu có Gemini hoặc OpenAI key thì gọi LLM. Nếu không có, hệ thống dùng template fallback để API vẫn hoạt động.
>
> Một điểm em muốn nhấn mạnh là `AQI warning` và `AI anomaly` không giống nhau. AQI warning là rule theo ngưỡng sức khỏe, ví dụ AQI >= 150. AI anomaly là model phát hiện pattern bất thường. Vì vậy UI tách hai chỉ số này để tránh hiểu nhầm.

Reasoning cần nắm:

- Isolation Forest vì thiếu label.
- LSTM vì chuỗi thời gian nhiều biến.
- Prophet vì fallback/baseline.
- LLM vì giải thích số liệu cho người dùng.
- Tách warning và anomaly vì semantics khác nhau.

### 10:30 - 12:30 | API Và Frontend

Lời thoại:

> FastAPI là lớp delivery. Nó cung cấp các route như `/api/summary`, `/api/provinces`, `/api/province/{id}`, `/api/compare`, `/api/anomalies` và `/api/insights/{id}`. WebSocket `/ws/live` giúp dashboard nhận cập nhật gần realtime.
>
> Frontend được chia theo use case. Dashboard là command center toàn quốc. Analytics dùng để xem xu hướng một tỉnh theo thời gian. Compare dùng để so sánh nhiều tỉnh. Map cho góc nhìn địa lý. Alerts tập trung vào các sự kiện cần chú ý.
>
> Frontend cũng luôn hiển thị source label như LIVE API hoặc MOCK FALLBACK. Đây là chi tiết nhỏ nhưng quan trọng, vì nó giúp người xem biết dữ liệu đang đến từ backend thật hay fallback.

Reasoning cần nắm:

- API là contract giữa backend và UI.
- Mỗi page trả lời một câu hỏi khác nhau.
- Source label giúp demo trung thực.

### 12:30 - 14:00 | Engineering Quality

Lời thoại:

> Nhóm cũng chú ý đến khả năng chịu lỗi. Health check không phụ thuộc DB. Nếu DB, model, Redis hoặc LLM lỗi, API cố gắng trả fallback có kiểm soát thay vì crash. Inference cache TTL giúp tránh gọi model lặp lại khi Dashboard, Insight và WebSocket cùng refresh.
>
> Về kiểm thử, project có test cho validator, producer, scheduler, consumer, collector, models, prompt, LLM client, insight cache và API routes. Frontend đã pass lint và build.

Reasoning cần nắm:

- Fallback không phải che lỗi, mà là graceful degradation.
- Cache vừa cải thiện performance, vừa giảm log nhiễu.
- Test nhiều lớp giúp bảo vệ contract.

### 14:00 - 15:00 | Hạn Chế Và Kết Luận

Lời thoại:

> Hiện hệ thống ở mức demo-ready end-to-end, chưa phải production-ready. Các phần tiếp theo là Airflow/MLOps để retrain model, alert manager qua Telegram/email, simulator tool để inject spike phục vụ demo, và tuning model khi dữ liệu nhiều hơn.
>
> Tóm lại, REIS không chỉ là một dashboard AQI. Nó là một pipeline hoàn chỉnh biến dữ liệu môi trường thô thành quan sát, dự báo, giải thích và hành động.

Reasoning cần nắm:

- Trung thực về hạn chế tạo cảm giác chuyên nghiệp.
- Chốt lại bằng vòng lặp giá trị.

---

## 16. Deep Dive: Input -> Process -> Output Theo Từng Module

| Module | Input | Process | Output |
|---|---|---|---|
| Collector | Tọa độ 63 tỉnh, Open-Meteo API | Batch request weather + air quality | Raw records |
| Validator | Raw record | Pydantic schema/range validation | `EnvironmentReading` hoặc reject |
| Producer | Validated reading | JSON serialize, key by province_id | Kafka message |
| Kafka | Messages | Buffer, partition, preserve ordering per key | Stream cho consumer |
| Consumer | Kafka messages | Parse, batch, insert, commit offset | Rows trong `env_readings` |
| Backfill | Archive hourly data | Normalize UTC, idempotent insert | Historical rows |
| Feature engineer | DB history | Lag, rolling, delta, time features | Feature matrix |
| Anomaly model | Feature vector | Isolation Forest scoring | `score`, `label`, `strict_alert` |
| Forecast model | Historical sequence | LSTM or Prophet | `values`, `lower`, `upper` |
| Insight engine | Current + anomaly + forecast | Prompt + LLM/cache/template | Vietnamese insight |
| FastAPI | Frontend request | Query DB + inference/cache | JSON response |
| WebSocket | Latest summaries | Periodic broadcast | Live payload |
| Frontend | API/WS payload | Normalize, visualize, fallback | Dashboard/pages |

---

## 17. Các Kết Luận Quan Trọng Và Reasoning Đi Kèm

### Kết luận 1: REIS cần Kafka

Reasoning:

- Collector và DB không nên phụ thuộc trực tiếp.
- Kafka làm buffer khi consumer hoặc DB chậm.
- Có thể mở rộng nhiều consumer sau này.
- Manual commit giúp giảm nguy cơ mất message.

Nói ngắn:

> Kafka giúp hệ thống đi từ batch script sang realtime pipeline có khả năng mở rộng.

### Kết luận 2: REIS cần dữ liệu lịch sử

Reasoning:

- Chart cần lịch sử để có ý nghĩa.
- Forecast cần sequence.
- Anomaly cần baseline.
- Feature engineering cần lag/rolling.

Nói ngắn:

> Realtime cho ta hiện tại, historical data cho ta ngữ cảnh.

### Kết luận 3: AQI warning không phải AI anomaly

Reasoning:

- AQI warning là threshold rule.
- AI anomaly là pattern detection.
- Một event có thể thuộc một trong hai hoặc cả hai.

Nói ngắn:

> AQI warning trả lời "có nguy hiểm theo ngưỡng không", AI anomaly trả lời "có bất thường so với pattern không".

### Kết luận 4: Insight cần fallback

Reasoning:

- LLM provider có thể thiếu key.
- LLM có thể timeout.
- Demo không nên chết vì external provider.
- Template fallback vẫn cung cấp giá trị cơ bản.

Nói ngắn:

> LLM là enhancement, không phải single point of failure.

### Kết luận 5: Frontend cần source label

Reasoning:

- Khi API down, fallback giúp UI không crash.
- Nhưng nếu không gắn nhãn, người xem có thể hiểu nhầm mock là dữ liệu thật.

Nói ngắn:

> Fallback tốt phải đi kèm minh bạch.

---

## 18. Nếu Thầy Hỏi Sâu

### Vì sao không chỉ dùng cron job ghi thẳng DB?

Cron ghi thẳng DB phù hợp bản đơn giản. Nhưng REIS muốn mô phỏng realtime system. Kafka giúp tách ingestion khỏi storage, tránh mất dữ liệu khi DB chậm, và mở đường cho nhiều consumer như alert service, monitoring hoặc model updater.

### Nếu Kafka down thì sao?

Producer có DLQ best-effort qua Redis khi publish lỗi. Ở production cần thêm retry policy, monitoring và alerting. Hiện mức xử lý này phù hợp demo-ready, chưa phải production guarantee đầy đủ.

### Nếu TimescaleDB bị mất kết nối thì sao?

API có fallback để không crash. Consumer nếu insert thất bại sẽ không commit offset, nên message có thể được đọc lại sau. Tuy nhiên production cần observability tốt hơn để phát hiện DB outage.

### Vì sao không dùng InfluxDB?

TimescaleDB dựa trên PostgreSQL nên thuận lợi với SQL, relational metadata, joins và ecosystem quen thuộc. Với dự án này, cần vừa time-series vừa metadata tỉnh, nên TimescaleDB là lựa chọn cân bằng.

### Tại sao dùng 50 ngày backfill, không phải 7 ngày?

7 ngày đủ để vẽ chart ngắn hạn nhưng yếu cho model và seasonality. 50 ngày tạo nhiều pattern hơn cho EDA, lag, rolling, forecast và anomaly baseline. Vẫn chưa phải hoàn hảo, nhưng đủ tốt cho demo và thí nghiệm.

### Dữ liệu Air Quality cập nhật 1 giờ mà scheduler 15 phút thì có vấn đề không?

Không phải lỗi. Weather có thể cập nhật 15 phút, air quality thường hourly. Trong một giờ có thể có 4 record AQ giống nhau nhưng weather khác nhau. Khi phân tích cần hiểu đặc tính nguồn dữ liệu này.

### Model có chính xác không?

Nên trả lời cẩn trọng:

> Mục tiêu hiện tại là demo một pipeline AI end-to-end có fallback và khả năng mở rộng. Model đã có baseline và artifact, nhưng để production cần đánh giá thêm trên dữ liệu dài hơn, drift monitoring và retraining định kỳ.

### Tại sao LSTM và Prophet cùng tồn tại?

LSTM phù hợp multivariate nonlinear forecasting nhưng nặng hơn và khó giải thích hơn. Prophet đơn giản hơn, dễ làm fallback/baseline. Dùng cả hai giúp hệ thống không phụ thuộc vào một model duy nhất.

### Nếu LLM trả lời sai thì sao?

Insight chỉ là lớp giải thích hỗ trợ, không phải nguồn quyết định duy nhất. Prompt giới hạn ngữ cảnh từ current/anomaly/forecast, đồng thời có template fallback. Production cần thêm guardrails và evaluation.

### Tại sao frontend có mock fallback?

Để UI không crash khi API tắt hoặc mạng lỗi. Nhưng mock fallback được gắn nhãn rõ để không gây hiểu nhầm. Đây là graceful degradation, không phải giả dữ liệu thật.

### Hệ thống hiện thiếu gì để production-ready?

Thiếu MLOps hoàn chỉnh, monitoring, auth, alert manager thật, simulator, observability, model validation dài hạn và deployment hardening.

---

## 19. Checklist Trước Khi Thuyết Trình

### 3 con số cần nhớ

- 63 tỉnh thành Việt Nam.
- Chu kỳ realtime mục tiêu: 15 phút.
- Backfill lịch sử: 50 ngày.

### 3 giá trị chính

- Realtime pipeline.
- Forecast và anomaly.
- Insight tiếng Việt có fallback.

### 3 quyết định kỹ thuật quan trọng

- Kafka để decouple ingestion và storage.
- TimescaleDB cho time-series.
- Redis cho cache/DLQ.

### 3 điều cần nói trung thực

- Demo-ready, chưa production-ready.
- MLOps/Airflow đang là hướng phát triển.
- Alert manager và simulator là task tiếp theo.

### 3 câu tránh nói quá

- Không nói model chính xác tuyệt đối.
- Không nói LLM luôn gọi thật.
- Không nói hệ thống đã production-grade.

---

## 20. Dàn Ý Slide Deck Đề Xuất

1. Title: REIS - Realtime Environmental Intelligence System.
2. Problem: AQI hiện tại là chưa đủ.
3. Vision: Observe -> Predict -> Explain -> Act.
4. End-to-end flow: Input -> Process -> Output.
5. Data ingestion: Open-Meteo, batch 63 provinces, validator.
6. Streaming/storage: Kafka, consumer, TimescaleDB, Redis.
7. Historical data: 50-day backfill.
8. Feature engineering: raw, lag, rolling, time features.
9. AI inference: Isolation Forest, LSTM/Prophet, insight.
10. API layer: REST contracts and WebSocket.
11. Frontend: Dashboard, Analytics, Compare, Map, Alerts.
12. Engineering quality: fallback, cache, tests.
13. Current limitations.
14. Roadmap.
15. Closing: from raw data to environmental decisions.

---

## 21. Phiên Bản 60 Giây

> REIS là hệ thống giám sát môi trường realtime cho 63 tỉnh thành Việt Nam. Điểm khác biệt là hệ thống không chỉ hiển thị AQI hiện tại, mà còn dự báo xu hướng, phát hiện pattern bất thường và sinh insight tiếng Việt.
>
> Input của hệ thống là dữ liệu weather và air quality từ Open-Meteo. Process gồm collector, validator, Kafka producer, Kafka consumer, TimescaleDB, feature engineering, ML inference và LLM insight. Output là dashboard, bản đồ, forecast, analytics, compare và alerts.
>
> Về kỹ thuật, Kafka giúp tách ingestion khỏi database, TimescaleDB phù hợp dữ liệu time-series, Redis hỗ trợ cache và DLQ, FastAPI/WebSocket đưa dữ liệu ra frontend. Hiện hệ thống demo-ready end-to-end, còn roadmap gồm MLOps, alert manager, simulator và model tuning.

---

## 22. Câu Kết Nên Dùng

> Điểm quan trọng nhất của REIS là hệ thống không dừng lại ở việc báo một con số AQI. Nó cố gắng biến dữ liệu môi trường thành một chuỗi quyết định: quan sát được hiện tại, dự báo được tương lai gần, giải thích được rủi ro và gợi ý được hành động.

