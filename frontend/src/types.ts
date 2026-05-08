export interface EnvironmentalData {
  time: string;
  province_id: number;
  province_name: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  precipitation: number;
  pm2_5: number;
  pm10: number;
  aqi: number;
  no2: number;
  ozone: number;
  uv_index: number;
  anomaly_score: number;
  is_anomaly: boolean;
  raw_json?: any;
}

export interface Province {
  id: number;
  name: string;
  en_name: string;
  lat: number;
  lng: number;
  region: 'North' | 'Central' | 'South';
}

export const PROVINCES: Province[] = [
    { id: 1, name: "Hà Nội", en_name: "Hanoi", lat: 21.0285, lng: 105.8542, region: "North" },
    { id: 2, name: "Hồ Chí Minh", en_name: "Ho Chi Minh", lat: 10.7769, lng: 106.7009, region: "South" },
    { id: 3, name: "Hải Phòng", en_name: "Hai Phong", lat: 20.8623, lng: 106.6799, region: "North" },
    { id: 4, name: "Đà Nẵng", en_name: "Da Nang", lat: 16.0544, lng: 108.2022, region: "Central" },
    { id: 5, name: "Hà Giang", en_name: "Ha Giang", lat: 22.8279, lng: 104.9823, region: "North" },
    { id: 6, name: "Cao Bằng", en_name: "Cao Bang", lat: 22.6761, lng: 106.2016, region: "North" },
    { id: 7, name: "Lai Châu", en_name: "Lai Chau", lat: 22.3862, lng: 103.4702, region: "North" },
    { id: 8, name: "Lào Cai", en_name: "Lao Cai", lat: 22.4962, lng: 103.9680, region: "North" },
    { id: 9, name: "Tuyên Quang", en_name: "Tuyen Quang", lat: 21.8212, lng: 105.1833, region: "North" },
    { id: 10, name: "Lạng Sơn", en_name: "Lang Son", lat: 22.1398, lng: 105.8320, region: "North" },
    { id: 11, name: "Bắc Kạn", en_name: "Bac Kan", lat: 22.1398, lng: 105.8320, region: "North" },
    { id: 12, name: "Thái Nguyên", en_name: "Thai Nguyen", lat: 21.5954, lng: 105.8387, region: "North" },
    { id: 13, name: "Yên Bái", en_name: "Yen Bai", lat: 21.7049, lng: 104.8791, region: "North" },
    { id: 14, name: "Sơn La", en_name: "Son La", lat: 21.3270, lng: 103.9144, region: "North" },
    { id: 15, name: "Phú Thọ", en_name: "Phu Tho", lat: 21.3135, lng: 105.3946, region: "North" },
    { id: 16, name: "Vĩnh Phúc", en_name: "Vinh Phuc", lat: 21.3079, lng: 105.5965, region: "North" },
    { id: 17, name: "Quảng Ninh", en_name: "Quang Ninh", lat: 20.9489, lng: 107.1035, region: "North" },
    { id: 18, name: "Bắc Giang", en_name: "Bac Giang", lat: 21.2804, lng: 106.1985, region: "North" },
    { id: 19, name: "Bắc Ninh", en_name: "Bac Ninh", lat: 21.2816, lng: 106.1989, region: "North" },
    { id: 20, name: "Hải Dương", en_name: "Hai Duong", lat: 20.9411, lng: 106.3330, region: "North" },
    { id: 21, name: "Hưng Yên", en_name: "Hung Yen", lat: 20.6626, lng: 106.0585, region: "North" },
    { id: 22, name: "Hòa Bình", en_name: "Hoa Binh", lat: 20.8199, lng: 105.3438, region: "North" },
    { id: 23, name: "Hà Nam", en_name: "Ha Nam", lat: 20.5514, lng: 105.9171, region: "North" },
    { id: 24, name: "Nam Định", en_name: "Nam Dinh", lat: 20.4272, lng: 106.1749, region: "North" },
    { id: 25, name: "Thái Bình", en_name: "Thai Binh", lat: 20.4480, lng: 106.3435, region: "North" },
    { id: 26, name: "Ninh Bình", en_name: "Ninh Binh", lat: 20.2573, lng: 105.9719, region: "North" },
    { id: 27, name: "Thanh Hóa", en_name: "Thanh Hoa", lat: 19.7996, lng: 105.7864, region: "North" },
    { id: 28, name: "Nghệ An", en_name: "Nghe An", lat: 18.6596, lng: 105.6970, region: "Central" },
    { id: 29, name: "Hà Tĩnh", en_name: "Ha Tinh", lat: 18.3393, lng: 105.9029, region: "Central" },
    { id: 30, name: "Quảng Bình", en_name: "Quang Binh", lat: 19.6868, lng: 105.7875, region: "Central" },
    { id: 31, name: "Quảng Trị", en_name: "Quang Tri", lat: 16.7468, lng: 107.1877, region: "Central" },
    { id: 32, name: "Thừa Thiên Huế", en_name: "Thua Thien Hue", lat: 16.4639, lng: 107.5863, region: "Central" },
    { id: 33, name: "Quảng Nam", en_name: "Quang Nam", lat: 15.5752, lng: 108.4743, region: "Central" },
    { id: 34, name: "Quảng Ngãi", en_name: "Quang Ngai", lat: 14.3512, lng: 108.0027, region: "Central" },
    { id: 35, name: "Kon Tum", en_name: "Kon Tum", lat: 13.8865, lng: 109.1133, region: "Central" },
    { id: 36, name: "Gia Lai", en_name: "Gia Lai", lat: 13.7700, lng: 109.2318, region: "Central" },
    { id: 37, name: "Bình Định", en_name: "Binh Dinh", lat: 13.0467, lng: 109.3108, region: "Central" },
    { id: 38, name: "Phú Yên", en_name: "Phu Yen", lat: 13.0467, lng: 109.3108, region: "Central" },
    { id: 39, name: "Đắk Lắk", en_name: "Dak Lak", lat: 12.6797, lng: 108.0447, region: "Central" },
    { id: 40, name: "Đắk Nông", en_name: "Dak Nong", lat: 12.0006, lng: 107.6960, region: "Central" },
    { id: 41, name: "Lâm Đồng", en_name: "Lam Dong", lat: 11.9402, lng: 108.4376, region: "Central" },
    { id: 42, name: "Bình Phước", en_name: "Binh Phuoc", lat: 11.5314, lng: 106.8943, region: "South" },
    { id: 43, name: "Tây Ninh", en_name: "Tay Ninh", lat: 10.9460, lng: 106.1900, region: "South" },
    { id: 44, name: "Bình Dương", en_name: "Binh Duong", lat: 11.2943, lng: 106.6750, region: "South" },
    { id: 45, name: "Đồng Nai", en_name: "Dong Nai", lat: 10.9508, lng: 106.8221, region: "South" },
    { id: 46, name: "Bình Thuận", en_name: "Binh Thuan", lat: 10.9378, lng: 108.0912, region: "South" },
    { id: 47, name: "Khánh Hòa", en_name: "Khanh Hoa", lat: 11.2349, lng: 109.1941, region: "Central" },
    { id: 48, name: "Ninh Thuận", en_name: "Ninh Thuan", lat: 11.5770, lng: 108.9865, region: "Central" },
    { id: 49, name: "Long An", en_name: "Long An", lat: 10.5389, lng: 106.4061, region: "South" },
    { id: 50, name: "Đồng Tháp", en_name: "Dong Thap", lat: 10.3585, lng: 106.3643, region: "South" },
    { id: 51, name: "An Giang", en_name: "An Giang", lat: 10.3904, lng: 105.4344, region: "South" },
    { id: 52, name: "Bà Rịa - Vũng Tàu", en_name: "Ba Ria Vung Tau", lat: 10.4963, lng: 107.1688, region: "South" },
    { id: 53, name: "Tiền Giang", en_name: "Tien Giang", lat: 10.3606, lng: 106.3658, region: "South" },
    { id: 54, name: "Kiên Giang", en_name: "Kien Giang", lat: 9.9356, lng: 106.3416, region: "South" },
    { id: 55, name: "Cần Thơ", en_name: "Can Tho", lat: 10.0362, lng: 105.7873, region: "South" },
    { id: 56, name: "Hậu Giang", en_name: "Hau Giang", lat: 9.7832, lng: 105.4670, region: "South" },
    { id: 57, name: "Vĩnh Long", en_name: "Vinh Long", lat: 9.9356, lng: 106.3416, region: "South" },
    { id: 58, name: "Bến Tre", en_name: "Ben Tre", lat: 10.2315, lng: 106.3599, region: "South" },
    { id: 59, name: "Trà Vinh", en_name: "Tra Vinh", lat: 9.9356, lng: 106.3416, region: "South" },
    { id: 60, name: "Sóc Trăng", en_name: "Soc Trang", lat: 9.6025, lng: 105.9731, region: "South" },
    { id: 61, name: "Bạc Liêu", en_name: "Bac Lieu", lat: 9.2869, lng: 105.7228, region: "South" },
    { id: 62, name: "Cà Mau", en_name: "Ca Mau", lat: 9.1762, lng: 105.1508, region: "South" },
    { id: 63, name: "Điện Biên", en_name: "Dien Bien", lat: 21.3924, lng: 103.0160, region: "North" }
];

