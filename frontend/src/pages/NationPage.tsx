import { useMemo, useState, type ReactNode } from 'react';
import { Activity, Globe, Radio, TrendingUp, Wind } from 'lucide-react';
import { VietnamLiveMap } from '@/src/components/VietnamLiveMap';
import { useProvinces } from '@/src/hooks/useAQIData';
import { useWebSocket } from '@/src/hooks/useWebSocket';
import { cn, formatFixed, getAQIColor, safeNumber } from '@/src/lib/utils';
import type { ProvinceSummary } from '@/src/types';

export default function NationalMap() {
  const [selectedProvinceId, setSelectedProvinceId] = useState(1);
  const provinceQuery = useProvinces();
  const liveQuery = useWebSocket();

  const summaries = liveQuery.lastMessage?.provinces.length ? liveQuery.lastMessage.provinces : provinceQuery.data;
  const ranked = useMemo(
    () => [...summaries]
      .filter((province) => province.current)
      .sort((left, right) => safeNumber(right.current?.aqi) - safeNumber(left.current?.aqi)),
    [summaries],
  );
  const selected = summaries.find((province) => province.province_id === selectedProvinceId) ?? ranked[0];
  const aqiAverage = Math.round(
    summaries.reduce((sum, province) => sum + safeNumber(province.current?.aqi), 0) / Math.max(1, summaries.length),
  );
  const pm25Average = summaries.reduce((sum, province) => sum + safeNumber(province.current?.pm2_5), 0) / Math.max(1, summaries.length);
  const sourceLabel = liveQuery.lastMessage?.provinces.length
    ? 'LIVE WS/API'
    : provinceQuery.source === 'api'
      ? 'LIVE API'
      : 'MOCK FALLBACK';

  return (
    <div className="mx-auto grid min-h-[calc(100vh-80px)] max-w-[1700px] grid-cols-1 gap-6 px-6 py-8 xl:grid-cols-[390px_1fr]">
      <aside className="flex flex-col gap-6">
        <section className="glass-card p-6">
          <h1 className="mb-5 flex items-center gap-2 text-2xl font-black">
            <Globe className="h-6 w-6 text-primary" />
            Bản đồ toàn quốc
          </h1>
          <div className="grid grid-cols-2 gap-3">
            <StatSmall label="AQI Avg" value={aqiAverage.toString()} tone={aqiAverage >= 150 ? 'text-error' : 'text-primary'} />
            <StatSmall label="PM2.5 Avg" value={formatFixed(pm25Average, 1)} tone="text-secondary" />
            <StatSmall label="Nguồn" value={sourceLabel} tone={sourceLabel.includes('MOCK') ? 'text-warning' : 'text-primary'} />
            <StatSmall label="Realtime" value={liveQuery.isConnected ? 'ON' : 'OFF'} tone={liveQuery.isConnected ? 'text-primary' : 'text-warning'} />
          </div>
          {provinceQuery.error && (
            <p className="mt-4 text-xs font-mono text-warning">API chưa sẵn sàng, map đang dùng fallback có nhãn rõ.</p>
          )}
        </section>

        <section className="glass-card flex min-h-0 flex-1 flex-col p-6">
          <h2 className="mb-5 flex items-center gap-2 text-xl font-black">
            <TrendingUp className="h-5 w-5 text-error" />
            Điểm nóng AQI
          </h2>
          <div className="custom-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
            {ranked.slice(0, 16).map((province, index) => (
              <HotspotRow
                key={province.province_id}
                province={province}
                rank={index + 1}
                selected={province.province_id === selectedProvinceId}
                onSelect={() => setSelectedProvinceId(province.province_id)}
              />
            ))}
          </div>
        </section>
      </aside>

      <section className="min-h-[760px]">
        <VietnamLiveMap
          summaries={summaries}
          selectedProvinceId={selected?.province_id ?? selectedProvinceId}
          onSelectProvince={setSelectedProvinceId}
        />
        {selected?.current && (
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <InfoCard icon={<Activity className="h-5 w-5" />} label={selected.name_vi} value={`${Math.round(safeNumber(selected.current.aqi))} AQI`} />
            <InfoCard icon={<Wind className="h-5 w-5" />} label="PM2.5" value={`${formatFixed(selected.current.pm2_5, 1)} µg/m³`} />
            <InfoCard icon={<Radio className="h-5 w-5" />} label="Data source" value={sourceLabel} />
          </div>
        )}
      </section>
    </div>
  );
}

function StatSmall({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-2xl border border-outline-variant/20 bg-surface-container-highest/30 p-4 text-center">
      <span className="mb-1 block text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">{label}</span>
      <span className={cn('block text-lg font-black', tone)}>{value}</span>
    </div>
  );
}

function HotspotRow({
  province,
  rank,
  selected,
  onSelect,
}: {
  province: ProvinceSummary;
  rank: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const aqi = safeNumber(province.current?.aqi);
  return (
    <button
      onClick={onSelect}
      className={cn(
        'w-full rounded-2xl border p-3 text-left transition',
        selected ? 'border-primary bg-primary/10' : 'border-outline-variant/20 bg-surface-container-low hover:bg-surface-container-high',
      )}
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-sm font-bold">
          <span className="mr-2 font-mono text-xs text-on-surface-variant">{rank.toString().padStart(2, '0')}</span>
          {province.name_vi}
        </span>
        <span className={cn('font-mono text-sm font-black', getAQIColor(aqi))}>{Math.round(aqi)} AQI</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-container-highest">
        <div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, (aqi / 300) * 100)}%` }} />
      </div>
    </button>
  );
}

function InfoCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
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
