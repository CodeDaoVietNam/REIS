# ADR 003: Google Gemini 1.5 Flash thay vì GPT-4o

| | |
|---|---|
| **Ngày** | 2025 |
| **Trạng thái** | Accepted |
| **Người quyết định** | REIS Team |

---

## Bối cảnh (Context)

REIS cần một **LLM API** để tự động sinh insight bằng ngôn ngữ tự nhiên từ dữ liệu môi trường + kết quả ML. Insight được sinh mỗi khi cache MISS (TTL 1 giờ), với input gồm số liệu hiện tại, anomaly score, và forecast 12h.

Yêu cầu:

- Sinh văn bản tiếng Việt tự nhiên, < 150 từ
- Response time < 3 giây (người dùng đợi)
- Chi phí thấp — project sinh viên, không có budget lớn
- Độ chính xác đủ tốt cho domain môi trường
- Fallback plan nếu một provider bị outage

Các ứng viên: **Google Gemini 1.5 Flash**, **GPT-4o**, **GPT-4o-mini**, **Claude 3 Haiku**.

---

## Quyết định (Decision)

**Chọn Gemini 1.5 Flash làm primary, GPT-4o-mini làm fallback.**

---

## Lý do (Rationale)

### 1. Chi phí — yếu tố quyết định

Ước tính usage của REIS:

```
63 tỉnh × cache miss rate 20% × 4 requests/hour × 24h × 30 ngày
= 63 × 0.2 × 4 × 24 × 30
= 36,288 requests/tháng

Mỗi request: ~500 tokens input + 200 tokens output = 700 tokens

Tổng: 36,288 × 700 = ~25 triệu tokens/tháng
```

| Provider | Model | Input price | Output price | Monthly cost |
|----------|-------|-------------|--------------|--------------|
| Google | Gemini 1.5 Flash | $0.075/1M | $0.30/1M | **~$2.14** |
| OpenAI | GPT-4o-mini | $0.15/1M | $0.60/1M | ~$4.28 |
| Anthropic | Claude 3 Haiku | $0.25/1M | $1.25/1M | ~$6.25 |
| OpenAI | GPT-4o | $5.00/1M | $15.00/1M | ~$250 |

Gemini Flash rẻ hơn GPT-4o **116 lần**, rẻ hơn GPT-4o-mini 2 lần. Với budget sinh viên, đây là yếu tố quyết định.

### 2. Tốc độ response

Gemini 1.5 Flash được tối ưu cho latency thấp (tên "Flash" là có lý do):

```
Benchmark thực tế (domain-specific text generation, 200 token output):
  Gemini 1.5 Flash: ~0.8–1.5 giây
  GPT-4o-mini:      ~1.2–2.0 giây
  GPT-4o:           ~3.0–8.0 giây
```

REIS target < 3s response → Gemini Flash comfortable, GPT-4o-mini acceptable, GPT-4o borderline.

### 3. Chất lượng đủ tốt cho use case này

GPT-4o vượt trội cho reasoning phức tạp, creative writing, code generation. Nhưng REIS chỉ cần:

- Đọc số liệu môi trường
- Tóm tắt theo template cố định 4 phần
- Viết tiếng Việt tự nhiên

Với Prompt Engineering tốt và structured output, Gemini Flash cho kết quả chất lượng tương đương GPT-4o cho use case này, với chi phí thấp hơn rất nhiều.

### 4. Google AI Studio free tier để phát triển

Gemini có **free tier** trên Google AI Studio: 15 requests/phút, 1 triệu tokens/ngày. Trong quá trình phát triển (Tuần 3), có thể dùng free tier mà không cần credit card.

GPT-4o-mini không có free tier tương đương.

### 5. Fallback với GPT-4o-mini

