
"use client";
import { useState, useEffect } from 'react';
import { Target, TrendingUp, AlertCircle, Shield, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function Dashboard() {
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/results');
            const data = await res.json();
            setResults(data);
        } catch (err) {
            console.error("Fetch error:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-10">
            <header className="flex justify-between items-end pb-8 border-b border-[#30363d]">
                <div>
                    <h1 className="text-3xl font-bold text-[#e6edf3]">Sinyal Radarı</h1>
                    <p className="text-[#8b949e] text-sm mt-1">Multi-layer analiz süreçlerinden geçen otonom sinyal akışı.</p>
                </div>
                <div className="flex gap-4">
                    <div className="bg-[#161b22] border border-[#30363d] px-6 py-3 rounded-lg flex flex-col items-center">
                        <span className="text-[10px] text-[#8b949e] font-bold uppercase tracking-wider">Aktif Analiz</span>
                        <span className="text-xl font-bold text-[#2f81f7]">{results.length}</span>
                    </div>
                </div>
            </header>

            {loading ? (
                <div className="flex items-center justify-center py-32">
                    <div className="w-10 h-10 border-4 border-[#30363d] border-t-[#2f81f7] rounded-full animate-spin"></div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {results.length === 0 ? (
                        <div className="col-span-full py-32 text-center border-2 border-dashed border-[#30363d] rounded-xl opacity-50">
                            <AlertCircle size={40} className="mx-auto mb-4 text-[#8b949e]" />
                            <p className="text-lg font-bold text-[#e6edf3]">Piyasa taranıyor...</p>
                            <p className="text-sm text-[#8b949e] mt-2">Henüz yeni bir sinyal yakalanmadı.</p>
                        </div>
                    ) : results.map((res: any, idx: number) => (
                        <div key={idx} className="card group">
                            <div className="card-header">
                                <div className="symbol-info">
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        {res.symbol}
                                        {res.decision === 'BUY' ? <ArrowUpRight className="text-[#3fb950]" size={18} /> : <ArrowDownRight className="text-[#f85149]" size={18} />}
                                    </h2>
                                    <span className="timestamp">{new Date().toLocaleTimeString()}</span>
                                </div>
                                <span className={`signal-type ${res.decision === 'BUY' ? 'buy' : 'sell'}`}>
                                    {res.decision} Sinyali
                                </span>
                            </div>

                            <div className="fiyat-grid">
                                <div className="fiyat-item">
                                    <span className="fiyat-label">Giriş</span>
                                    <span className="fiyat-value font-mono">{res.entry_price}</span>
                                </div>
                                <div className="fiyat-item">
                                    <span className="fiyat-label">R:R Oranı</span>
                                    <span className="fiyat-value text-[#2f81f7] font-mono">{res.rr_ratio}:1</span>
                                </div>
                            </div>

                            <div className="flex gap-3 mb-4">
                                <div className="flex-1 p-3 bg-[rgba(248,81,73,0.05)] border border-[rgba(248,81,73,0.1)] rounded-lg text-center">
                                    <span className="fiyat-label block text-[10px] mb-1">STOP LOSS</span>
                                    <span className="font-bold text-[#f85149] font-mono text-sm">{res.stop_loss}</span>
                                </div>
                                <div className="flex-1 p-3 bg-[rgba(63,185,80,0.05)] border border-[rgba(63,185,80,0.1)] rounded-lg text-center">
                                    <span className="fiyat-label block text-[10px] mb-1">TAKE PROFIT</span>
                                    <span className="font-bold text-[#3fb950] font-mono text-sm">{res.take_profit}</span>
                                </div>
                            </div>

                            <div className="confidence-bar-container">
                                <div className="confidence-bar" style={{ width: `${res.confidence}%`, background: res.decision === 'BUY' ? '#3fb950' : '#f85149' }}></div>
                            </div>

                            <div className="reasoning">
                                <div className="flex items-center gap-2 mb-2 text-[#e6edf3]">
                                    <Shield size={12} className="text-[#2f81f7]" />
                                    <span className="text-[11px] font-bold uppercase tracking-wider">AI Karar Notu</span>
                                </div>
                                <p className="text-[13px] italic leading-tight line-clamp-3">
                                    "{res.reasoning}"
                                </p>
                            </div>

                            <div className="rr-badge text-[#8b949e] font-bold font-mono">
                                CONFIDENCE: %{res.confidence}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
