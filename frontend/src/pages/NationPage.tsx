import { cloneElement, useState, type ReactElement } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';
import {
  AlertCircle,
  ChevronRight,
  Droplets,
  Globe,
  Layers,
  MapPin,
  Thermometer,
  TrendingUp,
  Wind,
  Zap,
} from 'lucide-react';
import { PROVINCES } from '@/src/mocks/mockData';
import { useProvinces } from '@/src/hooks/useAQIData';
import { useWebSocket } from '@/src/hooks/useWebSocket';
import { cn, getAQIBg, getAQIColor } from '@/src/lib/utils';
import type { EnvironmentalData, Region } from '@/src/types';

const geoUrl = '/vn-provinces.json';
type RegionFilter = Region | 'All';
const REGION_FILTERS: RegionFilter[] = ['North', 'Central', 'South', 'All'];

export default function NationalMap() {
  const [selectedRegion, setSelectedRegion] = useState<RegionFilter>('All');
  const [selectedProvinceId, setSelectedProvinceId] = useState<number | null>(null);
  const provinceQuery = useProvinces();
  const liveQuery = useWebSocket();

  const summaries = liveQuery.lastMessage?.provinces.length ? liveQuery.lastMessage.provinces : provinceQuery.data;
  const readingsById = new Map(summaries.map((summary) => [summary.province_id, summary.current]));
  const mapPoints = PROVINCES.map((province) => ({
    ...province,
    data: readingsById.get(province.id) as EnvironmentalData | null | undefined,
  })).filter((point) => point.data);
  const visiblePoints = mapPoints.filter((point) => selectedRegion === 'All' || point.region === selectedRegion);
  const rankings = [...mapPoints].sort((a, b) => (b.data?.aqi ?? 0) - (a.data?.aqi ?? 0));
  const selectedProvince = mapPoints.find((point) => point.id === selectedProvinceId);
  const aqiAverage = Math.round(mapPoints.reduce((sum, point) => sum + (point.data?.aqi ?? 0), 0) / Math.max(1, mapPoints.length));
  const pm25Average = (
    mapPoints.reduce((sum, point) => sum + (point.data?.pm2_5 ?? 0), 0) / Math.max(1, mapPoints.length)
  ).toFixed(1);

  return (
    <div className="max-w-[1700px] mx-auto px-6 py-8 h-[calc(100vh-80px)] min-h-[800px] flex gap-6">
      <aside className="w-96 flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
        <div className="glass-card p-6 shadow-xl">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            Báo cáo Tổng hợp
          </h2>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <StatSmall label="AQI Avg" value={aqiAverage.toString()} color="text-tertiary-container" />
            <StatSmall label="PM2.5 Avg" value={pm25Average} color="text-error" />
            <StatSmall label="Nguồn" value={provinceQuery.source.toUpperCase()} color="text-primary" />
            <StatSmall label="Realtime" value={liveQuery.isConnected ? 'ON' : 'OFF'} color={liveQuery.isConnected ? 'text-primary' : 'text-warning'} />
          </div>
          <div className="space-y-3 pt-4 border-t border-outline-variant/30">
            <MetricLine icon={<Thermometer />} label="Tỉnh đang theo dõi" value={mapPoints.length.toString()} />
            <MetricLine icon={<Wind />} label="Kết nối dữ liệu" value={provinceQuery.error ? 'Fallback' : 'API'} />
          </div>
        </div>

        <div className="glass-card p-6 flex-1 flex flex-col">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-error" />
            Điểm nóng ô nhiễm
          </h2>
          <div className="space-y-3 overflow-y-auto flex-1 h-0 pr-1 custom-scrollbar">
            {rankings.map((point, index) => {
              const data = point.data;
              if (!data) return null;

              return (
                <motion.div
                  key={point.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.03 }}
                  onClick={() => setSelectedProvinceId(point.id)}
                  className={cn(
                    'group p-3 rounded-xl border border-outline-variant/10 cursor-pointer transition-all',
                    selectedProvinceId === point.id ? 'bg-primary/10 border-primary' : 'bg-surface-container-low hover:bg-surface-container-high',
                  )}
                >
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold opacity-30">
                        {(index + 1).toString().padStart(2, '0')}
                      </span>
                      <span className="font-bold text-sm tracking-tight">{point.name}</span>
                    </div>
                    <span className={cn('font-mono font-bold text-sm', getAQIColor(data.aqi))}>{data.aqi} AQI</span>
                  </div>
                  <div className="h-1 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(100, (data.aqi / 300) * 100)}%` }}
                      className={cn('h-full rounded-full', getAQIBg(data.aqi))}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </aside>

      <section className="flex-1 glass-card border border-outline-variant/50 relative overflow-hidden flex shadow-2xl bg-surface-dim">
        <div className="absolute top-6 right-6 z-10 flex flex-col gap-2">
          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl p-1 border border-outline-variant/30 flex shadow-lg">
            {REGION_FILTERS.map((region) => (
              <button
                key={region}
                onClick={() => setSelectedRegion(region)}
                className={cn(
                  'px-4 py-2 rounded-xl text-xs font-bold transition-all',
                  selectedRegion === region ? 'bg-primary text-on-primary shadow-sm' : 'text-on-surface-variant hover:bg-surface-container-highest',
                )}
              >
                {region === 'All' ? 'Tất cả' : `Miền ${region === 'North' ? 'Bắc' : region === 'Central' ? 'Trung' : 'Nam'}`}
              </button>
            ))}
          </div>

          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl p-1 border border-outline-variant/30 flex shadow-lg">
            <button className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant">
              <MapPin className="w-5 h-5" />
            </button>
            <button className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant">
              <Layers className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="absolute bottom-6 left-6 z-10 glass-card p-4 space-y-2 border border-outline-variant/30 bg-surface/80 backdrop-blur-md">
          <LegendItem label="Tốt" color="bg-success" range="0-50" />
          <LegendItem label="Trung bình" color="bg-warning" range="51-100" />
          <LegendItem label="Kém" color="bg-error" range="101-150" />
          <LegendItem label="Xấu" color="bg-[#93000a]" range="151-200" />
          <LegendItem label="Cực xấu" color="bg-[#410002]" range="201+" />
        </div>

        <div className="flex-1 flex items-center justify-center relative p-12">
          <div className="flex-1 flex items-center justify-center relative p-4 h-full">
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{
                scale: 2600,
                center: [106, 16.5],
              }}
              className="w-full h-full"
            >
              <defs>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
                  <feOffset dx="2" dy="2" result="offsetblur" />
                  <feComponentTransfer>
                    <feFuncA type="linear" slope="0.5" />
                  </feComponentTransfer>
                  <feMerge>
                    <feMergeNode />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              <Geographies geography={geoUrl}>
                {({ geographies }) =>
                  geographies.map((geo) => (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      filter="url(#shadow)"
                      fill="var(--color-surface-container-highest)"
                      stroke="var(--color-outline-variant)"
                      strokeWidth={0.7}
                      style={{
                        default: { outline: 'none' },
                        hover: {
                          fill: 'var(--color-primary)',
                          stroke: '#fff',
                          strokeWidth: 1,
                          outline: 'none',
                          transition: 'all 250ms',
                        },
                        pressed: { outline: 'none' },
                      }}
                      className="cursor-pointer transition-all duration-300"
                    />
                  ))
                }
              </Geographies>

              {visiblePoints.map((point) => {
                const data = point.data;
                if (!data) return null;

                return (
                  <Marker key={point.id} coordinates={[point.lng, point.lat]} onClick={() => setSelectedProvinceId(point.id)}>
                    <g className="cursor-pointer group">
                      <motion.circle
                        r={data.aqi / 15 + 2}
                        className={cn(getAQIBg(data.aqi), 'opacity-40 blur-md')}
                        animate={{ scale: [1, 1.3, 1] }}
                        transition={{ repeat: Infinity, duration: 2 + (point.id % 5) * 0.35 }}
                      />
                      <circle r={3} className={cn(getAQIBg(data.aqi), 'border border-white/30')} />
                      <text
                        y={-8}
                        className="fill-on-surface font-mono text-[8px] opacity-0 group-hover:opacity-100 uppercase tracking-widest text-center drop-shadow-md font-bold"
                        textAnchor="middle"
                      >
                        {point.name}
                      </text>
                    </g>
                  </Marker>
                );
              })}
            </ComposableMap>
          </div>
        </div>

        <AnimatePresence>
          {selectedProvince && selectedProvince.data && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 glass-card p-8 border-primary/50 shadow-2xl z-30 min-w-[300px]"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-2xl font-bold">{selectedProvince.name}</h3>
                  <p className="text-xs font-mono text-on-surface-variant uppercase tracking-widest">{selectedProvince.region} VIETNAM</p>
                </div>
                <button onClick={() => setSelectedProvinceId(null)} className="text-on-surface-variant hover:text-primary transition-colors">
                  <Zap className="w-5 h-5" />
                </button>
              </div>

              <div className="flex items-center gap-6 mb-8">
                <div className="flex flex-col">
                  <span className={cn('text-6xl font-bold font-mono tracking-tighter', getAQIColor(selectedProvince.data.aqi))}>
                    {selectedProvince.data.aqi}
                  </span>
                  <span className="text-xs font-mono font-bold uppercase opacity-50">Chỉ số AQI</span>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <Thermometer className="w-3 h-3 text-secondary" />
                    <span>{selectedProvince.data.temperature.toFixed(1)}°C</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <Droplets className="w-3 h-3 text-primary" />
                    <span>{selectedProvince.data.humidity.toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <button className="w-full py-4 bg-primary text-on-primary rounded-2xl font-bold text-sm flex items-center justify-center gap-2 hover:scale-[1.02] transition-all">
                  Phân tích chi tiết <ChevronRight className="w-4 h-4" />
                </button>
                <button className="w-full py-4 bg-surface-container-high text-on-surface rounded-2xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-surface-container-highest transition-colors">
                  Sức khỏe vùng <AlertCircle className="w-4 h-4 text-tertiary-container" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </section>
    </div>
  );
}

function StatSmall({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-surface-container-highest/30 p-3 rounded-xl border border-outline-variant/20 text-center hover:bg-surface-container-highest/50 transition-colors">
      <span className="text-[10px] font-mono text-on-surface-variant block mb-1 uppercase opacity-70 tracking-widest">{label}</span>
      <span className={cn('text-lg font-bold block', color)}>{value}</span>
    </div>
  );
}

function MetricLine({ icon, label, value }: { icon: ReactElement; label: string; value: string }) {
  return (
    <div className="flex justify-between items-center text-sm group">
      <div className="flex items-center gap-2 text-on-surface-variant group-hover:text-primary transition-colors">
        {cloneElement(icon, { className: 'w-4 h-4' })}
        <span>{label}</span>
      </div>
      <span className="font-bold">{value}</span>
    </div>
  );
}

function LegendItem({ label, color, range }: { label: string; color: string; range: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className={cn('w-2 h-2 rounded-full', color)} />
      <span className="text-[10px] font-bold text-on-surface-variant">{label}</span>
      <span className="text-[10px] font-mono opacity-40 ml-auto">{range}</span>
    </div>
  );
}