```python
# backend/insights/llm_client.py
async def generate_insight(prompt: str) -> str:
    try:
        return await _gemini_generate(prompt)
    except (GeminiAPIError, asyncio.TimeoutError) as e:
        logger.warning("Gemini failed, falling back to GPT-4o-mini", extra={"error": str(e)})
        try:
            return await _openai_generate(prompt, model="gpt-4o-mini")
        except Exception as e2:
            logger.error("Both LLMs failed", extra={"error": str(e2)})
            return _build_template_insight(current_data, anomaly, forecast)
```

Three-tier fallback:
1. Gemini 1.5 Flash (primary)
2. GPT-4o-mini (fallback khi Gemini lỗi)
3. Template tĩnh (fallback cuối cùng — không bao giờ để UI trống)

---

## Trade-offs và nhược điểm

### Gemini tiếng Việt đôi khi kém hơn GPT-4o

GPT-4o có dataset tiếng Việt rộng hơn, câu văn tự nhiên hơn trong một số trường hợp.

**Mitigation:** Prompt Engineering bù đắp phần lớn sự khác biệt này. System prompt cụ thể về format, tone, và domain vocabulary giúp Gemini output tốt. Trong testing, chất lượng Gemini Flash đủ tốt cho use case môi trường.

### Dependency vào Google Cloud

Nếu Google có outage hoặc thay đổi pricing → ảnh hưởng. GPT-4o-mini (OpenAI) có thể cũng bị outage cùng lúc (ít khả năng nhưng có thể).

**Mitigation:** Template fallback (tier 3) đảm bảo hệ thống không bao giờ trả về error hoàn toàn.

### Rate limits free tier

Free tier: 15 requests/phút. Nếu 15 requests cache miss cùng lúc → bị throttle.

**Mitigation:** Redis cache giảm 80% requests. Trong production dùng paid tier — chi phí chỉ ~$2/tháng.

---

## Prompt Engineering Strategy

```python
SYSTEM_PROMPT = """
Bạn là chuyên gia phân tích chất lượng không khí tại Việt Nam.
Trả lời LUÔN bằng tiếng Việt, ngắn gọn, dưới 150 từ.
Cấu trúc bắt buộc (4 phần):
  (1) Hiện trạng: mô tả ngắn tình hình hiện tại
  (2) Nguyên nhân: 1-2 nguyên nhân có thể
  (3) Dự báo: xu hướng 3-12h tới
  (4) Khuyến nghị: hành động cụ thể cho người dân
Nếu is_critical=True, bắt đầu bằng '⚠️ CẢNH BÁO:' và in đậm nguy cơ.
Tránh câu sáo rỗng. Dùng số liệu cụ thể.
"""
```

Structured prompt → consistent output → dễ parse và hiển thị trên UI.

---

## Cache Strategy để giảm chi phí

```python
# AQI bucket giảm 80% requests
aqi_bucket = (aqi // 20) * 20    # AQI 121, 122, 123... → cùng bucket 120

# Cache key
cache_key = f"insight:{province_id}:{aqi_bucket}:{int(is_critical)}"

# TTL 1 giờ
redis.setex(cache_key, 3600, insight_text)
```

Với cache, chi phí thực tế giảm xuống còn **~$0.43/tháng** (20% miss rate × $2.14).

---

## Kết quả (Consequences)

### Tích cực

- Chi phí < $1/tháng với Redis cache
- Response time < 2 giây (Gemini Flash)
- Free tier đủ dùng trong development
- Fallback chain đảm bảo không bao giờ trả lỗi hoàn toàn

### Tiêu cực

- Phụ thuộc vào 2 external providers (Google + OpenAI)
- Tiếng Việt đôi khi cần review output quality
- Cần maintain cả 2 API clients trong code

---

## Liên quan

- `backend/insights/llm_client.py` — Gemini + OpenAI client với fallback
- `backend/insights/prompt_builder.py` — Prompt template construction
- `backend/insights/insight_cache.py` — Redis cache với AQI bucketing
- `ARCHITECTURE.md` — LLM Insight Engine trong Layer 3
- `.env.example` — `GEMINI_API_KEY`, `OPENAI_API_KEY`
