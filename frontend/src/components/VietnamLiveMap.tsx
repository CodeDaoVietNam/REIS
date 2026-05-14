import { useState } from 'react';
import { motion } from 'framer-motion';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';
import { Layers, MapPin } from 'lucide-react';
import { PROVINCES } from '@/src/mocks/mockData';
import { cn, getAQIColor } from '@/src/lib/utils';
import type { EnvironmentalData, ProvinceSummary, Region } from '@/src/types';

const geoUrl = '/vn-provinces.json';
type RegionFilter = Region | 'All';
const regionFilters: RegionFilter[] = ['North', 'Central', 'South', 'All'];

function aqiFill(aqi: number): string {
  if (aqi <= 50) return '#4edea3';
  if (aqi <= 100) return '#adc6ff';
  if (aqi <= 150) return '#e6c100';
  if (aqi <= 200) return '#ff9f43';
  return '#ffb4ab';
}

export function VietnamLiveMap({
  summaries,
  selectedProvinceId,
  onSelectProvince,
  compact = false,
}: {
  summaries: ProvinceSummary[];
  selectedProvinceId?: number | null;
  onSelectProvince?: (provinceId: number) => void;
  compact?: boolean;
}) {
  const [region, setRegion] = useState<RegionFilter>('All');
  const readingsById = new Map(summaries.map((summary) => [summary.province_id, summary.current]));
  const points = PROVINCES.map((province) => ({
    ...province,
    data: readingsById.get(province.id) as EnvironmentalData | null | undefined,
  })).filter((point) => point.data && (region === 'All' || point.region === region));
  const selected = points.find((point) => point.id === selectedProvinceId);

  return (
    <section className={cn('glass-card relative overflow-hidden border border-outline-variant/50 bg-surface-dim', compact ? 'h-[520px]' : 'h-full min-h-[760px]')}>
      <div className="absolute right-5 top-5 z-10 flex flex-col gap-2">
        <div className="flex rounded-2xl border border-outline-variant/30 bg-surface-container-low/80 p-1 backdrop-blur-md">
          {regionFilters.map((item) => (
            <button
              key={item}
              onClick={() => setRegion(item)}
              className={cn(
                'rounded-xl px-3 py-2 text-xs font-bold transition-all',
                region === item ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container-highest',
              )}
            >
              {item === 'All' ? 'Tất cả' : item}
            </button>
          ))}
        </div>
        <div className="ml-auto flex rounded-2xl border border-outline-variant/30 bg-surface-container-low/80 p-1 backdrop-blur-md">
          <button className="rounded-xl p-2 text-on-surface-variant hover:bg-surface-container-highest">
            <MapPin className="h-5 w-5" />
          </button>
          <button className="rounded-xl p-2 text-on-surface-variant hover:bg-surface-container-highest">
            <Layers className="h-5 w-5" />
          </button>
        </div>
      </div>

      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: compact ? 2300 : 2600, center: [106, 16.5] }}
        className="h-full w-full"
      >
        <defs>
          <filter id="mapShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
            <feOffset dx="2" dy="2" result="offsetblur" />
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.45" />
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
                filter="url(#mapShadow)"
                fill="var(--color-surface-container-highest)"
                stroke="var(--color-outline-variant)"
                strokeWidth={0.7}
                style={{
                  default: { outline: 'none' },
                  hover: { fill: 'var(--color-primary)', outline: 'none' },
                  pressed: { outline: 'none' },
                }}
              />
            ))
          }
        </Geographies>
        {points.map((point) => {
          const data = point.data;
          if (!data) return null;
          const selectedPoint = selectedProvinceId === point.id;
          return (
            <Marker key={point.id} coordinates={[point.lng, point.lat]} onClick={() => onSelectProvince?.(point.id)}>
              <g className="cursor-pointer group">
                <motion.circle
                  r={selectedPoint ? data.aqi / 12 + 4 : data.aqi / 16 + 2}
                  fill={aqiFill(data.aqi)}
                  fillOpacity={selectedPoint ? 0.42 : 0.2}
                  stroke={aqiFill(data.aqi)}
                  strokeOpacity={0.35}
                  className={cn(selectedPoint ? 'opacity-90' : 'opacity-70 blur-sm')}
                  animate={{ scale: [1, selectedPoint ? 1.45 : 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 2 + (point.id % 5) * 0.35 }}
                />
                <circle
                  r={selectedPoint ? 5 : 3.5}
                  fill={aqiFill(data.aqi)}
                  stroke="rgba(255,255,255,0.72)"
                  strokeWidth={selectedPoint ? 1.4 : 0.8}
                />
                <text y={-8} className="fill-on-surface text-[8px] font-bold opacity-0 drop-shadow-md group-hover:opacity-100" textAnchor="middle">
                  {point.name}
                </text>
              </g>
            </Marker>
          );
        })}
      </ComposableMap>

      {selected?.data && (
        <div className="absolute bottom-5 right-5 z-10 rounded-3xl border border-primary/40 bg-surface/80 p-4 backdrop-blur-xl">
          <p className="font-bold">{selected.name}</p>
          <p className={cn('text-3xl font-black', getAQIColor(selected.data.aqi))}>{Math.round(selected.data.aqi)} AQI</p>
        </div>
      )}
    </section>
  );
}
