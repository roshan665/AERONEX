import React from 'react';
import { 
  AlertTriangle, 
  MapPin, 
  Calendar, 
  Clock, 
  ChevronRight
} from 'lucide-react';

const ICON_MAP = {
  AlertTriangle,
  MapPin,
  Calendar,
  Clock,
};

export default function StatCard({ item }) {
  const IconComponent = ICON_MAP[item.icon] || AlertTriangle;

  // Visual design specifications matching the 4 reference cards
  const colorConfigs = {
    red: {
      border: 'border-[#FF4568]/30 hover:border-[#FF4568]/70 hover:shadow-[0_0_22px_rgba(255,69,104,0.18)]',
      iconBox: 'bg-[#FF4568]/15 text-[#FF4568] border border-[#FF4568]/30',
      badgeColor: 'text-[#FF4568]',
      sparklineColor: '#FF4568',
      type: 'sparkline',
    },
    blue: {
      border: 'border-[#168BFF]/30 hover:border-[#168BFF]/70 hover:shadow-[0_0_22px_rgba(22,139,255,0.18)]',
      iconBox: 'bg-[#168BFF]/15 text-[#168BFF] border border-[#168BFF]/30',
      badgeColor: 'text-[#168BFF]',
      type: 'worldmap',
    },
    green: {
      border: 'border-[#00D6A0]/30 hover:border-[#00D6A0]/70 hover:shadow-[0_0_22px_rgba(0,214,160,0.18)]',
      iconBox: 'bg-[#00D6A0]/15 text-[#00D6A0] border border-[#00D6A0]/30',
      badgeColor: 'text-[#00D6A0]',
      type: 'barchart',
    },
    purple: {
      border: 'border-[#A855F7]/30 hover:border-[#A855F7]/70 hover:shadow-[0_0_22px_rgba(168,85,247,0.18)]',
      iconBox: 'bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/30',
      badgeColor: 'text-[#A855F7]',
      sparklineColor: '#A855F7',
      type: 'sparkline-purple',
    },
  };

  const config = colorConfigs[item.color] || colorConfigs.blue;

  return (
    <div 
      className={`relative bg-[#0B1730] rounded-2xl p-5 border transition-all duration-300 flex flex-col justify-between select-none group cursor-default min-h-[145px] ${config.border}`}
    >
      {/* Top Row: Icon Square, Title, Chevron */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:scale-105 ${config.iconBox}`}>
            <IconComponent className="w-5 h-5" />
          </div>
          <span className="text-xs font-semibold text-[#93A9C8] tracking-tight">
            {item.title}
          </span>
        </div>

        <ChevronRight className="w-4 h-4 text-[#93A9C8]/50 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
      </div>

      {/* Middle: Big Metric Value */}
      <div className="my-2 pl-1">
        <div className={`font-extrabold text-[#F4F7FF] tracking-tight truncate ${
          item.id === 'latest-data' ? 'text-lg sm:text-xl font-mono' : 'text-2xl sm:text-3xl'
        }`}>
          {item.id === 'latest-data' ? (
            <>
              Apr 26, 2025 <span className="text-sm font-normal text-[#93A9C8]">14:32 UTC</span>
            </>
          ) : (
            item.value
          )}
        </div>
      </div>

      {/* Bottom Row: Subtext & Graphic Decoration */}
      <div className="flex items-center justify-between pt-1 border-t border-[#122040]/70 pl-1">
        {/* Left Subtext with Trend */}
        <div className="flex items-center gap-1.5 text-xs">
          {item.trend === 'up' && (
            <span className="text-[#FF4568] font-bold flex items-center gap-0.5">
              <span>↑</span> 2
            </span>
          )}
          <span className="text-[#93A9C8] font-medium text-[11px] truncate">
            {item.trend === 'up' ? 'from last 24h' : item.subtext}
          </span>
        </div>

        {/* Right Graphic Decoration */}
        <div className="shrink-0 flex items-center">
          {/* Card 1: Red Sparkline */}
          {config.type === 'sparkline' && (
            <svg width="48" height="20" viewBox="0 0 48 20" fill="none" className="text-[#FF4568]">
              <path 
                d="M1 18L10 12L18 15L28 6L36 10L47 2" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
              />
            </svg>
          )}

          {/* Card 2: World Map Silhouette */}
          {config.type === 'worldmap' && (
            <svg width="44" height="24" viewBox="0 0 44 24" fill="none" className="text-[#168BFF]/60">
              <path 
                d="M4 5C6 4 10 5 12 7C14 9 13 13 10 14C8 15 5 13 4 11C3 9 2 6 4 5Z" 
                fill="currentColor" 
                opacity="0.8"
              />
              <path 
                d="M18 4C22 3 26 4 28 7C30 9 29 13 26 14C24 15 20 14 18 12C16 10 16 6 18 4Z" 
                fill="currentColor" 
                opacity="0.7"
              />
              <path 
                d="M32 6C35 5 39 6 40 8C41 10 40 13 37 14C35 15 32 14 31 12C30 9 30 7 32 6Z" 
                fill="currentColor" 
                opacity="0.8"
              />
              <path 
                d="M8 17C10 16 13 17 14 19C15 21 14 23 12 24C10 24 8 23 7 21C7 19 7 18 8 17Z" 
                fill="currentColor" 
                opacity="0.6"
              />
              <path 
                d="M33 17C36 16 39 17 40 19C41 21 40 23 38 24C36 24 34 23 33 21C32 19 32 18 33 17Z" 
                fill="currentColor" 
                opacity="0.6"
              />
            </svg>
          )}

          {/* Card 3: Ascending Teal Bars */}
          {config.type === 'barchart' && (
            <div className="flex items-end gap-1 h-5">
              <div className="w-1 bg-[#00D6A0]/40 rounded-xs h-2"></div>
              <div className="w-1 bg-[#00D6A0]/60 rounded-xs h-3"></div>
              <div className="w-1 bg-[#00D6A0]/70 rounded-xs h-2.5"></div>
              <div className="w-1 bg-[#00D6A0]/90 rounded-xs h-4"></div>
              <div className="w-1 bg-[#00D6A0] rounded-xs h-5 shadow-[0_0_8px_rgba(0,214,160,0.5)]"></div>
            </div>
          )}

          {/* Card 4: Purple Sparkline */}
          {config.type === 'sparkline-purple' && (
            <svg width="48" height="20" viewBox="0 0 48 20" fill="none" className="text-[#A855F7]">
              <path 
                d="M1 15C8 17 14 6 22 10C30 14 38 4 47 12" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round" 
              />
            </svg>
          )}
        </div>
      </div>
    </div>
  );
}
