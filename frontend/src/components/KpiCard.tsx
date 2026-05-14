import type { ReactNode } from 'react';
import { cn } from '@/src/lib/utils';

export function KpiCard({
  label,
  value,
  suffix,
  icon,
  tone = 'text-primary',
}: {
  label: string;
  value: string | number;
  suffix?: string;
  icon?: ReactNode;
  tone?: string;
}) {
  return (
    <div className="glass-card p-5 border border-outline-variant/30 min-h-28 flex flex-col justify-between">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-bold text-on-surface-variant">{label}</span>
        <span className={cn('opacity-80', tone)}>{icon}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={cn('text-4xl font-black tracking-tighter', tone)}>{value}</span>
        {suffix && <span className="mb-1 text-sm font-mono text-on-surface-variant">{suffix}</span>}
      </div>
    </div>
  );
}
