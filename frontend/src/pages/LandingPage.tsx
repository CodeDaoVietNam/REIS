import React from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { ArrowRight, Wind, Droplets, Sun, Cloud, Leaf, Shield, Zap, Globe, MousePointer2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  const { scrollYProgress } = useScroll();
  const y1 = useTransform(scrollYProgress, [0, 1], [0, -200]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, -500]);

  const features = [
    {
      icon: <Wind className="w-8 h-8 text-primary" />,
      title: "Khí quyển Thông minh",
      desc: "Hệ thống AI phân tích hàng tỷ điểm dữ liệu để dự báo chính xác nồng độ bụi mịn PM2.5 trong 48 giờ tới.",
      tag: "Dự báo AI"
    },
    {
      icon: <Sun className="w-8 h-8 text-warning" />,
      title: "Chỉ số Bức xạ UV",
      desc: "Cảnh báo thời gian thực về cường độ tia cực tím, giúp bảo vệ làn da và sức khỏe cộng đồng hiệu quả.",
      tag: "An toàn Sức khỏe"
    },
    {
      icon: <Droplets className="w-8 h-8 text-secondary" />,
      title: "Thủy văn & Độ ẩm",
      desc: "Giám sát lưu lượng mưa và độ ẩm không khí, hỗ trợ quản lý tài nguyên nước và nông nghiệp thông minh.",
      tag: "Giám sát Thủy văn"
    }
  ];

  return (
    <div className="min-h-screen bg-background text-on-surface selection:bg-primary/30 overflow-x-hidden">
      {/* Sophisticated Background System */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_-20%,var(--color-primary-container),transparent_60%)] opacity-30" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_0%_40%,var(--color-secondary),transparent_40%)] opacity-10" />
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-[0.03] invert dark:invert-0" />
        
        {/* Animated Particles */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            animate={{
              y: [0, -100, 0],
              opacity: [0.1, 0.3, 0.1],
              scale: [1, 1.2, 1]
            }}
            transition={{
              duration: 10 + i * 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute bg-primary/20 blur-3xl rounded-full"
            style={{
              width: `${100 + i * 50}px`,
              height: `${100 + i * 50}px`,
              left: `${i * 20}%`,
              top: `${20 + i * 15}%`,
            }}
          />
        ))}
      </div>

      <header className="relative z-10 pt-24 pb-12 px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
            className="text-center relative"
          >
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="inline-flex items-center gap-3 py-2 px-5 rounded-full bg-surface-container-low border border-outline-variant/30 text-primary text-xs font-bold mb-10 shadow-lg backdrop-blur-md cursor-default"
            >
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              CHỈ SỐ THỰC THỜI: HANOI 42 AQI (TỐT)
            </motion.div>

            <h1 className="text-6xl md:text-[120px] font-black tracking-tighter leading-[0.9] mb-12">
              QUYỀN NĂNG <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-b from-primary via-primary to-secondary drop-shadow-2xl">
                DỮ LIỆU XANH
              </span>
            </h1>

            <p className="text-lg md:text-2xl text-on-surface-variant max-w-3xl mx-auto mb-16 leading-relaxed font-medium">
              Kiến tạo tương lai bền vững với nền tảng phân tích môi trường thông minh nhất Việt Nam. AeroSense chuyển hóa dữ liệu thô thành hành động bảo vệ sức khỏe.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Link 
                to="/dashboard"
                className="group relative px-10 py-5 bg-primary text-on-primary rounded-2xl font-black text-lg overflow-hidden transition-all hover:scale-105 active:scale-95 shadow-[0_20px_50px_rgba(78,222,163,0.3)]"
              >
                <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500" />
                <span className="flex items-center gap-3 relative z-10">
                  KHÁM PHÁ NGAY <ArrowRight className="w-6 h-6" />
                </span>
              </Link>
              <button className="group px-10 py-5 bg-surface-container-high text-on-surface rounded-2xl font-black text-lg hover:bg-surface-container-highest transition-all flex items-center gap-3 border border-outline-variant/20">
                TÀI LIỆU API <Zap className="w-6 h-6 group-hover:text-warning transition-colors" />
              </button>
            </div>
          </motion.div>
        </div>

        {/* Floating Elements for Parallax */}
        <motion.div style={{ y: y1 }} className="absolute top-1/4 -left-20 opacity-10 pointer-events-none hidden lg:block">
          <Globe className="w-96 h-96 text-primary" />
        </motion.div>
        <motion.div style={{ y: y2 }} className="absolute bottom-0 -right-20 opacity-5 pointer-events-none hidden lg:block">
          <Shield className="w-[500px] h-[500px] text-secondary" />
        </motion.div>
      </header>

      <section className="relative z-10 max-w-7xl mx-auto px-6 py-32">
        <div className="flex flex-col md:flex-row justify-between items-end mb-20 gap-8">
          <div className="max-w-xl">
            <h2 className="text-sm font-black text-primary uppercase tracking-[0.3em] mb-4">Giá trị cốt lõi</h2>
            <p className="text-4xl md:text-5xl font-bold tracking-tight">Công nghệ vị nhân sinh, môi trường vì tương lai.</p>
          </div>
          <p className="text-on-surface-variant max-w-sm text-lg italic">"Chúng tôi tin rằng mọi người dân đều có quyền được biết chính xác về chất lượng bầu không khí họ đang hít thở."</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -15 }}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2 }}
              className="group p-1 bg-gradient-to-b from-outline-variant/30 to-transparent rounded-[2.5rem]"
            >
              <div className="bg-surface-container-low p-10 rounded-[2.4rem] h-full transition-colors group-hover:bg-surface-container-high">
                <div className="text-[10px] font-black text-primary mb-8 tracking-[0.2em]">{f.tag}</div>
                <div className="p-5 bg-surface-container-highest rounded-3xl w-fit mb-10 shadow-inner group-hover:scale-110 transition-transform">
                  {f.icon}
                </div>
                <h3 className="text-2xl font-black mb-6 tracking-tight uppercase">{f.title}</h3>
                <p className="text-on-surface-variant leading-relaxed text-lg">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Featured Dashboard Preview */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pb-48">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="group relative rounded-[4rem] overflow-hidden border-[1px] border-outline-variant/30 shadow-[0_50px_100px_rgba(0,0,0,0.4)]"
        >
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10 pointer-events-none" />
          <img 
            src="https://images.unsplash.com/photo-1590055531615-f16d36ffe8bb?q=80&w=2000&auto=format&fit=crop"
            alt="Data Visualization"
            className="w-full h-[700px] object-cover transition-transform duration-[2s] group-hover:scale-110"
          />
          
          <div className="absolute inset-0 z-20 flex flex-col justify-center items-center text-center p-12 bg-black/40 backdrop-blur-[2px]">
            <motion.div 
               animate={{ y: [0, 10, 0] }}
               transition={{ duration: 2, repeat: Infinity }}
               className="w-20 h-20 rounded-full border-2 border-white flex items-center justify-center mb-10"
            >
               <MousePointer2 className="w-8 h-8 text-white fill-white" />
            </motion.div>
            <h3 className="text-5xl md:text-7xl font-black text-white mb-8 tracking-tighter">BẢN ĐỒ NHIỆT <br /> THỜI GIAN THỰC</h3>
            <Link to="/map" className="px-12 py-5 bg-white text-black rounded-full font-black hover:scale-110 transition-all shadow-2xl">
               TRUY CẬP HỆ THỐNG PHÂN TÍCH
            </Link>
          </div>
        </motion.div>

        {/* Stats Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20">
           {[
             { label: "Trạm đo", val: "2,400+" },
             { label: "Người dùng", val: "1.2M" },
             { label: "Độ chính xác", val: "99.2%" },
             { label: "Vùng phủ", val: "63 Tỉnh" }
           ].map((s, i) => (
             <div key={i} className="text-center p-8 bg-surface-container-low rounded-3xl border border-outline-variant/10 hover:border-primary/30 transition-all">
                <div className="text-3xl font-black text-primary mb-2 tracking-tighter">{s.val}</div>
                <div className="text-xs font-bold text-on-surface-variant uppercase tracking-widest">{s.label}</div>
             </div>
           ))}
        </div>
      </section>

      <footer className="relative z-10 py-20 border-t border-outline-variant/20 bg-surface-container-low/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-12 text-center md:text-left">
          <div>
            <div className="text-3xl font-black tracking-tighter mb-4">REIS<span className="text-primary">.</span></div>
            <p className="text-on-surface-variant max-w-sm">Dự án mã nguồn mở vì cộng đồng, nhằm cung cấp dữ liệu môi trường minh bạch cho mọi người dân Việt Nam.</p>
          </div>
          <div className="flex gap-10 font-bold text-sm">
            <a href="#" className="hover:text-primary transition-colors">VỀ CHÚNG TÔI</a>
            <a href="#" className="hover:text-primary transition-colors">ĐIỀU KHOẢN</a>
            <a href="#" className="hover:text-primary transition-colors">LIÊN HỆ</a>
          </div>
          <div className="flex gap-4">
            <div className="w-12 h-12 bg-surface-container-highest rounded-full flex items-center justify-center hover:bg-primary hover:text-on-primary transition-all cursor-pointer"><Leaf className="w-5 h-5" /></div>
            <div className="w-12 h-12 bg-surface-container-highest rounded-full flex items-center justify-center hover:bg-primary hover:text-on-primary transition-all cursor-pointer"><Globe className="w-5 h-5" /></div>
          </div>
        </div>
        <div className="text-center mt-20 text-[10px] font-bold text-on-surface-variant opacity-30 tracking-[0.5em] uppercase">© 2026 AEROSENSE VIETNAM - ALL RIGHTS RESERVED</div>
      </footer>
    </div>
  );
}
