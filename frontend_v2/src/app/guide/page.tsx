
"use client";
import { BookOpen, Info, Shield, Zap, Search, HelpCircle } from 'lucide-react';

export default function GuidePage() {
    return (
        <div className="space-y-10 max-w-5xl">
            <header className="pb-8 border-b border-[#30363d]">
                <h1 className="text-3xl font-bold text-[#e6edf3]">Sistem Rehberi</h1>
                <p className="text-[#8b949e] text-sm mt-1">Sniper v2.1 Otonom Trading Motoru çalışma prensipleri.</p>
            </header>

            <div className="guide-section">
                <div className="guide-title">
                    <Info size={20} />
                    Sistem Nasıl Çalışır?
                </div>
                <p className="text-[#8b949e] text-sm mb-6 leading-relaxed">
                    Sniper Trading Bot, teknik analiz, haber sentimenti ve LLM (Büyük Dil Modelleri) onay mekanizmasını birleştiren 3 aşamalı bir karar yapısı kullanır.
                </p>
                <div className="guide-grid">
                    <div className="guide-item">
                        <h3 className="flex items-center gap-2">
                            <Search size={14} className="text-[#2f81f7]" />
                            1. Aşama: Teknik Filtre
                        </h3>
                        <p>RSI, MACD ve Hareketli Ortalamalar kullanılarak piyasa taranır. Sadece güçlü sinyal veren pariteler bir sonraki aşamaya geçer.</p>
                    </div>
                    <div className="guide-item">
                        <h3 className="flex items-center gap-2">
                            <Zap size={14} className="text-[#3fb950]" />
                            2. Aşama: Haber Analizi
                        </h3>
                        <p>Seçilen parite hakkında son 24 saatteki global haberler taranır. Sentiment skoru teknik sinyali desteklemiyorsa işlem reddedilir.</p>
                    </div>
                    <div className="guide-item">
                        <h3 className="flex items-center gap-2">
                            <Shield size={14} className="text-[#7000ff]" />
                            3. Aşama: LLM Kararı
                        </h3>
                        <p>Gemini veya Ollama, tüm verileri (Teknik + Haber) birleştirerek nihai kararı verir ve stop/profit seviyelerini hesaplar.</p>
                    </div>
                </div>
            </div>

            <div className="guide-grid">
                <div className="card">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <HelpCircle size={18} className="text-[#d29922]" />
                        Terimler Sözlüğü
                    </h3>
                    <ul className="space-y-4">
                        <li>
                            <span className="block text-sm font-bold text-[#e6edf3]">R:R Oranı (Risk/Reward)</span>
                            <span className="text-[12px] text-[#8b949e]">Riski göze alınan 1 birim karşılığında beklenen kazanç potansiyeli. En az 1.5 olması önerilir.</span>
                        </li>
                        <li>
                            <span className="block text-sm font-bold text-[#e6edf3]">Confidence (Güven Skoru)</span>
                            <span className="text-[12px] text-[#8b949e]">Modelin bu işleme olan güven yüzdesi. %75 ve üzeri işlemler daha güvenilir kabul edilir.</span>
                        </li>
                        <li>
                            <span className="block text-sm font-bold text-[#e6edf3]">Sentiment Score</span>
                            <span className="text-[12px] text-[#8b949e]">Haberlerin pozitif (+100) veya negatif (-100) olma durumu.</span>
                        </li>
                    </ul>
                </div>

                <div className="card flex flex-col justify-between">
                    <div>
                        <h3 className="text-lg font-bold mb-4">Sistem Notları</h3>
                        <p className="text-sm text-[#8b949e] leading-relaxed italic">
                            "Bu bot şu an simülasyon (Dry-Run) modundadır. Verilen tüm sinyallar bilgilendirme amaçlıdır ve gerçek bir finansal danışmanlık içermez."
                        </p>
                    </div>
                    <div className="mt-8 p-4 bg-[#0d1117] border border-[#30363d] rounded-lg">
                        <span className="text-[10px] font-bold text-[#8b949e] uppercase block mb-1">Build ID</span>
                        <span className="font-mono text-xs text-[#2f81f7]">02A.99B.SNPR</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
