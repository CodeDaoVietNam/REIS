import type {
  AnomalyRecord,
  ApiProvinceDetail,
  ApiProvinceSummary,
  ForecastPayload,
  InsightResponse,
} from '@/src/types';

export const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API ${path} failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getProvinces(): Promise<ApiProvinceSummary[]> {
  return requestJson<ApiProvinceSummary[]>('/api/provinces');
}

export function getProvinceDetail(provinceId: number): Promise<ApiProvinceDetail> {
  return requestJson<ApiProvinceDetail>(`/api/province/${provinceId}`);
}

export function getForecast(provinceId: number): Promise<ForecastPayload> {
  return requestJson<ForecastPayload>(`/api/forecast/${provinceId}`);
}

export function getInsight(provinceId: number): Promise<InsightResponse> {
  return requestJson<InsightResponse>(`/api/insights/${provinceId}`);
}

export function getAnomalies(): Promise<AnomalyRecord[]> {
  return requestJson<AnomalyRecord[]>('/api/anomalies');
}
