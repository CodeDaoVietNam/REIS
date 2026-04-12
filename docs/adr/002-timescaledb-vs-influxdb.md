# ADR 002: TimescaleDB thay vì InfluxDB

| | |
|---|---|
| **Ngày** | 2025 |
| **Trạng thái** | Accepted |
| **Người quyết định** | REIS Team |

---

## Bối cảnh (Context)

REIS cần lưu trữ dữ liệu môi trường dạng **time-series**: mỗi 15 phút có 63 records mới, mỗi record gồm ~15 numeric fields + timestamp + province_id. Sau 1 năm: ~2.2 triệu rows.

Yêu cầu:

- Query nhanh theo time range: "48 giờ gần nhất của tỉnh 48"
- JOIN với bảng `provinces` để lấy tên, tọa độ
- Python ORM/driver phổ biến
- Miễn phí và self-hosted được

Hai ứng viên chính: **TimescaleDB** (PostgreSQL extension) và **InfluxDB** (purpose-built time-series database).

---

## Quyết định (Decision)

**Chọn TimescaleDB.**

---

## Lý do (Rationale)

### 1. SQL quen thuộc — không học ngôn ngữ mới

InfluxDB dùng **InfluxQL** (v1) hoặc **Flux** (v2). Flux là functional language hoàn toàn khác SQL:

```flux
// InfluxDB Flux — query 48h gần nhất
from(bucket: "reis")
  |> range(start: -48h)
  |> filter(fn: (r) => r["province_id"] == "48")
  |> filter(fn: (r) => r["_field"] == "aqi")
  |> aggregateWindow(every: 1h, fn: mean)
```

```sql
-- TimescaleDB SQL — cùng query
SELECT time_bucket('1 hour', time) AS hour, AVG(aqi)
FROM env_readings
WHERE province_id = 48
  AND time > NOW() - INTERVAL '48 hours'
GROUP BY hour
ORDER BY hour;
```

Team đã biết SQL → không tốn thời gian học Flux → ít bug hơn trong giai đoạn đầu.

### 2. JOIN với relational data

REIS cần JOIN `env_readings` với `provinces` để lấy tên tỉnh, tọa độ, region:

```sql
-- TimescaleDB: JOIN tự nhiên như PostgreSQL thường
SELECT e.time, p.name_vi, p.latitude, e.aqi, e.pm2_5
FROM env_readings e
JOIN provinces p ON e.province_id = p.id
WHERE e.time > NOW() - INTERVAL '1 hour'
ORDER BY e.time DESC;
```

InfluxDB không support JOIN — phải fetch riêng rồi merge trong Python code. Phức tạp hơn và chậm hơn.

### 3. TimescaleDB IS PostgreSQL

TimescaleDB là PostgreSQL extension — tất cả tính năng PostgreSQL vẫn hoạt động:

- `asyncpg` Python driver — nhanh, async-native, team đã quen
- Full ACID transactions
- JSON/JSONB column cho `raw_json` field
- Constraint, foreign key, index — đúng relational model
- `psql` CLI để debug

InfluxDB cần driver riêng, query language riêng, không có transactions.

### 4. Hypertable performance đủ tốt

TimescaleDB Hypertable tự động partition data theo 7 ngày:

```
Sau 6 tháng:
  Chunk 1: Jan 1–7    (~270,000 rows)
  Chunk 2: Jan 8–14   (~270,000 rows)
  ...
  Chunk 26: Jun 24–30 (~270,000 rows)

Query "48h gần nhất" → chỉ đọc 1 chunk (~270k rows)
Không full scan 26 chunks (~7M rows)
```

Benchmark TimescaleDB: query 1 tháng data trên 63 tỉnh < 50ms với index đúng.

InfluxDB sẽ nhanh hơn ở raw ingestion throughput (hàng triệu points/giây), nhưng REIS chỉ cần 4.2 records/phút → TimescaleDB đủ dùng với margin rất lớn.

---

## Trade-offs và nhược điểm

### InfluxDB tối ưu hơn cho pure time-series

InfluxDB được thiết kế từ đầu cho time-series: data model (measurement, tags, fields) tự nhiên hơn, compression tốt hơn, retention policy built-in.

**Mitigation:** TimescaleDB có native compression (`timescaledb_compression_settings`) giảm storage ~90% cho cold data. Với 2.2M rows/năm, InfluxDB's compression advantage không đáng kể.

### TimescaleDB cần setup thêm bước

Phải chạy `SELECT create_hypertable(...)` sau khi tạo bảng. InfluxDB tự động là time-series.

**Mitigation:** `backend/scripts/setup_db.py` handle hết, chỉ cần chạy 1 lần.

### InfluxDB có built-in retention policy

InfluxDB tự động xóa data cũ hơn N ngày. TimescaleDB cần setup chunk retention thủ công.

**Mitigation:** TimescaleDB có `add_retention_policy()` với cú pháp đơn giản:
```sql
SELECT add_retention_policy('env_readings', INTERVAL '1 year');
```

---

## Kết quả (Consequences)

### Tích cực

- Team dùng SQL ngay từ ngày 1, không cần học Flux
- JOIN với `provinces` table natively
- `asyncpg` driver — codebase đồng nhất (không mix nhiều DB drivers)
- Full PostgreSQL ecosystem: DBeaver GUI, pgAdmin, pg_dump backup
- Dễ dàng add relational tables sau này (nếu cần users, alerts history...)

### Tiêu cực

- Cần Zookeeper-like setup? Không — TimescaleDB chỉ là PostgreSQL, không cần gì thêm
- Ingestion throughput thấp hơn InfluxDB — không ảnh hưởng vì REIS throughput rất thấp
- Cần nhớ luôn có `WHERE time > ...` khi query, không có safety net như InfluxDB

---

## Anti-patterns cần tránh

```sql
-- ❌ Full table scan — có thể treo hệ thống sau 6 tháng data
SELECT * FROM env_readings WHERE province_id = 48;

-- ✅ Luôn giới hạn time range
SELECT * FROM env_readings
WHERE province_id = 48
  AND time > NOW() - INTERVAL '48 hours'
ORDER BY time DESC;
```

---

## Liên quan

- `backend/scripts/setup_db.py` — Tạo hypertable và indexes
- `backend/processing/consumer.py` — Batch insert với asyncpg
- `ARCHITECTURE.md` — Database schema chi tiết
- `docs/ml-models.md` — Cách LSTM query 48h history
