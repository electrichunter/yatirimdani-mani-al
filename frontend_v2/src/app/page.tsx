
"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Database, BrainCircuit, Timer, Zap, Cpu, Activity, ShieldCheck, Terminal as TerminalIcon, Shell } from 'lucide-react';
import Terminal from '@/components/Terminal';

export default function SetupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('Checking');
  const [config, setConfig] = useState({
    dataSource: 'C',
    llm: 'G',
    timeframe: '1'
  });

  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/status');
        if (res.ok) setApiStatus('Online');
        else setApiStatus('Offline');
      } catch {
        setApiStatus('Offline');
      }
    };
    checkApi();
    const inv = setInterval(checkApi, 3000);
    return () => clearInterval(inv);
  }, []);

  const handleFire = async () => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...config, duration: 0, mode: 'T' })
      });
      if (resp.ok) {
        setTimeout(() => router.push('/dashboard'), 1000);
      } else {
        alert("Bağlantı Hatası: Konfigürasyon kaydedilemedi.");
        setLoading(false);
      }
    } catch (err) {
      alert("Hata: API sunucusuna ulaşılamıyor!");
      setLoading(false);
    }
  };

  const handleStop = async () => {
    if (!confirm("Tüm sistemi kapatmak istediğinize emin misiniz?")) return;
    try {
      const resp = await fetch('http://localhost:8000/api/stop', { method: 'POST' });
      if (resp.ok) {
        alert("Kapatma sinyali gönderildi. Terminal otomatik kapanacak.");
      }
    } catch (err) {
      alert("Hata: API'ye ulaşılamadı.");
    }
  };

  return (
    <div className="max-w-[1200px] mx-auto pb-20">
      {/* Header Info */}
      <header className="flex justify-between items-center mb-10 pb-6 border-b border-[#30363d]">
        <div>
          <h1 className="text-3xl font-bold text-[#e6edf3]">Bot Kurulumu</h1>
          <p className="text-[#8b949e] text-sm mt-1">Sistemi başlatmak için temel parametreleri belirleyin.</p>
        </div>
        <div className={`status-badge ${apiStatus === 'Online' ? 'badge-green' : 'badge-red'}`}>
          <span className="live-dot" style={{ background: apiStatus === 'Online' ? '#3fb950' : '#f85149' }}></span>
          API: {apiStatus}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
        {/* Source Selection */}
        <div className="card h-full">
          <div className="flex items-center gap-2 mb-6 text-[#2f81f7]">
            <Database size={20} />
            <h3 className="text-lg font-bold">Veri Kaynağı</h3>
          </div>
          <div className="space-y-3">
            <button
              onClick={() => setConfig({ ...config, dataSource: 'C' })}
              className={`w-full p-4 text-left border rounded-lg transition-all ${config.dataSource === 'C' ? 'border-[#2f81f7] bg-[#1f242b] text-[#e6edf3]' : 'border-[#30363d] bg-transparent text-[#8b949e] hover:border-[#8b949e]'}`}
            >
              <div className="font-bold">Yahoo Finance (Canlı)</div>
              <div className="text-[11px] opacity-70 mt-1">Eşzamanlı küresel piyasa verileri</div>
            </button>
            <button
              onClick={() => setConfig({ ...config, dataSource: 'D' })}
              className={`w-full p-4 text-left border rounded-lg transition-all ${config.dataSource === 'D' ? 'border-[#2f81f7] bg-[#1f242b] text-[#e6edf3]' : 'border-[#30363d] bg-transparent text-[#8b949e] hover:border-[#8b949e]'}`}
            >
              <div className="font-bold">Simüle Veri (Demo)</div>
              <div className="text-[11px] opacity-70 mt-1">Yapay veri ile test analizi</div>
            </button>
          </div>
        </div>

        {/* Brain Selection */}
        <div className="card h-full">
          <div className="flex items-center gap-2 mb-6 text-[#7000ff]">
            <BrainCircuit size={20} />
            <h3 className="text-lg font-bold">Analiz Motoru</h3>
          </div>
          <div className="space-y-3">
            <button
              onClick={() => setConfig({ ...config, llm: 'G' })}
              className={`w-full p-4 text-left border rounded-lg transition-all ${config.llm === 'G' ? 'border-[#2f81f7] bg-[#1f242b] text-[#e6edf3]' : 'border-[#30363d] bg-transparent text-[#8b949e] hover:border-[#8b949e]'}`}
            >
              <div className="font-bold">Google Gemini 2.0</div>
              <div className="text-[11px] opacity-70 mt-1">Ultra- hızlı bulut bilişim</div>
            </button>
            <button
              onClick={() => setConfig({ ...config, llm: 'O' })}
              className={`w-full p-4 text-left border rounded-lg transition-all ${config.llm === 'O' ? 'border-[#2f81f7] bg-[#1f242b] text-[#e6edf3]' : 'border-[#30363d] bg-transparent text-[#8b949e] hover:border-[#8b949e]'}`}
            >
              <div className="font-bold">Ollama (Lokal)</div>
              <div className="text-[11px] opacity-70 mt-1">Donanım destekli yerel analiz</div>
            </button>
          </div>
        </div>

        {/* Timeframe Selection */}
        <div className="card h-full">
          <div className="flex items-center gap-2 mb-6 text-[#d29922]">
            <Timer size={20} />
            <h3 className="text-lg font-bold">Tarama Hızı</h3>
          </div>
          <div className="space-y-4">
            <select
              value={config.timeframe}
              onChange={(e) => setConfig({ ...config, timeframe: e.target.value })}
              className="w-full bg-[#0d1117] border border-[#30363d] p-4 rounded-lg font-bold text-sm outline-none text-[#e6edf3] focus:border-[#2f81f7] cursor-pointer"
            >
              <option value="S">🔥 Ultra Hızlı Tarama (10s)</option>
              <option value="1">Her Saat Yenile (H1)</option>
              <option value="4">4 Saatte Bir (H4)</option>
              <option value="D">Günlük Analiz (D1)</option>
            </select>
            <div className="p-4 bg-[rgba(210,153,34,0.05)] border border-[rgba(210,153,34,0.1)] rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Activity size={14} className="text-[#d29922]" />
                <span className="text-[10px] font-bold text-[#d29922] uppercase">Operasyon Modu</span>
              </div>
              <p className="text-[12px] text-[#8b949e]">Sistem sonsuz otonom döngüde çalışır.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Area */}
      <div className="flex flex-col items-center gap-8 mb-16">
        <div className="flex w-full max-w-3xl gap-4">
          <button
            onClick={handleFire}
            disabled={loading || apiStatus === 'Offline'}
            className="fire-button flex-1 py-8 text-xl group"
          >
            {loading ? (
              <div className="w-6 h-6 border-4 border-white/20 border-t-white rounded-full animate-spin"></div>
            ) : (
              <Zap size={24} fill="white" />
            )}
            <span>{loading ? 'YÜKLENİYOR...' : 'BOTU BAŞLAT'}</span>
          </button>

          <button
            onClick={handleStop}
            className="px-8 py-8 border border-[#da3633] bg-[rgba(218,54,51,0.05)] text-[#f85149] hover:bg-[#da3633] hover:text-white rounded-lg font-bold transition-all flex items-center gap-3"
            title="Sistemi Tamamen Kapat"
          >
            <Shell size={20} className="animate-spin-slow" />
            <span>DURDUR</span>
          </button>
        </div>

        <div className="flex gap-8">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#8b949e]">
            <ShieldCheck size={16} className="text-[#238636]" />
            Risk Yönetimi: %10 Maks.
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#8b949e]">
            <Cpu size={16} className="text-[#2f81f7]" />
            Engine: Autonomous V2
          </div>
        </div>
      </div>

      {/* Log Console */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-[#8b949e]">
          <TerminalIcon size={16} />
          <h4 className="text-xs font-bold uppercase tracking-wider">Sistem Kayıtları (Log Console)</h4>
        </div>
        <Terminal />
      </div>
    </div>
  );
}
