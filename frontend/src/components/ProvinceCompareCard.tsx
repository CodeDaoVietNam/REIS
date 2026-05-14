import { Radar, RadarChart, PolarAngleAxis, PolarGrid, ResponsiveContainer, Tooltip } from 'recharts';
import { AqiGauge } from '@/src/components/AqiGauge';
import { cn } from '@/src/lib/utils';
import type { CompareProvince } from '@/src/types';

export function ProvinceCompareCard({ item }: { item: CompareProvince }) {
  const current = item.current;
  const aqi = current?.aqi ?? 0;
  const radarData = [
    { subject: 'AQI', value: item.radar.aqi ?? 0 },
    { subject: 'PM2.5', value: item.radar.pm2_5 ?? 0 },
    { subject: 'PM10', value: item.radar.pm10 ?? 0 },
    { subject: 'NO2', value: item.radar.no2 ?? 0 },
    { subject: 'Ozone', value: item.radar.ozone ?? 0 },
    { subject: 'UV', value: (item.radar.uv_index ?? 0) * 10 },
  ];

  return (
    <div className="glass-card p-5 border border-primary/30">
      <div className="mb-3 flex items-start justify-between">
        <h3 className="text-xl font-black">{item.province.name_vi}</h3>
        <span className={cn('rounded-full px-3 py-1 text-xs font-mono', item.anomaly.label === 'NORMAL' ? 'bg-primary/10 text-primary' : 'bg-error/10 text-error')}>
          {item.anomaly.label}
        </span>
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <AqiGauge aqi={aqi} label="AQI" />
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid stroke="#3c4a42" />
              <PolarAngleAxis dataKey="subject" stroke="#bbcabf" fontSize={10} />
              <Radar dataKey="value" stroke="#4edea3" fill="#4edea3" fillOpacity={0.35} />
              <Tooltip contentStyle={{ backgroundColor: '#1a211d', border: '1px solid #3c4a42', borderRadius: 12 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