// Hàm nội suy sinh dữ liệu thực tế hơn thay vì random hoàn toàn
const generateRealisticData = (province: Province): EnvironmentalData => {
  const isNorth = province.region === 'North';
  const isSouth = province.region === 'South';
  
  // Miền Bắc thường ô nhiễm hơn vào mùa đông/xuân
  const baseAQI = isNorth ? 120 : isSouth ? 60 : 80; 
  const aqiVariance = (Math.random() - 0.5) * 40;
  let currentAqi = Math.max(10, Math.round(baseAQI + aqiVariance));
  
  // Đặc thù một số tỉnh công nghiệp
  if (['Hà Nội', 'Bắc Ninh', 'Hưng Yên'].includes(province.name)) {
    currentAqi += 40 + Math.random() * 50;
  }

  const tempBase = isNorth ? 22 : isSouth ? 32 : 28;
  const temp = tempBase + (Math.random() - 0.5) * 5;

  // AQI tương quan với PM2.5 (PM2.5 x 2 ~ AQI)
  const pm25 = currentAqi * 0.4 + Math.random() * 10;
  
  const isAnomaly = currentAqi > 180 || temp > 38 || currentAqi < 20;

  return {
    time: new Date().toISOString(),
    province_id: province.id,
    province_name: province.name,
    temperature: temp,
    humidity: isNorth ? 75 + Math.random() * 20 : 60 + Math.random() * 25,
    wind_speed: 3 + Math.random() * 15,
    precipitation: Math.random() > 0.8 ? Math.random() * 20 : 0, // 20% có mưa
    pm2_5: pm25,
    pm10: pm25 * 1.5 + Math.random() * 20,
    aqi: currentAqi,
    no2: currentAqi * 0.3 + Math.random() * 10,
    ozone: 30 + Math.random() * 60,
    uv_index: isSouth ? 6 + Math.random() * 4 : 3 + Math.random() * 5,
    anomaly_score: isAnomaly ? 0.8 + Math.random() * 0.2 : Math.random() * 0.4,
    is_anomaly: isAnomaly,
    raw_json: { source: "sensor_network_v1", status: "ok" }
  };
};

