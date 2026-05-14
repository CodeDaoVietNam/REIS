import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { EnvironmentalData, ForecastPayload, MetricKey } from '@/src/types';

const metricLabels: Record<MetricKey, string> = {
  aqi: 'AQI',
  pm2_5: 'PM2.5',
  pm10: 'PM10',
  temperature: 'Temperature',
  humidity: 'Humidity',
  wind_speed: 'Wind',
};

function metricValue(row: EnvironmentalData, metric: MetricKey): number {
  return Number(row[metric] ?? 0);
}

function labelTime(value: string): string {
  if (/^\d{2}:/.test(value)) return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

export function ForecastBandChart({
  history,
  forecast,
  metric = 'aqi',
  title = '48h history / forecast',
}: {
  history: EnvironmentalData[];
  forecast?: ForecastPayload;
  metric?: MetricKey;
  title?: string;
}) {
  const historyRows = history.slice(-48).map((row) => ({
    label: labelTime(row.time),
    actual: metricValue(row, metric),
  }));
  const base = historyRows.at(-1)?.actual ?? 0;
  const forecastRows = (forecast?.values ?? []).slice(0, 12).map((value, index) => ({
    label: `+${index + 1}h`,
    forecast: metric === 'aqi' ? value : base,
    upper: metric === 'aqi' ? forecast?.upper?.[index] : base * 1.08,
    lower: metric === 'aqi' ? forecast?.lower?.[index] : base * 0.92,
  }));
  const data = [...historyRows, ...forecastRows];

  return (
    <div className="glass-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-bold">{title}</h3>
        <span className="text-xs font-mono text-on-surface-variant">{metricLabels[metric]}</span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4edea3" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#4edea3" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ffb4ab" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#ffb4ab" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#344139" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" stroke="#86948a" fontSize={10} tickLine={false} axisLine={false} />
            <YAxis stroke="#86948a" fontSize={10} tickLine={false} axisLine={false} width={34} />
            <Tooltip contentStyle={{ backgroundColor: '#161d19', border: '1px solid #3c4a42', borderRadius: 12 }} />
            <Area type="monotone" dataKey="actual" stroke="#4edea3" strokeWidth={2.5} fill="url(#actualGradient)" connectNulls />
            <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#forecastGradient)" connectNulls />
            <Line type="monotone" dataKey="forecast" stroke="#ffb4ab" strokeDasharray="5 5" strokeWidth={2.5} dot={false} connectNulls />
            <Line type="monotone" dataKey="lower" stroke="#ffb4ab" strokeOpacity={0.35} strokeWidth={1} dot={false} connectNulls />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
