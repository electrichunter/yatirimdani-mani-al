
"use client";
import { useState, useEffect, useRef } from 'react';

const Terminal = () => {
    const [logs, setLogs] = useState<string[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        try {
            const resp = await fetch('http://localhost:8000/api/terminal');
            const data = await resp.json();
            if (data.logs) {
                setLogs(data.logs);
            }
        } catch (err) {
            console.error("Log fetch error", err);
        }
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 2000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                    Live Backend Engine Logs
                </h3>
                <span className="text-[10px] text-white/20 font-mono">system.process_monitor</span>
            </div>
            <div className="terminal-window" ref={scrollRef}>
                {logs.length === 0 ? (
                    <div className="text-white/20 italic">Datalink kuruluyor, loglar bekleniyor...</div>
                ) : logs.map((log, i) => {
                    const isError = log.includes('ERROR') || log.includes('CRITICAL') || log.includes('Exception') || log.includes('Hata');
                    const isInfo = log.includes('INFO');
                    const isWarn = log.includes('WARNING');

                    return (
                        <div key={i} className={`terminal-line ${isError ? 'terminal-error' : isInfo ? 'terminal-info' : isWarn ? 'terminal-warn' : ''}`}>
                            {log}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Terminal;
