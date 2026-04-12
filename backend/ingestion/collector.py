"""
collector.py — Thu thập dữ liệu thời tiết + chất lượng không khí
               cho 64 tỉnh Việt Nam từ Open-Meteo API.

Luồng hoạt động:
    1. Gọi song song 2 API (weather + air quality) cho tất cả 64 tỉnh
       → 1 request lớn cho tất cả tỉnh (batch), KHÔNG phải 64 request riêng lẻ
    2. Merge kết quả weather + AQ theo index (cùng thứ tự tỉnh)
    3. Chuẩn hóa tên field (us_aqi → aqi, nitrogen_dioxide → no2, ...)
    4. Trả về list[dict] — mỗi dict = 1 tỉnh

Chạy độc lập:
    python collector.py
Chạy như module:
    from ingestion.collector import collect_all_provinces
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH API
# ══════════════════════════════════════════════════════════════════════════════

# Endpoint: Lấy dữ liệu thời tiết hiện tại (temperature, humidity, wind, rain)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Endpoint: Lấy dữ liệu chất lượng không khí (PM2.5, PM10, AQI, NO2, ozone)
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Các biến thời tiết cần lấy (ngăn cách bằng dấu phẩy, KHÔNG có khoảng trắng)
#   temperature_2m        → Nhiệt độ (°C), đo ở độ cao 2m
#   wind_speed_10m        → Tốc độ gió (km/h), đo ở độ cao 10m
#   relative_humidity_2m  → Độ ẩm tương đối (%)
#   precipitation         → Lượng mưa (mm)
WEATHER_VARS = "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation"

# Các biến chất lượng không khí cần lấy
#   pm2_5             → Bụi mịn PM2.5 (µg/m³) — bụi nhỏ hơn 2.5 micromet
#   pm10              → Bụi mịn PM10  (µg/m³) — bụi nhỏ hơn 10 micromet
#   nitrogen_dioxide  → NO2 (µg/m³) — khí đioxit nitơ (ô nhiễm từ xe cộ, nhà máy)
#   ozone             → Ozone (µg/m³) — tầng ozone bề mặt
#   uv_index          → Chỉ số tia UV (0-20)
#   us_aqi            → US EPA Air Quality Index (0-500)
AQ_VARS = "pm10,pm2_5,nitrogen_dioxide,ozone,uv_index,us_aqi"


# ══════════════════════════════════════════════════════════════════════════════
# TỌA ĐỘ 64 TỈNH VIỆT NAM
# ══════════════════════════════════════════════════════════════════════════════
# Key: province_id (số nguyên, khớp với bảng provinces trong DB)
# Value: (latitude, longitude) — lấy từ Mapbox Geocoding API
#
# THỨ TỰ RẤT QUAN TRỌNG:
#   - Province ID phải khớp với cột "id" trong bảng provinces (init-db.sql)
#   - Khi gọi batch API, thứ tự lat/lon phải SORT theo province_id tăng dần
#   - API trả về kết quả theo thứ tự lat/lon gửi vào → index 0 = province_id 1
#
# Miền Bắc (region = 'Bắc'): ID 1-29, 62, 64
# Miền Trung (region = 'Trung'): ID 4, 29-40, 63
# Miền Nam (region = 'Nam'): ID 2-3, 41-61, 64

PROVINCE_COORDS: dict[int, tuple[float, float]] = {
    # ── Miền Bắc ───────────────────────────────────────────────────────────
    1:  (21.0283, 105.8540),   # Hà Nội
    5:  (22.8279, 104.9823),   # Hà Giang
    6:  (22.6761, 106.2016),   # Cao Bằng
    7:  (22.3862, 103.4702),   # Lai Châu
    8:  (22.4962, 103.9680),   # Lào Cai
    9:  (21.8212, 105.1833),   # Tuyên Quang
    10: (21.8511, 106.7622),   # Lạng Sơn
    11: (22.1398, 105.8320),   # Bắc Kạn
    12: (21.5954, 105.8387),   # Thái Nguyên
    13: (21.7049, 104.8791),   # Yên Bái
    14: (21.3270, 103.9144),   # Sơn La
    15: (21.3135, 105.3946),   # Phú Thọ
    16: (21.3079, 105.5965),   # Vĩnh Phúc
    17: (20.9489, 107.1035),   # Quảng Ninh
    18: (21.2804, 106.1985),   # Bắc Giang
    19: (21.2816, 106.1989),   # Bắc Ninh
    20: (20.8623, 106.6799),   # Hải Phòng
    21: (20.9411, 106.3330),   # Hải Dương
    22: (20.6626, 106.0585),   # Hưng Yên
    23: (20.8199, 105.3438),   # Hòa Bình
    24: (20.5514, 105.9171),   # Hà Nam
    25: (20.4272, 106.1749),   # Nam Định
    26: (20.4480, 106.3435),   # Thái Bình
    27: (20.2573, 105.9719),   # Ninh Bình
    28: (19.7996, 105.7864),   # Thanh Hóa
    62: (21.3924, 103.0160),   # Điện Biên
    # ── Miền Trung ─────────────────────────────────────────────────────────
    4:  (16.0680, 108.2120),   # Đà Nẵng
    29: (18.6596, 105.6970),   # Nghệ An
    30: (18.3393, 105.9029),   # Hà Tĩnh
    31: (19.6868, 105.7875),   # Quảng Bình
    32: (16.7468, 107.1877),   # Quảng Trị
    33: (16.4639, 107.5863),   # Thừa Thiên Huế
    34: (15.5752, 108.4743),   # Quảng Nam
    35: (15.1190, 108.8096),   # Quảng Ngãi
    36: (14.3512, 108.0027),   # Kon Tum
    37: (13.8865, 109.1133),   # Bình Định
    38: (13.7700, 109.2318),   # Gia Lai
    39: (13.0467, 109.3108),   # Phú Yên
    40: (12.6797, 108.0447),   # Đắk Lắk
    41: (12.2349, 109.1941),   # Khánh Hòa
    42: (11.9402, 108.4376),   # Lâm Đồng
    45: (11.5770, 108.9865),   # Ninh Thuận
    47: (10.9378, 108.0912),   # Bình Thuận
    63: (12.0006, 107.6960),   # Đắk Nông
    # ── Miền Nam ───────────────────────────────────────────────────────────
    2:  (10.7755, 106.7021),   # Hồ Chí Minh
    3:  (20.8623, 106.6799),   # Hải Phòng (thực ra là miền Bắc, giữ đúng notebook)
    43: (11.5314, 106.8943),   # Bình Phước
    44: (11.2943, 106.6750),   # Bình Dương
    46: (10.5373, 106.4086),   # Tây Ninh
    48: (10.9508, 106.8221),   # Đồng Nai
    49: (10.5389, 106.4061),   # Long An
    50: (10.3585, 106.3643),   # Đồng Tháp
    51: (10.3904, 105.4344),   # An Giang
    52: (10.4963, 107.1688),   # Bà Rịa - Vũng Tàu
    53: (10.3606, 106.3658),   # Tiền Giang
    54: (10.0107, 105.0833),   # Kiên Giang
    55: (10.0362, 105.7873),   # Cần Thơ
    56: (10.2315, 106.3599),   # Bến Tre
    57: (10.2548, 105.9715),   # Vĩnh Long
    58: (9.9356,  106.3416),   # Trà Vinh
    59: (9.6025,  105.9731),   # Sóc Trăng
    60: (9.2869,  105.7228),   # Bạc Liêu
    61: (9.1762,  105.1508),   # Cà Mau
    64: (9.7832,  105.4670),   # Hậu Giang
}


# ══════════════════════════════════════════════════════════════════════════════
# HÀM GỌI API VỚI RETRY
# ══════════════════════════════════════════════════════════════════════════════

async def _fetch(
    session: aiohttp.ClientSession,
    url: str,
    params: dict,
    retries: int = 3,
) -> list[dict]:
    """
    Gọi HTTP GET với retry exponential backoff.

    Exponential backoff là gì?
        - Lần 1 thất bại → chờ 1 giây → thử lại
        - Lần 2 thất bại → chờ 2 giây → thử lại
        - Lần 3 thất bại → chờ 4 giây → thử lần cuối
        → Tránh làm nghẽn server khi có lỗi tạm thời

    Args:
        session: aiohttp ClientSession (tái sử dụng connection)
        url: URL API
        params: Dict query parameters gửi kèm
        retries: Số lần thử lại (mặc định 3)

    Returns:
        List dict: API response. Open-Meteo batch trả về list khi
        có nhiều tọa độ, hoặc dict khi 1 tọa độ. Luôn trả về list.

    Raises:
        aiohttp.ClientError: Khi tất cả retries đều thất bại
    """
    for attempt in range(retries):
        try:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()   # Ném exception nếu status 4xx/5xx
                data = await resp.json()

                # Open-Meteo trả về:
                #   - list khi query nhiều tọa độ: [{...}, {...}]
                #   - dict khi query 1 tọa độ:  {...}
                # → Luôn normalize thành list để xử lý统一
                return data if isinstance(data, list) else [data]

        except aiohttp.ClientError as e:
            wait = 2 ** attempt  # 1, 2, 4 giây
            logger.warning(
                "Attempt %d/%d failed for %s: %s. Retrying in %ds",
                attempt + 1, retries, url, e, wait,
            )
            if attempt < retries - 1:
                await asyncio.sleep(wait)
            else:
                # Đã thử đủ → log lỗi và raise để caller xử lý
                logger.error("All %d attempts failed for %s", retries, url)
                raise


# ══════════════════════════════════════════════════════════════════════════════
# HÀM CHÍNH: THU THẬP TẤT CẢ TỈNH
# ══════════════════════════════════════════════════════════════════════════════

async def collect_all_provinces(
    coords: dict[int, tuple[float, float]] | None = None,
) -> list[dict[str, Any]]:
    """
    Thu thập dữ liệu thời tiết + chất lượng không khí cho tất cả 64 tỉnh.

    Kỹ thuật batch request:
        Thay vì gọi 64 lần API riêng lẻ (mất ~64 × 500ms = 32 giây),
        ta gửi 1 request với tất cả tọa độ (ngăn cách bằng dấu phẩy):
            ?latitude=21.0283,22.8279,...&longitude=105.8540,104.9823,...
        → Chỉ mất ~500ms cho cả 64 tỉnh

    Kỹ thuật song song:
        Dùng asyncio.gather() gọi weather API và AQ API CÙNG LÚC:
            asyncio.gather(weather_task, aq_task)
        → Tiết kiệm thêm ~500ms nữa

    Args:
        coords: Dict tọa độ. Mặc định dùng PROVINCE_COORDS.
                Có thể truyền subset để test (vd: {1: (21.0283, 105.8540)})

    Returns:
        List[dict]. Mỗi dict = 1 tỉnh, chứa:
        {
            "province_id":   int,        # ID tỉnh (1-64)
            "time":          datetime,   # Thời điểm đọc (UTC timezone)
            "temperature":   float,      # °C
            "humidity":      float,      # %
            "wind_speed":    float,      # km/h
            "precipitation":float,      # mm
            "pm2_5":         float,      # µg/m³
            "pm10":          float,      # µg/m³
            "aqi":           int,        # US EPA AQI (0-500)
            "no2":           float,      # µg/m³
            "ozone":         float,      # µg/m³
            "uv_index":      float,      # 0-20
            "raw_json":       dict,       # JSON gốc từ cả 2 API (để debug/audit)
        }

    Ví dụ:
        records = await collect_all_provinces()
        for r in records:
            print(f"Tỉnh {r['province_id']}: AQI={r['aqi']}, PM2.5={r['pm2_5']}")
    """
    if coords is None:
        coords = PROVINCE_COORDS

    # ── Bước 1: Chuẩn bị tọa độ theo thứ tự province_id tăng dần ─────────
    # Sắp xếp theo province_id để index ở response khớp với province_id
    sorted_items = sorted(coords.items())  # [(1, (lat,lon)), (2, (lat,lon)), ...]

    # Tạo 2 chuỗi lat, lon nối bằng dấu phẩy
    # Ví dụ: "21.0283,22.8279,22.6761,..."
    lats = ",".join(str(lat) for _, (lat, _) in sorted_items)
    lons = ",".join(str(lon) for _, (_, lon) in sorted_items)

    # ── Bước 2: Gọi 2 API song song (asyncio.gather) ───────────────────────
    # Shared session: aiohttp tái sử dụng TCP connection → nhanh hơn
    async with aiohttp.ClientSession() as session:
        # Task 1: Weather API
        weather_task = _fetch(
            session,
            WEATHER_URL,
            {
                "latitude": lats,
                "longitude": lons,
                "current": WEATHER_VARS,
                "timezone": "Asia/Ho_Chi_Minh",
            },
        )

        # Task 2: Air Quality API
        aq_task = _fetch(
            session,
            AQ_URL,
            {
                "latitude": lats,
                "longitude": lons,
                "current": AQ_VARS,
                "timezone": "Asia/Ho_Chi_Minh",
            },
        )

        # Chạy song song → đợi CẢ 2 cùng xong
        # → Thay vì đợi weather → rồi mới đợi AQ (tốn 1 giây),
        #   ta đợi cả 2 cùng lúc (~500ms total)
        weather_list, aq_list = await asyncio.gather(weather_task, aq_task)

    # ── Bước 3: Merge weather + AQ theo index ──────────────────────────────
    # weather_list[idx] và aq_list[idx] cùng ứng với province_id = idx + 1
    # Ví dụ: index 0 → province_id 1 (Hà Nội)
    records: list[dict[str, Any]] = []

    for idx, (province_id, _) in enumerate(sorted_items):
        w  = weather_list[idx]   # Dict thời tiết của tỉnh này
        aq = aq_list[idx]        # Dict chất lượng không khí của tỉnh này

        # Parse ISO timestamp → Python datetime với timezone UTC
        # API trả về: "2026-04-08T21:30" hoặc "2026-04-08T21:30+07:00"
        raw_time = w["current"]["time"]
        # Replace 'Z' (UTC) bằng +00:00 để fromisoformat hiểu
        time_str = raw_time.replace("Z", "+00:00") if raw_time.endswith("Z") else raw_time
        time_dt  = datetime.fromisoformat(time_str)

        # ── Build record ──────────────────────────────────────────────────
        record: dict[str, Any] = {
            # ID tỉnh (từ dict, KHỚP với bảng provinces)
            "province_id": province_id,

            # Thời điểm đọc (datetime object với timezone)
            "time": time_dt,

            # ── Weather fields ─────────────────────────────────────────
            # Key trong API ≠ tên trong DB → phải rename
            "temperature":   w["current"].get("temperature_2m"),           # °C
            "humidity":      w["current"].get("relative_humidity_2m"),    # %
            "wind_speed":    w["current"].get("wind_speed_10m"),          # km/h
            "precipitation": w["current"].get("precipitation"),           # mm

            # ── Air Quality fields ───────────────────────────────────────
            # Rename key cho khớp với schema DB
            "pm2_5":  aq["current"].get("pm2_5"),
            "pm10":   aq["current"].get("pm10"),
            "aqi":    aq["current"].get("us_aqi"),      # API: us_aqi → DB: aqi
            "no2":    aq["current"].get("nitrogen_dioxide"),  # API: nitrogen_dioxide → DB: no2
            "ozone":  aq["current"].get("ozone"),
            "uv_index": aq["current"].get("uv_index"),

            # ── Raw JSON (lưu response gốc để debug/audit) ─────────────
            "raw_json": {"weather": w, "air_quality": aq},
        }

        records.append(record)

    # ── Bước 4: Log thống kê ────────────────────────────────────────────────
    # Đếm số tỉnh có PM2.5 > 50 (ngưỡng "không tốt cho sức khỏe")
    unhealthy = sum(1 for r in records if r["pm2_5"] is not None and r["pm2_5"] > 50)
    logger.info(
        "Collected %d province records (AQI range: %d-%d, %d provinces with PM2.5 > 50)",
        len(records),
        min(r["aqi"] for r in records if r["aqi"] is not None),
        max(r["aqi"] for r in records if r["aqi"] is not None),
        unhealthy,
    )

    return records

def _aqi_label(aqi: int | None) -> str:
    """Trả về nhãn tiếng Việt theo US EPA AQI."""
    if aqi is None:
        return "N/A"
    if aqi <= 50:
        return "Tốt"
    if aqi <= 100:
        return "Trung bình"
    if aqi <= 150:
        return "Kém"
    if aqi <= 200:
        return "Xấu"
    if aqi <= 300:
        return "Rất xấu"
    return "Nguy hiểm"
# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT — Chạy trực tiếp bằng python collector.py
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Cấu hình logging để thấy thông báo
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

    # Chạy async function trong sync context
    records = asyncio.run(collect_all_provinces())

    # In kết quả
    print(f"\n✅ Collected {len(records)} province records\n")
    for r in records:
        label_aqi = _aqi_label(r["aqi"])
        print(
            f"  [{r['province_id']:2d}] "
            f"AQI={r['aqi']:3d} ({label_aqi:10s}) "
            f"PM2.5={r['pm2_5']:5.1f} "
            f"Temp={r['temperature']:4.1f}°C"
        )

