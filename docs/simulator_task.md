# Task Spec — `tools/simulator.py`

> Status: Ready for implementation.  
> Owner gợi ý: Backend/Data member.  
> Goal: tạo spike AQI/PM2.5 giả qua Kafka để demo pipeline realtime phản ứng end-to-end.

---

## 1. Mục Tiêu

Tạo CLI tool:

```text
tools/simulator.py
```

Tool này dùng để inject một record ô nhiễm giả cho một tỉnh, đi qua pipeline thật:

```text
simulator.py
  -> Kafka topic env.readings.raw
  -> processing/consumer.py
  -> TimescaleDB env_readings
  -> FastAPI routes
  -> WebSocket/frontend
```

Mục tiêu demo:

- Tạo một AQI/PM2.5 spike có chủ đích.
- Chứng minh producer/consumer/DB/API/frontend hoạt động end-to-end.
- Giúp người thuyết trình không phải chờ ô nhiễm thật xảy ra.

Không phải mục tiêu V1:

- Không ghi thẳng DB.
- Không tự sửa `anomaly_score` hoặc `is_anomaly` trong DB.
- Không giả vờ đây là dữ liệu thật.
- Không implement Telegram/email alert thật.
- Không thay đổi consumer schema.

Ghi chú quan trọng:

> Consumer hiện set `anomaly_score = NULL` và `is_anomaly = FALSE` khi insert. Vì vậy simulator V1 chủ yếu demo `AQI warning` qua ngưỡng AQI cao. `AI anomaly` vẫn phụ thuộc inference/model hoặc pipeline ML riêng.

---

## 2. Vì Sao Cần Simulator?

Trong demo, nếu chỉ chờ dữ liệu realtime tự nhiên:

- AQI có thể không đủ cao.
- Anomaly có thể không xảy ra.
- Người xem khó thấy hệ thống phản ứng với sự kiện bất thường.

Simulator giải quyết bằng cách tạo một event có kiểm soát:

```text
Province Hà Nội
AQI = 260
PM2.5 = 180
time = now
source = reis_simulator
```

Sau khi consumer ghi DB:

- `/api/province/1` có current reading spike.
- `/api/anomalies` có thể hiện record vì `aqi >= 150`.
- Dashboard/Map/Alerts có thể hiển thị trạng thái cảnh báo sau refresh/WebSocket.

---

## 3. CLI Contract

Lệnh chạy mặc định:

```bash
cd /home/ductien/Documents/reis

KAFKA_BOOTSTRAP_SERVERS=localhost:9092 REDIS_HOST=localhost REDIS_PORT=6379 \
/home/ductien/miniconda3/envs/reis/bin/python tools/simulator.py \
  --province-id 1 \
  --aqi 260 \
  --pm25 180
```

### Arguments bắt buộc/cơ bản

| Argument | Default | Validation | Mô tả |
|---|---:|---|---|
| `--province-id` | `1` | `1..63` | Tỉnh cần inject spike |
| `--aqi` | `260` | `0..500` | US AQI synthetic value |
| `--pm25` | `180` | `0..1000` | PM2.5 synthetic value |

### Arguments optional

| Argument | Default | Validation | Mô tả |
|---|---:|---|---|
| `--pm10` | derived from PM2.5 | `0..1000` | PM10 |
| `--temperature` | `32.0` | `-20..60` | Nhiệt độ |
| `--humidity` | `70.0` | `0..100` | Độ ẩm |
| `--wind-speed` | `4.0` | `0..200` | Gió |
| `--precipitation` | `0.0` | `>=0` | Mưa |
| `--no2` | `45.0` | `>=0` | Nitrogen dioxide |
| `--ozone` | `70.0` | `>=0` | Ozone |
| `--uv-index` | `6.0` | `0..20` | UV index |
| `--time` | now UTC | ISO datetime | Timestamp của spike |
| `--dry-run` | false | boolean | Chỉ in payload, không publish Kafka |

### Exit codes

| Code | Ý nghĩa |
|---:|---|
| `0` | Success hoặc dry-run success |
| `1` | Validation error / invalid province / publish failed |

---

## 4. Payload Contract

Payload phải pass `EnvironmentReading` trong `backend/ingestion/validator.py`.

Shape logic:

