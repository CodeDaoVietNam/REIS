import { useEffect, useState } from 'react';
import {
  getAnomalies,
  getCompare,
  getInsight,
  getProvinceDetail,
  getProvinceDetailWithHours,
  getProvinces,
  getSummary,
} from '@/src/services/apiClient';
import {
  getMockAnomalies,
  getMockCompare,
  getMockInsight,
  getMockProvinceDetail,
  getMockProvinceSummaries,
  getMockSummary,
} from '@/src/mocks/mockData';
import type {
  AnomalyPayload,
  AnomalyRecord,
  ApiProvinceDetail,
  ApiProvinceSummary,
  CompareResponse,
  EnvironmentalData,
  ForecastPayload,
  InsightPayload,
  MetricKey,
  ProvinceDetail,
  ProvinceMeta,
  ProvinceSummary,
  SummaryPayload,
} from '@/src/types';

type DataSource = 'api' | 'mock';

interface QueryState<T> {
  data: T;
  loading: boolean;
  error: string | null;
  source: DataSource;
}

function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function toNullableNumber(value: unknown, fallback: number | null = null): number | null {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function normalizeReading(
  reading: Partial<EnvironmentalData> | null | undefined,
  province: ProvinceMeta,
  fallback?: EnvironmentalData,
): EnvironmentalData {
  const source = reading ?? fallback ?? {};
  const sourceRecord = source as Partial<EnvironmentalData> & {
    temp?: unknown;
    o3?: unknown;
    rainfall?: unknown;
  };

  return {
    time: String(sourceRecord.time ?? fallback?.time ?? new Date().toISOString()),
    province_id: toNumber(sourceRecord.province_id, province.province_id),
    province_name: String(sourceRecord.province_name ?? province.name_vi),
    temperature: toNumber(sourceRecord.temperature ?? sourceRecord.temp, fallback?.temperature ?? 0),
    humidity: toNumber(sourceRecord.humidity, fallback?.humidity ?? 0),
    wind_speed: toNumber(sourceRecord.wind_speed, fallback?.wind_speed ?? 0),
    precipitation: toNumber(sourceRecord.precipitation ?? sourceRecord.rainfall, fallback?.precipitation ?? 0),
    pm2_5: toNumber(sourceRecord.pm2_5, fallback?.pm2_5 ?? 0),
    pm10: toNumber(sourceRecord.pm10, fallback?.pm10 ?? 0),
    aqi: toNumber(sourceRecord.aqi, fallback?.aqi ?? 0),
    no2: toNumber(sourceRecord.no2, fallback?.no2 ?? 0),
    ozone: toNumber(sourceRecord.ozone ?? sourceRecord.o3, fallback?.ozone ?? 0),
    uv_index: toNumber(sourceRecord.uv_index, fallback?.uv_index ?? 0),
    anomaly_score: toNullableNumber(sourceRecord.anomaly_score, fallback?.anomaly_score ?? null),
    is_anomaly: Boolean(sourceRecord.is_anomaly ?? fallback?.is_anomaly ?? false),
    raw_json: sourceRecord.raw_json ?? fallback?.raw_json ?? {},
  };
}

function normalizeAnomaly(payload: Partial<AnomalyPayload> | undefined, fallback: AnomalyPayload): AnomalyPayload {
  return {
    score: toNumber(payload?.score, fallback.score),
    label: String(payload?.label ?? fallback.label),
    strict_alert: Boolean(payload?.strict_alert ?? fallback.strict_alert),
  };
}

function normalizeForecast(payload: Partial<ForecastPayload> | undefined, fallback: ForecastPayload): ForecastPayload {
  return {
    province_id: payload?.province_id ?? fallback.province_id,
    values: payload?.values?.length ? payload.values : fallback.values,
    lower: payload?.lower?.length ? payload.lower : fallback.lower,
    upper: payload?.upper?.length ? payload.upper : fallback.upper,
    model_family: payload?.model_family ?? fallback.model_family,
  };
}

function normalizeSummaryPayload(payload: Partial<SummaryPayload>): SummaryPayload {
  const fallback = getMockSummary();
  const aqiWarningCount = toNumber(payload.aqi_warning_count ?? payload.warning_count, fallback.aqi_warning_count);
  const aiAnomalyCount = toNumber(payload.ai_anomaly_count ?? payload.anomaly_count, fallback.ai_anomaly_count);

  return {
    aqi_avg: toNumber(payload.aqi_avg, fallback.aqi_avg),
    pm25_avg: toNumber(payload.pm25_avg, fallback.pm25_avg),
    aqi_warning_count: aqiWarningCount,
    ai_anomaly_count: aiAnomalyCount,
    warning_count: aqiWarningCount,
    anomaly_count: aiAnomalyCount,
    province_count: toNumber(payload.province_count, fallback.province_count),
    latest_time: payload.latest_time ?? fallback.latest_time,
  };
}

function normalizeSummary(summary: ApiProvinceSummary): ProvinceSummary {
  const fallback = getMockProvinceDetail(summary.province_id);
  return {
    ...summary,
    current: summary.current ? normalizeReading(summary.current, summary, fallback.current) : fallback.current,
  };
}

function normalizeDetail(payload: ApiProvinceDetail, provinceId: number): ProvinceDetail {
  const fallback = getMockProvinceDetail(provinceId);
  const province = payload.province ?? fallback.province;
  const current = normalizeReading(payload.current, province, fallback.current);
  const history = payload.history?.length
    ? payload.history.map((row) => normalizeReading(row, province, fallback.current))
    : fallback.history;

  return {
    province,
    current,
    history,
    anomaly: normalizeAnomaly(payload.anomaly, fallback.anomaly),
    forecast: normalizeForecast(payload.forecast, fallback.forecast),
    data_source: payload.data_source ?? fallback.data_source,
    inference_source: payload.inference_source ?? fallback.inference_source,
    updated_at: payload.updated_at ?? current.time,
  };
}

export function useProvinces(): QueryState<ProvinceSummary[]> {
  const [state, setState] = useState<QueryState<ProvinceSummary[]>>({
    data: getMockProvinceSummaries(),
    loading: true,
    error: null,
    source: 'mock',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const provinces = await getProvinces();
        if (!cancelled) {
          setState({
            data: provinces.map(normalizeSummary),
            loading: false,
            error: null,
            source: 'api',
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: getMockProvinceSummaries(),
            loading: false,
            error: error instanceof Error ? error.message : 'API unavailable',
            source: 'mock',
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export function useProvinceDetail(provinceId: number, hours = 48): QueryState<ProvinceDetail> {
  const fallback = getMockProvinceDetail(provinceId);
  const [state, setState] = useState<QueryState<ProvinceDetail>>({
    data: fallback,
    loading: true,
    error: null,
    source: 'mock',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const detail = hours === 48
          ? await getProvinceDetail(provinceId)
          : await getProvinceDetailWithHours(provinceId, hours);
        if (!cancelled) {
          setState({
            data: normalizeDetail(detail, provinceId),
            loading: false,
            error: null,
            source: 'api',
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: getMockProvinceDetail(provinceId),
            loading: false,
            error: error instanceof Error ? error.message : 'API unavailable',
            source: 'mock',
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [provinceId, hours]);

  if (state.data.province.province_id !== provinceId) {
    return {
      data: fallback,
      loading: true,
      error: null,
      source: 'mock',
    };
  }

  return state;
}

export function useInsight(provinceId: number): QueryState<InsightPayload> {
  const fallback = getMockInsight(provinceId);
  const [state, setState] = useState<QueryState<InsightPayload> & { provinceId: number }>({
    data: fallback,
    loading: true,
    error: null,
    source: 'mock',
    provinceId,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await getInsight(provinceId);
        if (!cancelled) {
          setState({
            data: response.insight,
            loading: false,
            error: null,
            source: 'api',
            provinceId,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: getMockInsight(provinceId),
            loading: false,
            error: error instanceof Error ? error.message : 'API unavailable',
            source: 'mock',
            provinceId,
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [provinceId]);

  if (state.provinceId !== provinceId) {
    return {
      data: fallback,
      loading: true,
      error: null,
      source: 'mock',
    };
  }

  return state;
}

export function useAnomalies(): QueryState<AnomalyRecord[]> {
  const [state, setState] = useState<QueryState<AnomalyRecord[]>>({
    data: getMockAnomalies(),
    loading: true,
    error: null,
    source: 'mock',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const anomalies = await getAnomalies();
        if (!cancelled) {
          setState({
            data: anomalies,
            loading: false,
            error: null,
            source: 'api',
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: getMockAnomalies(),
            loading: false,
            error: error instanceof Error ? error.message : 'API unavailable',
            source: 'mock',
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export function useSummary(): QueryState<SummaryPayload> {
  const [state, setState] = useState<QueryState<SummaryPayload>>({
    data: getMockSummary(),
    loading: true,
    error: null,
    source: 'mock',
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const summary = await getSummary();
        if (!cancelled) {
          setState({ data: normalizeSummaryPayload(summary), loading: false, error: null, source: 'api' });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: getMockSummary(),
            loading: false,
            error: error instanceof Error ? error.message : 'API unavailable',
            source: 'mock',
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export function useCompare(
  provinceIds: number[],
  days: number,
  metric: MetricKey,
): QueryState<CompareResponse> {
  const key = provinceIds.join(',');
  const fallback = getMockCompare(provinceIds, days, metric);
  const [state, setState] = useState<QueryState<CompareResponse> & { key: string; days: number; metric: MetricKey }>({
    data: fallback,
    loading: true,
    error: null,
    source: 'mock',
    key,
    days,
    metric,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const ids = key.split(',').map(Number).filter(Number.isFinite);
      try {
        const compare = await getCompare(ids, days, metric);
        if (!cancelled) {
          setState({ data: compare, loading: false, error: null, source: 'api', key, days, metric });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            data: getMockCompare(ids, days, metric),
            loading: false,
            error: error instanceof Error ? error.message : 'API unavailable',
            source: 'mock',
            key,
            days,
            metric,
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [key, days, metric]);

  if (state.key !== key || state.days !== days || state.metric !== metric) {
    return { data: fallback, loading: true, error: null, source: 'mock' };
  }

  return state;
}
