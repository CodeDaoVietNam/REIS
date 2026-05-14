export type Region = 'North' | 'Central' | 'South';
export type BackendRegion = 'Bac' | 'Trung' | 'Nam' | string;

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
  raw_json?: Record<string, unknown>;
}

export interface Province {
  id: number;
  name: string;
  en_name: string;
  lat: number;
  lng: number;
  region: Region;
}

export interface ProvinceMeta {
  province_id: number;
  name_vi: string;
  name_en: string;
  latitude: number;
  longitude: number;
  region: BackendRegion;
}

export interface ForecastPayload {
  province_id?: number;
  values: number[];
  lower: number[];
  upper: number[];
  model_family: string;
}

export interface AnomalyPayload {
  score: number;
  label: string;
  strict_alert: boolean;
}

export interface ProvinceSummary extends ProvinceMeta {
  current: EnvironmentalData | null;
}

export interface ApiProvinceSummary extends ProvinceMeta {
  current: Partial<EnvironmentalData> | null;
}

export interface ProvinceDetail {
  province: ProvinceMeta;
  current: EnvironmentalData;
  history: EnvironmentalData[];
  anomaly: AnomalyPayload;
  forecast: ForecastPayload;
}

export interface ApiProvinceDetail {
  province: ProvinceMeta;
  current: Partial<EnvironmentalData> | null;
  history: Array<Partial<EnvironmentalData>>;
  anomaly: Partial<AnomalyPayload>;
  forecast: Partial<ForecastPayload>;
}

export interface InsightPayload {
  text?: string;
  summary?: string;
  health_advice?: string;
  recommended_actions?: string[];
  recommendations?: string[];
  risk_level?: string;
  source?: string;
  cached?: boolean;
}

export interface InsightResponse {
  province_id: number;
  insight: InsightPayload;
}

export interface AnomalyRecord {
  province: ProvinceMeta;
  reading: EnvironmentalData;
}

export interface AIAdvice {
  status: string;
  warning: string;
  recommendations: string[];
}

export interface LiveUpdateMessage {
  type: 'live_update';
  timestamp: string;
  provinces: ProvinceSummary[];
}