export const MOCK_ENV_DATA: EnvironmentalData[] = PROVINCES.map(generateRealisticData);

// Sinh lịch sử 24h có tính chu kỳ (nhiệt độ cao vào buổi trưa, AQI cao vào giờ cao điểm)
export const MOCK_HISTORY: EnvironmentalData[] = Array.from({ length: 24 }).map((_, i) => {
  // i là giờ trong ngày (0-23)
  const hour = i;
  
  // Nhiệt độ: dạng hình sin, thấp nhất lúc 4h sáng, cao nhất lúc 14h chiều
  const tempWave = Math.sin(((hour - 8) / 24) * Math.PI * 2);
  const temp = 25 + tempWave * 6; // Biến thiên từ 19 đến 31 độ
  
  // AQI: Cao vào giờ cao điểm đi làm (7h-9h) và tan tầm (17h-19h)
  let aqiBase = 80;
  if (hour >= 7 && hour <= 9) aqiBase += 50;
  if (hour >= 17 && hour <= 20) aqiBase += 70;
  // Ban đêm AQI giảm dần
  if (hour >= 0 && hour <= 5) aqiBase -= 20;
  
  const aqi = aqiBase + (Math.random() - 0.5) * 15;
  const pm25 = aqi * 0.45;

  return {
    time: `${hour.toString().padStart(2, '0')}:00`,
    province_id: 1,
    province_name: 'Hà Nội',
    temperature: temp,
    humidity: 85 - tempWave * 20, // Nắng lên thì độ ẩm giảm
    wind_speed: 5 + Math.random() * 5,
    precipitation: 0,
    pm2_5: pm25,
    pm10: pm25 * 1.5,
    aqi: Math.round(aqi),
    no2: aqi * 0.3,
    ozone: 20 + tempWave * 30, // Ozone sinh ra nhiều khi có nắng gắt
    uv_index: hour >= 8 && hour <= 16 ? Math.max(0, tempWave * 9) : 0,
    anomaly_score: aqi > 150 ? 0.8 : 0.2,
    is_anomaly: aqi > 150,
  };
});
