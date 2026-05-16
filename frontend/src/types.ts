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
  anomaly_score: number | null;
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

export type MetricKey = 'aqi' | 'pm2_5' | 'pm10' | 'temperature' | 'humidity' | 'wind_speed';

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
  data_source: 'db' | 'fallback' | string;
  inference_source: 'model' | 'cache' | 'default' | 'fallback' | string;
  updated_at: string | null;
}

export interface ApiProvinceDetail {
  province: ProvinceMeta;
  current: Partial<EnvironmentalData> | null;
  history: Array<Partial<EnvironmentalData>>;
  anomaly: Partial<AnomalyPayload>;
  forecast: Partial<ForecastPayload>;
  data_source?: string;
  inference_source?: string;
  updated_at?: string | null;
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

export interface SummaryPayload {
  aqi_avg: number;
  pm25_avg: number;
  aqi_warning_count: number;
  ai_anomaly_count: number;
  warning_count: number;
  anomaly_count: number;
  province_count: number;
  latest_time: string | null;
}

export interface InsightFinding {
  id: string;
  title: string;
  question: string;
  claim: string;
  evidence: string;
  interpretation: string;
  practical_value: string;
  source: string;
  confidence: string;
}

export interface InsightSummaryPayload {
  generated_at: string;
  source: 'eda_live_hybrid' | 'eda_baseline' | string;
  latest_time: string | null;
  context?: {
    available?: boolean;
    province_count_with_data?: number;
    aqi_warning_count?: number;
  };
  findings: InsightFinding[];
  charts?: {
    top_polluted?: Array<Record<string, unknown>>;
    regional_aqi?: Array<Record<string, unknown>>;
  };
}

export interface CompareProvince {
  province: ProvinceMeta;
  current: EnvironmentalData | null;
  history: EnvironmentalData[];
  anomaly: AnomalyPayload;
  radar: Record<string, number>;
}

export interface CompareResponse {
  metric: MetricKey;
  days: number;
  provinces: CompareProvince[];
}

export interface AnomalyRecord {
  province: ProvinceMeta;
  reading: EnvironmentalData;
  event_type?: 'aqi_warning' | 'ai_anomaly' | 'combined' | 'aqi_or_persisted_anomaly' | string;
  severity?: 'moderate' | 'high' | 'critical' | string;
  reason?: string;
  recommendations?: string[];
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
