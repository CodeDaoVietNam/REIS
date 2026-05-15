import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Activity, AlertTriangle, Brain, Clock, HeartPulse, ShieldAlert, Sparkles, Wind } from 'lucide-react';
import { useAnomalies, useSummary } from '@/src/hooks/useAQIData';
import { cn, formatFixed, getAQIColor, getAQILabel, safeNumber } from '@/src/lib/utils';
import type { AnomalyRecord } from '@/src/types';

type AlertKind = 'aqi_warning' | 'ai_anomaly' | 'combined';

export default function HealthAlerts() {
  const navigate = useNavigate();
  const anomalyQuery = useAnomalies();
  const summaryQuery = useSummary();
  const events = anomalyQuery.data;
  const isMock = anomalyQuery.source === 'mock';

  const normalizedEvents = useMemo(
    () => events
      .map(normalizeAlertRecord)
      .sort((left, right) => severityRank(right.severity) - severityRank(left.severity)
        || safeNumber(right.reading.aqi) - safeNumber(left.reading.aqi)),
    [events],
  );
  const aqiEvents = normalizedEvents.filter((event) => event.kind === 'aqi_warning' || event.kind === 'combined');
  const aiEvents = normalizedEvents.filter((event) => event.kind === 'ai_anomaly' || event.kind === 'combined');
  const criticalCount = normalizedEvents.filter((event) => event.severity === 'critical').length;
  const lastUpdated = normalizedEvents[0]?.reading.time ?? summaryQuery.data.latest_time;

  return (
    <div className="mx-auto max-w-[1500px] px-6 py-8">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="mb-2 text-xs font-mono uppercase tracking-[0.28em] text-primary">Operational alert center</p>
          <h1 className="text-4xl font-black tracking-tight">Alert Center</h1>
          <p className="mt-3 max-w-3xl text-sm text-on-surface-variant">
            Trang này tách rõ cảnh báo sức khỏe theo AQI và sự kiện bất thường do AI. Dashboard KPI là trạng thái mới nhất; danh sách bên dưới là event trong 24 giờ gần nhất.
          </p>
        </div>
        <div className="rounded-3xl border border-outline-variant/30 bg-surface-container-high px-5 py-4 text-sm">
          <p className="font-mono text-xs uppercase tracking-widest text-on-surface-variant">Nguồn dữ liệu</p>
          <p className={cn('mt-1 font-black', isMock ? 'text-warning' : 'text-primary')}>
            {isMock ? 'Demo fallback data' : 'Live API /api/anomalies'}
          </p>
        </div>
      </div>

      {isMock && (
        <div className="mb-6 rounded-3xl border border-warning/30 bg-warning/10 p-4 text-sm text-on-surface">
          <span className="font-black text-warning">Demo fallback data:</span>{' '}
          Backend/API chưa sẵn sàng hoặc đang lỗi, nên các cảnh báo bên dưới chỉ là dữ liệu minh họa. UI không xem đây là cảnh báo vận hành thật.
        </div>
      )}

      <section className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryTile
          icon={<ShieldAlert className="h-5 w-5" />}
          label="AQI warnings"
          value={summaryQuery.data.aqi_warning_count}
          suffix={`/ ${summaryQuery.data.province_count}`}
          caption="Latest state, AQI >= 150"
          tone="text-warning"
        />
        <SummaryTile
          icon={<Brain className="h-5 w-5" />}
          label="AI anomalies"
          value={summaryQuery.data.ai_anomaly_count}
          suffix={`/ ${summaryQuery.data.province_count}`}
          caption="Latest model inference"
          tone={summaryQuery.data.ai_anomaly_count > 0 ? 'text-error' : 'text-primary'}
        />
        <SummaryTile
          icon={<AlertTriangle className="h-5 w-5" />}
          label="Critical events"
          value={criticalCount}
          caption="24h event window"
          tone={criticalCount > 0 ? 'text-error' : 'text-primary'}
        />
        <SummaryTile
          icon={<Clock className="h-5 w-5" />}
          label="Last updated"
          value={formatAlertTime(lastUpdated)}
          caption={anomalyQuery.loading ? 'Loading...' : 'Latest event/API timestamp'}
          tone="text-secondary"
        />
      </section>

      <section className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <AlertSection
          title="AQI Health Warnings"
          description="Tỉnh có AQI vượt ngưỡng sức khỏe. Đây là cảnh báo dễ hiểu nhất cho người dùng cuối."
          icon={<HeartPulse className="h-6 w-6" />}
          events={aqiEvents}
          emptyText="Không có AQI warning trong 24 giờ gần nhất."
          sourceIsMock={isMock}
          onOpenProvince={(provinceId) => navigate(`/dashboard?province=${provinceId}`)}
        />
        <AlertSection
          title="AI Anomaly Events"
          description="Sự kiện model phát hiện pattern bất thường, có thể xảy ra cả khi AQI chưa vượt ngưỡng đỏ."
          icon={<Sparkles className="h-6 w-6" />}
          events={aiEvents}
          emptyText="Không có AI anomaly event trong 24 giờ gần nhất."
          sourceIsMock={isMock}
          onOpenProvince={(provinceId) => navigate(`/dashboard?province=${provinceId}`)}
        />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="glass-card border border-outline-variant/25 p-6 xl:col-span-2">
          <h2 className="mb-3 flex items-center gap-2 text-2xl font-black">
            <Activity className="h-6 w-6 text-primary" />
            Operating Notes
          </h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <NoteCard title="AQI warning" text="Dua tren nguong suc khoe AQI >= 150, de truyen dat cho nguoi dung pho thong." />
            <NoteCard title="AI anomaly" text="Dua tren Isolation Forest score/label, dung de bat pattern bat thuong khong chi nhin AQI." />
            <NoteCard title="24h window" text="Danh sach event la cua 24 gio gan nhat; KPI tren Dashboard la latest state." />
          </div>
        </div>
        <div className="glass-card border border-outline-variant/25 p-6">
          <h2 className="mb-3 flex items-center gap-2 text-xl font-black">
            <Wind className="h-5 w-5 text-secondary" />
            Pollen / Allergy
          </h2>
          <p className="text-sm text-on-surface-variant">
            Coming soon. Phan nay chua noi voi nguon pollen/allergy that nen khong hien thi nhu canh bao van hanh.
          </p>
        </div>
      </section>
    </div>
  );
}

