import { BookOpenText, Download, Lightbulb, TrendingUp } from 'lucide-react';
import { getInsightReportUrl } from '@/src/services/apiClient';
import type { InsightSummaryPayload } from '@/src/types';
import { cn } from '@/src/lib/utils';

export function KeyFindings({
  payload,
  loading,
  source,
}: {
  payload: InsightSummaryPayload;
  loading?: boolean;
  source: 'api' | 'mock';
}) {
  const findings = payload.findings.slice(0, 5);
  const isLive = source === 'api' && payload.source === 'eda_live_hybrid';

  return (
    <section className="glass-card p-6">
      <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-warning" />
            <h2 className="text-2xl font-black">Key Findings</h2>
          </div>
          <p className="max-w-3xl text-sm leading-relaxed text-on-surface-variant">
            Phần này biến notebook EDA thành kết luận: xu hướng chính, pattern đáng chú ý,
            giải thích/forecast và giá trị hành động. Đây là insight cấp hệ thống, khác với
            LLM insight theo từng tỉnh.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              'rounded-full px-3 py-1 text-[10px] font-mono uppercase tracking-widest',
              isLive ? 'bg-primary/10 text-primary' : 'bg-warning/10 text-warning',
            )}
          >
            {isLive ? 'EDA + LIVE DB' : 'EDA fallback'}
          </span>
          <a
            href={getInsightReportUrl()}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-bold text-primary transition hover:border-primary"
          >
            <Download className="h-3.5 w-3.5" />
            Export insight PDF
          </a>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-44 animate-pulse rounded-3xl bg-surface-container-highest/50" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          {findings.map((finding, index) => (
            <article key={finding.id} className="rounded-3xl border border-outline-variant/25 bg-surface-container-low p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <span className="rounded-full bg-primary/10 px-2 py-1 text-[10px] font-mono font-bold text-primary">
                  #{index + 1}
                </span>
                <span className="text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">
                  {finding.confidence.replace('_', ' ')}
                </span>
              </div>
              <h3 className="mb-2 text-base font-black">{finding.title}</h3>
              <p className="mb-3 text-sm font-semibold leading-relaxed text-on-surface">{finding.claim}</p>
              <div className="space-y-2 text-xs leading-relaxed text-on-surface-variant">
                <p>
                  <BookOpenText className="mr-1 inline h-3.5 w-3.5 text-secondary" />
                  {finding.evidence}
                </p>
                <p>
                  <TrendingUp className="mr-1 inline h-3.5 w-3.5 text-tertiary-container" />
                  {finding.practical_value}
                </p>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