```json
{
  "province_id": 1,
  "time": "2026-05-15T10:30:00+00:00",
  "temperature": 32.0,
  "humidity": 70.0,
  "wind_speed": 4.0,
  "precipitation": 0.0,
  "pm2_5": 180.0,
  "pm10": 260.0,
  "aqi": 260,
  "no2": 45.0,
  "ozone": 70.0,
  "uv_index": 6.0,
  "raw_json": {
    "source": "reis_simulator",
    "scenario": "pm25_spike",
    "province_name": "Hà Nội",
    "synthetic": true,
    "created_at": "2026-05-15T10:30:00+00:00",
    "note": "Synthetic demo spike injected through Kafka"
  }
}
```

Rules:

- `province_id` phải có trong `PROVINCES_BY_ID`.
- `time` phải timezone-aware; default UTC now.
- `raw_json.source = "reis_simulator"` để phân biệt dữ liệu synthetic.
- Không thêm field `anomaly_score` hoặc `is_anomaly` vì consumer hiện set hai field này khi insert.

---

## 5. Implementation Design

File:

```text
tools/simulator.py
```

Các hàm nên có:

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ...

def parse_timestamp(value: str | None) -> datetime:
    ...

def build_spike_payload(args: argparse.Namespace) -> dict:
    ...

def validate_spike_payload(payload: dict) -> EnvironmentReading:
    ...

async def publish_spike(reading: EnvironmentReading, *, dry_run: bool = False) -> dict[str, int]:
    ...

def main(argv: list[str] | None = None) -> int:
    ...
```

### Import path setup

Vì script nằm ở `tools/` nhưng cần import backend modules, đầu file nên setup path:

```python
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"

