import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MOCK_ENV_DATA, PROVINCES } from '../types';
import { cn, getAQIColor, getAQIBg } from '../lib/utils';
import { MapPin, Info, Layers, Wind, Droplets, Thermometer, AlertCircle, ChevronRight, Globe, TrendingUp, Navigation, Zap } from 'lucide-react';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';

const geoUrl = "/vn-provinces.json"
export default function NationalMap() {
  const [selectedRegion, setSelectedRegion] = useState<'All' | 'North' | 'Central' | 'South'>('All');
  const [selectedProvinceId, setSelectedProvinceId] = useState<number | null>(null);

  const rankings = [...PROVINCES].sort((a, b) => {
    const dataA = MOCK_ENV_DATA.find(d => d.province_name === a.name);
    const dataB = MOCK_ENV_DATA.find(d => d.province_name === b.name);
    return (dataB?.aqi || 0) - (dataA?.aqi || 0);
  });

  // Simplified Vietnam S-Curve Path (Stylized mainland)
  const vietnamPath = "M120,40 C140,30 160,30 170,50 C180,70 160,110 140,140 C120,170 130,210 150,240 C170,270 180,310 170,340 C160,370 140,410 130,470 L140,480 L160,490 L180,500";

  return (
    <div className="max-w-[1700px] mx-auto px-6 py-8 h-[calc(100vh-80px)] min-h-[800px] flex gap-6">
      <aside className="w-96 flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
        {/* National Stats Card */}
        <div className="glass-card p-6 shadow-xl">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            Báo cáo Tổng hợp
          </h2>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <StatSmall label="AQI Avg" value="94" color="text-tertiary-container" />
            <StatSmall label="PM2.5 Avg" value="32.4" color="text-error" />
            <StatSmall label="Độ ẩm" value="72%" color="text-primary" />
            <StatSmall label="Gió" value="12km/h" color="text-on-surface" />
          </div>
          <div className="space-y-3 pt-4 border-t border-outline-variant/30">
            <MetricLine icon={<Thermometer />} label="Nhiệt độ tối đa" value="34°C" />
            <MetricLine icon={<Wind />} label="Hướng gió" value="Đông Bắc" />
          </div>
        </div>

        {/* Pollution Rankings Card */}
        <div className="glass-card p-6 flex-1 flex flex-col">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-error" />
            Điểm nóng ô nhiễm
          </h2>
          <div className="space-y-3 overflow-y-auto flex-1 h-0 pr-1 custom-scrollbar">
             {rankings.map((p, i) => {
                const data = MOCK_ENV_DATA.find(d => d.province_name === p.name);
                if (!data) return null;
                return (
                  <motion.div 
                    key={p.id} 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    onClick={() => setSelectedProvinceId(p.id)}
                    className={cn(
                      "group p-3 rounded-xl border border-outline-variant/10 cursor-pointer transition-all",
                      selectedProvinceId === p.id ? "bg-primary/10 border-primary" : "bg-surface-container-low hover:bg-surface-container-high"
                    )}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold opacity-30">0{i+1}</span>
                        <span className="font-bold text-sm tracking-tight">{p.name}</span>
                      </div>
                      <span className={cn("font-mono font-bold text-sm", getAQIColor(data.aqi))}>{data.aqi} AQI</span>
                    </div>
                    <div className="h-1 w-full bg-surface-container-highest rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }} 
                        animate={{ width: `${(data.aqi / 300) * 100}%` }} 
                        className={cn("h-full rounded-full", getAQIBg(data.aqi))} 
                      />
                    </div>
                  </motion.div>
                );
             })}
          </div>
        </div>
      </aside>

      {/* Map Section */}
      <section className="flex-1 glass-card border border-outline-variant/50 relative overflow-hidden flex shadow-2xl bg-surface-dim">
        {/* Controls Overlay */}
        <div className="absolute top-6 right-6 z-10 flex flex-col gap-2">
          <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl p-1 border border-outline-variant/30 flex shadow-lg">
             {['North', 'Central', 'South', 'All'].map(r => (
                <button 
                  key={r}
                  onClick={() => setSelectedRegion(r as any)}
                  className={cn(
                    "px-4 py-2 rounded-xl text-xs font-bold transition-all", 
                    selectedRegion === r ? "bg-primary text-on-primary shadow-sm" : "text-on-surface-variant hover:bg-surface-container-highest"
                  )}
                >
                  {r === 'All' ? 'Tất cả' : `Miền ${r === 'North' ? 'Bắc' : r === 'Central' ? 'Trung' : 'Nam'}`}
                </button>
             ))}
          </div>
          
          <div className="flex gap-2">
            <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl p-1 border border-outline-variant/30 flex shadow-lg">
              <button onClick={handleZoomIn} className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant" title="Phóng to"><Plus className="w-5 h-5" /></button>
              <button onClick={handleZoomOut} className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant" title="Thu nhỏ"><Minus className="w-5 h-5" /></button>
              <button onClick={handleReset} className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant" title="Đặt lại"><Maximize className="w-5 h-5" /></button>
            </div>
            <div className="bg-surface-container-low/80 backdrop-blur-md rounded-2xl p-1 border border-outline-variant/30 flex shadow-lg">
              <button className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant"><MapPin className="w-5 h-5" /></button>
              <button className="p-2 hover:bg-surface-container-highest rounded-xl text-on-surface-variant"><Layers className="w-5 h-5" /></button>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-6 left-6 z-10 glass-card p-4 space-y-2 border border-outline-variant/30 bg-surface/80 backdrop-blur-md">
          <LegendItem label="Tốt" color="bg-success" range="0-50" />
          <LegendItem label="Trung bình" color="bg-warning" range="51-100" />
          <LegendItem label="Kém" color="bg-error" range="101-150" />
          <LegendItem label="Xấu" color="bg-[#93000a]" range="151-200" />
          <LegendItem label="Cực xấu" color="bg-[#410002]" range="201+" />
        </div>

        {/* SVG Drawing Area */}
        <div className="flex-1 flex items-center justify-center relative p-12">
                   {/* Bản đồ Việt Nam thực tế */}
        <div className="flex-1 flex items-center justify-center relative p-4 h-full">
          <ComposableMap
            projection="geoMercator"
            projectionConfig={{
              scale: 2600, // Độ zoom của bản đồ
              center: [106, 16.5] // Tọa độ trung tâm Việt Nam
            }}
            className="w-full h-full"
          >
            {/* SVG Filter for Depth */}
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

            {/* Ranh giới các tỉnh */}
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
                      default: { outline: "none" },
                      hover: { 
                        fill: "var(--color-primary)",
                        stroke: "#fff",
                        strokeWidth: 1,
                        outline: "none",
                        transition: "all 250ms"
                      },
                      pressed: { outline: "none" }
                    }}
                    className="cursor-pointer transition-all duration-300"
                  />
                ))
              }
            </Geographies>

            {/* Các điểm sáng (Markers) tương ứng với 63 tỉnh thành */}
            {PROVINCES.map((p) => {
              const data = MOCK_ENV_DATA.find(d => d.province_name === p.name);
              if (!data || (selectedRegion !== 'All' && p.region !== selectedRegion)) return null;
              
              return (
                <Marker key={p.id} coordinates={[p.lng, p.lat]} onClick={() => setSelectedProvinceId(p.id)}>
                  <g className="cursor-pointer group">
                    <motion.circle
                      r={data.aqi / 15 + 2}
                      className={cn(getAQIBg(data.aqi), "opacity-40 blur-md")}
                      animate={{ scale: [1, 1.3, 1] }}
                      transition={{ repeat: Infinity, duration: 2 + Math.random() * 2 }}
                    />
                    <circle
                      r={3}
                      className={cn(getAQIBg(data.aqi), "border border-white/30")}
                    />
                    <text
                      y={-8}
                      className="fill-on-surface font-mono text-[8px] opacity-0 group-hover:opacity-100 uppercase tracking-widest text-center drop-shadow-md font-bold"
                      textAnchor="middle"
                    >
                      {p.name}
                    </text>
                  </g>
                </Marker>
              );
            })}
          </ComposableMap>
        </div>
        </div>

        {/* Overlay Details */}
        <AnimatePresence>
          {selectedProvinceId && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 glass-card p-8 border-primary/50 shadow-2xl z-30 min-w-[300px]"
            >
               <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-2xl font-bold">{PROVINCES.find(p => p.id === selectedProvinceId)?.name}</h3>
                    <p className="text-xs font-mono text-on-surface-variant uppercase tracking-widest">{PROVINCES.find(p => p.id === selectedProvinceId)?.region} VIETNAM</p>
                  </div>
                  <button onClick={() => setSelectedProvinceId(null)} className="text-on-surface-variant hover:text-primary transition-colors">
                    <Zap className="w-5 h-5" />
                  </button>
               </div>
               
               <div className="flex items-center gap-6 mb-8">
                  <div className="flex flex-col">
                    <span className={cn("text-6xl font-bold font-mono tracking-tighter", getAQIColor(MOCK_ENV_DATA.find(d => d.province_name === PROVINCES.find(p => p.id === selectedProvinceId)?.name)?.aqi || 0))}>
                      {MOCK_ENV_DATA.find(d => d.province_name === PROVINCES.find(p => p.id === selectedProvinceId)?.name)?.aqi}
                    </span>
                    <span className="text-xs font-mono font-bold uppercase opacity-50">Chỉ số AQI</span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-xs">
                      <Thermometer className="w-3 h-3 text-secondary" />
                      <span>{MOCK_ENV_DATA.find(d => d.province_name === PROVINCES.find(p => p.id === selectedProvinceId)?.name)?.temperature}°C</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Droplets className="w-3 h-3 text-primary" />
                      <span>{MOCK_ENV_DATA.find(d => d.province_name === PROVINCES.find(p => p.id === selectedProvinceId)?.name)?.humidity}%</span>
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

function StatSmall({ label, value, color }: { label: string, value: string, color: string }) {
  return (
    <div className="bg-surface-container-highest/30 p-3 rounded-xl border border-outline-variant/20 text-center hover:bg-surface-container-highest/50 transition-colors">
      <span className="text-[10px] font-mono text-on-surface-variant block mb-1 uppercase opacity-70 tracking-widest">{label}</span>
      <span className={cn("text-lg font-bold block", color)}>{value}</span>
    </div>
  );
}

function MetricLine({ icon, label, value }: { icon: React.ReactNode, label: string, value: string }) {
  return (
    <div className="flex justify-between items-center text-sm group">
      <div className="flex items-center gap-2 text-on-surface-variant group-hover:text-primary transition-colors">
        {React.cloneElement(icon as React.ReactElement, { className: "w-4 h-4" })}
        <span>{label}</span>
      </div>
      <span className="font-bold">{value}</span>
    </div>
  );
}

function LegendItem({ label, color, range }: { label: string, color: string, range: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className={cn("w-2 h-2 rounded-full", color)} />
      <span className="text-[10px] font-bold text-on-surface-variant">{label}</span>
      <span className="text-[10px] font-mono opacity-40 ml-auto">{range}</span>
    </div>
  );
}
