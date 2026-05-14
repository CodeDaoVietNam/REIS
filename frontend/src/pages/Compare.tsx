import { useMemo, useState, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import {
  Area,
  CartesianGrid,
  Line,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { GitCompareArrows, SlidersHorizontal, TimerReset } from 'lucide-react';
import { ProvinceCompareCard } from '@/src/components/ProvinceCompareCard';
import { useCompare, useProvinces } from '@/src/hooks/useAQIData';
import { cn, formatDateLabel, safeNumber } from '@/src/lib/utils';
import type { CompareProvince, MetricKey } from '@/src/types';

const metricOptions: Array<{ key: MetricKey; label: string }> = [
  { key: 'aqi', label: 'AQI' },
  { key: 'pm2_5', label: 'PM2.5' },
  { key: 'temperature', label: 'Temperature' },
  { key: 'wind_speed', label: 'Wind Speed' },
];

const dayOptions = [7, 14, 30];
const colors = ['#4edea3', '#f8d66d', '#ff7b93'];

export default function Compare() {
  const [provinceIds, setProvinceIds] = useState([1, 2, 4]);
  const [days, setDays] = useState(7);
  const [metric, setMetric] = useState<MetricKey>('aqi');
  const provinceQuery = useProvinces();
  const compareQuery = useCompare(provinceIds, days, metric);

  const lineData = useMemo(
    () => buildLineData(compareQuery.data.provinces, metric),
    [compareQuery.data.provinces, metric],
  );

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-8">
      <div className="mb-8 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-[0.28em] text-primary">Multi province cockpit</p>
          <h1 className="text-4xl font-black tracking-tight">Compare</h1>
          <p className="mt-2 text-on-surface-variant">
            So sánh tối đa 3 tỉnh theo lịch sử, radar và bảng heatmap.
            {compareQuery.error && <span className="ml-2 text-xs font-mono text-warning">(mock fallback)</span>}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
          {provinceIds.map((id, index) => (
            <ControlBox key={index}>
              <select
                value={id}
                onChange={(event) => {
                  const next = [...provinceIds];
                  next[index] = Number(event.target.value);
                  setProvinceIds(next);
                }}
                className="w-full bg-transparent font-bold outline-none"
              >
                {provinceQuery.data.map((province) => (
                  <option key={province.province_id} value={province.province_id} className="bg-surface">
                    {province.name_vi}
                  </option>
                ))}
              </select>
            </ControlBox>
          ))}
          <ControlBox icon={<TimerReset className="h-4 w-4" />}>
            <select value={days} onChange={(event) => setDays(Number(event.target.value))} className="w-full bg-transparent font-bold outline-none">
              {dayOptions.map((option) => (
                <option key={option} value={option} className="bg-surface">
                  {option} days
                </option>
              ))}
            </select>
          </ControlBox>
          <ControlBox icon={<SlidersHorizontal className="h-4 w-4" />}>
            <select value={metric} onChange={(event) => setMetric(event.target.value as MetricKey)} className="w-full bg-transparent font-bold outline-none">
              {metricOptions.map((option) => (
                <option key={option.key} value={option.key} className="bg-surface">
                  {option.label}
                </option>
              ))}
            </select>
          </ControlBox>
        </div>
      </div>

      <motion.section
        key={`${provinceIds.join('-')}-${days}-${metric}`}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card mb-6 p-6"
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xl font-black">
            <GitCompareArrows className="h-5 w-5 text-primary" />
            Multi-line trend
          </h2>
          <span className="rounded-full bg-surface-container-highest px-3 py-1 text-xs font-mono uppercase text-on-surface-variant">
            {compareQuery.source === 'api' ? 'API compare' : 'Mock fallback'}
          </span>
        </div>
        <div className="h-[420px]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={lineData}>
              <defs>
                <linearGradient id="compareBackdrop" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4edea3" stopOpacity={0.16} />
                  <stop offset="100%" stopColor="#4edea3" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#344139" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" stroke="#86948a" fontSize={10} tickLine={false} axisLine={false} />
              <YAxis stroke="#86948a" fontSize={10} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#161d19', border: '1px solid #3c4a42', borderRadius: 12 }} />
              <Area dataKey="backdrop" stroke="transparent" fill="url(#compareBackdrop)" />
              {compareQuery.data.provinces.map((province, index) => (
                <Line
                  key={province.province.province_id}
                  type="monotone"
                  dataKey={`p${province.province.province_id}`}
                  name={province.province.name_vi}
                  stroke={colors[index % colors.length]}
                  strokeWidth={3}
                  dot={false}
                  connectNulls
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </motion.section>

      <div className="mb-6 grid grid-cols-1 gap-5 xl:grid-cols-3">
        {compareQuery.data.provinces.map((province) => (
          <ProvinceCompareCard key={province.province.province_id} item={province} />
        ))}
      </div>

      <section className="glass-card overflow-hidden p-6">
        <h2 className="mb-5 text-xl font-black">Heatmap Table</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-separate border-spacing-0 overflow-hidden rounded-2xl text-sm">
            <thead>
              <tr>
                <th className="bg-surface-container-high p-4 text-left font-mono text-on-surface-variant">Metric</th>
                {compareQuery.data.provinces.map((province) => (
                  <th key={province.province.province_id} className="bg-surface-container-high p-4 text-left">
                    {province.province.name_vi}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {heatRows(compareQuery.data.provinces).map((row) => (
                <tr key={row.label}>
                  <td className="border-t border-outline-variant/20 bg-surface-container-high p-4 font-bold">{row.label}</td>
                  {row.values.map((value, index) => (
                    <td
                      key={`${row.label}-${index}`}
                      className={cn('border-t border-outline-variant/20 p-4 text-center font-mono font-bold text-surface', heatColor(row.kind, value))}
                    >
                      {row.format(value)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function ControlBox({ icon, children }: { icon?: ReactNode; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2 rounded-2xl border border-outline-variant bg-surface-container-high px-4 py-3">
      {icon && <span className="text-primary">{icon}</span>}
      {children}
    </div>
  );
}

function buildLineData(provinces: CompareProvince[], metric: MetricKey) {
  const maxRows = Math.max(...provinces.map((province) => province.history.length), 0);
  return Array.from({ length: maxRows }).map((_, index) => {
    const first = provinces[0]?.history[index];
    const label = first ? formatDateLabel(first.time, `${index + 1}`) : `${index + 1}`;
    const row: Record<string, string | number | undefined> = {
      label,
      backdrop: first ? Number(first[metric] ?? 0) : undefined,
    };
    provinces.forEach((province) => {
      row[`p${province.province.province_id}`] = safeNumber(province.history[index]?.[metric]);
    });
    return row;
  });
}

function heatRows(provinces: CompareProvince[]) {
  return [
    {
      label: 'AQI',
      kind: 'aqi',
      values: provinces.map((province) => safeNumber(province.current?.aqi)),
      format: (value: number) => Math.round(value).toString(),
    },
    {
      label: 'PM2.5',
      kind: 'pollutant',
      values: provinces.map((province) => safeNumber(province.current?.pm2_5)),
      format: (value: number) => value.toFixed(1),
    },
    {
      label: 'Temperature',
      kind: 'temperature',
      values: provinces.map((province) => safeNumber(province.current?.temperature)),
      format: (value: number) => `${value.toFixed(1)}°C`,
    },
    {
      label: 'Wind Speed',
      kind: 'wind',
      values: provinces.map((province) => safeNumber(province.current?.wind_speed)),
      format: (value: number) => `${value.toFixed(1)} km/h`,
    },
    {
      label: 'Anomaly Score',
      kind: 'anomaly',
      values: provinces.map((province) => safeNumber(province.anomaly.score)),
      format: (value: number) => value.toFixed(2),
    },
  ];
}

function heatColor(kind: string, value: number): string {
  const threshold = kind === 'temperature' ? 35 : kind === 'wind' ? 25 : kind === 'anomaly' ? 0.7 : kind === 'pollutant' ? 55 : 150;
  if (value >= threshold) return 'bg-error';
  if (value >= threshold * 0.65) return 'bg-warning';
  return 'bg-primary';
}
