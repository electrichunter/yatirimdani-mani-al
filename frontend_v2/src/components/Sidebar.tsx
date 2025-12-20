
"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Zap, Activity, Newspaper, BookOpen, Settings, Shell } from 'lucide-react';

const Sidebar = () => {
    const pathname = usePathname();

    const menuItems = [
        { name: 'Kurulum', icon: Settings, path: '/' },
        { name: 'Sinyaller', icon: Zap, path: '/dashboard' },
        { name: 'Pörtföy', icon: Activity, path: '/tracking' },
        { name: 'Haber Analizi', icon: Newspaper, path: '/news' },
        { name: 'Sistem Rehberi', icon: BookOpen, path: '/guide' },
    ];

    return (
        <div className="sidebar flex flex-col">
            <div className="flex items-center gap-3 mb-10 px-2">
                <div className="w-8 h-8 text-primary">
                    <Shell size={32} />
                </div>
                <div>
                    <h1 className="text-xl font-bold tracking-tight text-[#f0f6fc]">SNIPER</h1>
                    <p className="text-[10px] text-[#8b949e] font-semibold uppercase tracking-wider">Trading Intelligence</p>
                </div>
            </div>

            <nav className="flex flex-col gap-1">
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            href={item.path}
                            className={`flex items-center gap-3 px-4 py-2.5 rounded-md transition-all group ${isActive
                                    ? 'bg-[#1f242b] text-[#f0f6fc] border-l-2 border-primary shadow-sm'
                                    : 'text-[#8b949e] hover:bg-[#161b22] hover:text-[#f0f6fc]'
                                }`}
                        >
                            <Icon size={18} className={isActive ? 'text-primary' : ''} />
                            <span className="font-medium text-[14px]">{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="mt-auto pt-6 border-t border-[#30363d]">
                <div className="flex items-center gap-3 px-2 mb-4">
                    <div className="w-2 h-2 bg-[#238636] rounded-full animate-pulse shadow-[0_0_8px_#238636]"></div>
                    <span className="text-[12px] font-semibold text-[#8b949e]">Market Engine Live</span>
                </div>
                <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-md text-[11px] font-mono text-[#8b949e] leading-relaxed">
                    <span className="text-[#3fb950]">$</span> node sniper_v2.js<br />
                    <span className="opacity-50">status: established</span>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
