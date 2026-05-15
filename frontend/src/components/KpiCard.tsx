import type { ReactNode } from 'react';
import { cn } from '@/src/lib/utils';

export function KpiCard({
  label,
  value,
  suffix,
  icon,
  tone = 'text-primary',
  onClick,
  hint,
}: {
  label: string;
  value: string | number;
  suffix?: string;
  icon?: ReactNode;
  tone?: string;
  onClick?: () => void;
  hint?: string;
}) {
  const content = (
    <>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-bold text-on-surface-variant">{label}</span>
        <span className={cn('opacity-80', tone)}>{icon}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={cn('text-4xl font-black tracking-tighter', tone)}>{value}</span>
        {suffix && <span className="mb-1 text-sm font-mono text-on-surface-variant">{suffix}</span>}
      </div>
      {hint && <span className="mt-2 text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">{hint}</span>}
    </>
  );
  const className = cn(
    'glass-card min-h-28 border border-outline-variant/30 p-5 text-left flex flex-col justify-between',
    onClick && 'cursor-pointer transition hover:-translate-y-0.5 hover:border-primary/50 hover:bg-surface-container-high',
  );

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={className}>
        {content}
      </button>
    );
  }

  return (
    <div className={className}>
      {content}
    </div>
  );
}
