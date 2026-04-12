# Data Sources

Tài liệu này mô tả tất cả nguồn dữ liệu của REIS: endpoints, variables, rate limits, và ý nghĩa thực tế của từng chỉ số môi trường.

---

## Tổng quan

REIS sử dụng **duy nhất** Open-Meteo làm nguồn dữ liệu — miễn phí, không cần API key, độ phủ toàn cầu. Hai loại data được fetch song song mỗi 15 phút:

| API | Endpoint Base | Loại data | Interval |
|-----|--------------|-----------|----------|
| Open-Meteo Weather | `api.open-meteo.com/v1/forecast` | Thời tiết | 15 phút |
| Open-Meteo Air Quality | `air-quality-api.open-meteo.com/v1/air-quality` | Chất lượng không khí | 1 giờ |
| Open-Meteo Archive | `archive-api.open-meteo.com/v1/archive` | Lịch sử (one-time) | Hourly |

---

## Weather API

### Endpoint

```
GET https://api.open-meteo.com/v1/forecast
```

### Parameters

| Parameter | Value trong REIS | Mô tả |
|-----------|-----------------|-------|
| `latitude` | `10.7769,21.0285,...` (63 values) | Vĩ độ, cách nhau dấu phẩy |
| `longitude` | `106.7009,105.8542,...` (63 values) | Kinh độ, cách nhau dấu phẩy |
| `current` | Xem biến bên dưới | Lấy dữ liệu hiện tại |
| `timezone` | `Asia/Ho_Chi_Minh` | Timezone cho timestamp |
| `forecast_days` | `1` | Chỉ lấy ngày hiện tại |

### Variables được fetch

| Variable | Unit | Range | Ý nghĩa |
|----------|------|-------|---------|
| `temperature_2m` | °C | -20 → 60 | Nhiệt độ không khí ở độ cao 2m so với mặt đất |
| `relative_humidity_2m` | % | 0 → 100 | Độ ẩm tương đối. > 80% = oi bức, dễ tích bụi |
| `wind_speed_10m` | km/h | 0 → 200 | Tốc độ gió ở 10m. Gió mạnh phân tán ô nhiễm |
| `precipitation` | mm | 0 → 500 | Lượng mưa. Mưa rửa PM2.5 khỏi không khí |

### Response format (single province)

```json
{
  "latitude": 10.75,
  "longitude": 106.6667,
  "timezone": "Asia/Ho_Chi_Minh",
  "current_units": {
    "temperature_2m": "°C",
    "wind_speed_10m": "km/h"
  },
  "current": {
    "time": "2024-01-15T08:00",
    "interval": 900,
    "temperature_2m": 32.4,
    "relative_humidity_2m": 75,
    "wind_speed_10m": 8.2,
    "precipitation": 0.0
  }
}
```

> **Lưu ý:** `interval: 900` = dữ liệu này đại diện cho khoảng 15 phút (900 giây). Khi batch 63 tỉnh, response là **array** thay vì object đơn.

---

## Air Quality API

### Endpoint

```
GET https://air-quality-api.open-meteo.com/v1/air-quality
```

### Variables được fetch

| Variable | Unit | Range hợp lệ | Ý nghĩa thực tế |
|----------|------|-------------|-----------------|
| `pm2_5` | µg/m³ | 0 → 1000 | Bụi mịn < 2.5 micromet. Xâm nhập sâu vào phổi, gây ung thư phổi. Chỉ số quan trọng nhất |
| `pm10` | µg/m³ | 0 → 1000 | Bụi < 10 micromet. Gây kích ứng mũi họng, hen suyễn |
| `nitrogen_dioxide` | µg/m³ | 0 → 500 | NO₂ từ xe cộ và nhà máy. WHO limit: 25 µg/m³/ngày |
| `ozone` | µg/m³ | 0 → 400 | O₃ tầng thấp. Kích ứng phổi, nguy hiểm với trẻ em và người già |
| `carbon_monoxide` | µg/m³ | 0 → 10000 | CO từ đốt nhiên liệu. Ngăn hemoglobin gắn O₂ |
| `uv_index` | — | 0 → 20 | Tia UV. > 11 = cực kỳ nguy hiểm |
| `us_aqi` | USAQI | 0 → 500 | Chỉ số tổng hợp US EPA, tính từ PM2.5 + PM10 + O₃ + NO₂ |

### Response format

```json
{
  "current": {
    "time": "2024-01-15T08:00",
    "interval": 3600,
    "pm2_5": 45.2,
    "pm10": 68.0,
    "nitrogen_dioxide": 28.4,
    "ozone": 57.0,
    "carbon_monoxide": 449.0,
    "uv_index": 0.0,
    "us_aqi": 120
  }
}
```

> **Lưu ý:** `interval: 3600` = dữ liệu AQ cập nhật mỗi **1 giờ**, không phải 15 phút. Trong vòng 1 giờ, cùng một giá trị AQ được ghi 4 lần vào DB (không sao — là expected behavior).

---

## Archive API — Lịch sử 90 ngày

Dùng **một lần duy nhất** khi setup project để seed dữ liệu huấn luyện ML.

### Endpoint

```
GET https://archive-api.open-meteo.com/v1/archive
```

### Parameters bổ sung

| Parameter | Value | Mô tả |
|-----------|-------|-------|
| `start_date` | `2024-10-01` | YYYY-MM-DD, ngày bắt đầu |
| `end_date` | `2025-01-01` | YYYY-MM-DD, ngày kết thúc |
| `hourly` | Các biến cần lấy | Trả về array theo giờ thay vì `current` |

