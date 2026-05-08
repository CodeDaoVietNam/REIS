import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, ShieldAlert, Activity, Heart, Thermometer, Wind, Droplets } from 'lucide-react';
import { cn } from '@/src/lib/utils';

export default function HealthAlerts() {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-12">
        <h1 className="text-4xl font-bold mb-2">Trung tâm Y tế Môi trường</h1>
        <p className="text-on-surface-variant max-w-2xl">Giám sát thời gian thực và các biện pháp can thiệp y tế do AI điều khiển cho môi trường sống của bạn.</p>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-12 glass-card p-8 border-2 border-error bg-error/10"
      >
        <div className="flex items-start gap-6">
          <ShieldAlert className="w-12 h-12 text-error" />
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-error mb-2 tracking-tight uppercase">GIAO THỨC KHẨN CẤP ĐƯỢC KÍCH HOẠT</h2>
            <p className="text-on-surface-variant text-lg mb-6 leading-relaxed">
              Phát hiện sự kết hợp nguy hiểm: Sóng nhiệt cực đại (42°C) + Khói cháy rừng nghiêm trọng (PM2.5: 245 µg/m³).
            </p>
            <div className="flex flex-wrap gap-4">
              <AlertAction icon={<Activity />} text="Ở TRONG NHÀ" active />
              <AlertAction icon={<Wind />} text="LỌC KHÍ TỐI ĐA" />
              <AlertAction icon={<Thermometer />} text="DUY TRÌ LÀM MÁT" />
            </div>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        <div className="md:col-span-12 glass-card p-6 border-l-4 border-l-error">
           <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-error uppercase font-mono tracking-wider">Cảnh báo: Bụi mịn nguy hại</h3>
              <span className="text-xs font-mono text-on-surface-variant">2 phút trước</span>
           </div>
           <p className="text-on-surface-variant">Sự gia tăng đột ngột của nồng độ bụi mịn PM2.5 được ghi nhận tại các quận nội thành Hà Nội. Tầm nhìn giảm xuống còn dưới 500m.</p>
        </div>

        <div className="md:col-span-8 glass-card p-8">
           <h3 className="text-2xl font-bold mb-8 flex items-center gap-2">
              <Activity className="w-6 h-6 text-primary" />
              Dự báo Dị ứng & Phấn hoa
           </h3>
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
                <li className="flex gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                  <span>Sử dụng máy lọc không khí HEPA liên tục.</span>
                </li>
                <li className="flex gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                  <span>Súc họng và nhỏ mắt thường xuyên bằng nước muối sinh lý.</span>
                </li>
                <li className="flex gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5" />
                  <span>Hạn chế sử dụng bếp than, bếp củi trong thời gian này.</span>
                </li>
              </ul>
           </div>
        </div>
      </div>
    </div>
  );
}

function AlertAction({ icon, text, active }: { icon: React.ReactNode, text: string, active?: boolean }) {
  return (
    <div className={cn(
      "px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 border transition-all",
      active ? "bg-error text-on-error border-error shadow-lg shadow-error/20" : "bg-surface-container-high border-outline-variant/30 text-on-surface"
    )}>
      {icon}
      <span>{text}</span>
    </div>
  );
}

function ProgressBar({ label, value, color, status }: { label: string, value: number, color: string, status: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="font-bold">{label}</span>
        <span className="font-mono">{status}</span>
      </div>
      <div className="w-full bg-surface-container-highest h-2.5 rounded-full">
        <motion.div initial={{ width: 0 }} animate={{ width: `${value}%` }} className={cn("h-full rounded-full", color)} />
      </div>
    </div>
  );
}