function AlertSection({
  title,
  description,
  icon,
  events,
  emptyText,
  sourceIsMock,
  onOpenProvince,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  events: NormalizedAlertRecord[];
  emptyText: string;
  sourceIsMock: boolean;
  onOpenProvince: (provinceId: number) => void;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card border border-outline-variant/25 p-6"
    >
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 text-2xl font-black">
            <span className="text-primary">{icon}</span>
            {title}
          </h2>
          <p className="mt-2 text-sm text-on-surface-variant">{description}</p>
        </div>
        <span className={cn(
          'rounded-full px-3 py-1 text-xs font-mono uppercase',
          sourceIsMock ? 'bg-warning/10 text-warning' : 'bg-primary/10 text-primary',
        )}>
          {sourceIsMock ? 'mock' : 'api'}
        </span>
      </div>

      {events.length === 0 ? (
        <div className="rounded-3xl border border-outline-variant/20 bg-surface-container-low p-5 text-sm text-on-surface-variant">
          {emptyText}
        </div>
      ) : (
        <div className="space-y-3">
          {events.slice(0, 12).map((event) => (
            <AlertEventCard
              key={`${event.province.province_id}-${event.reading.time}-${event.kind}`}
              event={event}
              onOpenProvince={onOpenProvince}
            />
          ))}
        </div>
      )}
    </motion.section>
  );
}

function AlertEventCard({
  event,
  onOpenProvince,
}: {
  event: NormalizedAlertRecord;
  onOpenProvince: (provinceId: number) => void;
}) {
  const aqi = safeNumber(event.reading.aqi);
  const anomalyScore = event.reading.anomaly_score;
  return (
    <button
      type="button"
      onClick={() => onOpenProvince(event.province.province_id)}
      className="w-full rounded-3xl border border-outline-variant/20 bg-surface-container-low p-4 text-left transition hover:border-primary/50 hover:bg-surface-container-high"
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-lg font-black">{event.province.name_vi}</p>
          <p className="text-xs font-mono uppercase tracking-wider text-on-surface-variant">
            {formatAlertTime(event.reading.time)} · {event.province.region}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone={severityTone(event.severity)}>{event.severity}</Badge>
          <Badge tone={event.kind === 'combined' ? 'text-error' : event.kind === 'ai_anomaly' ? 'text-secondary' : 'text-warning'}>
            {event.kind.replace('_', ' ')}
          </Badge>
        </div>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2 md:grid-cols-4">
        <Metric label="AQI" value={Math.round(aqi)} tone={getAQIColor(aqi)} />
        <Metric label="AQI level" value={getAQILabel(aqi)} />
        <Metric label="PM2.5" value={`${formatFixed(event.reading.pm2_5, 1)} µg/m³`} />
        <Metric label="AI score" value={anomalyScore == null ? 'N/A' : safeNumber(anomalyScore).toFixed(2)} />
      </div>

      <p className="mb-3 text-sm text-on-surface-variant">{event.reason}</p>
      <div className="space-y-1">
        {event.recommendations.slice(0, 3).map((recommendation) => (
          <p key={recommendation} className="text-xs text-on-surface-variant">
            <span className="text-primary">-</span> {recommendation}
          </p>
        ))}
      </div>
    </button>
  );
}

