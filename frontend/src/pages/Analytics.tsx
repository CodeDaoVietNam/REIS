import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Area,
  Bar,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import { Activity, BarChart3, Box, Download, Search, TrendingUp, Zap } from 'lucide-react';
import { PROVINCES } from '@/src/mocks/mockData';
import { useProvinceDetail } from '@/src/hooks/useAQIData';
import { cn } from '@/src/lib/utils';

export default function Analytics() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProvinceId, setSelectedProvinceId] = useState<number>(1);
  const detailQuery = useProvinceDetail(selectedProvinceId);
  const currentProvince = PROVINCES.find((province) => province.id === selectedProvinceId) ?? PROVINCES[0];
  const currentData = detailQuery.data.current;

  const filteredProvinces = PROVINCES.filter((province) =>
    province.name.toLowerCase().includes(searchQuery.toLowerCase())
    || province.en_name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const dynamicHistory = detailQuery.data.history.map((row, index) => {
    const scale = Math.max(0.5, Math.min(1.8, currentData.aqi / 120));
    const deterministicOffset = ((index % 5) - 2) * 2;
    return {
      ...row,
      aqi: Math.round(Math.max(0, Math.min(300, row.aqi * scale + deterministicOffset))),
      pm2_5: Math.round(Math.max(0, row.pm2_5 * Math.max(0.4, currentData.pm2_5 / 60))),
      temperature: Number((row.temperature - 25 + currentData.temperature).toFixed(1)),
      humidity: Math.min(100, Math.max(0, row.humidity - 70 + currentData.humidity)),
    };
  });

  const radarData = [
    { subject: 'Nhiệt độ', A: currentData.temperature * 4, fullMark: 150 },
    { subject: 'Độ ẩm', A: currentData.humidity, fullMark: 100 },
    { subject: 'Gió', A: currentData.wind_speed * 5, fullMark: 100 },
    { subject: 'UV', A: currentData.uv_index * 10, fullMark: 100 },
    { subject: 'PM2.5', A: currentData.pm2_5, fullMark: 200 },
    { subject: 'Ozone', A: currentData.ozone, fullMark: 150 },
  ];

  const correlationData = dynamicHistory.map((row) => ({
    x: row.temperature,
    y: row.aqi,
    z: row.pm2_5 * 2,
  }));

  const districtComparison = [
    { name: 'Trung tâm', aqi: currentData.aqi + 30, color: '#ffb4ab' },
    { name: 'Phía Đông', aqi: currentData.aqi - 15, color: '#ffdad6' },
    { name: 'Khu công nghiệp', aqi: currentData.aqi + 60, color: '#93000a' },
    { name: 'Ngoại thành', aqi: Math.max(20, currentData.aqi - 40), color: '#4edea3' },
    { name: 'Khu sinh thái', aqi: Math.max(10, currentData.aqi - 60), color: '#adc6ff' },
  ];

  const pollutantData = [
    { name: 'PM2.5', value: currentData.pm2_5, color: '#ffb4ab' },
    { name: 'PM10', value: currentData.pm10, color: '#ffdad6' },
    { name: 'NO2', value: currentData.no2, color: '#adc6ff' },
    { name: 'Ozone', value: currentData.ozone, color: '#4edea3' },
  ];

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
        <div>
          <h1 className="text-4xl font-bold flex items-center gap-3">
            Phân tích Chuyên sâu
            <span className="bg-primary/20 text-primary border border-primary/30 px-2 py-1 rounded text-xs font-mono uppercase tracking-widest">
              Pro Mode
            </span>
          </h1>
          <p className="text-on-surface-variant mt-2">
            Dữ liệu hiện tại:{' '}
            <strong className="text-primary">{currentProvince.name}</strong>
            {detailQuery.error && <span className="ml-2 text-xs text-warning">(mock fallback)</span>}
          </p>
        </div>
        <div className="flex flex-col md:flex-row gap-3 relative">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant" />
            <input
              type="text"
              placeholder="Tìm kiếm tỉnh/thành phố..."
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              className="pl-12 pr-4 py-3 bg-surface-container-high border border-outline-variant rounded-2xl w-full md:w-[300px] text-on-surface focus:border-primary focus:outline-none transition-all shadow-lg"
            />
            {searchQuery && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-surface-container-highest border border-outline-variant rounded-2xl max-h-[300px] overflow-y-auto z-50 shadow-2xl custom-scrollbar">
                {filteredProvinces.map((province) => (
                  <button
                    key={province.id}
                    onClick={() => {
                      setSelectedProvinceId(province.id);
                      setSearchQuery('');
                    }}
                    className="w-full text-left px-4 py-3 hover:bg-primary/20 transition-colors border-b border-outline-variant/10 last:border-0 flex justify-between items-center"
                  >
                    <div>
                      <span className="font-bold">{province.name}</span>
                      <span className="text-xs text-on-surface-variant ml-2">({province.en_name})</span>
                    </div>
                    <span className="text-[10px] uppercase font-mono px-2 py-1 bg-surface-container-low rounded-md">{province.region}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button className="bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant text-on-surface px-6 py-3 rounded-2xl transition-all flex items-center gap-2 font-mono text-sm shadow-lg">
            <Download className="w-4 h-4" /> Xuất dữ liệu
          </button>
        </div>
      </div>

      <motion.div
        key={selectedProvinceId}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        <MetricCard label="AQI Hiện tại" value={Math.round(currentData.aqi).toString()} tone={currentData.aqi > 100 ? 'text-error' : 'text-primary'} />
        <MetricCard label="Nhiệt độ" value={`${currentData.temperature.toFixed(1)}°C`} />
        <MetricCard label="Bất thường AI" value={currentData.anomaly_score.toFixed(2)} tone={currentData.is_anomaly ? 'text-warning' : 'text-primary'} />
        <MetricCard label="UV Index" value={currentData.uv_index.toFixed(1)} />
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div className="md:col-span-8 glass-card p-8">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-primary" />
              Biến thiên Ô nhiễm (24h)
            </h2>
          </div>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={dynamicHistory}>
                <XAxis dataKey="time" stroke="#86948a" fontSize={10} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(78, 222, 163, 0.05)' }} contentStyle={{ backgroundColor: '#161d19', border: '1px solid #3c4a42', borderRadius: '12px' }} />
                <Area type="monotone" dataKey="aqi" fill="#adc6ff" stroke="#adc6ff" fillOpacity={0.2} />
                <Bar dataKey="pm2_5" barSize={20} fill="#4edea3" radius={[4, 4, 0, 0]} />
                <Line type="monotone" dataKey="temperature" stroke="#ffb4ab" strokeWidth={3} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="md:col-span-4 glass-card p-8 flex flex-col">
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <Activity className="w-6 h-6 text-warning" />
            Cấu thành Ô nhiễm
          </h2>
          <div className="flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pollutantData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value" stroke="none">
                  {pollutantData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1a211d', border: '1px solid #3c4a42', borderRadius: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {pollutantData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-2 text-xs font-mono uppercase">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                {entry.name}
              </div>
            ))}
          </div>
        </div>

        <div className="md:col-span-4 glass-card p-8 flex flex-col">
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <Zap className="w-6 h-6 text-tertiary-container" />
            Chỉ số đa chiều
          </h2>
          <div className="flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                <PolarGrid stroke="#3c4a42" />
                <PolarAngleAxis dataKey="subject" stroke="#bbcabf" fontSize={10} />
                <Radar name={currentProvince.name} dataKey="A" stroke="#4edea3" fill="#4edea3" fillOpacity={0.4} />
                <Tooltip contentStyle={{ backgroundColor: '#1a211d', border: '1px solid #3c4a42', borderRadius: '12px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="md:col-span-4 glass-card p-8">
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-secondary" />
            Khu vực nội bộ
          </h2>
          <div className="space-y-6">
            {districtComparison.map((district) => (
              <div key={district.name}>
                <div className="flex justify-between text-sm font-mono text-on-surface-variant mb-2">
                  <span>{district.name}</span>
                  <span className="font-bold text-on-surface">AQI: {Math.round(district.aqi)}</span>
                </div>
                <div className="w-full bg-surface-container-highest h-3 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, (district.aqi / 300) * 100)}%` }}
                    className="h-full rounded-full"
                    style={{ backgroundColor: district.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="md:col-span-4 glass-card p-8">
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <Box className="w-6 h-6 text-error" />
            Phân tán Bất thường
          </h2>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <XAxis type="number" dataKey="x" name="Nhiệt độ" unit="°C" stroke="#86948a" fontSize={10} />
                <YAxis type="number" dataKey="y" name="AQI" stroke="#86948a" fontSize={10} />
                <ZAxis type="number" dataKey="z" range={[50, 400]} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1a211d', border: '1px solid #3c4a42', borderRadius: '12px' }} />
                <Scatter name="Dữ liệu điểm" data={correlationData} fill="#ffb4ab" fillOpacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, tone = 'text-on-surface' }: { label: string; value: string; tone?: string }) {
  return (
    <div className="glass-card p-6">
      <p className="text-xs font-mono text-on-surface-variant mb-1 uppercase tracking-widest">{label}</p>
      <div className="flex items-end gap-2">
        <span className="text-4xl font-bold tracking-tighter">{value}</span>
        <span className={cn('font-bold mb-1', tone)}>{tone === 'text-error' ? 'Cảnh báo' : 'Ổn định'}</span>
      </div>
    </div>
  );
}
