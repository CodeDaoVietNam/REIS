import { useMemo, useState, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, Brain, Gauge, Radio, ShieldAlert, Wind } from 'lucide-react';
import { AqiGauge } from '@/src/components/AqiGauge';
import { ForecastBandChart } from '@/src/components/ForecastBandChart';
import { InsightCard } from '@/src/components/InsightCard';
import { KpiCard } from '@/src/components/KpiCard';
import { VietnamLiveMap } from '@/src/components/VietnamLiveMap';
import { useInsight, useProvinceDetail, useProvinces, useSummary } from '@/src/hooks/useAQIData';
import { useWebSocket } from '@/src/hooks/useWebSocket';
import { formatFixed, getAQILabel, safeNumber } from '@/src/lib/utils';

export default function Dashboard() {
  const [selectedProvinceId, setSelectedProvinceId] = useState(1);
  const provincesQuery = useProvinces();
  const summaryQuery = useSummary();
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
  const sourceLabel = liveSummaries.length
    ? 'LIVE WS/API'
    : provincesQuery.source === 'api' && summaryQuery.source === 'api'
      ? 'LIVE API'
      : 'MOCK FALLBACK';
  const realtimeLabel = realtime.isConnected ? 'Realtime connected' : 'Realtime polling/fallback';
  const aqiWarningCount = safeNumber(summaryQuery.data.aqi_warning_count ?? summaryQuery.data.warning_count);
  const aiAnomalyCount = safeNumber(summaryQuery.data.ai_anomaly_count ?? summaryQuery.data.anomaly_count);

  const provinceOptions = useMemo(
    () => summaries.map((province) => ({ id: province.province_id, name: province.name_vi })),
    [summaries],
  );

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
          {(provincesQuery.error || summaryQuery.error) && (
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
            onChange={(event) => setSelectedProvinceId(Number(event.target.value))}
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
        />
        <KpiCard
          label="AI anomalies"
          value={aiAnomalyCount}
          suffix={`/ ${summaryQuery.data.province_count}`}
          icon={<AlertTriangle className="h-5 w-5" />}
          tone={aiAnomalyCount > 0 ? 'text-error' : 'text-primary'}
        />
      </motion.div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <VietnamLiveMap
            summaries={summaries}
            selectedProvinceId={selectedProvinceId}
            onSelectProvince={setSelectedProvinceId}
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

      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <InfoStrip icon={<Activity className="h-5 w-5" />} label="AQI hiện tại" value={`${Math.round(selectedAqi)} AQI`} />
        <InfoStrip
          icon={<Brain className="h-5 w-5" />}
          label={selectedStrictAlert ? 'Anomaly score - alert' : 'Anomaly score - normal'}
          value={selectedAnomalyScore.toFixed(2)}
        />
        <InfoStrip icon={<Radio className="h-5 w-5" />} label="Nguồn realtime" value={realtime.error ? 'WS fallback' : 'WS/API active'} />
      </div>
    </div>
  );
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
