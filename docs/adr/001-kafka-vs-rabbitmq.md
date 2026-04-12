# ADR 001: Apache Kafka thay vì RabbitMQ

| | |
|---|---|
| **Ngày** | 2025 |
| **Trạng thái** | Accepted |
| **Người quyết định** | REIS Team |

---

## Bối cảnh (Context)

REIS cần một **Message Broker** làm trạm trung chuyển giữa Data Collector (producer) và Database Writer (consumer). Hai ứng viên chính là **Apache Kafka** và **RabbitMQ** — cả hai đều phổ biến, đều có Docker image, đều hỗ trợ Python client.

Yêu cầu cụ thể của REIS:

- Collector đẩy 63 messages mỗi 15 phút (throughput thấp)
- Consumer ghi vào TimescaleDB — phải đảm bảo **không mất data** dù DB chậm
- Trong tương lai, nhiều services (ML inference, monitoring, backup) có thể cần đọc cùng data
- Cần khả năng **đọc lại** data cũ nếu consumer có bug phải reprocess
- Team quen với Python hơn là Java/Scala

---

## Quyết định (Decision)

**Chọn Apache Kafka.**

---

## Lý do (Rationale)

### 1. Log-based storage vs Queue-based storage

RabbitMQ là **queue**: message bị xóa sau khi consumer ACK. Kafka là **log**: message được giữ lại theo retention policy (mặc định 7 ngày, REIS dùng 24h).

Điều này quan trọng vì:

```
Scenario: Consumer có bug, ghi sai data vào DB.
  
RabbitMQ:
  Consumer ACK messages → chúng bị xóa → không thể reprocess
  Phải khôi phục từ backup DB (nếu có)

Kafka:
  Reset offset về thời điểm trước bug
  Consumer đọc lại toàn bộ messages đó
  Reprocess sạch sẽ
```

### 2. Multiple consumers độc lập

RabbitMQ: mỗi consumer đọc một message → message biến mất. Để nhiều consumers nhận cùng message phải dùng Exchange + nhiều Queue — phức tạp.

Kafka: tất cả consumers trong **Consumer Group khác nhau** đều đọc toàn bộ topic độc lập.

```
REIS future state:
  Topic: env.readings.raw
    ├── Consumer Group: db-writer     → ghi vào TimescaleDB
    ├── Consumer Group: ml-inference  → chạy LSTM realtime
    ├── Consumer Group: monitoring    → track data quality
    └── Consumer Group: backup        → export sang S3
  
  Thêm consumer mới = không ảnh hưởng gì đến các consumers hiện tại
```

### 3. Ordering guarantee per partition

Kafka đảm bảo thứ tự message **trong cùng một partition**. REIS dùng `province_id` làm partition key → tất cả data của tỉnh 48 vào partition 0, đọc ra đúng thứ tự thời gian → time-series đúng.

RabbitMQ không đảm bảo ordering khi có nhiều consumers.

### 4. Decoupling tốc độ producer/consumer

```
Collector: đẩy 63 messages trong 0.4 giây
DB Writer: insert 63 rows, có thể mất 2–5 giây

RabbitMQ: có thể bị overload nếu consumer chậm hơn producer nhiều
Kafka:    message nằm trên disk, consumer đọc theo tốc độ của mình
          → không bao giờ mất data do producer quá nhanh
```

---

## Trade-offs và nhược điểm

### Kafka phức tạp hơn

Kafka cần **Zookeeper** (hoặc KRaft từ v3.3+) để quản lý cluster metadata. RabbitMQ chỉ cần 1 container.

```yaml
# Kafka: 2 containers
services:
  zookeeper: ...
  kafka: ...

# RabbitMQ: 1 container
services:
  rabbitmq: ...
```

**Mitigation:** REIS dùng Docker Compose, thêm Zookeeper không đáng kể. Kafka UI (Kowl) ở port 8090 giúp debug dễ hơn.

### Kafka overkill cho throughput thấp

REIS chỉ cần 63 messages/15 phút = 4.2 messages/phút. Kafka được thiết kế cho hàng triệu messages/giây. Về mặt kỹ thuật, RabbitMQ đủ dùng cho throughput hiện tại.

**Mitigation:** Đây là trade-off có chủ đích — REIS được thiết kế để scale lên 50+ thành phố toàn cầu (Phase 2). Bắt đầu với Kafka từ đầu tránh migration phức tạp sau này. Ngoài ra, kinh nghiệm làm việc với Kafka có giá trị cao hơn trong CV.

### Learning curve

Các khái niệm Kafka (topic, partition, offset, consumer group) cần thời gian học. RabbitMQ đơn giản hơn cho người mới.

**Mitigation:** Tài liệu `docs/` và `CLAUDE.md` giải thích chi tiết. Thực tế code Kafka Python chỉ cần 20–30 dòng cho producer và consumer cơ bản.

---

## Kết quả (Consequences)

### Tích cực

- Data không bao giờ bị mất dù consumer crash hay DB chậm
- Có thể thêm consumers mới (monitoring, ML inference) mà không cần sửa code hiện tại
- Replay capability để debug và reprocess
- Ordering guarantee cho time-series data
- Production-grade technology — valuable trong CV/portfolio

### Tiêu cực

- Cần maintain thêm Zookeeper container
- Setup phức tạp hơn (cần tạo topic thủ công trước khi dùng)
- Cần đợi 60 giây sau `docker-compose up` để Kafka sẵn sàng

---

## Liên quan

- `docker-compose.yml` — Kafka + Zookeeper service config
- `backend/ingestion/producer.py` — Kafka producer implementation
- `backend/processing/consumer.py` — Kafka consumer với manual commit
- `ARCHITECTURE.md` — Mô tả chi tiết Layer 2
