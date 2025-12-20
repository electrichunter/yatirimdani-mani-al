
"use client";
import { useState, useEffect } from 'react';
import { Newspaper, TrendingUp, AlertTriangle, Target, Globe } from 'lucide-react';

export default function NewsPage() {
    const [news, setNews] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/news');
            const data = await res.json();
            setNews(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const inv = setInterval(fetchData, 30000);
        return () => clearInterval(inv);
    }, []);

    return (
        <div className="space-y-10">
            <header className="flex justify-between items-end pb-8 border-b border-[#30363d]">
                <div>
                    <h1 className="text-3xl font-bold text-[#e6edf3]">Haber Analizi</h1>
                    <p className="text-[#8b949e] text-sm mt-1">Küresel haber akışının sentiment analizi ve piyasa etkisi.</p>
                </div>
                <div className="flex gap-4">
                    <div className="status-badge badge-green flex items-center gap-2">
                        <Globe size={14} />
                        Global Feed Active
                    </div>
                </div>
            </header>

            {loading ? (
                <div className="flex items-center justify-center py-32">
                    <div className="w-10 h-10 border-4 border-[#30363d] border-t-[#2f81f7] rounded-full animate-spin"></div>
                </div>
            ) : (
                <div className="news-section !mt-0">
                    <div className="news-container">
                        {news.length === 0 ? (
                            <div className="text-center py-20 bg-[#161b22] border border-[#30363d] rounded-xl opacity-50">
                                <p className="text-[#8b949e]">Haber verisi bekleniyor...</p>
                            </div>
                        ) : news.map((item, i) => (
                            <div key={i} className="news-card group transition-all">
                                <div className="news-content">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className={`news-impact impact-${item.impact || 'MEDIUM'}`}>
                                            {item.impact || 'MEDIUM'} IMPACT
                                        </span>
                                        <span className="text-[11px] font-mono text-[#8b949e]">{item.time || 'Canlı'}</span>
                                    </div>
                                    <h3 className="news-title text-[#e6edf3] group-hover:text-[#2f81f7] transition-colors">
                                        {item.title}
                                    </h3>
                                    <div className="news-symbols">
                                        {item.symbols?.map((sym: string, si: number) => (
                                            <span key={si} className="symbol-tag">{sym}</span>
                                        ))}
                                        {(item.topics || []).map((topic: string, ti: number) => (
                                            <span key={ti} className="text-[10px] bg-[#21262d] text-[#8b949e] px-2 py-0.5 rounded border border-[#30363d]">
                                                {topic}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="flex flex-col items-end gap-3 ml-10">
                                    <div className="text-right">
                                        <span className="text-[10px] font-bold text-[#8b949e] uppercase block mb-1">Sentiment</span>
                                        <div className={`text-lg font-black ${item.sentiment_score > 0 ? 'text-[#3fb950]' : item.sentiment_score < 0 ? 'text-[#f85149]' : 'text-[#d29922]'}`}>
                                            {item.sentiment_score > 0 ? '+' : ''}{item.sentiment_score}%
                                        </div>
                                    </div>
                                    <div className={`px-4 py-1.5 rounded-md text-[11px] font-black tracking-widest uppercase ${item.action === 'LONG' ? 'bg-[rgba(35,134,54,0.1)] text-[#3fb950] border border-[#238636]' :
                                            item.action === 'SHORT' ? 'bg-[rgba(218,54,51,0.1)] text-[#f85149] border border-[#da3633]' :
                                                'bg-[#30363d] text-[#8b949e]'
                                        }`}>
                                        {item.action || 'NEUTRAL'}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
