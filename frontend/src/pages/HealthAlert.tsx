import { type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, Heart, ShieldAlert, Thermometer, Wind } from 'lucide-react';
import { useAnomalies } from '@/src/hooks/useAQIData';
import { cn, formatFixed, safeNumber } from '@/src/lib/utils';

export default function HealthAlerts() {
  const anomalyQuery = useAnomalies();
  const primaryAlert = anomalyQuery.data[0];
  const provinceName = primaryAlert?.province.name_vi ?? 'Việt Nam';
  const reading = primaryAlert?.reading;
  const isAiAnomaly = primaryAlert?.event_type === 'ai_anomaly' || Boolean(reading?.is_anomaly) || safeNumber(reading?.anomaly_score) >= 0.7;
  const isAqiWarning = safeNumber(reading?.aqi) >= 150;
  const alertType = isAiAnomaly ? 'AI Anomaly Event' : isAqiWarning ? 'AQI Health Alert' : 'Monitoring Event';
  const headline = reading
    ? `AQI ${Math.round(safeNumber(reading.aqi))} tại ${provinceName}, PM2.5 ${formatFixed(reading.pm2_5, 1)} µg/m³`
    : 'Chưa có cảnh báo nghiêm trọng từ API trong 24 giờ gần nhất.';

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-12">
        <h1 className="text-4xl font-bold mb-2">Trung tâm Y tế Môi trường</h1>
        <p className="text-on-surface-variant max-w-2xl">
          Giám sát thời gian thực và các biện pháp can thiệp y tế do AI điều khiển cho môi trường sống của bạn.
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          'mb-12 glass-card p-8 border-2',
          primaryAlert ? 'border-error bg-error/10' : 'border-primary/30 bg-primary/5',
        )}
      >
        <div className="flex items-start gap-6">
          {primaryAlert ? <ShieldAlert className="w-12 h-12 text-error" /> : <Heart className="w-12 h-12 text-primary" />}
          <div className="flex-1">
            <h2 className={cn('text-2xl font-bold mb-2 tracking-tight uppercase', primaryAlert ? 'text-error' : 'text-primary')}>
              {primaryAlert ? 'GIAO THỨC CẢNH BÁO ĐƯỢC KÍCH HOẠT' : 'TRẠNG THÁI THEO DÕI ỔN ĐỊNH'}
            </h2>
            <p className="text-on-surface-variant text-lg mb-6 leading-relaxed">{headline}</p>
            {anomalyQuery.error && (
              <p className="mb-4 text-xs font-mono text-warning">
                API anomalies chưa sẵn sàng, đang dùng danh sách fallback để UI không bị trống.
              </p>
            )}
            {!anomalyQuery.error && (
              <p className="mb-4 text-xs font-mono text-on-surface-variant">
                Nguồn: {anomalyQuery.source === 'api' ? 'API thật /api/anomalies' : 'mock fallback khi API lỗi'}.
              </p>
            )}
            <div className="flex flex-wrap gap-4">
              <AlertAction icon={<Activity />} text={primaryAlert ? 'Ở TRONG NHÀ' : 'TIẾP TỤC THEO DÕI'} active={Boolean(primaryAlert)} />
              <AlertAction icon={<Wind />} text="LỌC KHÍ TỐI ƯU" />
              <AlertAction icon={<Thermometer />} text="GIẢM VẬN ĐỘNG MẠNH" />
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div className="md:col-span-12 glass-card p-6 border-l-4 border-l-error">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-xl font-bold text-error uppercase font-mono tracking-wider">
              {primaryAlert ? `${alertType}: ${provinceName}` : 'AQI Health Alerts / AI Anomaly Events: Không có sự kiện mới'}
            </h3>
            <span className="text-xs font-mono text-on-surface-variant">
              {reading ? new Date(reading.time).toLocaleString('vi-VN') : '24 giờ gần nhất'}
            </span>
          </div>
          <p className="text-on-surface-variant">
            {reading
              ? `Hệ thống ghi nhận ${isAiAnomaly ? 'pattern bất thường theo model AI' : 'AQI vượt ngưỡng sức khỏe'}. Người dùng nhạy cảm nên giảm tiếp xúc ngoài trời.`
              : 'API không trả về anomaly hoặc AQI warning trong 24 giờ gần nhất. Đây là trạng thái ổn định, không phải dữ liệu giả.'}
          </p>
        </div>

        <div className="md:col-span-8 glass-card p-8">
          <h3 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <Activity className="w-6 h-6 text-primary" />
            Demo placeholder: Dị ứng & Phấn hoa
          </h3>
          <p className="mb-6 text-sm text-on-surface-variant">
            Khối này là minh họa UI, chưa nối với nguồn pollen/allergy thật. Các cảnh báo thật đang nằm ở phần API events phía trên.
          </p>
          <div className="space-y-8">
            <ProgressBar label="Phấn hoa Cỏ" value={85} color="bg-error" status="Rất cao" />
            <ProgressBar label="Bào tử Nấm mốc" value={65} color="bg-tertiary-container" status="Cao" />
            <ProgressBar label="Bụi hữu cơ" value={25} color="bg-primary" status="Thấp" />
          </div>
        </div>

        <div className="md:col-span-4 flex flex-col gap-8">
          <div className="glass-card p-8 border-l-4 border-l-primary-container">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-primary">
              <Heart className="w-5 h-5" /> Khuyến nghị Y tế
            </h3>
            <ul className="space-y-4 text-sm text-on-surface-variant">
              <Recommendation text="Sử dụng máy lọc không khí HEPA khi AQI vượt 100." />
              <Recommendation text="Đeo khẩu trang lọc bụi mịn khi ra ngoài vào giờ cao điểm." />
              <Recommendation text="Theo dõi nhóm nhạy cảm: trẻ em, người cao tuổi và người có bệnh hô hấp." />
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertAction({ icon, text, active }: { icon: ReactNode; text: string; active?: boolean }) {
  return (
    <div
      className={cn(
        'px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 border transition-all',
        active ? 'bg-error text-on-error border-error shadow-lg shadow-error/20' : 'bg-surface-container-high border-outline-variant/30 text-on-surface',
      )}
    >
      {icon}
      <span>{text}</span>
    </div>
  );
}

function Recommendation({ text }: { text: string }) {
  return (
    <li className="flex gap-3">
      <AlertTriangle className="w-4 h-4 text-primary mt-0.5 shrink-0" />
      <span>{text}</span>
    </li>
  );
}

function ProgressBar({ label, value, color, status }: { label: string; value: number; color: string; status: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="font-bold">{label}</span>
        <span className="font-mono">{status}</span>
      </div>
      <div className="w-full bg-surface-container-highest h-2.5 rounded-full">
        <motion.div initial={{ width: 0 }} animate={{ width: `${value}%` }} className={cn('h-full rounded-full', color)} />
      </div>
    </div>
  );
}
