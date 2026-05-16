import type {
  AnomalyRecord,
  ApiProvinceDetail,
  ApiProvinceSummary,
  CompareResponse,
  ForecastPayload,
  InsightSummaryPayload,
  InsightResponse,
  MetricKey,
  SummaryPayload,
} from '@/src/types';

export const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
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
    } catch (error) {
      lastError = error;
      if (attempt < 2) {
        await new Promise((resolve) => setTimeout(resolve, 350 * (attempt + 1)));
      }
    }
  }

  throw lastError instanceof Error ? lastError : new Error(`API ${path} unavailable`);
}

export function getProvinces(): Promise<ApiProvinceSummary[]> {
  return requestJson<ApiProvinceSummary[]>('/api/provinces');
}

export function getProvinceDetail(provinceId: number): Promise<ApiProvinceDetail> {
  return requestJson<ApiProvinceDetail>(`/api/province/${provinceId}`);
}

export function getProvinceDetailWithHours(provinceId: number, hours: number): Promise<ApiProvinceDetail> {
  return requestJson<ApiProvinceDetail>(`/api/province/${provinceId}?hours=${hours}`);
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

export function getSummary(): Promise<SummaryPayload> {
  return requestJson<SummaryPayload>('/api/summary');
}

export function getInsightSummary(): Promise<InsightSummaryPayload> {
  return requestJson<InsightSummaryPayload>('/api/insight-summary');
}

export function getCompare(provinceIds: number[], days: number, metric: MetricKey): Promise<CompareResponse> {
  const ids = provinceIds.join(',');
  return requestJson<CompareResponse>(`/api/compare?province_ids=${ids}&days=${days}&metric=${metric}`);
}

export function getProvinceReportUrl(provinceId: number, hours = 48): string {
  return buildApiUrl(`/api/report/province/${provinceId}.pdf?hours=${hours}`);
}

export function getCompareReportUrl(provinceIds: number[], days: number, metric: MetricKey): string {
  const ids = provinceIds.join(',');
  return buildApiUrl(`/api/report/compare.pdf?province_ids=${ids}&days=${days}&metric=${metric}`);
}

export function getInsightReportUrl(): string {
  return buildApiUrl('/api/report/insights.pdf');
}