function SummaryTile({
  icon,
  label,
  value,
  suffix,
  caption,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  suffix?: string;
  caption: string;
  tone: string;
}) {
  return (
    <div className="glass-card min-h-32 border border-outline-variant/30 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="text-sm font-bold text-on-surface-variant">{label}</span>
        <span className={tone}>{icon}</span>
      </div>
      <div className="flex items-end gap-2">
        <span className={cn('text-4xl font-black tracking-tighter', tone)}>{value}</span>
        {suffix && <span className="mb-1 text-sm font-mono text-on-surface-variant">{suffix}</span>}
      </div>
      <p className="mt-2 text-xs font-mono uppercase tracking-widest text-on-surface-variant">{caption}</p>
    </div>
  );
}

function NoteCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-3xl border border-outline-variant/20 bg-surface-container-low p-4">
      <p className="font-black">{title}</p>
      <p className="mt-2 text-sm text-on-surface-variant">{text}</p>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <span className="rounded-2xl bg-surface-container-high px-3 py-2">
      <span className="block text-[10px] font-mono uppercase tracking-widest text-on-surface-variant">{label}</span>
      <span className={cn('font-black', tone)}>{value}</span>
    </span>
  );
}

function Badge({ children, tone }: { children: React.ReactNode; tone: string }) {
  return (
    <span className={cn('rounded-full bg-surface-container-highest px-3 py-1 text-xs font-mono uppercase', tone)}>
      {children}
    </span>
  );
}

interface NormalizedAlertRecord extends AnomalyRecord {
  kind: AlertKind;
  severity: 'moderate' | 'high' | 'critical';
  reason: string;
  recommendations: string[];
}

function normalizeAlertRecord(record: AnomalyRecord): NormalizedAlertRecord {
  const aqi = safeNumber(record.reading.aqi);
  const score = safeNumber(record.reading.anomaly_score);
  const eventType = record.event_type;
  const hasAqiWarning = aqi >= 150;
  const hasAiAnomaly = eventType === 'ai_anomaly'
    || eventType === 'combined'
    || Boolean(record.reading.is_anomaly)
    || score >= 0.7;
  const kind: AlertKind = eventType === 'combined' || (hasAqiWarning && hasAiAnomaly)
    ? 'combined'
    : hasAiAnomaly
      ? 'ai_anomaly'
      : 'aqi_warning';
  const severity = normalizeSeverity(record.severity, aqi, score);

  return {
    ...record,
    kind,
    severity,
    reason: record.reason ?? fallbackReason(kind, aqi, score),
    recommendations: record.recommendations?.length ? record.recommendations : fallbackRecommendations(kind, severity),
  };
}

function normalizeSeverity(value: string | undefined, aqi: number, score: number): 'moderate' | 'high' | 'critical' {
  if (value === 'critical' || value === 'high' || value === 'moderate') return value;
  if (aqi >= 200 || score >= 0.9) return 'critical';
  if (aqi >= 150 || score >= 0.7) return 'high';
  return 'moderate';
}

function fallbackReason(kind: AlertKind, aqi: number, score: number) {
  if (kind === 'combined') return `AQI ${Math.round(aqi)} cao va AI score ${score.toFixed(2)} cung dang bat thuong.`;
  if (kind === 'ai_anomaly') return `Model phat hien pattern bat thuong voi AI score ${score.toFixed(2)}.`;
  return `AQI ${Math.round(aqi)} vuot nguong canh bao suc khoe.`;
}

function fallbackRecommendations(kind: AlertKind, severity: string) {
  if (severity === 'critical') {
    return [
      'Han che ra ngoai neu khong can thiet.',
      'Dong cua so va bat may loc khong khi neu co.',
      'Nguoi nhay cam nen theo doi trieu chung ho hap.',
    ];
  }
  if (kind === 'ai_anomaly') {
    return [
      'Theo doi them cac chu ky du lieu tiep theo.',
      'Kiem tra dong thoi AQI, PM2.5 va dieu kien thoi tiet.',
    ];
  }
  return [
    'Giam hoat dong ngoai troi keo dai.',
    'Can nhac khau trang loc bui min khi di chuyen.',
  ];
}

function severityRank(severity: string) {
  if (severity === 'critical') return 3;
  if (severity === 'high') return 2;
  return 1;
}

function severityTone(severity: string) {
  if (severity === 'critical') return 'text-error';
  if (severity === 'high') return 'text-warning';
  return 'text-primary';
}

function formatAlertTime(value: string | null | undefined) {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('vi-VN');
}
