import { useMemo, useState, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Activity, CalendarDays, MapPin, SlidersHorizontal, TrendingUp } from 'lucide-react';
import { ForecastBandChart } from '@/src/components/ForecastBandChart';
import { KpiCard } from '@/src/components/KpiCard';
import { useProvinceDetail, useProvinces } from '@/src/hooks/useAQIData';
import { cn, safeNumber } from '@/src/lib/utils';
import type { EnvironmentalData, MetricKey } from '@/src/types';

const ranges = [
  { label: 'Last 24h', hours: 24 },
  { label: 'Last 7 days', hours: 168 },
  { label: 'Last 30 days', hours: 720 },
];

const metrics: Array<{ key: MetricKey; label: string }> = [
  { key: 'aqi', label: 'AQI' },
  { key: 'pm2_5', label: 'PM2.5' },
  { key: 'temperature', label: 'Temperature' },
];

const metricLabels: Record<MetricKey, string> = {
  aqi: 'AQI',
  pm2_5: 'PM2.5',
  pm10: 'PM10',
  temperature: 'Temperature',
  humidity: 'Humidity',
  wind_speed: 'Wind Speed',
};

export default function Analytics() {
  const [selectedProvinceId, setSelectedProvinceId] = useState(1);
  const [rangeHours, setRangeHours] = useState(168);
  const [metric, setMetric] = useState<MetricKey>('aqi');
  const provinceQuery = useProvinces();
  const detailQuery = useProvinceDetail(selectedProvinceId, rangeHours);
  const current = detailQuery.data.current;
  const history = detailQuery.data.history;
  const activeRange = ranges.find((range) => range.hours === rangeHours) ?? ranges[1];
  const anomalyScore = safeNumber(detailQuery.data.anomaly.score, safeNumber(current.anomaly_score));
  const isAiAnomaly = detailQuery.data.anomaly.strict_alert || detailQuery.data.anomaly.label !== 'NORMAL';

  const topProvinces = useMemo(
    () => provinceQuery.data
      .filter((province) => province.current)
      .map((province) => ({
        name: province.name_vi.replace('Tinh ', '').replace('Thanh pho ', ''),
        value: safeNumber(province.current?.[metric]),
      }))
      .sort((left, right) => right.value - left.value)
      .slice(0, 10),
    [provinceQuery.data, metric],
  );

  const calendarCells = useMemo(() => buildCalendarCells(history, metric), [history, metric]);
  const radarData = [
    { subject: 'AQI', value: safeNumber(current.aqi) },
    { subject: 'PM2.5', value: safeNumber(current.pm2_5) },
    { subject: 'PM10', value: safeNumber(current.pm10) },
    { subject: 'NO2', value: safeNumber(current.no2) },
    { subject: 'Ozone', value: safeNumber(current.ozone) },
    { subject: 'UV', value: safeNumber(current.uv_index) * 10 },
  ];
  const pollutantData = [
    { name: 'Good', value: history.filter((row) => row.aqi <= 50).length, color: '#4edea3' },
    { name: 'Moderate', value: history.filter((row) => row.aqi > 50 && row.aqi <= 100).length, color: '#f8d66d' },
    { name: 'Unhealthy', value: history.filter((row) => row.aqi > 100 && row.aqi <= 150).length, color: '#ff9f43' },
    { name: 'Very Unhealthy', value: history.filter((row) => row.aqi > 150).length, color: '#fc7c78' },
  ];

  return (
    <div className="mx-auto max-w-[1600px] px-6 py-8">
      <div className="mb-8">
        <p className="mb-2 text-xs font-mono uppercase tracking-[0.28em] text-primary">Forecast analytics lab</p>
        <h1 className="text-4xl font-black tracking-tight">Analytics</h1>
        {detailQuery.error && <p className="mt-2 text-xs font-mono text-warning">API fallback đang bật cho tỉnh này.</p>}
        {detailQuery.loading && <p className="mt-2 text-xs font-mono text-secondary">Đang tải history/forecast từ API...</p>}
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <FilterBox icon={<MapPin className="h-5 w-5" />}>
          <select
            value={selectedProvinceId}
            onChange={(event) => setSelectedProvinceId(Number(event.target.value))}
            className="w-full bg-transparent text-lg font-bold outline-none"
          >
            {provinceQuery.data.map((province) => (
              <option key={province.province_id} value={province.province_id} className="bg-surface">
                Province: {province.name_vi}
              </option>
            ))}
          </select>
        </FilterBox>
        <FilterBox icon={<CalendarDays className="h-5 w-5" />}>
          <select
            value={rangeHours}
            onChange={(event) => setRangeHours(Number(event.target.value))}
            className="w-full bg-transparent text-lg font-bold outline-none"
          >
            {ranges.map((range) => (
              <option key={range.hours} value={range.hours} className="bg-surface">
                {range.label}
              </option>
            ))}
          </select>
        </FilterBox>
        <FilterBox icon={<SlidersHorizontal className="h-5 w-5" />}>
          <select
            value={metric}
            onChange={(event) => setMetric(event.target.value as MetricKey)}
            className="w-full bg-transparent text-lg font-bold outline-none"
          >
            {metrics.map((item) => (
              <option key={item.key} value={item.key} className="bg-surface">
                {item.label}
              </option>
            ))}
          </select>
        </FilterBox>
      </div>

      <motion.div
        key={`${selectedProvinceId}-${rangeHours}-${metric}`}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <KpiCard label={`${metricLabels[metric]} hiện tại`} value={formatMetric(current, metric)} icon={<Activity className="h-5 w-5" />} />
        <KpiCard label="AQI hiện tại" value={Math.round(current.aqi)} suffix="AQI" tone={current.aqi > 150 ? 'text-error' : 'text-primary'} />
        <KpiCard label="AI anomaly score" value={anomalyScore.toFixed(2)} tone={isAiAnomaly ? 'text-error' : 'text-secondary'} />
        <KpiCard label="Khoảng dữ liệu" value={activeRange.label} icon={<TrendingUp className="h-5 w-5" />} tone="text-on-surface" />
      </motion.div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12">
          <ForecastBandChart
            history={history}
            forecast={detailQuery.data.forecast}
            metric={metric}
            title={`${metricLabels[metric]} history + forecast confidence band`}
          />
        </div>

        <Panel className="xl:col-span-6" title="Daily AQI Calendar">
          <div className="mb-4 flex justify-end gap-2 text-xs font-mono text-on-surface-variant">
            <span>Avg:</span>
            <span className="h-3 w-8 rounded bg-primary" />
            <span className="h-3 w-8 rounded bg-warning" />
            <span className="h-3 w-8 rounded bg-error" />
          </div>
          <div className="grid grid-cols-7 gap-2">
            {calendarCells.map((cell) => (
              <div
                key={cell.label}
                className={cn('rounded-xl p-3 text-center font-bold text-surface shadow-sm', heatColor(cell.value))}
                title={`${cell.label}: ${safeNumber(cell.value).toFixed(1)}`}
              >
                {cell.day}
              </div>
            ))}
          </div>
        </Panel>

        <Panel className="xl:col-span-6" title="Top 10 Provinces">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topProvinces}>
                <XAxis dataKey="name" stroke="#86948a" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#86948a" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#161d19', border: '1px solid #3c4a42', borderRadius: 12 }} />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {topProvinces.map((entry) => (
                    <Cell key={entry.name} fill={entry.value > 150 ? '#fc7c78' : entry.value > 100 ? '#ff9f43' : '#4edea3'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel className="xl:col-span-6" title="Radar profile">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#3c4a42" />
                <PolarAngleAxis dataKey="subject" stroke="#bbcabf" fontSize={11} />
                <Radar dataKey="value" stroke="#4edea3" fill="#4edea3" fillOpacity={0.35} />
                <Tooltip contentStyle={{ backgroundColor: '#161d19', border: '1px solid #3c4a42', borderRadius: 12 }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel className="xl:col-span-6" title="AQI distribution">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pollutantData} dataKey="value" outerRadius={120} innerRadius={48} paddingAngle={3}>
                  {pollutantData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#161d19', border: '1px solid #3c4a42', borderRadius: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 text-xs font-mono">
            {pollutantData.map((entry) => (
              <span key={entry.name} className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: entry.color }} />
                {entry.name}
              </span>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function FilterBox({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <div className="glass-card flex items-center gap-3 rounded-3xl p-4">
      <div className="rounded-2xl bg-surface-container-highest p-3 text-primary">{icon}</div>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

function Panel({ title, className, children }: { title: string; className?: string; children: ReactNode }) {
  return (
    <section className={cn('glass-card p-6', className)}>
      <h2 className="mb-5 text-xl font-black">{title}</h2>
      {children}
    </section>
  );
}

function formatMetric(row: EnvironmentalData, metric: MetricKey): string {
  const value = safeNumber(row[metric]);
  if (metric === 'temperature') return `${value.toFixed(1)}°C`;
  if (metric === 'humidity') return `${value.toFixed(0)}%`;
  if (metric === 'wind_speed') return `${value.toFixed(1)} km/h`;
  return metric === 'aqi' ? Math.round(value).toString() : value.toFixed(1);
}

function buildCalendarCells(history: EnvironmentalData[], metric: MetricKey) {
  const byDate = new Map<string, number[]>();
  history.forEach((row) => {
    const date = new Date(row.time);
    const label = Number.isNaN(date.getTime()) ? row.time.slice(0, 10) : date.toISOString().slice(0, 10);
    const values = byDate.get(label) ?? [];
    values.push(safeNumber(row[metric]));
    byDate.set(label, values);
  });

  return Array.from(byDate.entries()).slice(-35).map(([label, values]) => {
    const date = new Date(label);
    const day = Number.isNaN(date.getTime()) ? label.slice(-2) : date.getDate().toString();
    const value = values.reduce((sum, item) => sum + item, 0) / Math.max(1, values.length);
    return { label, day, value };
  });
}

function heatColor(value: number): string {
  if (value > 150) return 'bg-error';
  if (value > 100) return 'bg-warning';
  if (value > 50) return 'bg-tertiary-container';
  return 'bg-primary';
}
