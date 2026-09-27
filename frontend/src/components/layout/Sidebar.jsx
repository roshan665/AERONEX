import React from 'react';
import { 
  LayoutDashboard, 
  Map, 
  AlertTriangle, 
  TrendingUp, 
  FileText, 
  Settings,
  Cpu,
  X
} from 'lucide-react';

export default function Sidebar({ 
  activeNav, 
  setActiveNav, 
  isMobileOpen, 
  setIsMobileOpen,
  anomalyCount = 5
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'map', label: 'Interactive Map', icon: Map },
    { id: 'anomalies', label: 'Anomalies', icon: AlertTriangle, badge: anomalyCount },
    { id: 'ai-models', label: 'AI & Uncertainty', icon: Cpu, badge: 'ML' },
    { id: 'forecast', label: 'Forecast Explorer', icon: TrendingUp },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];


  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/75 backdrop-blur-xs z-40 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside 
        className={`fixed lg:static top-0 bottom-0 left-0 z-50 w-64 bg-[#071126] border-r border-[#122040] flex flex-col justify-between transition-transform duration-300 ease-in-out select-none shrink-0
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Top Branding Section */}
        <div>
          <div className="h-20 px-5 flex items-center justify-between border-b border-[#122040]">
            <div className="flex items-center gap-3">
              {/* Stylized AeroNex Logo Icon with Purple-Cyan Gradient */}
              <div className="relative w-10 h-10 flex items-center justify-center shrink-0">
                <div className="absolute inset-0 bg-gradient-to-tr from-[#9333EA] via-[#168BFF] to-[#00D9F5] rounded-xl blur-[2px] opacity-80"></div>
                <div className="relative w-10 h-10 bg-[#071126] border border-[#00D9F5]/40 rounded-xl flex items-center justify-center overflow-hidden shadow-inner">
                  <svg 
                    viewBox="0 0 28 28" 
                    className="w-6 h-6"
                  >
                    <defs>
                      <linearGradient id="aeroLogoGrad" x1="0%" y1="100%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#A855F7" />
                        <stop offset="50%" stopColor="#168BFF" />
                        <stop offset="100%" stopColor="#00D9F5" />
                      </linearGradient>
                    </defs>
                    <path 
                      d="M14 3L4 24h5.5l2.5-5.5h4L18.5 24H24L14 3z" 
                      fill="url(#aeroLogoGrad)" 
                    />
                    <path 
                      d="M14 9l-2 4.5h4L14 9z" 
                      fill="#071126"
                    />
                  </svg>
                </div>
              </div>

              {/* Title & Subtitle */}
              <div>
                <h1 className="text-xl font-bold tracking-tight text-[#F4F7FF] flex items-center gap-1 leading-none">
                  AeroNex
                </h1>
                <p className="text-[9px] uppercase font-semibold tracking-wider text-cyan-400 mt-1">
                  EXTREME WEATHER INTELLIGENCE
                </p>
              </div>
            </div>

            {/* Mobile close button */}
            <button 
              className="lg:hidden p-1.5 text-[#93A9C8] hover:text-white rounded-lg hover:bg-[#101F3D]"
              onClick={() => setIsMobileOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Items List */}
          <nav className="p-3.5 space-y-1.5 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeNav === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveNav(item.id);
                    setIsMobileOpen(false);
                  }}
                  className={`w-full flex items-center gap-3.5 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 group text-left cursor-pointer ${
                    isActive 
                      ? 'bg-gradient-to-r from-[#1875F0] to-[#1262D2] text-white shadow-[0_0_18px_rgba(24,117,240,0.35)] border border-[#3894FF]/40' 
                      : 'text-[#93A9C8] hover:text-[#F4F7FF] hover:bg-[#0E1A33] border border-transparent'
                  }`}
                >
                  <Icon className={`w-4.5 h-4.5 transition-colors shrink-0 ${
                    isActive ? 'text-white' : 'text-[#93A9C8] group-hover:text-[#F4F7FF]'
                  }`} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FF4568] text-white shadow-sm shadow-[#FF4568]/40">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Atmospheric Mountain Artwork Widget */}
        <div className="p-3.5 border-t border-[#122040]">
          <div className="relative rounded-2xl overflow-hidden bg-[#0A1428] border border-[#142344] group">
            {/* Mountain Night-Sky Image */}
            <div className="relative h-36 w-full overflow-hidden">
              <img 
                src="/sidebar-mountains.jpg" 
                alt="Atmospheric Weather Horizon" 
                className="w-full h-full object-cover object-bottom transition-transform duration-700 group-hover:scale-105"
              />
              {/* Gradient overlays to smoothly blend with card */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#071126] via-[#071126]/20 to-transparent"></div>
              <div className="absolute inset-0 bg-radial-at-c from-transparent via-[#071126]/30 to-[#071126]/80"></div>
            </div>

            {/* Slogan & Glowing Wavy Accent */}
            <div className="px-3.5 pb-3.5 -mt-4 relative z-10 text-left">
              <p className="text-xs font-semibold text-[#F4F7FF] leading-snug">
                Better Forecasts.
              </p>
              <p className="text-xs font-medium text-[#93A9C8] leading-snug">
                Safer Tomorrow.
              </p>

              {/* Cyan Wavy Lines Accent */}
              <div className="mt-2 flex items-center gap-1">
                <svg width="28" height="6" viewBox="0 0 28 6" fill="none" className="text-[#00D9F5]">
                  <path 
                    d="M1 3C3 1 5 1 7 3C9 5 11 5 13 3C15 1 17 1 19 3C21 5 23 5 25 3" 
                    stroke="currentColor" 
                    strokeWidth="1.5" 
                    strokeLinecap="round" 
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
