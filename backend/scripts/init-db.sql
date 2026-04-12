-- REIS Database Initialization Script
-- TimescaleDB schema: provinces + env_readings hypertable
-- Run via Docker: docker exec -i reis-timescaledb psql -U reis -d reis_db < init-db.sql

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ── provinces lookup table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS provinces (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(10) UNIQUE NOT NULL,  -- matches notebook "MA_TINH" (01..64)
    name_vi         VARCHAR(100) NOT NULL,
    latitude        FLOAT8 NOT NULL,
    longitude       FLOAT8 NOT NULL,
    region          VARCHAR(20) CHECK (region IN ('Bắc', 'Trung', 'Nam')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── env_readings hypertable ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS env_readings (
    time              TIMESTAMPTZ NOT NULL,
    province_id       INT NOT NULL,  -- FK: provinces.id
    temperature       FLOAT4,
    humidity          FLOAT4,
    wind_speed        FLOAT4,
    precipitation     FLOAT4,
    pm2_5             FLOAT4,
    pm10              FLOAT4,
    aqi               INT,
    no2               FLOAT4,
    ozone             FLOAT4,
    uv_index          FLOAT4,
    anomaly_score     FLOAT4,
    is_anomaly        BOOLEAN DEFAULT FALSE,
    raw_json          JSONB,
    inserted_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'env_readings',
    'time',
    chunk_time_interval => INTERVAL '7 days',
    migrate_data => true
);

-- ── Indexes ──────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_readings_province_time
    ON env_readings (province_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_readings_anomaly
    ON env_readings (is_anomaly, time DESC)
    WHERE is_anomaly = TRUE;

-- ── Seed 64 provinces (from notebook 01_api_exploration) ───────────
INSERT INTO provinces (code, name_vi, latitude, longitude, region) VALUES
('01', 'Hà Nội',              21.0283, 105.8540, 'Bắc'),
('02', 'Hồ Chí Minh',         10.7755, 106.7021, 'Nam'),
('03', 'Hải Phòng',           20.8623, 106.6799, 'Bắc'),
('04', 'Đà Nẵng',             16.0680, 108.2120, 'Trung'),
('05', 'Hà Giang',           22.8279, 104.9823, 'Bắc'),
('06', 'Cao Bằng',            22.6761, 106.2016, 'Bắc'),
('07', 'Lai Châu',            22.3862, 103.4702, 'Bắc'),
('08', 'Lào Cai',             22.4962, 103.9680, 'Bắc'),
('09', 'Tuyên Quang',         21.8212, 105.1833, 'Bắc'),
('10', 'Lạng Sơn',            21.8511, 106.7622, 'Bắc'),
('11', 'Bắc Kạn',             22.1398, 105.8320, 'Bắc'),
('12', 'Thái Nguyên',         21.5954, 105.8387, 'Bắc'),
('13', 'Yên Bái',             21.7049, 104.8791, 'Bắc'),
('14', 'Sơn La',              21.3270, 103.9144, 'Bắc'),
('15', 'Phú Thọ',             21.3135, 105.3946, 'Bắc'),
('16', 'Vĩnh Phúc',           21.3079, 105.5965, 'Bắc'),
('17', 'Quảng Ninh',          20.9489, 107.1035, 'Bắc'),
('18', 'Bắc Giang',           21.2804, 106.1985, 'Bắc'),
('19', 'Bắc Ninh',            21.2816, 106.1989, 'Bắc'),
('21', 'Hải Dương',           20.9411, 106.3330, 'Bắc'),
('22', 'Hưng Yên',            20.6626, 106.0585, 'Bắc'),
('23', 'Hòa Bình',            20.8199, 105.3438, 'Bắc'),
('24', 'Hà Nam',              20.5514, 105.9171, 'Bắc'),
('25', 'Nam Định',            20.4272, 106.1749, 'Bắc'),
('26', 'Thái Bình',           20.4480, 106.3435, 'Bắc'),
('27', 'Ninh Bình',           20.2573, 105.9719, 'Bắc'),
('28', 'Thanh Hóa',           19.7996, 105.7864, 'Bắc'),
('29', 'Nghệ An',             18.6596, 105.6970, 'Trung'),
('30', 'Hà Tĩnh',             18.3393, 105.9029, 'Trung'),
('31', 'Quảng Bình',          19.6868, 105.7875, 'Trung'),
('32', 'Quảng Trị',           16.7468, 107.1877, 'Trung'),
('33', 'Thừa Thiên Huế',      16.4639, 107.5863, 'Trung'),
('34', 'Quảng Nam',           15.5752, 108.4743, 'Trung'),
('35', 'Quảng Ngãi',          15.1190, 108.8096, 'Trung'),
('36', 'Kon Tum',             14.3512, 108.0027, 'Trung'),
('37', 'Bình Định',           13.8865, 109.1133, 'Trung'),
('38', 'Gia Lai',             13.7700, 109.2318, 'Trung'),
('39', 'Phú Yên',             13.0467, 109.3108, 'Trung'),
('40', 'Đắk Lắk',             12.6797, 108.0447, 'Trung'),
('41', 'Khánh Hòa',           12.2349, 109.1941, 'Trung'),
('42', 'Lâm Đồng',            11.9402, 108.4376, 'Trung'),
('43', 'Bình Phước',          11.5314, 106.8943, 'Nam'),
('44', 'Bình Dương',          14.2943, 109.0812, 'Nam'),
('45', 'Ninh Thuận',          11.5770, 108.9865, 'Trung'),
('46', 'Tây Ninh',            10.5373, 106.4086, 'Nam'),
('47', 'Bình Thuận',          10.9378, 108.0912, 'Trung'),
('48', 'Đồng Nai',            10.9508, 106.8221, 'Nam'),
('49', 'Long An',             10.5389, 106.4061, 'Nam'),
('50', 'Đồng Tháp',           10.3585, 106.3643, 'Nam'),
('51', 'An Giang',            10.3904, 105.4344, 'Nam'),
('52', 'Bà Rịa - Vũng Tàu',  10.4963, 107.1688, 'Nam'),
('53', 'Tiền Giang',          10.3606, 106.3658, 'Nam'),
('54', 'Kiên Giang',          10.0107, 105.0833, 'Nam'),
('55', 'Cần Thơ',             10.0362, 105.7873, 'Nam'),
('56', 'Bến Tre',             10.2315, 106.3599, 'Nam'),
('57', 'Vĩnh Long',           10.2548, 105.9715, 'Nam'),
('58', 'Trà Vinh',            9.9356,  106.3416, 'Nam'),
('59', 'Sóc Trăng',           9.6025,  105.9731, 'Nam'),
('60', 'Bạc Liêu',            9.2869,  105.7228, 'Nam'),
('61', 'Cà Mau',              9.1762,  105.1508, 'Nam'),
('62', 'Điện Biên',          21.3924, 103.0160, 'Bắc'),
('63', 'Đắk Nông',            12.0006, 107.6960, 'Trung'),
('64', 'Hậu Giang',           9.7832,  105.4670, 'Nam')
ON CONFLICT (code) DO NOTHING;
