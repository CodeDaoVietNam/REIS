import type {
  AnomalyPayload,
  AnomalyRecord,
  CompareResponse,
  EnvironmentalData,
  ForecastPayload,
  InsightPayload,
  MetricKey,
  Province,
  ProvinceDetail,
  ProvinceSummary,
  Region,
  SummaryPayload,
} from '@/src/types';

export const PROVINCES: Province[] = [
  { id: 1, name: 'Hà Nội', en_name: 'Hanoi', lat: 21.0285, lng: 105.8542, region: 'North' },
  { id: 2, name: 'Hồ Chí Minh', en_name: 'Ho Chi Minh', lat: 10.7769, lng: 106.7009, region: 'South' },
  { id: 3, name: 'Hải Phòng', en_name: 'Hai Phong', lat: 20.8623, lng: 106.6799, region: 'North' },
  { id: 4, name: 'Đà Nẵng', en_name: 'Da Nang', lat: 16.0544, lng: 108.2022, region: 'Central' },
  { id: 5, name: 'Hà Giang', en_name: 'Ha Giang', lat: 22.8279, lng: 104.9823, region: 'North' },
  { id: 6, name: 'Cao Bằng', en_name: 'Cao Bang', lat: 22.6761, lng: 106.2016, region: 'North' },
  { id: 7, name: 'Lai Châu', en_name: 'Lai Chau', lat: 22.3862, lng: 103.4702, region: 'North' },
  { id: 8, name: 'Lào Cai', en_name: 'Lao Cai', lat: 22.4962, lng: 103.9680, region: 'North' },
  { id: 9, name: 'Tuyên Quang', en_name: 'Tuyen Quang', lat: 21.8212, lng: 105.1833, region: 'North' },
  { id: 10, name: 'Lạng Sơn', en_name: 'Lang Son', lat: 22.1398, lng: 105.832, region: 'North' },
  { id: 11, name: 'Bắc Kạn', en_name: 'Bac Kan', lat: 22.1398, lng: 105.832, region: 'North' },
  { id: 12, name: 'Thái Nguyên', en_name: 'Thai Nguyen', lat: 21.5954, lng: 105.8387, region: 'North' },
  { id: 13, name: 'Yên Bái', en_name: 'Yen Bai', lat: 21.7049, lng: 104.8791, region: 'North' },
  { id: 14, name: 'Sơn La', en_name: 'Son La', lat: 21.327, lng: 103.9144, region: 'North' },
  { id: 15, name: 'Phú Thọ', en_name: 'Phu Tho', lat: 21.3135, lng: 105.3946, region: 'North' },
  { id: 16, name: 'Vĩnh Phúc', en_name: 'Vinh Phuc', lat: 21.3079, lng: 105.5965, region: 'North' },
  { id: 17, name: 'Quảng Ninh', en_name: 'Quang Ninh', lat: 20.9489, lng: 107.1035, region: 'North' },
  { id: 18, name: 'Bắc Giang', en_name: 'Bac Giang', lat: 21.2804, lng: 106.1985, region: 'North' },
  { id: 19, name: 'Bắc Ninh', en_name: 'Bac Ninh', lat: 21.2816, lng: 106.1989, region: 'North' },
  { id: 20, name: 'Hải Dương', en_name: 'Hai Duong', lat: 20.9411, lng: 106.333, region: 'North' },
  { id: 21, name: 'Hưng Yên', en_name: 'Hung Yen', lat: 20.6626, lng: 106.0585, region: 'North' },
  { id: 22, name: 'Hòa Bình', en_name: 'Hoa Binh', lat: 20.8199, lng: 105.3438, region: 'North' },
  { id: 23, name: 'Hà Nam', en_name: 'Ha Nam', lat: 20.5514, lng: 105.9171, region: 'North' },
  { id: 24, name: 'Nam Định', en_name: 'Nam Dinh', lat: 20.4272, lng: 106.1749, region: 'North' },
  { id: 25, name: 'Thái Bình', en_name: 'Thai Binh', lat: 20.448, lng: 106.3435, region: 'North' },
  { id: 26, name: 'Ninh Bình', en_name: 'Ninh Binh', lat: 20.2573, lng: 105.9719, region: 'North' },
  { id: 27, name: 'Thanh Hóa', en_name: 'Thanh Hoa', lat: 19.7996, lng: 105.7864, region: 'North' },
  { id: 28, name: 'Nghệ An', en_name: 'Nghe An', lat: 18.6596, lng: 105.697, region: 'Central' },
  { id: 29, name: 'Hà Tĩnh', en_name: 'Ha Tinh', lat: 18.3393, lng: 105.9029, region: 'Central' },
  { id: 30, name: 'Quảng Bình', en_name: 'Quang Binh', lat: 19.6868, lng: 105.7875, region: 'Central' },
  { id: 31, name: 'Quảng Trị', en_name: 'Quang Tri', lat: 16.7468, lng: 107.1877, region: 'Central' },
  { id: 32, name: 'Thừa Thiên Huế', en_name: 'Thua Thien Hue', lat: 16.4639, lng: 107.5863, region: 'Central' },
  { id: 33, name: 'Quảng Nam', en_name: 'Quang Nam', lat: 15.5752, lng: 108.4743, region: 'Central' },
  { id: 34, name: 'Quảng Ngãi', en_name: 'Quang Ngai', lat: 14.3512, lng: 108.0027, region: 'Central' },
  { id: 35, name: 'Kon Tum', en_name: 'Kon Tum', lat: 13.8865, lng: 109.1133, region: 'Central' },
  { id: 36, name: 'Gia Lai', en_name: 'Gia Lai', lat: 13.77, lng: 109.2318, region: 'Central' },
  { id: 37, name: 'Bình Định', en_name: 'Binh Dinh', lat: 13.0467, lng: 109.3108, region: 'Central' },
  { id: 38, name: 'Phú Yên', en_name: 'Phu Yen', lat: 13.0467, lng: 109.3108, region: 'Central' },
  { id: 39, name: 'Đắk Lắk', en_name: 'Dak Lak', lat: 12.6797, lng: 108.0447, region: 'Central' },
  { id: 40, name: 'Đắk Nông', en_name: 'Dak Nong', lat: 12.0006, lng: 107.696, region: 'Central' },
  { id: 41, name: 'Lâm Đồng', en_name: 'Lam Dong', lat: 11.9402, lng: 108.4376, region: 'Central' },
  { id: 42, name: 'Bình Phước', en_name: 'Binh Phuoc', lat: 11.5314, lng: 106.8943, region: 'South' },
  { id: 43, name: 'Tây Ninh', en_name: 'Tay Ninh', lat: 10.946, lng: 106.19, region: 'South' },
  { id: 44, name: 'Bình Dương', en_name: 'Binh Duong', lat: 11.2943, lng: 106.675, region: 'South' },
  { id: 45, name: 'Đồng Nai', en_name: 'Dong Nai', lat: 10.9508, lng: 106.8221, region: 'South' },
  { id: 46, name: 'Bình Thuận', en_name: 'Binh Thuan', lat: 10.9378, lng: 108.0912, region: 'South' },
  { id: 47, name: 'Khánh Hòa', en_name: 'Khanh Hoa', lat: 11.2349, lng: 109.1941, region: 'Central' },
  { id: 48, name: 'Ninh Thuận', en_name: 'Ninh Thuan', lat: 11.577, lng: 108.9865, region: 'Central' },
  { id: 49, name: 'Long An', en_name: 'Long An', lat: 10.5389, lng: 106.4061, region: 'South' },
  { id: 50, name: 'Đồng Tháp', en_name: 'Dong Thap', lat: 10.3585, lng: 106.3643, region: 'South' },
  { id: 51, name: 'An Giang', en_name: 'An Giang', lat: 10.3904, lng: 105.4344, region: 'South' },
  { id: 52, name: 'Bà Rịa - Vũng Tàu', en_name: 'Ba Ria Vung Tau', lat: 10.4963, lng: 107.1688, region: 'South' },
  { id: 53, name: 'Tiền Giang', en_name: 'Tien Giang', lat: 10.3606, lng: 106.3658, region: 'South' },
  { id: 54, name: 'Kiên Giang', en_name: 'Kien Giang', lat: 9.9356, lng: 106.3416, region: 'South' },
  { id: 55, name: 'Cần Thơ', en_name: 'Can Tho', lat: 10.0362, lng: 105.7873, region: 'South' },
  { id: 56, name: 'Hậu Giang', en_name: 'Hau Giang', lat: 9.7832, lng: 105.467, region: 'South' },
  { id: 57, name: 'Vĩnh Long', en_name: 'Vinh Long', lat: 9.9356, lng: 106.3416, region: 'South' },
  { id: 58, name: 'Bến Tre', en_name: 'Ben Tre', lat: 10.2315, lng: 106.3599, region: 'South' },
  { id: 59, name: 'Trà Vinh', en_name: 'Tra Vinh', lat: 9.9356, lng: 106.3416, region: 'South' },
  { id: 60, name: 'Sóc Trăng', en_name: 'Soc Trang', lat: 9.6025, lng: 105.9731, region: 'South' },
  { id: 61, name: 'Bạc Liêu', en_name: 'Bac Lieu', lat: 9.2869, lng: 105.7228, region: 'South' },
  { id: 62, name: 'Cà Mau', en_name: 'Ca Mau', lat: 9.1762, lng: 105.1508, region: 'South' },
  { id: 63, name: 'Điện Biên', en_name: 'Dien Bien', lat: 21.3924, lng: 103.016, region: 'North' },
];

