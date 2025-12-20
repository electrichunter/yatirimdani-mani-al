
"use client";
import { useState, useEffect } from 'react';
import { Briefcase, History, TrendingUp, DollarSign, PieChart } from 'lucide-react';

export default function TrackingPage() {
    const [openTrades, setOpenTrades] = useState<any[]>([]);
    const [closedTrades, setClosedTrades] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);

    const fetchData = async () => {
        try {
            const [openRes, closedRes, statsRes] = await Promise.all([
                fetch('http://localhost:8000/api/trades/open'),
                fetch('http://localhost:8000/api/trades/closed'),
                fetch('http://localhost:8000/api/stats')
            ]);
            setOpenTrades(await openRes.json());
            setClosedTrades(await closedRes.json());
            setStats(await statsRes.json());
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-10">
            <header className="flex justify-between items-center pb-8 border-b border-[#30363d]">
                <div>
                    <h1 className="text-3xl font-bold text-[#e6edf3]">Portföy Takibi</h1>
                    <p className="text-[#8b949e] text-sm mt-1">Simüle edilen açık ve kapalı pozisyonların dökümü.</p>
                </div>

                {stats && (
                    <div className="flex gap-4">
                        <div className="bg-[#161b22] border border-[#30363d] px-6 py-4 rounded-xl text-center">
                            <span className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider block mb-1">Win Rate</span>
                            <span className="text-2xl font-bold text-[#3fb950]">%{stats.success_rate}</span>
                        </div>
                        <div className="bg-[#161b22] border border-[#30363d] px-6 py-4 rounded-xl text-center min-w-[120px]">
                            <span className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider block mb-1">Net Kâr/Zarar</span>
                            <span className={`text-2xl font-bold ${stats.total_profit >= 0 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                                ${stats.total_profit}
                            </span>
                        </div>
                    </div>
                )}
            </header>

            {/* Grid for Active Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card text-center p-6 border-b-2 border-b-[#2f81f7]">
                    <PieChart className="mx-auto mb-3 text-[#2f81f7]" size={24} />
                    <h4 className="text-xs font-bold text-[#8b949e] uppercase tracking-widest mb-1">Aktif Pozisyon</h4>
                    <p className="text-2xl font-black text-[#e6edf3]">{openTrades.length}</p>
                </div>
                <div className="card text-center p-6 border-b-2 border-b-[#238636]">
                    <TrendingUp className="mx-auto mb-3 text-[#238636]" size={24} />
                    <h4 className="text-xs font-bold text-[#8b949e] uppercase tracking-widest mb-1">Toplam İşlem</h4>
                    <p className="text-2xl font-black text-[#e6edf3]">{stats?.total_trades || 0}</p>
                </div>
                <div className="card text-center p-6 border-b-2 border-b-[#d29922]">
                    <DollarSign className="mx-auto mb-3 text-[#d29922]" size={24} />
                    <h4 className="text-xs font-bold text-[#8b949e] uppercase tracking-widest mb-1">Sanal Bakiye</h4>
                    <p className="text-2xl font-black text-[#e6edf3]">${stats?.free_balance || 100}</p>
                </div>
            </div>

            {/* Active Positions Table */}
            <section className="guide-section !p-0 overflow-hidden">
                <div className="px-6 py-4 border-b border-[#30363d] flex items-center gap-3">
                    <Briefcase className="text-[#2f81f7]" size={18} />
                    <h2 className="text-sm font-bold uppercase tracking-wider text-[#e6edf3]">Açık Pozisyonlar</h2>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#0d1117] text-[11px] font-bold uppercase tracking-wider text-[#8b949e]">
                                <th className="p-4 border-b border-[#30363d]">Sembol</th>
                                <th className="p-4 border-b border-[#30363d]">Yön / Lot</th>
                                <th className="p-4 border-b border-[#30363d]">Giriş / TP-SL</th>
                                <th className="p-4 border-b border-[#30363d]">Güncel Fiyat</th>
                                <th className="p-4 border-b border-[#30363d] text-right">Anlık P/L ($)</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#30363d]">
                            {openTrades.length === 0 ? (
                                <tr><td colSpan={5} className="p-12 text-center text-[#8b949e] italic text-sm">Gösterilecek aktif işlem bulunmuyor.</td></tr>
                            ) : openTrades.map((t, i) => (
                                <tr key={i} className="hover:bg-[#1f242b] transition-colors">
                                    <td className="p-4 font-bold text-[#e6edf3]">{t.symbol}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold mr-3 ${t.direction === 'BUY' ? 'bg-[rgba(35,134,54,0.2)] text-[#3fb950]' : 'bg-[rgba(218,54,51,0.2)] text-[#f85149]'}`}>
                                            {t.direction}
                                        </span>
                                        <span className="font-mono text-xs text-[#8b949e]">{t.position_size || t.lot} L</span>
                                    </td>
                                    <td className="p-4">
                                        <div className="font-bold text-sm text-[#e6edf3]">{t.entry_price}</div>
                                        <div className="text-[10px] text-[#8b949e] font-mono mt-0.5">SL: {t.stop_loss} | TP: {t.take_profit}</div>
                                    </td>
                                    <td className="p-4 font-mono font-bold text-sm">{t.current_price || '--'}</td>
                                    <td className={`p-4 font-bold text-right ${t.profit_amount >= 0 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                                        {t.profit_amount >= 0 ? '+' : ''}{t.profit_amount || t.unrealized_usd}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            {/* History Grid */}
            <section className="news-section">
                <div className="flex items-center gap-3 mb-6">
                    <History className="text-[#8b949e]" size={20} />
                    <h2 className="text-sm font-bold uppercase tracking-widest text-[#8b949e]">Kapatılan İşlemler</h2>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {closedTrades.length === 0 ? (
                        <div className="col-span-full py-12 text-center text-[#8b949e] border-2 border-dashed border-[#30363d] rounded-xl opacity-30">Henüz sonlanmış işlem kaydı yok.</div>
                    ) : closedTrades.slice().reverse().map((t, i) => (
                        <div key={i} className="bg-[#161b22] border border-[#30363d] p-5 rounded-xl relative overflow-hidden group hover:border-[#2f81f7] transition-all">
                            <div className={`absolute top-0 right-0 px-3 py-1 text-[9px] font-black uppercase ${t.realized_usd > 0 ? 'bg-[#238636] text-white' : 'bg-[#da3633] text-white'}`}>
                                {t.realized_usd > 0 ? 'W I N' : 'S T O P'}
                            </div>
                            <h3 className="text-lg font-bold text-[#e6edf3] mb-1">{t.symbol}</h3>
                            <p className="text-[10px] text-[#8b949e] mb-4 font-mono">{new Date(t.closed_at).toLocaleDateString()} {new Date(t.closed_at).toLocaleTimeString()}</p>
                            <div className={`text-2xl font-black ${t.realized_usd > 0 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                                {t.realized_usd > 0 ? '+' : ''}{t.realized_usd}$
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}
