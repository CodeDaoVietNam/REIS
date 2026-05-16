import { useMemo, useState, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import { Activity, AlertTriangle, Brain, Gauge, Radio, ShieldAlert, Wind, X } from 'lucide-react';
import { AqiGauge } from '@/src/components/AqiGauge';
import { ForecastBandChart } from '@/src/components/ForecastBandChart';
import { InsightCard } from '@/src/components/InsightCard';
import { KeyFindings } from '@/src/components/KeyFindings';
import { KpiCard } from '@/src/components/KpiCard';
import { VietnamLiveMap } from '@/src/components/VietnamLiveMap';
import { useInsight, useInsightSummary, useProvinceDetail, useProvinces, useSummary } from '@/src/hooks/useAQIData';
import { useWebSocket } from '@/src/hooks/useWebSocket';
import { cn, formatFixed, getAQIColor, getAQILabel, safeNumber } from '@/src/lib/utils';
import type { ProvinceSummary } from '@/src/types';

type DrilldownType = 'aqi' | 'anomaly' | null;

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedProvinceId = normalizeProvinceId(searchParams.get('province')) ?? 1;
  const [drilldown, setDrilldown] = useState<DrilldownType>(null);
  const provincesQuery = useProvinces();
  const summaryQuery = useSummary();
  const insightSummaryQuery = useInsightSummary();
  const detailQuery = useProvinceDetail(selectedProvinceId, 48);
  const insightQuery = useInsight(selectedProvinceId);
  const realtime = useWebSocket();

  const liveSummaries = realtime.lastMessage?.provinces ?? [];
  const summaries = liveSummaries.length ? liveSummaries : provincesQuery.data;
  const selectedSummary = summaries.find((province) => province.province_id === selectedProvinceId);
  const selectedCurrent = selectedSummary?.current ?? detailQuery.data.current;
  const latestTime = summaryQuery.data.latest_time ?? selectedCurrent.time;
  const selectedAqi = safeNumber(selectedCurrent.aqi);
  const selectedAnomalyScore = safeNumber(detailQuery.data.anomaly.score, safeNumber(selectedCurrent.anomaly_score));
  const selectedStrictAlert = detailQuery.data.anomaly.strict_alert || detailQuery.data.anomaly.label !== 'NORMAL';
  const hasLiveWebSocketData = Boolean(liveSummaries.length);
  const isUsingFallback = sourceIsMock(provincesQuery.source, summaryQuery.source, hasLiveWebSocketData);
  const hasModelAnomalyScore = detailQuery.source === 'api' && detailQuery.data.inference_source !== 'default';
  const selectedAnomalyScoreDisplay = hasModelAnomalyScore ? selectedAnomalyScore.toFixed(2) : 'N/A';
  const sourceLabel = liveSummaries.length
    ? 'LIVE WS/API'
    : provincesQuery.source === 'api' && summaryQuery.source === 'api'
      ? 'LIVE API'
      : 'MOCK FALLBACK';
  const realtimeLabel = realtime.isConnected ? 'Realtime connected' : 'Realtime polling/fallback';
  const aqiWarningCount = safeNumber(summaryQuery.data.aqi_warning_count ?? summaryQuery.data.warning_count);
  const aiAnomalyCount = safeNumber(summaryQuery.data.ai_anomaly_count ?? summaryQuery.data.anomaly_count);
  const aqiWarnings = useMemo(
    () => summaries
      .filter((province) => safeNumber(province.current?.aqi) >= 150)
      .sort((left, right) => safeNumber(right.current?.aqi) - safeNumber(left.current?.aqi)),
    [summaries],
  );
  const aiAnomalies = useMemo(
    () => summaries
      .filter((province) => Boolean(province.current?.is_anomaly) || safeNumber(province.current?.anomaly_score) >= 0.7)
      .sort((left, right) => safeNumber(right.current?.anomaly_score) - safeNumber(left.current?.anomaly_score)),
    [summaries],
  );
  const activeDrilldownItems = drilldown === 'aqi' ? aqiWarnings : drilldown === 'anomaly' ? aiAnomalies : [];

  const provinceOptions = useMemo(
    () => summaries.map((province) => ({ id: province.province_id, name: province.name_vi })),
    [summaries],
  );

  function selectProvince(provinceId: number) {
    setSearchParams({ province: String(provinceId) });
  }

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-8">
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-[0.28em] text-primary">National live command center</p>
          <h1 className="text-4xl font-black tracking-tight">Dashboard</h1>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-on-surface-variant">
            <span className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 font-mono text-xs font-bold text-primary">
              {sourceLabel}
            </span>
            <span className="rounded-full border border-outline-variant/30 bg-surface-container-high px-3 py-1 font-mono text-xs">
              {realtimeLabel}
            </span>
            <span>Cập nhật: {new Date(latestTime).toLocaleString('vi-VN')}</span>
          </div>
          {isUsingFallback && (provincesQuery.error || summaryQuery.error) && (
            <p className="mt-2 text-xs font-mono text-warning">API chưa sẵn sàng, UI đang dùng fallback an toàn.</p>
          )}
          <p className="mt-2 max-w-3xl text-xs text-on-surface-variant">
            AQI warnings = tỉnh có AQI từ 150 trở lên. AI anomalies = pattern bất thường do model phát hiện, có thể khác với cảnh báo AQI.
          </p>
        </div>

        <label className="flex flex-col gap-2 text-xs font-mono uppercase tracking-widest text-on-surface-variant">
          Tỉnh đang xem
          <select
            value={selectedProvinceId}
            onChange={(event) => selectProvince(Number(event.target.value))}
            className="min-w-64 rounded-2xl border border-outline-variant bg-surface-container-high px-4 py-3 text-base font-bold normal-case tracking-normal text-on-surface outline-none transition focus:border-primary"
          >
            {provinceOptions.map((province) => (
              <option key={province.id} value={province.id} className="bg-surface text-on-surface">
                {province.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <KpiCard
          label="Tổng quan AQI"
          value={Math.round(summaryQuery.data.aqi_avg)}
          suffix={getAQILabel(summaryQuery.data.aqi_avg)}
          icon={<Gauge className="h-5 w-5" />}
          tone={summaryQuery.data.aqi_avg > 150 ? 'text-error' : 'text-primary'}
        />
        <KpiCard
          label="PM2.5 trung bình"
          value={formatFixed(summaryQuery.data.pm25_avg, 1)}
          suffix="µg/m³"
          icon={<Wind className="h-5 w-5" />}
          tone="text-secondary"
        />
        <KpiCard
          label="AQI warnings"
          value={aqiWarningCount}
          suffix={`/ ${summaryQuery.data.province_count}`}
          icon={<ShieldAlert className="h-5 w-5" />}
          tone="text-warning"
          onClick={() => setDrilldown((current) => current === 'aqi' ? null : 'aqi')}
          hint="Click để xem tỉnh"
        />
        <KpiCard
          label="AI anomalies"
          value={aiAnomalyCount}
          suffix={`/ ${summaryQuery.data.province_count}`}
          icon={<AlertTriangle className="h-5 w-5" />}
          tone={aiAnomalyCount > 0 ? 'text-error' : 'text-primary'}
          onClick={() => setDrilldown((current) => current === 'anomaly' ? null : 'anomaly')}
          hint="Click để xem tỉnh"
        />
      </motion.div>

      {drilldown && (
        <DrilldownPanel
          type={drilldown}
          items={activeDrilldownItems}
          selectedProvinceId={selectedProvinceId}
          onClose={() => setDrilldown(null)}
          onSelectProvince={(provinceId) => {
            selectProvince(provinceId);
            setDrilldown(null);
          }}
        />
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <VietnamLiveMap
            summaries={summaries}
            selectedProvinceId={selectedProvinceId}
            onSelectProvince={selectProvince}
            compact
          />
        </div>

        <aside className="flex flex-col gap-6 xl:col-span-4">
          <AqiGauge aqi={selectedAqi} label={detailQuery.data.province.name_vi} />
          <ForecastBandChart
            history={detailQuery.data.history}
            forecast={detailQuery.data.forecast}
            metric="aqi"
            title="48h history of AQI / 12h forecast"
          />
          <InsightCard
            insight={insightQuery.data}
            loading={insightQuery.loading}
            source={insightQuery.source}
            updatedAt={selectedCurrent.time}
          />
        </aside>
      </div>

      <div className="mt-6">
        <KeyFindings
          payload={insightSummaryQuery.data}
          loading={insightSummaryQuery.loading}
          source={insightSummaryQuery.source}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <InfoStrip icon={<Activity className="h-5 w-5" />} label="AQI hiện tại" value={`${Math.round(selectedAqi)} AQI`} />
        <InfoStrip
          icon={<Brain className="h-5 w-5" />}
          label={selectedStrictAlert ? 'Anomaly score - alert' : 'Anomaly score - normal'}
          value={selectedAnomalyScoreDisplay}
        />
        <InfoStrip icon={<Radio className="h-5 w-5" />} label="Nguồn realtime" value={realtime.error ? 'WS fallback' : 'WS/API active'} />
      </div>
    </div>
  );
}

function normalizeProvinceId(value: string | null) {
  const provinceId = Number(value);
  return Number.isInteger(provinceId) && provinceId >= 1 && provinceId <= 63 ? provinceId : null;
}

function DrilldownPanel({
  type,
  items,
  selectedProvinceId,
  onClose,
  onSelectProvince,
}: {
  type: Exclude<DrilldownType, null>;
  items: ProvinceSummary[];
  selectedProvinceId: number;
  onClose: () => void;
  onSelectProvince: (provinceId: number) => void;
}) {
  const title = type === 'aqi' ? 'Danh sách tỉnh AQI warning' : 'Danh sách tỉnh AI anomaly';
  const description = type === 'aqi'
    ? 'Các tỉnh có AQI từ 150 trở lên, cần chú ý sức khỏe.'
    : 'Các tỉnh được model đánh dấu bất thường hoặc score vượt ngưỡng.';

  return (
    <motion.section
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card mb-6 border border-primary/30 p-5"
    >
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-black">{title}</h2>
          <p className="mt-1 text-sm text-on-surface-variant">{description}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full bg-surface-container-highest p-2 text-on-surface-variant transition hover:text-on-surface"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      {items.length === 0 ? (
        <p className="rounded-2xl border border-outline-variant/20 bg-surface-container-low p-4 text-sm text-on-surface-variant">
          Chưa có tỉnh nào thuộc nhóm này trong dữ liệu hiện tại.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {items.slice(0, 18).map((province) => {
            const aqi = safeNumber(province.current?.aqi);
            const anomalyScore = province.current?.anomaly_score;
            const isSelected = province.province_id === selectedProvinceId;
            return (
              <button
                key={province.province_id}
                type="button"
                onClick={() => onSelectProvince(province.province_id)}
                className={cn(
                  'rounded-2xl border p-4 text-left transition hover:border-primary/60 hover:bg-surface-container-high',
                  isSelected ? 'border-primary bg-primary/10' : 'border-outline-variant/25 bg-surface-container-low',
                )}
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <p className="font-black">{province.name_vi}</p>
                    <p className="text-xs font-mono uppercase tracking-wider text-on-surface-variant">{province.region}</p>
                  </div>
                  <span className={cn('font-mono text-lg font-black', getAQIColor(aqi))}>{Math.round(aqi)}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <MetricPill label="PM2.5" value={formatFixed(province.current?.pm2_5, 1)} />
                  <MetricPill label="AQI" value={getAQILabel(aqi)} />
                  <MetricPill label="AI" value={anomalyScore == null ? 'N/A' : safeNumber(anomalyScore).toFixed(2)} />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </motion.section>
  );
}

function MetricPill({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded-xl bg-surface-container-highest/60 px-2 py-2 text-center">
      <span className="block font-mono text-[10px] uppercase tracking-widest text-on-surface-variant">{label}</span>
      <span className="font-bold">{value}</span>
    </span>
  );
}

function sourceIsMock(provinceSource: string, summarySource: string, hasLiveWebSocketData: boolean): boolean {
  return !hasLiveWebSocketData && (provinceSource !== 'api' || summarySource !== 'api');
}

function InfoStrip({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="glass-card flex items-center gap-4 p-5">
      <div className="rounded-2xl bg-primary/10 p-3 text-primary">{icon}</div>
      <div>
        <p className="text-xs font-mono uppercase tracking-widest text-on-surface-variant">{label}</p>
        <p className="text-xl font-black">{value}</p>
      </div>
    </div>
  );
}
