"""
constants.py — Hằng số dùng chung cho toàn bộ REIS.

Đặt ở đây thay vì hardcode để:
  - Một chỗ sửa → ảnh hưởng toàn bộ modules
  - Import vào bất kỳ đâu: from config.constants import PROVINCES
"""

# ══════════════════════════════════════════════════════════════════════════════
# KAFKA TOPICS
# ══════════════════════════════════════════════════════════════════════════════

KAFKA_TOPICS = {
    "ENV_READINGS_RAW":  "env.readings.raw",
    "ENV_ANOMALIES":     "env.anomalies",
    "ENV_DEAD_LETTER":   "env.dead-letter",
}

# ══════════════════════════════════════════════════════════════════════════════
# ML / FORECASTING CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

FORECAST_HORIZON = 12
HISTORY_WINDOW = 12
TARGET_COLUMN = "aqi"

# Feature set chọn từ notebook tuning vòng 2.
FEATURE_COLUMNS = [
    "pm2_5",
    "pm10",
    "aqi",
    "no2",
    "ozone",
    "temperature",
    "humidity",
    "wind_speed",
    "pm2_5_lag_1h",
    "pm2_5_lag_3h",
    "pm2_5_lag_6h",
    "aqi_lag_1h",
    "aqi_lag_3h",
    "aqi_lag_6h",
    "aqi_lag_24h",
    "pm10_lag_1h",
    "pm10_lag_3h",
    "aqi_rolling_mean_3h",
    "aqi_rolling_mean_6h",
    "aqi_rolling_std_6h",
    "aqi_rolling_max_3h",
    "pm2_5_rolling_mean_6h",
    "pm2_5_rolling_std_6h",
    "delta_aqi_1h",
    "delta_pm2_5_1h",
    "aqi_rolling_min_3h",
    "aqi_rolling_min_6h",
    "pm10_rolling_std_6h",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
]

ANOMALY_FEATURES = [
    "pm2_5",
    "pm10",
    "aqi",
    "no2",
    "ozone",
    "temperature",
    "wind_speed",
    "aqi_lag_3h",
    "aqi_lag_6h",
    "aqi_rolling_std_6h",
    "aqi_rolling_max_3h",
    "pm2_5_rolling_std_6h",
    "delta_aqi_1h",
    "delta_pm2_5_1h",
]

STRICT_ALERT_SCORE = 0.55
STRICT_ALERT_AQI = 150
STRICT_ALERT_PM25 = 100
STRICT_ALERT_DELTA_PM25 = 20

# ══════════════════════════════════════════════════════════════════════════════
# OPEN-METEO API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
AQ_BASE_URL  = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Weather variables (comma-separated, NO spaces)
WEATHER_VARS = "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation"

# Air quality variables
AQ_VARS = "pm10,pm2_5,nitrogen_dioxide,ozone,uv_index,us_aqi"

# ══════════════════════════════════════════════════════════════════════════════
# 63 TỈNH VIỆT NAM — đầy đủ thông tin
# ══════════════════════════════════════════════════════════════════════════════
# (id, name_vi, name_en, lat, lon, region)
# region: "Bac" | "Trung" | "Nam"