### Chạy script

```bash
# Fetch 90 ngày lịch sử cho cả 63 tỉnh
python backend/scripts/fetch_historical.py \
  --days 90 \
  --output data/historical/
```

### Output ước tính

```
90 ngày × 24 giờ × 63 tỉnh = 136,080 rows
File size: ~45 MB (CSV) / ~12 MB (Parquet)
Thời gian fetch: ~8-12 phút (rate limiting friendly)
```

---

## AQI Scale — US EPA Standard

REIS sử dụng thang **US AQI** (United States Air Quality Index), không phải VN-AQI:

| AQI Range | Category | Màu | Ý nghĩa |
|-----------|----------|-----|---------|
| 0 – 50 | Good | 🟢 Xanh lá | Chất lượng không khí tốt |
| 51 – 100 | Moderate | 🟡 Vàng | Chấp nhận được, nhạy cảm nên cẩn thận |
| 101 – 150 | Unhealthy for Sensitive Groups | 🟠 Cam | Nhóm nhạy cảm bị ảnh hưởng |
| 151 – 200 | Unhealthy | 🔴 Đỏ | Mọi người bắt đầu bị ảnh hưởng |
| 201 – 300 | Very Unhealthy | 🟣 Tím | Cảnh báo sức khỏe nghiêm trọng |
| 301 – 500 | Hazardous | 🟤 Nâu | Khẩn cấp — toàn bộ dân số bị ảnh hưởng |

### PM2.5 → AQI mapping (simplified)

```
PM2.5 (µg/m³)    AQI       Category
0 – 12.0      →  0–50      Good
12.1 – 35.4   →  51–100    Moderate
35.5 – 55.4   →  101–150   Unhealthy for Sensitive
55.5 – 150.4  →  151–200   Unhealthy
150.5 – 250.4 →  201–300   Very Unhealthy
250.5+        →  301–500   Hazardous
```

> US AQI tính theo công thức linear interpolation. Open-Meteo đã tính sẵn `us_aqi` — REIS dùng trực tiếp, không cần tính lại.

---

## Rate Limits & Best Practices

### Rate limits Open-Meteo (free tier)

| Limit | Value | Ảnh hưởng |
|-------|-------|-----------|
| Requests per day | 10,000 | 63 tỉnh × 2 APIs × 96 cycles/day = 12,096 → **gần limit!** |
| Requests per minute | 600 | Không vấn đề với REIS |
| Concurrent connections | 10 | Không vấn đề |

**Chiến lược tránh rate limit:**

```python
# ✅ Batch 63 tỉnh vào 1 request = 2 requests/cycle × 96 cycles = 192 req/day
params = {
    "latitude":  ",".join([str(p["lat"]) for p in PROVINCES]),
    "longitude": ",".join([str(p["lon"]) for p in PROVINCES]),
}

# ❌ 63 requests riêng lẻ = 126 req/cycle × 96 cycles = 12,096 req/day
for province in PROVINCES:
    r = requests.get(url, params={"latitude": province["lat"]})
```

### Retry strategy

```python
# Exponential backoff: 1s → 2s → 4s → give up
for attempt in range(3):
    try:
        response = await session.get(url, timeout=30)
        if response.status == 429:       # Rate limited
            await asyncio.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        return await response.json()
    except asyncio.TimeoutError:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)
```

---

## Data Quality Notes

### Fields có thể là `null`

| Field | Khi nào null | Xử lý trong REIS |
|-------|-------------|-----------------|
| `pm2_5` | Tỉnh không có trạm đo AQ | Optional field, Isolation Forest bỏ qua |
| `uv_index` | Ban đêm (UV = 0, không null) | Luôn có giá trị |
| `us_aqi` | Thiếu đủ data thành phần | Optional, fallback tính từ PM2.5 |
| `ozone` | Một số tỉnh miền núi | Optional |

### Timestamp alignment

Weather API cập nhật mỗi **15 phút** (`interval: 900`).  
Air Quality API cập nhật mỗi **1 giờ** (`interval: 3600`).

```
08:00  Weather: temp=32.4, wind=8.2    AQ: pm2_5=45.2, aqi=120  ← mới nhất
08:15  Weather: temp=32.8, wind=7.9    AQ: pm2_5=45.2, aqi=120  ← AQ lặp lại
08:30  Weather: temp=33.1, wind=7.5    AQ: pm2_5=45.2, aqi=120  ← AQ lặp lại
08:45  Weather: temp=33.0, wind=8.0    AQ: pm2_5=45.2, aqi=120  ← AQ lặp lại
09:00  Weather: temp=32.5, wind=8.5    AQ: pm2_5=47.8, aqi=125  ← AQ cập nhật
```

Đây là behavior bình thường — không cần xử lý đặc biệt, TimescaleDB lưu tất cả.

---

## Liên quan

- `backend/config/constants.py` — `PROVINCES_COORDS`: danh sách 63 tỉnh với lat/lon
- `backend/ingestion/collector.py` — Implementation của batch fetch
- `backend/ingestion/validator.py` — Validation rules cho từng field
- `backend/scripts/fetch_historical.py` — Script fetch lịch sử 90 ngày
- `notebooks/01_api_exploration.ipynb` — Khám phá API interactively
- `notebooks/02_historical_fetch.ipynb` — Fetch và kiểm tra historical data
