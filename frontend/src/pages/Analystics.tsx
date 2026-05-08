import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MOCK_ENV_DATA, MOCK_HISTORY, PROVINCES } from '@/src/types';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ScatterChart, Scatter, ZAxis, ComposedChart, Area, Line, PieChart, Pie, Cell } from 'recharts';
import { BarChart3, TrendingUp, Filter, Download, Box, Zap, MapPin, Search, Activity, Droplets } from 'lucide-react';
import { cn } from '@/src/lib/utils';

export default function Analytics() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProvinceId, setSelectedProvinceId] = useState<number>(1); // Mặc định Hà Nội

  const filteredProvinces = PROVINCES.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    p.en_name.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const currentProvince = PROVINCES.find(p => p.id === selectedProvinceId) || PROVINCES[0];
  const currentData = MOCK_ENV_DATA.find(d => d.province_id === selectedProvinceId) || MOCK_ENV_DATA[0];

  // Tạo dữ liệu lịch sử động dựa trên tỉnh đang chọn để biểu đồ trông hợp lý
  const dynamicHistory = MOCK_HISTORY.map(d => ({
    ...d,
    aqi: Math.round(d.aqi * (currentData.aqi / 150) + (Math.random() - 0.5) * 10),
    pm2_5: Math.round(d.pm2_5 * (currentData.pm2_5 / 80)),
    temperature: Number((d.temperature - 25 + currentData.temperature).toFixed(1)),
    humidity: Math.min(100, Math.max(0, d.humidity - 70 + currentData.humidity))
  }));

  const radarData = [
    { subject: 'Nhiệt độ', A: currentData.temperature * 4, fullMark: 150 },
    { subject: 'Độ ẩm', A: currentData.humidity, fullMark: 100 },
    { subject: 'Gió', A: currentData.wind_speed * 5, fullMark: 100 },
    { subject: 'UV', A: currentData.uv_index * 10, fullMark: 100 },
    { subject: 'PM2.5', A: currentData.pm2_5, fullMark: 200 },
    { subject: 'Ozone', A: currentData.ozone, fullMark: 150 },
  ];

  const correlationData = dynamicHistory.map(d => ({
    x: d.temperature,
    y: d.aqi,
    z: d.pm2_5 * 2
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
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
        <div>
          <h1 className="text-4xl font-bold flex items-center gap-3">
            Phân tích Chuyên sâu
            <span className="bg-primary/20 text-primary border border-primary/30 px-2 py-1 rounded text-xs font-mono uppercase tracking-widest">Pro Mode</span>
          </h1>
          <p className="text-on-surface-variant mt-2">Dữ liệu hiện tại: <strong className="text-primary">{currentProvince.name}</strong></p>
        </div>
        <div className="flex flex-col md:flex-row gap-3 relative">
          {/* Search Box */}
          <div className="relative">
            <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant" />
            <input 
              type="text" 
              placeholder="Tìm kiếm tỉnh/thành phố..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 pr-4 py-3 bg-surface-container-high border border-outline-variant rounded-2xl w-full md:w-[300px] text-on-surface focus:border-primary focus:outline-none transition-all shadow-lg"
            />
            {searchQuery && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-surface-container-highest border border-outline-variant rounded-2xl max-h-[300px] overflow-y-auto z-50 shadow-2xl custom-scrollbar">
                {filteredProvinces.map(p => (
                  <button 
                    key={p.id}
                    onClick={() => { setSelectedProvinceId(p.id); setSearchQuery(''); }}
                    className="w-full text-left px-4 py-3 hover:bg-primary/20 transition-colors border-b border-outline-variant/10 last:border-0 flex justify-between items-center"
                  >
                    <div>
                      <span className="font-bold">{p.name}</span>
                      <span className="text-xs text-on-surface-variant ml-2">({p.en_name})</span>
                    </div>
                    <span className="text-[10px] uppercase font-mono px-2 py-1 bg-surface-container-low rounded-md">{p.region}</span>
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

      {/* Mini Dashboard cho tỉnh đang chọn */}
      <motion.div 
        key={selectedProvinceId}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      >
        <div className="glass-card p-6 border-primary/20">
          <p className="text-xs font-mono text-on-surface-variant mb-1 uppercase tracking-widest">AQI Hiện tại</p>
          <div className="flex items-end gap-2">
            <span className="text-4xl font-bold tracking-tighter">{Math.round(currentData.aqi)}</span>
            <span className={cn("font-bold mb-1", currentData.aqi > 100 ? "text-error" : "text-primary")}>
              {currentData.aqi > 100 ? "Ô Nhiễm" : "Tốt"}
            </span>
          </div>
        </div>
        <div className="glass-card p-6">
          <p className="text-xs font-mono text-on-surface-variant mb-1 uppercase tracking-widest">Nhiệt độ</p>
          <div className="flex items-center gap-2">
            <span className="text-4xl font-bold tracking-tighter">{currentData.temperature.toFixed(1)}°C</span>
          </div>
        </div>
        <div className="glass-card p-6">
          <p className="text-xs font-mono text-on-surface-variant mb-1 uppercase tracking-widest">Bất thường (AI)</p>
          <div className="flex items-center gap-2">
            <span className="text-4xl font-bold tracking-tighter">{currentData.anomaly_score.toFixed(2)}</span>
            {currentData.is_anomaly && <Zap className="w-5 h-5 text-warning animate-pulse" />}
          </div>
        </div>
        <div className="glass-card p-6">
          <p className="text-xs font-mono text-on-surface-variant mb-1 uppercase tracking-widest">UV Index</p>
          <div className="flex items-center gap-2">
            <span className="text-4xl font-bold tracking-tighter">{currentData.uv_index.toFixed(1)}</span>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Temporal Flux Chart */}
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

        {/* Cấu thành ô nhiễm (Pie Chart) */}
        <div className="md:col-span-4 glass-card p-8 flex flex-col">
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <Activity className="w-6 h-6 text-warning" />
            Cấu thành Ô nhiễm
          </h2>
          <div className="flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pollutantData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {pollutantData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1a211d', border: '1px solid #3c4a42', borderRadius: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {pollutantData.map(d => (
              <div key={d.name} className="flex items-center gap-2 text-xs font-mono uppercase">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
                {d.name}
              </div>
            ))}
          </div>
        </div>

        {/* Variable Correlation Radar */}
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

        {/* District Comparison */}
        <div className="md:col-span-4 glass-card p-8">
          <h2 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-secondary" />
            Khu vực nội bộ
          </h2>
          <div className="space-y-6">
            {districtComparison.map((d, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm font-mono text-on-surface-variant mb-2">
                  <span>{d.name}</span>
                  <span className="font-bold text-on-surface">AQI: {Math.round(d.aqi)}</span>
                </div>
                <div className="w-full bg-surface-container-highest h-3 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, (d.aqi / 300) * 100)}%` }}
                    className="h-full rounded-full" 
                    style={{ backgroundColor: d.color }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Anomaly Detection Scatter */}
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
