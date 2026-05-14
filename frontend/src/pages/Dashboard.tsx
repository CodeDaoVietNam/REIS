import { cloneElement, useState, type ReactElement, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Area, AreaChart, ResponsiveContainer, Tooltip } from 'recharts';
import {
  Activity,
  AlertTriangle,
  Brain,
  Compass,
  Droplets,
  Plus,
  Share2,
  ShieldAlert,
  ShieldCheck,
  Sun,
  Thermometer,
  Wind,
  Zap,
} from 'lucide-react';
import { PROVINCES } from '@/src/mocks/mockData';
import { useInsight, useProvinceDetail, useProvinces } from '@/src/hooks/useAQIData';
import { cn, getAQIColor, getAQILabel } from '@/src/lib/utils';

export default function Dashboard() {
  const [selectedProvinceId, setSelectedProvinceId] = useState(1);
  const provinceQuery = useProvinces();
  const detailQuery = useProvinceDetail(selectedProvinceId);
  const insightQuery = useInsight(selectedProvinceId);

  const data = detailQuery.data.current;
  const province = detailQuery.data.province;
  const history = detailQuery.data.history;
  const recommendations = insightQuery.data.recommended_actions
    ?? insightQuery.data.recommendations
    ?? [
      data.aqi > 100 ? 'Bật máy lọc không khí ở chế độ cao.' : 'Không khí ổn định, có thể thông gió ngắn.',
      data.temperature > 35 ? 'Tránh vận động mạnh ngoài trời giữa trưa.' : 'Duy trì lịch sinh hoạt bình thường.',
      'Theo dõi PM2.5 vào các khung giờ cao điểm.',
    ];
  const insightText = insightQuery.data.text
    ?? insightQuery.data.summary
    ?? insightQuery.data.health_advice
    ?? `AQI ${Math.round(data.aqi)} tại ${province.name_vi} đang ở mức ${getAQILabel(data.aqi).toLowerCase()}.`;

  const provinceOptions = provinceQuery.data.length
    ? provinceQuery.data.map((item) => ({ id: item.province_id, name: item.name_vi }))
    : PROVINCES.map((item) => ({ id: item.id, name: item.name }));
  const fallbackNotice = detailQuery.error ?? provinceQuery.error ?? insightQuery.error;

  return (
    <div className="max-w-[1440px] mx-auto px-6 py-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">🇻🇳</span>
            <select
              value={selectedProvinceId}
              onChange={(event) => setSelectedProvinceId(Number(event.target.value))}
              className="text-4xl font-bold text-on-surface bg-transparent border-none focus:ring-0 cursor-pointer hover:text-primary transition-colors appearance-none"
            >
              {provinceOptions.map((item) => (
                <option key={item.id} value={item.id} className="bg-surface-container-high text-lg">
                  {item.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-[10px] font-mono font-bold text-primary">
                {detailQuery.source === 'api' ? 'LIVE API' : 'MOCK FALLBACK'}
              </span>
            </div>
            <span className="text-on-surface-variant text-sm tracking-tight opacity-70">
              Cập nhật: {new Date(data.time).toLocaleString('vi-VN')}
            </span>
          </div>
          {fallbackNotice && (
            <p className="mt-3 text-xs font-mono text-warning">
              API chưa sẵn sàng, dashboard đang dùng dữ liệu fallback có kiểm soát.
            </p>
          )}
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
        <div className="lg:col-span-7 flex flex-col gap-6">
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
              <p className="text-[12px] font-mono font-medium text-on-surface-variant mb-6 uppercase tracking-[0.2em]">
                Chỉ số chất lượng không khí hiện tại
              </p>
              <div className="relative w-[320px] h-[160px] mx-auto overflow-hidden">
                <div className="aqi-gauge-gradient w-[320px] h-[320px] opacity-90" />
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center w-full">
                  <div className="text-8xl font-bold leading-none tracking-tighter drop-shadow-2xl">
                    {Math.round(data.aqi)}
                  </div>
                </div>
              </div>
              <div className={cn('text-xl font-bold uppercase tracking-widest mt-6', getAQIColor(data.aqi))}>
                {getAQILabel(data.aqi)}
              </div>
            </div>
          </motion.div>

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
              <StatChip icon={<Brain />} label="BẤT THƯỜNG" value={`${detailQuery.data.anomaly.score.toFixed(2)}`} colorClass="text-tertiary-container" />
              <StatChip icon={<Compass />} label="MODEL" value={detailQuery.data.forecast.model_family.toUpperCase()} />
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 flex flex-col gap-6">
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
              <span className="text-[10px] font-mono font-bold text-tertiary-container px-2 py-1 bg-tertiary-container/10 border border-tertiary-container/20 rounded">
                {insightQuery.source === 'api' ? 'API ADVISOR' : 'FALLBACK'}
              </span>
            </div>

            {insightQuery.loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-surface-container-highest rounded w-3/4" />
                <div className="h-4 bg-surface-container-highest rounded w-5/6" />
                <div className="h-4 bg-surface-container-highest rounded w-2/3" />
              </div>
            ) : (
              <>
                <p className="text-on-surface-variant leading-relaxed mb-4">{insightText}</p>
                {data.aqi > 150 && (
                  <div className="flex items-center gap-2 text-error font-medium bg-error/10 p-3 rounded-xl border border-error/20">
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    <span className="text-sm">Ô nhiễm cao, nên giảm hoạt động ngoài trời.</span>
                  </div>
                )}
                {data.is_anomaly && (
                  <div className="mt-3 flex items-center gap-2 text-primary font-medium bg-primary/10 p-3 rounded-xl border border-primary/20">
                    <Brain className="w-5 h-5" />
                    <span className="text-sm">Mô hình phát hiện tín hiệu bất thường cục bộ.</span>
                  </div>
                )}
              </>
            )}
          </motion.div>

          <div className="glass-card p-8 flex-1">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold">Dữ liệu 24 giờ</h3>
              <div className="flex bg-surface-container-highest/50 rounded-lg p-1 border border-outline-variant/20">
                <button className="px-3 py-1 text-xs font-mono font-bold rounded-md bg-surface-container shadow-sm">AQI</button>
                <button className="px-3 py-1 text-xs font-mono text-on-surface-variant">PM2.5</button>
              </div>
            </div>
            <div className="h-64 mt-auto">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="colorAqi" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#fc7c78" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#fc7c78" stopOpacity={0} />
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

          <div className="glass-card p-8">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-primary" />
              Khuyến nghị Sức khỏe
            </h3>
            <div className="space-y-3">
              {recommendations.map((recommendation, index) => (
                <Recommendation
                  key={recommendation}
                  icon={index === 0 ? <Wind /> : index === 1 ? <Zap /> : <ShieldCheck />}
                  text={recommendation}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatChip({
  icon,
  label,
  value,
  colorClass = 'text-on-surface',
}: {
  icon: ReactElement;
  label: string;
  value: string;
  colorClass?: string;
}) {
  return (
    <div className="p-4 bg-surface-container-low/50 rounded-2xl border border-outline-variant/10 flex items-center gap-3">
      <div className="p-2 bg-surface-container-highest/50 rounded-xl text-on-surface-variant">
        {cloneElement(icon, { className: 'w-5 h-5' })}
      </div>
      <div>
        <p className="text-[10px] font-mono text-on-surface-variant leading-none mb-1 uppercase tracking-wider">{label}</p>
        <p className={cn('text-lg font-bold leading-none', colorClass)}>{value}</p>
      </div>
    </div>
  );
}

function Recommendation({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-2xl bg-surface-container-high/60 border border-outline-variant/10">
      <div className="text-secondary">{icon}</div>
      <p className="font-medium text-on-surface">{text}</p>
    </div>
  );
}
