"""
collector.py — Thu thập dữ liệu thời tiết + chất lượng không khí
               cho 63 tỉnh Việt Nam từ Open-Meteo API.

Luồng hoạt động:
    1. Gọi song song 2 API (weather + air quality) cho tất cả 63 tỉnh
       → 1 request lớn cho tất cả tỉnh (batch), KHÔNG phải 63 request riêng lẻ
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

# Import tọa độ 63 tỉnh từ constants.py — single source of truth
sys_path_insert_guard = None  # noqa: F841
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.constants import PROVINCES_COORDS

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
# TỌA ĐỘ 63 TỈNH VIỆT NAM
# ══════════════════════════════════════════════════════════════════════════════
# Dùng PROVINCES_COORDS từ config/constants.py — single source of truth.
# KHÔNG hardcode ở đây để tránh lệch với schema DB.
#
# PROVINCES_COORDS: dict[int, tuple[float, float]]
# Key: province_id 1-63 (khớp với cột "id" trong bảng provinces)
# Value: (latitude, longitude)

PROVINCE_COORDS = PROVINCES_COORDS  # alias giữ backward compat


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
    Thu thập dữ liệu thời tiết + chất lượng không khí cho tất cả 63 tỉnh.

    Kỹ thuật batch request:
        Thay vì gọi 63 lần API riêng lẻ (mất ~63 × 500ms = 31 giây),
        ta gửi 1 request với tất cả tọa độ (ngăn cách bằng dấu phẩy):
            ?latitude=21.0283,22.8279,...&longitude=105.8540,104.9823,...
        → Chỉ mất ~500ms cho cả 63 tỉnh

    Kỹ thuật song song:
        Dùng asyncio.gather() gọi weather API và AQ API CÙNG LÚC:
            asyncio.gather(weather_task, aq_task)
        → Tiết kiệm thêm ~500ms nữa

    Args:
        coords: Dict tọa độ. Mặc định dùng PROVINCE_COORDS (= PROVINCES_COORDS từ constants.py).
                Có thể truyền subset để test (vd: {1: (21.0283, 105.8540)})

    Returns:
        List[dict]. Mỗi dict = 1 tỉnh, chứa:
        {
            "province_id":   int,        # ID tỉnh (1-63)
            "time":          datetime,   # Thời điểm đọc (UTC timezone)
            "temperature":   float,      # °C
            "humidity":      float,      # %
            "wind_speed":    float,      # km/h
            "precipitation": float,      # mm
            "pm2_5":         float,      # µg/m³
            "pm10":          float,      # µg/m³
            "aqi":           int,        # US EPA AQI (0-500)
            "no2":           float,      # µg/m³
            "ozone":         float,      # µg/m³
            "uv_index":      float,      # 0-20
            "raw_json":      dict,       # JSON gốc từ cả 2 API (để debug/audit)
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

