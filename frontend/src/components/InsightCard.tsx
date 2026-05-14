import { Brain, Database, Sparkles } from 'lucide-react';
import type { InsightPayload } from '@/src/types';
import { cn } from '@/src/lib/utils';

export function InsightCard({
  insight,
  loading,
  source,
  updatedAt,
}: {
  insight: InsightPayload;
  loading?: boolean;
  source: 'api' | 'mock';
  updatedAt?: string | null;
}) {
  const text = insight.text ?? insight.summary ?? insight.health_advice ?? 'Đang chờ dữ liệu insight.';
  const provider = insight.source ?? source;
  const cached = insight.cached === true;

  return (
    <div className="glass-card p-6 border-l-4 border-l-tertiary-container">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-tertiary-container" />
          <h3 className="text-lg font-black">Insights</h3>
        </div>
        <div className="flex gap-2">
          <span className={cn('rounded-full px-2 py-1 text-[10px] font-mono uppercase', source === 'api' ? 'bg-primary/10 text-primary' : 'bg-warning/10 text-warning')}>
            {provider}
          </span>
          <span className="rounded-full bg-surface-container-highest px-2 py-1 text-[10px] font-mono text-on-surface-variant">
            {cached ? 'cached' : 'fresh'}
          </span>
        </div>
      </div>
      {loading ? (
        <div className="space-y-3 animate-pulse">
          <div className="h-4 rounded bg-surface-container-highest" />
          <div className="h-4 w-5/6 rounded bg-surface-container-highest" />
          <div className="h-4 w-2/3 rounded bg-surface-container-highest" />
        </div>
      ) : (
        <p className="leading-relaxed text-on-surface-variant">{text}</p>
      )}
      <div className="mt-5 flex flex-wrap items-center gap-3 text-xs font-mono text-on-surface-variant">
        <span className="flex items-center gap-1">
          <Sparkles className="h-3.5 w-3.5" />
          risk: {insight.risk_level ?? 'unknown'}
        </span>
        <span className="flex items-center gap-1">
          <Database className="h-3.5 w-3.5" />
          {updatedAt ? new Date(updatedAt).toLocaleString('vi-VN') : 'no timestamp'}
        </span>
      </div>
    </div>
  );
}
