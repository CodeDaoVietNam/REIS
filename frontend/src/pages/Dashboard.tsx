import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MOCK_ENV_DATA, MOCK_HISTORY, PROVINCES } from '@/src/types';
import { getAQIColor, getAQIBg, getAQILabel, cn } from '@/src/lib/utils';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Thermometer, Droplets, Wind, Sun, Compass, Activity, Brain, Share2, Plus, AlertTriangle, ShieldCheck, Zap, ShieldAlert, MapPin, Search, Bell, Settings, ChevronRight } from 'lucide-react';
import { getAIEnvironmentalAdvice } from '@/src/services/geminiService';

export default function Dashboard() {
  const [selectedProvinceId, setSelectedProvinceId] = useState(0); // Hanoi (index 0)
  const [isAIReady, setIsAIReady] = useState(false);
  const [aiAdvice, setAiAdvice] = useState<any>(null);

  const data = MOCK_ENV_DATA[selectedProvinceId];
  const province = PROVINCES[selectedProvinceId];

  useEffect(() => {
    async function fetchAIAdvice() {
      setIsAIReady(false);
      const advice = await getAIEnvironmentalAdvice(data);
      setAiAdvice(advice);
      setIsAIReady(true);
    }
    fetchAIAdvice();
  }, [selectedProvinceId]);

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🇻🇳</span>
            <select 
              value={selectedProvinceId}
              onChange={(e) => setSelectedProvinceId(Number(e.target.value))}
              className="text-4xl font-bold text-on-surface bg-transparent border-none focus:ring-0 cursor-pointer hover:text-primary transition-colors appearance-none"
            >
              {PROVINCES.map((p, i) => (
                <option key={p.id} value={i} className="bg-surface-container-high text-lg">
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] font-mono font-bold text-primary">LIVE</span>
            </div>
            <span className="text-on-surface-variant text-sm tracking-tight opacity-70">Cập nhật 2 phút trước</span>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-surface-container-high border border-outline-variant hover:bg-surface-container-highest transition-all group">
            <Share2 className="w-5 h-5 text-on-surface-variant group-hover:text-primary transition-colors" />
            <span className="font-semibold">Chia sẻ</span>
          </button>
          <button className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-primary text-on-primary font-bold hover:brightness-110 transition-all shadow-lg shadow-primary/20">
            <Plus className="w-5 h-5" />
            <span>Ghim vào Dashboard</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Metrics */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          {/* Main Visual AQI */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card p-10 flex flex-col items-center justify-center relative overflow-hidden min-h-[400px]"
          >
            <div className="absolute inset-0 opacity-10 pointer-events-none">
              <img 
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuDAMo_oEKR3zS-SiPsyNq_ut27NNNc5UWJnEIARQ5YeftrI12ZcQbennn4GNXdkxwgDjnZ6_HApSwvO3d205sCui7KncVzSSBSccJl0HGBWLt9AkHPtIxANKhM98npscURIEvgOY-jOvryJMY0iw1Ds252x_nXW0OZ57oWxaTZfKjRKm2zALF-lcWyjC0xhf4Sx62FAXohv9lkp8E3jVB8l-2tUV1ve420_CHBXIIl0mFmeiyvGEWDz1FR1ESQLpPGi6CgXykYhbckj"
                className="w-full h-full object-cover"
                alt="Cityscape"
              />
            </div>
            <div className="relative z-10 text-center">
              <p className="text-[12px] font-mono font-medium text-on-surface-variant mb-6 uppercase tracking-[0.2em]">Chỉ số chất lượng không khí hiện tại</p>
              <div className="relative w-[320px] h-[160px] mx-auto overflow-hidden">
                <div className="aqi-gauge-gradient w-[320px] h-[320px] opacity-90" />
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center w-full">
                  <div className="text-8xl font-bold leading-none tracking-tighter drop-shadow-2xl">{Math.round(data.aqi)}</div>
                </div>
              </div>
              <div className={cn("text-xl font-bold uppercase tracking-widest mt-6", getAQIColor(data.aqi))}>
                {getAQILabel(data.aqi)}
              </div>
            </div>
          </motion.div>

          {/* Detailed Stats Grid */}
          <div className="glass-card p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-secondary" />
              Chỉ số chi tiết
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatChip icon={<Thermometer />} label="NHIỆT ĐỘ" value={`${data.temperature.toFixed(1)}°C`} />
              <StatChip icon={<Droplets />} label="ĐỘ ẨM" value={`${data.humidity.toFixed(0)}%`} colorClass="text-primary" />
              <StatChip icon={<Wind />} label="GIÓ" value={`${data.wind_speed.toFixed(1)} km/h`} />
              <StatChip icon={<Sun />} label="CHỈ SỐ UV" value={`${data.uv_index.toFixed(1)}`} colorClass="text-tertiary-container" />
              <StatChip icon={<Activity />} label="PM2.5" value={`${data.pm2_5.toFixed(1)} µg/m³`} colorClass="text-error" />
              <StatChip icon={<ShieldCheck />} label="OZONE" value={`${data.ozone.toFixed(1)} µg/m³`} colorClass="text-secondary" />
              <StatChip icon={<Brain />} label="BẤT THƯỜNG" value={`${data.anomaly_score.toFixed(2)}`} colorClass="text-tertiary-container" />
              <StatChip icon={<Compass />} label="ÁP SUẤT" value="1012 hPa" />
            </div>
          </div>
        </div>

        {/* Right Column: AI & Forecast */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {/* AI Insight */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-card p-8 border-l-4 border-l-tertiary-container"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Brain className="w-6 h-6 text-tertiary-container" />
                <h3 className="text-xl font-bold font-mono uppercase tracking-tighter">AeroSense AI Insight</h3>
              </div>
              <span className="text-[10px] font-mono font-bold text-tertiary-container px-2 py-1 bg-tertiary-container/10 border border-tertiary-container/20 rounded">LIVE ADVISOR</span>
            </div>
            
            {!isAIReady ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-surface-container-highest rounded w-3/4"></div>
                <div className="h-4 bg-surface-container-highest rounded w-5/6"></div>
                <div className="h-4 bg-surface-container-highest rounded w-2/3"></div>
              </div>
            ) : (
              <>
                <p className="text-on-surface-variant leading-relaxed mb-4">
                  {aiAdvice?.status || `Chỉ số AQI ${data.aqi} tại ${province.name} cho thấy mức độ ô nhiễm cao. Tránh các hoạt động ngoài trời.`}
                </p>
                {aiAdvice?.warning && aiAdvice.warning !== "Không có cảnh báo đặc biệt." && (
                  <div className="flex items-center gap-2 text-error font-medium bg-error/10 p-3 rounded-xl border border-error/20">
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    <span className="text-sm">{aiAdvice.warning}</span>
                  </div>
                )}
                {data.is_anomaly && (
                  <div className="mt-3 flex items-center gap-2 text-primary font-medium bg-primary/10 p-3 rounded-xl border border-primary/20">
                    <Brain className="w-5 h-5" />
                    <span className="text-sm">Tọa độ phát hiện bất thường cục bộ</span>
                  </div>
                )}
              </>
            )}
          </motion.div>

          {/* 12h Forecast */}
          <div className="glass-card p-8 flex-1">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold">Dự báo 24 giờ</h3>
              <div className="flex bg-surface-container-highest/50 rounded-lg p-1 border border-outline-variant/20">
                <button className="px-3 py-1 text-xs font-mono font-bold rounded-md bg-surface-container shadow-sm">AQI</button>
                <button className="px-3 py-1 text-xs font-mono text-on-surface-variant">NHIỆT</button>
              </div>
            </div>
            <div className="h-64 mt-auto">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={MOCK_HISTORY}>
                  <defs>
                    <linearGradient id="colorAqi" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#fc7c78" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#fc7c78" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1a211d', border: '1px solid #3c4a42', borderRadius: '12px' }}
                    itemStyle={{ color: '#4edea3' }}
                  />
                  <Area type="monotone" dataKey="aqi" stroke="#fc7c78" strokeWidth={3} fillOpacity={1} fill="url(#colorAqi)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recommendations */}
          <div className="glass-card p-8">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-primary" />
              Khuyến nghị Sức khỏe
            </h3>
            <div className="space-y-3">
              {!isAIReady ? (
                [1, 2, 3].map(i => (
                  <div key={i} className="h-14 bg-surface-container-high/60 rounded-2xl animate-pulse" />
                ))
              ) : (
                aiAdvice?.recommendations?.map((rec: string, i: number) => (
                  <Recommendation 
                    key={i} 
                    icon={i === 0 ? <Wind /> : i === 1 ? <Zap /> : <ShieldCheck />} 
                    text={rec} 
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatChip({ icon, label, value, colorClass = "text-on-surface" }: { icon: React.ReactNode, label: string, value: string, colorClass?: string }) {
  return (
    <div className="p-4 bg-surface-container-low/50 rounded-2xl border border-outline-variant/10 flex items-center gap-3">
      <div className="p-2 bg-surface-container-highest/50 rounded-xl text-on-surface-variant">
        {React.cloneElement(icon as React.ReactElement, { className: "w-5 h-5" })}
      </div>
      <div>
        <p className="text-[10px] font-mono text-on-surface-variant leading-none mb-1 uppercase tracking-wider">{label}</p>
        <p className={cn("text-lg font-bold leading-none", colorClass)}>{value}</p>
      </div>
    </div>
  );
}

const Recommendation: React.FC<{ icon: React.ReactNode, text: string }> = ({ icon, text }) => {
  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl bg-surface-container-high/60 border border-outline-variant/10">
      <div className="text-secondary">{icon}</div>
      <p className="font-medium text-on-surface">{text}</p>
    </div>
  );
};