const regionBaseAqi: Record<Region, number> = {
  North: 118,
  Central: 82,
  South: 68,
};

const regionBaseTemp: Record<Region, number> = {
  North: 23,
  Central: 29,
  South: 32,
};

const industrialBoost = new Set(['Hà Nội', 'Bắc Ninh', 'Hưng Yên', 'Bình Dương', 'Đồng Nai']);

function noise(seed: number, span: number): number {
  const value = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return (value - Math.floor(value)) * span;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function toBackendRegion(region: Region): 'Bac' | 'Trung' | 'Nam' {
  if (region === 'North') return 'Bac';
  if (region === 'Central') return 'Trung';
  return 'Nam';
}

export function provinceToSummary(province: Province, current: EnvironmentalData | null): ProvinceSummary {
  return {
    province_id: province.id,
    name_vi: province.name,
    name_en: province.en_name,
    latitude: province.lat,
    longitude: province.lng,
    region: toBackendRegion(province.region),
    current,
  };
}

export function generateMockReading(province: Province, hourOffset = 0): EnvironmentalData {
  const dailyWave = Math.sin(((new Date().getHours() + hourOffset - 8) / 24) * Math.PI * 2);
  const baseAqi = regionBaseAqi[province.region] + (industrialBoost.has(province.name) ? 35 : 0);
  const aqi = Math.round(clamp(baseAqi + noise(province.id + hourOffset, 34) - 12 + dailyWave * 14, 12, 260));
  const pm25 = Number(clamp(aqi * 0.42 + noise(province.id * 3 + hourOffset, 8), 3, 180).toFixed(1));
  const temperature = Number((regionBaseTemp[province.region] + dailyWave * 5 + noise(province.id * 5, 2.5)).toFixed(1));
  const isAnomaly = aqi >= 150 || pm25 >= 90;

  return {
    time: new Date(Date.now() + hourOffset * 60 * 60 * 1000).toISOString(),
    province_id: province.id,
    province_name: province.name,
    temperature,
    humidity: Math.round(clamp(78 - dailyWave * 12 + noise(province.id * 7, 10), 42, 96)),
    wind_speed: Number((4 + noise(province.id * 11 + hourOffset, 10)).toFixed(1)),
    precipitation: noise(province.id * 13 + hourOffset, 1) > 0.78 ? Number(noise(province.id * 17, 20).toFixed(1)) : 0,
    pm2_5: pm25,
    pm10: Number((pm25 * 1.45 + noise(province.id * 19, 15)).toFixed(1)),
    aqi,
    no2: Number((aqi * 0.26 + noise(province.id * 23, 8)).toFixed(1)),
    ozone: Number((28 + Math.max(0, dailyWave) * 38 + noise(province.id * 29, 12)).toFixed(1)),
    uv_index: Number(clamp((province.region === 'South' ? 6 : 3) + dailyWave * 4, 0, 11).toFixed(1)),
    anomaly_score: Number((isAnomaly ? 0.72 + noise(province.id * 31, 0.2) : 0.12 + noise(province.id * 37, 0.28)).toFixed(2)),
    is_anomaly: isAnomaly,
    raw_json: { source: 'mock_fallback', deterministic: true },
  };
}

export const MOCK_ENV_DATA: EnvironmentalData[] = PROVINCES.map((province) => generateMockReading(province));

export const MOCK_HISTORY: EnvironmentalData[] = Array.from({ length: 24 }).map((_, hour) => {
  const hanoi = PROVINCES[0];
  const reading = generateMockReading(hanoi, hour - 23);
  const rushHourBoost = hour >= 7 && hour <= 9 ? 36 : hour >= 17 && hour <= 20 ? 48 : 0;
  const nightRelief = hour <= 5 ? -22 : 0;
  const aqi = Math.round(clamp(78 + rushHourBoost + nightRelief + noise(hour + 101, 12), 18, 220));
  const pm25 = Number((aqi * 0.45).toFixed(1));

  return {
    ...reading,
    time: `${hour.toString().padStart(2, '0')}:00`,
    aqi,
    pm2_5: pm25,
    pm10: Number((pm25 * 1.5).toFixed(1)),
    anomaly_score: aqi > 150 ? 0.82 : 0.24,
    is_anomaly: aqi > 150,
  };
});

const DEFAULT_ANOMALY: AnomalyPayload = {
  score: 0,
  label: 'NORMAL',
  strict_alert: false,
};

const DEFAULT_FORECAST: ForecastPayload = {
  values: MOCK_HISTORY.slice(-12).map((row) => row.aqi),
  lower: MOCK_HISTORY.slice(-12).map((row) => Math.max(0, row.aqi - 12)),
  upper: MOCK_HISTORY.slice(-12).map((row) => Math.min(500, row.aqi + 12)),
  model_family: 'mock',
};

export function getMockProvinceDetail(provinceId: number): ProvinceDetail {
  const province = PROVINCES.find((item) => item.id === provinceId) ?? PROVINCES[0];
  const current = MOCK_ENV_DATA.find((item) => item.province_id === province.id) ?? generateMockReading(province);
  const history = MOCK_HISTORY.map((row, index) => {
    const scale = clamp(current.aqi / 105, 0.55, 1.9);
    const offset = (index % 5) - 2;
    return {
      ...row,
      province_id: province.id,
      province_name: province.name,
      aqi: Math.round(clamp(row.aqi * scale + offset * 3, 0, 300)),
      pm2_5: Number(clamp(row.pm2_5 * scale, 0, 220).toFixed(1)),
      temperature: Number((row.temperature - 23 + current.temperature).toFixed(1)),
      humidity: Math.round(clamp(row.humidity - 72 + current.humidity, 20, 100)),
    };
  });

  return {
    province: provinceToSummary(province, current),
    current,
    history,
    anomaly: current.is_anomaly
      ? { score: current.anomaly_score ?? 0, label: 'ANOMALY', strict_alert: current.aqi >= 150 }
      : DEFAULT_ANOMALY,
    forecast: DEFAULT_FORECAST,
    data_source: 'fallback',
    inference_source: 'mock',
    updated_at: current.time,
  };
}

export function getMockProvinceSummaries(): ProvinceSummary[] {
  return PROVINCES.map((province) => {
    const current = MOCK_ENV_DATA.find((item) => item.province_id === province.id) ?? generateMockReading(province);
    return provinceToSummary(province, current);
  });
}

export function getMockInsight(provinceId: number): InsightPayload {
  const detail = getMockProvinceDetail(provinceId);
  const aqi = detail.current.aqi;
  const isRisky = aqi > 120;

  return {
    text: `AQI ${aqi} tại ${detail.province.name_vi} đang ở mức ${isRisky ? 'cần chú ý' : 'ổn định'}.`,
    health_advice: isRisky
      ? 'Hạn chế hoạt động ngoài trời kéo dài và ưu tiên khẩu trang lọc bụi mịn.'
      : 'Có thể sinh hoạt bình thường, tiếp tục theo dõi nếu thời tiết thay đổi.',
    recommended_actions: [
      isRisky ? 'Bật máy lọc không khí trong phòng kín.' : 'Mở cửa thông gió khi chỉ số duy trì tốt.',
      'Theo dõi biến động PM2.5 trong giờ cao điểm.',
      'Ưu tiên tuyến đường ít xe nếu phải di chuyển ngoài trời.',
    ],
    risk_level: isRisky ? 'moderate' : 'low',
    source: 'mock',
    cached: false,
  };
}

export function getMockAnomalies(): AnomalyRecord[] {
  return getMockProvinceSummaries()
    .filter((summary) => summary.current?.is_anomaly)
    .slice(0, 8)
    .map((summary) => ({
      province: summary,
      reading: summary.current as EnvironmentalData,
    }));
}

export function getMockSummary(): SummaryPayload {
  const readings = MOCK_ENV_DATA;
  const aqiAvg = readings.reduce((sum, row) => sum + row.aqi, 0) / readings.length;
  const pm25Avg = readings.reduce((sum, row) => sum + row.pm2_5, 0) / readings.length;
  return {
    aqi_avg: Number(aqiAvg.toFixed(1)),
    pm25_avg: Number(pm25Avg.toFixed(1)),
    aqi_warning_count: readings.filter((row) => row.aqi >= 150).length,
    ai_anomaly_count: readings.filter((row) => row.is_anomaly).length,
    warning_count: readings.filter((row) => row.aqi >= 150).length,
    anomaly_count: readings.filter((row) => row.is_anomaly).length,
    province_count: PROVINCES.length,
    latest_time: readings[0]?.time ?? null,
  };
}

export function getMockCompare(provinceIds: number[] = [1, 2, 4], days = 7, metric: MetricKey = 'aqi'): CompareResponse {
  return {
    metric,
    days,
    provinces: provinceIds.map((provinceId) => {
      const detail = getMockProvinceDetail(provinceId);
      return {
        province: detail.province,
        current: detail.current,
        history: detail.history,
        anomaly: detail.anomaly,
        radar: {
          aqi: detail.current.aqi,
          pm2_5: detail.current.pm2_5,
          pm10: detail.current.pm10,
          no2: detail.current.no2,
          ozone: detail.current.ozone,
          uv_index: detail.current.uv_index,
        },
      };
    }),
  };
}