PROVINCES = [
    (1,  "Hà Nội",         "Hanoi",           21.0285, 105.8542, "Bac"),
    (2,  "Hồ Chí Minh",    "Ho Chi Minh",     10.7769, 106.7009, "Nam"),
    (3,  "Hải Phòng",      "Hai Phong",       20.8623, 106.6799, "Bac"),
    (4,  "Đà Nẵng",        "Da Nang",         16.0544, 108.2022, "Trung"),
    (5,  "Hà Giang",       "Ha Giang",        22.8279, 104.9823, "Bac"),
    (6,  "Cao Bằng",       "Cao Bang",        22.6761, 106.2016, "Bac"),
    (7,  "Lai Châu",       "Lai Chau",        22.3862, 103.4702, "Bac"),
    (8,  "Lào Cai",        "Lao Cai",         22.4962, 103.9680, "Bac"),
    (9,  "Tuyên Quang",    "Tuyen Quang",     21.8212, 105.1833, "Bac"),
    (10, "Lạng Sơn",       "Lang Son",        22.1398, 105.8320, "Bac"),
    (11, "Bắc Kạn",        "Bac Kan",         22.1398, 105.8320, "Bac"),
    (12, "Thái Nguyên",    "Thai Nguyen",     21.5954, 105.8387, "Bac"),
    (13, "Yên Bái",        "Yen Bai",         21.7049, 104.8791, "Bac"),
    (14, "Sơn La",         "Son La",          21.3270, 103.9144, "Bac"),
    (15, "Phú Thọ",        "Phu Tho",         21.3135, 105.3946, "Bac"),
    (16, "Vĩnh Phúc",      "Vinh Phuc",       21.3079, 105.5965, "Bac"),
    (17, "Quảng Ninh",     "Quang Ninh",      20.9489, 107.1035, "Bac"),
    (18, "Bắc Giang",      "Bac Giang",       21.2804, 106.1985, "Bac"),
    (19, "Bắc Ninh",       "Bac Ninh",        21.2816, 106.1989, "Bac"),
    (20, "Hải Dương",      "Hai Duong",       20.9411, 106.3330, "Bac"),
    (21, "Hưng Yên",       "Hung Yen",        20.6626, 106.0585, "Bac"),
    (22, "Hòa Bình",       "Hoa Binh",        20.8199, 105.3438, "Bac"),
    (23, "Hà Nam",          "Ha Nam",          20.5514, 105.9171, "Bac"),
    (24, "Nam Định",        "Nam Dinh",        20.4272, 106.1749, "Bac"),
    (25, "Thái Bình",       "Thai Binh",       20.4480, 106.3435, "Bac"),
    (26, "Ninh Bình",       "Ninh Binh",       20.2573, 105.9719, "Bac"),
    (27, "Thanh Hóa",       "Thanh Hoa",       19.7996, 105.7864, "Bac"),
    (28, "Nghệ An",         "Nghe An",         18.6596, 105.6970, "Trung"),
    (29, "Hà Tĩnh",         "Ha Tinh",         18.3393, 105.9029, "Trung"),
    (30, "Quảng Bình",      "Quang Binh",      19.6868, 105.7875, "Trung"),
    (31, "Quảng Trị",       "Quang Tri",       16.7468, 107.1877, "Trung"),
    (32, "Thừa Thiên Huế",  "Thua Thien Hue",  16.4639, 107.5863, "Trung"),
    (33, "Quảng Nam",       "Quang Nam",       15.5752, 108.4743, "Trung"),
    (34, "Quảng Ngãi",      "Quang Ngai",      14.3512, 108.0027, "Trung"),
    (35, "Kon Tum",         "Kon Tum",         13.8865, 109.1133, "Trung"),
    (36, "Gia Lai",         "Gia Lai",         13.7700, 109.2318, "Trung"),
    (37, "Bình Định",       "Binh Dinh",       13.0467, 109.3108, "Trung"),
    (38, "Phú Yên",         "Phu Yen",         13.0467, 109.3108, "Trung"),
    (39, "Đắk Lắk",         "Dak Lak",         12.6797, 108.0447, "Trung"),
    (40, "Đắk Nông",         "Dak Nong",        12.0006, 107.6960, "Trung"),
    (41, "Lâm Đồng",         "Lam Dong",        11.9402, 108.4376, "Trung"),
    (42, "Bình Phước",       "Binh Phuoc",      11.5314, 106.8943, "Nam"),
    (43, "Tây Ninh",         "Tay Ninh",        10.9460, 106.1900, "Nam"),
    (44, "Bình Dương",       "Binh Duong",       11.2943, 106.6750, "Nam"),
    (45, "Đồng Nai",         "Dong Nai",        10.9508, 106.8221, "Nam"),
    (46, "Bình Thuận",       "Binh Thuan",       10.9378, 108.0912, "Nam"),
    (47, "Khánh Hòa",        "Khanh Hoa",       11.2349, 109.1941, "Trung"),
    (48, "Ninh Thuận",       "Ninh Thuan",       11.5770, 108.9865, "Trung"),
    (49, "Long An",           "Long An",         10.5389, 106.4061, "Nam"),
    (50, "Đồng Tháp",        "Dong Thap",        10.3585, 106.3643, "Nam"),
    (51, "An Giang",          "An Giang",        10.3904, 105.4344, "Nam"),
    (52, "Bà Rịa - Vũng Tàu","Ba Ria Vung Tau", 10.4963, 107.1688, "Nam"),
    (53, "Tiền Giang",       "Tien Giang",      10.3606, 106.3658, "Nam"),
    (54, "Kiên Giang",        "Kien Giang",      9.9356,  106.3416, "Nam"),
    (55, "Cần Thơ",           "Can Tho",         10.0362, 105.7873, "Nam"),
    (56, "Hậu Giang",         "Hau Giang",       9.7832,  105.4670, "Nam"),
    (57, "Vĩnh Long",         "Vinh Long",        9.9356,  106.3416, "Nam"),
    (58, "Bến Tre",            "Ben Tre",         10.2315, 106.3599, "Nam"),
    (59, "Trà Vinh",           "Tra Vinh",        9.9356,  106.3416, "Nam"),
    (60, "Sóc Trăng",          "Soc Trang",       9.6025,  105.9731, "Nam"),
    (61, "Bạc Liêu",           "Bac Lieu",        9.2869,  105.7228, "Nam"),
    (62, "Cà Mau",              "Ca Mau",          9.1762,  105.1508, "Nam"),
    (63, "Điện Biên",          "Dien Bien",       21.3924, 103.0160, "Bac"),
]

# ── PROVINCES_COORDS: dict[int, tuple[float, float]] ─────────────────────────
# Dùng cho collector.py (API batch requests)
PROVINCES_COORDS: dict[int, tuple[float, float]] = {
    row[0]: (row[3], row[4]) for row in PROVINCES
}

# ── PROVINCES_BY_ID: dict[int, dict] ─────────────────────────────────────────
# Dùng cho API routes (tra name_vi, name_en, region nhanh)
PROVINCES_BY_ID: dict[int, dict] = {
    row[0]: {
        "id":       row[0],
        "name_vi":  row[1],
        "name_en":  row[2],
        "latitude": row[3],
        "longitude": row[4],
        "region":   row[5],
    }
    for row in PROVINCES
}

# ── Province count ─────────────────────────────────────────────────────────────
assert len(PROVINCES) == 63, f"Expected 63 provinces, got {len(PROVINCES)}"