for path in (REPO_ROOT, BACKEND_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
```

Imports chính:

```python
from backend.config.constants import PROVINCES_BY_ID
from ingestion.validator import EnvironmentReading, validate_record
from ingestion.producer import publish_records, close
```

Ghi chú:

- `publish_records()` có sẵn và publish vào Kafka topic `env.readings.raw`.
- Sau publish phải gọi `close()` để shutdown Kafka producer/Redis cleanly.

---

## 6. Logic Chi Tiết

### 6.1 `parse_args`

Responsibilities:

- Định nghĩa CLI options.
- Convert type cơ bản.
- Không làm validation phức tạp ở đây.

Example:

```bash
python tools/simulator.py --province-id 2 --aqi 220 --pm25 140 --dry-run
```

### 6.2 `parse_timestamp`

Rules:

- Nếu không truyền `--time`, dùng `datetime.now(timezone.utc)`.
- Nếu truyền `Z`, convert thành `+00:00`.
- Nếu timestamp không có timezone, gắn UTC để tránh naive datetime.

### 6.3 `build_spike_payload`

Rules:

- Lookup province trong `PROVINCES_BY_ID`.
- Nếu `--pm10` không truyền, default:

```python
pm10 = min(1000, max(pm25 * 1.45, pm25))
```

- Tạo `raw_json` metadata.

### 6.4 `validate_spike_payload`

Rules:

- Gọi `validate_record(payload)`.
- Nếu invalid, raise `ValueError` với message rõ.
- Return `EnvironmentReading`.

### 6.5 `publish_spike`

Rules:

- Nếu `dry_run=True`, print JSON payload và return `{"published": 0, "dlq": 0}`.
- Nếu không dry-run:
  - call `publish_records([reading])`.
  - call `close()` trong `finally`.
  - nếu `published != 1`, return/raise lỗi rõ.

### 6.6 `main`

Responsibilities:

- Configure logging.
- Parse args.
- Build payload.
- Validate payload.
- Publish hoặc dry-run.
- Print summary thân thiện:

```text
REIS simulator spike
Province: Hà Nội (#1)
AQI: 260
PM2.5: 180.0
Time: 2026-05-15T10:30:00+00:00
Kafka result: published=1, dlq=0
Next: wait up to 10s for consumer batch timeout, then refresh Dashboard/Alerts.
```

---

## 7. Test Plan

Test file:

```text
backend/tests/test_simulator.py
```

### Test cases bắt buộc

1. Build default payload:
   - `province_id = 1`
   - `aqi = 260`
   - `pm2_5 = 180`
   - `raw_json.source = "reis_simulator"`
   - validate pass.

2. Invalid province:
   - `province_id = 999`
   - raise `ValueError` hoặc exit code `1`.

3. Invalid AQI:
   - `aqi = 999`
   - validation fail.

4. Dry-run:
   - monkeypatch `publish_records`.
   - assert không gọi Kafka publish.

5. Publish path:
   - monkeypatch `publish_records` return `{"published": 1, "dlq": 0}`.
   - monkeypatch `close`.
   - assert publish called with one `EnvironmentReading`.

### Test command

```bash
/home/ductien/miniconda3/envs/reis/bin/python -m pytest backend/tests/test_simulator.py -v
```

Full selected test:

```bash
/home/ductien/miniconda3/envs/reis/bin/python -m pytest \
  backend/tests/test_api_routes.py \
  backend/tests/test_consumer.py \
  backend/tests/test_isolation_forest.py \
  backend/tests/test_simulator.py \
  -v
```

---

## 8. Manual Smoke Test

### Terminal 1 — Infra

```bash
cd /home/ductien/Documents/reis
docker-compose up -d zookeeper kafka redis timescaledb kafka-ui
```

### Terminal 2 — Consumer

```bash
cd /home/ductien/Documents/reis/backend

KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
DB_HOST=localhost DB_PORT=5432 DB_USER=reis DB_PASSWORD=reis_secret DB_NAME=reis_db \
/home/ductien/miniconda3/envs/reis/bin/python processing/consumer.py
```

### Terminal 3 — Simulator

Dry-run trước:

```bash
cd /home/ductien/Documents/reis

/home/ductien/miniconda3/envs/reis/bin/python tools/simulator.py \
  --province-id 1 \
  --aqi 260 \
  --pm25 180 \
  --dry-run
```

Publish thật:

```bash
cd /home/ductien/Documents/reis

KAFKA_BOOTSTRAP_SERVERS=localhost:9092 REDIS_HOST=localhost REDIS_PORT=6379 \
/home/ductien/miniconda3/envs/reis/bin/python tools/simulator.py \
  --province-id 1 \
  --aqi 260 \
  --pm25 180
```

### Verify DB

```bash
cd /home/ductien/Documents/reis

docker-compose exec timescaledb psql -U reis -d reis_db -c "
select province_id, aqi, pm2_5, time, raw_json
from env_readings
where province_id = 1
order by time desc
limit 5;
"
```

### Verify API

```bash
curl http://localhost:8000/api/province/1
curl http://localhost:8000/api/anomalies
```

Acceptance smoke:

- Consumer log có flush record hoặc batch timeout flush.
- DB latest row của province có AQI/PM2.5 spike.
- `/api/anomalies` có province đó nếu `aqi >= 150`.
- Dashboard/Alerts reflect spike sau refresh hoặc WebSocket update.

---

## 9. Acceptance Criteria

Task hoàn thành khi:

- `tools/simulator.py` tồn tại.
- CLI `--dry-run` in payload hợp lệ và không cần Kafka.
- CLI publish thật gửi đúng 1 message vào Kafka.
- Consumer insert row vào TimescaleDB.
- Payload có `raw_json.source = "reis_simulator"`.
- Invalid province/AQI/PM2.5 bị reject rõ ràng.
- Tests cho simulator pass.
- Docs hoặc output CLI nói rõ đây là synthetic demo data.

---

## 10. Risks Và Cách Tránh

### Risk 1 — Duplicate timestamp

Nếu chạy simulator nhiều lần cùng `--time`, DB unique `(province_id, time)` có thể ignore record.

Cách tránh:

- Default dùng `now UTC`.
- Nếu truyền `--time`, cảnh báo user tránh dùng timestamp cũ/trùng.

### Risk 2 — Consumer chưa chạy

Message vẫn nằm trong Kafka, nhưng DB chưa có row.

Cách nói:

> Simulator chỉ publish Kafka. Muốn thấy trên API/frontend cần consumer đang chạy để ghi DB.

### Risk 3 — AI anomaly vẫn bằng 0

Vì consumer không ghi `anomaly_score`.

Cách nói:

> V1 simulator demo AQI warning. AI anomaly cần inference/model pipeline đánh giá sau khi record vào DB.

### Risk 4 — Frontend chưa update ngay

WebSocket polling/broadcast có interval, API cũng cần refresh.

Cách tránh:

- Chờ 10-15 giây.
- Refresh Dashboard/Alerts.
- Check DB/API trước khi kết luận lỗi frontend.

---

## 11. Handoff Cho Thành Viên Implement

Giao task như sau:

```text
Implement tools/simulator.py theo docs/simulator_task.md.
Scope V1: Kafka single spike + dry-run + tests.
Không ghi thẳng DB, không sửa consumer schema, không implement alert manager.
```

Checklist PR:

- [ ] `tools/simulator.py`
- [ ] `backend/tests/test_simulator.py`
- [ ] `python -m pytest backend/tests/test_simulator.py -v` pass
- [ ] Manual dry-run pass
- [ ] Manual Kafka smoke pass nếu có infra
- [ ] Update `PROGRESS.md` Stage 2G từ 0% lên trạng thái phù hợp

