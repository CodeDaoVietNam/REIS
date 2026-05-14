import { cn, getAQIColor, getAQILabel } from '@/src/lib/utils';

export function AqiGauge({ aqi, label }: { aqi: number; label?: string }) {
  const rotation = Math.min(180, Math.max(0, (aqi / 300) * 180));
  const needleX = 50 + Math.cos((180 - rotation) * (Math.PI / 180)) * 38;
  const needleY = 100 - Math.sin((180 - rotation) * (Math.PI / 180)) * 82;

  return (
    <div className="glass-card p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">{label ?? 'AQI'}</h3>
        <span className={cn('text-xs font-mono font-bold uppercase', getAQIColor(aqi))}>{getAQILabel(aqi)}</span>
      </div>
      <div className="relative mx-auto h-36 w-72 overflow-hidden">
        <div className="absolute inset-x-0 bottom-0 h-72 w-72 rounded-full bg-[conic-gradient(from_270deg,#4edea3_0deg,#f8d66d_55deg,#ff9f43_100deg,#fc7c78_145deg,#410002_180deg,transparent_181deg)]" />
        <div className="absolute inset-x-8 bottom-0 h-56 w-56 rounded-full bg-surface" />
        <div
          className="absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-white shadow-[0_0_24px_rgba(255,255,255,0.75)] transition-all"
          style={{ left: `${needleX}%`, top: `${needleY}%` }}
        />
        <div className="absolute bottom-4 left-0 right-0 z-10 text-center">
          <div className="text-5xl font-black tracking-tighter">{Math.round(aqi)}</div>
          <div className="text-xs font-mono text-on-surface-variant">AQI</div>
        </div>
      </div>
    </div>
  );
}
