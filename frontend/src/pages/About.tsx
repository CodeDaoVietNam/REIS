import { motion } from 'framer-motion';
import {
  Brain,
  Cloud,
  Code2,
  Database,
  Gauge,
  Layers,
  LineChart,
  Radio,
  Server,
  Shield,
  Sparkles,
  Users,
  Zap,
} from 'lucide-react';
import type { ReactNode } from 'react';

const TECH_STACK = [
  { icon: <Server className="h-6 w-6" />, name: 'FastAPI', desc: 'Async Python REST + WebSocket API' },
  { icon: <Radio className="h-6 w-6" />, name: 'Apache Kafka', desc: 'Event streaming & message broker' },
  { icon: <Database className="h-6 w-6" />, name: 'TimescaleDB', desc: 'Time-series database (hypertable)' },
  { icon: <Zap className="h-6 w-6" />, name: 'Redis', desc: 'Cache, DLQ, latest state store' },
  { icon: <Brain className="h-6 w-6" />, name: 'Isolation Forest', desc: 'Unsupervised anomaly detection' },
  { icon: <LineChart className="h-6 w-6" />, name: 'LSTM / Prophet', desc: 'Time-series AQI forecasting' },
  { icon: <Sparkles className="h-6 w-6" />, name: 'Gemini AI', desc: 'Natural language insight generation' },
  { icon: <Cloud className="h-6 w-6" />, name: 'Docker Compose', desc: '12 containers, 1 command deployment' },
];

const ARCH_LAYERS = [
  { num: '01', name: 'Data Ingestion', desc: 'Batch API requests cho 63 tỉnh, async parallel, Pydantic validation, exponential backoff retry' },
  { num: '02', name: 'Message Broker', desc: 'Kafka decoupling với 7-day retention, at-least-once delivery, manual offset commit' },
  { num: '03', name: 'Storage', desc: 'TimescaleDB hypertable (chunk 7 ngày), partial indexes, Redis triple-role (DLQ + cache + state)' },
  { num: '04', name: 'AI Inference', desc: 'IsolationForest (anomaly) + LSTM (forecast) chạy song song, Gemini LLM insight với AQI bucketing cache' },
  { num: '05', name: 'Delivery & MLOps', desc: 'FastAPI REST + WebSocket broadcast, Telegram alerts, Airflow weekly retrain, MLflow registry' },
];

export default function About() {
  return (
    <div className="mx-auto max-w-[1200px] px-6 py-12">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-16 text-center"
      >
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.3em] text-primary">About the system</p>
        <h1 className="text-5xl font-black tracking-tight">
          REIS
        </h1>
        <p className="mt-2 text-xl text-on-surface-variant">
          Realtime Environmental Intelligence System
        </p>
        <p className="mx-auto mt-6 max-w-2xl text-on-surface-variant">
          Hệ thống giám sát chất lượng không khí realtime cho 63 tỉnh thành Việt Nam,
          kết hợp AI phát hiện bất thường, dự báo AQI, và giải thích bằng ngôn ngữ tự nhiên tiếng Việt.
        </p>
      </motion.div>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className="mb-8 text-2xl font-bold">Kiến trúc 5 tầng</h2>
        <div className="space-y-4">
          {ARCH_LAYERS.map((layer, i) => (
            <motion.div
              key={layer.num}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card flex items-start gap-6 p-6"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 font-mono text-lg font-black text-primary">
                {layer.num}
              </div>
              <div>
                <h3 className="text-lg font-bold">{layer.name}</h3>
                <p className="mt-1 text-sm text-on-surface-variant">{layer.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Data Flow */}
      <section className="mb-16">
        <h2 className="mb-6 text-2xl font-bold">Luồng dữ liệu</h2>
        <div className="glass-card overflow-x-auto p-6">
          <div className="flex items-center justify-between gap-2 text-center text-xs font-mono min-w-[700px]">
            <FlowStep icon={<Gauge className="h-5 w-5" />} label="Open-Meteo API" sub="63 tỉnh × 15min" />
            <Arrow />
            <FlowStep icon={<Shield className="h-5 w-5" />} label="Pydantic Validate" sub="10 biến / tỉnh" />
            <Arrow />
            <FlowStep icon={<Radio className="h-5 w-5" />} label="Kafka" sub="7-day retention" />
            <Arrow />
            <FlowStep icon={<Database className="h-5 w-5" />} label="TimescaleDB" sub="hypertable" />
            <Arrow />
            <FlowStep icon={<Brain className="h-5 w-5" />} label="Dual AI" sub="IsoForest + LSTM" />
            <Arrow />
            <FlowStep icon={<Sparkles className="h-5 w-5" />} label="LLM Insight" sub="Gemini tiếng Việt" />
            <Arrow />
            <FlowStep icon={<Layers className="h-5 w-5" />} label="Dashboard" sub="React + WS" />
          </div>
        </div>
      </section>

      {/* Tech Stack Grid */}
      <section className="mb-16">
        <h2 className="mb-8 text-2xl font-bold">Công nghệ sử dụng</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {TECH_STACK.map((tech, i) => (
            <motion.div
              key={tech.name}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card flex flex-col items-center p-6 text-center"
            >
              <div className="mb-3 rounded-2xl bg-primary/10 p-3 text-primary">{tech.icon}</div>
              <h3 className="font-bold">{tech.name}</h3>
              <p className="mt-1 text-xs text-on-surface-variant">{tech.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Team */}
      <section className="mb-16">
        <h2 className="mb-8 text-2xl font-bold flex items-center gap-3">
          <Users className="h-6 w-6 text-primary" />
          Nhóm phát triển
        </h2>
        <div className="glass-card p-8 text-center">
          <p className="text-on-surface-variant">
            Dự án được phát triển bởi nhóm sinh viên, ứng dụng kiến thức Big Data, Machine Learning,
            và Software Engineering để giải quyết bài toán giám sát môi trường thực tế tại Việt Nam.
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <a
              href="https://github.com/CodeDaoVietNam/REIS"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-6 py-3 font-mono text-sm font-bold text-primary transition hover:bg-primary/20"
            >
              <Code2 className="h-4 w-4" />
              Source Code
            </a>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Tỉnh thành" value="63" />
          <StatCard label="Biến / tỉnh" value="10" />
          <StatCard label="Chu kỳ" value="15 min" />
          <StatCard label="Records / năm" value="~2.2M" />
        </div>
      </section>
    </div>
  );
}

function FlowStep({ icon, label, sub }: { icon: ReactNode; label: string; sub: string }) {
  return (
    <div className="flex flex-col items-center gap-1 min-w-[80px]">
      <div className="rounded-xl bg-primary/10 p-2 text-primary">{icon}</div>
      <span className="font-bold text-on-surface text-[11px]">{label}</span>
      <span className="text-on-surface-variant text-[10px]">{sub}</span>
    </div>
  );
}

function Arrow() {
  return <div className="text-primary font-bold text-lg shrink-0">→</div>;
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="glass-card p-6 text-center">
      <p className="text-3xl font-black text-primary">{value}</p>
      <p className="mt-1 text-xs font-mono uppercase tracking-widest text-on-surface-variant">{label}</p>
    </div>
  );
}
