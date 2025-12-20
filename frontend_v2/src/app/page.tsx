"use client";

import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Zap,
  Info,
  Clock,
  Target,
  Activity,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Navigation
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Helper for tailwind classes
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface TradeResult {
  symbol: string;
  display_name: string;
  timestamp: string;
  data: {
    decision: string;
    confidence: number;
    reasoning: string;
    entry_price: number;
    stop_loss: number;
    take_profit: number;
    rr_ratio: number;
    technical_score: number;
    sentiment_score: number;
    user_message?: string;
    presented_confidence?: number;
  };
}

const ScoreBadge = ({ label, score, colorClass }: { label: string, score: number, colorClass: string }) => (
  <div className="flex flex-col gap-1">
    <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider text-slate-500">
      <span>{label}</span>
      <span>{score}%</span>
    </div>
    <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden border border-white/5">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${score}%` }}
        className={cn("h-full rounded-full", colorClass)}
      />
    </div>
  </div>
);

export default function Home() {
  const [results, setResults] = useState<TradeResult[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/results');
      if (!res.ok) throw new Error('Network response was not ok');
      const data = await res.json();
      setResults(data);
      setLoading(false);
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-slate-100 p-4 md:p-8 font-sans">
      {/* Background Decorative Elements */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/10 rounded-full blur-[120px]" />
      </div>

      <header className="max-w-7xl mx-auto mb-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-6 border-b border-white/5 pb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500 border border-blue-500/20">
              <Activity size={24} />
            </div>
            <h1 className="text-3xl font-black tracking-tighter">
              SNIPER <span className="gradient-text">QUANT</span> OS
            </h1>
          </div>
          <p className="text-slate-400 text-sm font-medium flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            İşlem Motoru Aktif • Gerçek Zamanlı Analiz
          </p>
        </div>

        <div className="flex gap-3">
          <div className="glass px-5 py-2.5 rounded-xl border-white/10 flex flex-col gap-0.5">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Sistem Durumu</span>
            <span className="text-emerald-400 text-sm font-black flex items-center gap-1.5">
              <Zap size={14} fill="currentColor" /> OPTİMİZE
            </span>
          </div>
          <div className="glass px-5 py-2.5 rounded-xl border-white/10 flex flex-col gap-0.5">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Motor Modu</span>
            <span className="text-blue-400 text-sm font-black">AI ENSEMBLE</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto">
        {loading ? (
          <div className="h-[60vh] flex flex-col items-center justify-center gap-4 text-slate-500">
            <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
            <p className="font-bold tracking-widest text-xs uppercase">Veriler Yükleniyor...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            <AnimatePresence mode="popLayout">
              {results.length > 0 ? (
                results.map((item, idx) => {
                  const isBuy = item.data.decision?.includes('BUY');
                  const isSell = item.data.decision?.includes('SELL');
                  const confidence = item.data.presented_confidence || item.data.confidence || 0;

                  return (
                    <motion.div
                      layout
                      key={item.symbol + item.timestamp}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ duration: 0.4, ease: "circOut" }}
                      className="glass rounded-[32px] overflow-hidden border-white/5 glow flex flex-col group"
                    >
                      {/* Sub-header */}
                      <div className="p-5 flex justify-between items-center bg-white/5">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "w-10 h-10 rounded-2xl flex items-center justify-center font-black text-lg border transition-all duration-500 group-hover:scale-110",
                            isBuy ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.1)]" :
                              isSell ? "bg-red-500/10 text-red-400 border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.1)]" :
                                "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          )}>
                            {item.symbol.charAt(0)}
                          </div>
                          <div>
                            <h2 className="font-black text-lg leading-tight uppercase tracking-tight">{item.display_name.split(' ')[0]}</h2>
                            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{item.symbol}</p>
                          </div>
                        </div>
                        <div className={cn(
                          "px-4 py-1.5 rounded-full text-[10px] font-black tracking-widest border uppercase",
                          isBuy ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" :
                            isSell ? "bg-red-500/20 text-red-400 border-red-500/30" :
                              "bg-slate-800 text-slate-400 border-white/5"
                        )}>
                          {item.data.decision}
                        </div>
                      </div>

                      {/* Reasoning Box */}
                      <div className="px-5 pt-4">
                        <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-xs text-slate-400 leading-relaxed min-h-[80px] flex items-start gap-3">
                          <Navigation className={cn("shrink-0 mt-0.5", isBuy ? "text-emerald-500 rotate-45" : isSell ? "text-red-500 rotate-[225deg]" : "text-slate-500")} size={16} />
                          <p>{item.data.user_message || item.data.reasoning}</p>
                        </div>
                      </div>

                      {/* Financial Detail Grid */}
                      <div className="p-5 grid grid-cols-2 gap-3">
                        <div className="bg-white/2 p-3 rounded-xl border border-white/5 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-500 font-bold uppercase flex items-center gap-1.5">
                            <Target size={12} className="text-blue-500" /> Giriş
                          </span>
                          <span className="text-sm font-mono font-black text-slate-200">{item.data.entry_price?.toFixed(5)}</span>
                        </div>
                        <div className="bg-white/2 p-3 rounded-xl border border-white/5 flex flex-col gap-1">
                          <span className="text-[10px] text-slate-500 font-bold uppercase flex items-center gap-1.5">
                            <ShieldCheck size={12} className="text-emerald-500" /> Risk/Ödül
                          </span>
                          <span className={cn("text-sm font-mono font-black",
                            item.data.rr_ratio >= 1.5 ? "text-blue-400" : "text-slate-500"
                          )}>
                            {item.data.rr_ratio?.toFixed(2)}:1
                          </span>
                        </div>
                      </div>

                      {/* Scores Card */}
                      <div className="px-5 pb-5 mt-auto">
                        <div className="space-y-4 bg-white/5 p-4 rounded-2xl border border-white/5">
                          <ScoreBadge label="Teknik Onay" score={item.data.technical_score || 0} colorClass="bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.3)]" />
                          <ScoreBadge label="Piyasa Duyarlılığı" score={item.data.sentiment_score || 0} colorClass="bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]" />
                          <ScoreBadge label="Motor Güveni" score={confidence} colorClass="bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]" />
                        </div>
                      </div>

                      {/* Footer */}
                      <div className="px-5 py-3 bg-white/5 border-t border-white/5 flex justify-between items-center">
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                          <Clock size={12} /> {item.timestamp.split(' ')[1]}
                        </div>
                        <div className="flex gap-4">
                          <span className="text-[10px] font-black text-red-500/80">SL: {item.data.stop_loss?.toFixed(5)}</span>
                          <span className="text-[10px] font-black text-emerald-500/80">TP: {item.data.take_profit?.toFixed(5)}</span>
                        </div>
                      </div>
                    </motion.div>
                  );
                })
              ) : (
                <div className="col-span-full py-20 text-center">
                  <p className="text-slate-500 font-bold uppercase tracking-widest text-sm">Aktif Sinyal Bulunmuyor</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        )}
      </main>

      <footer className="max-w-7xl mx-auto mt-20 pb-10 border-t border-white/5 pt-10 flex flex-col md:flex-row justify-between items-center gap-6 opacity-40 hover:opacity-100 transition-opacity">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-[0.2em]">© 2025 Sniper AI QuantOS • Tüm Hakları Saklıdır</p>
        <div className="flex gap-8 text-[10px] font-black uppercase tracking-widest text-slate-400">
          <a href="#" className="hover:text-blue-400 transition-colors">Dökümantasyon</a>
          <a href="#" className="hover:text-blue-400 transition-colors">API Erişimi</a>
          <a href="#" className="hover:text-blue-400 transition-colors">Sistem Kayıtları</a>
        </div>
      </footer>
    </div>
  );
}
