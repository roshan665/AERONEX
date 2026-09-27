import React, { useEffect } from 'react';
import { Play, Pause } from 'lucide-react';

export default function ForecastControls({ 
  forecastDay = 3, 
  setForecastDay, 
  isPlaying, 
  setIsPlaying 
}) {
  // Auto-advance forecast day when in play mode
  useEffect(() => {
    let timer = null;
    if (isPlaying) {
      timer = setInterval(() => {
        setForecastDay((prev) => (prev >= 10 ? 1 : prev + 1));
      }, 1500);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, setForecastDay]);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const days = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  return (
    <div className="bg-[#071126]/90 backdrop-blur-md border border-[#16274a] rounded-full px-3 py-1.5 shadow-2xl flex items-center gap-3 select-none">
      {/* Play / Pause Circular Button with Blue Glow */}
      <button
        onClick={togglePlay}
        className="w-7 h-7 rounded-full bg-[#168BFF] hover:bg-[#3894FF] text-white flex items-center justify-center transition-all cursor-pointer shadow-[0_0_12px_rgba(22,139,255,0.6)] shrink-0"
        aria-label={isPlaying ? 'Pause forecast timeline' : 'Play forecast timeline'}
      >
        {isPlaying ? (
          <Pause className="w-3.5 h-3.5 fill-current" />
        ) : (
          <Play className="w-3.5 h-3.5 fill-current translate-x-0.5" />
        )}
      </button>

      {/* Current Day Label */}
      <div className="text-xs font-bold text-[#F4F7FF] font-mono tracking-tight shrink-0 whitespace-nowrap">
        Day {forecastDay} <span className="text-[#93A9C8] font-normal">/ 10</span>
      </div>

      {/* Interactive Step Dots Timeline */}
      <div className="flex items-center gap-1.5 sm:gap-2 px-1">
        {days.map((d) => {
          const isActive = d === forecastDay;
          const isPast = d < forecastDay;
          return (
            <button
              key={d}
              onClick={() => setForecastDay(d)}
              className={`transition-all cursor-pointer rounded-full flex items-center justify-center ${
                isActive 
                  ? 'w-3 h-3 bg-[#168BFF] ring-2 ring-[#00D9F5] shadow-[0_0_8px_rgba(0,217,245,0.8)] scale-110' 
                  : isPast
                  ? 'w-1.5 h-1.5 bg-[#168BFF]/70 hover:bg-[#168BFF]'
                  : 'w-1.5 h-1.5 bg-[#1A2E56] hover:bg-[#93A9C8]'
              }`}
              title={`Jump to Forecast Day ${d}`}
              aria-label={`Forecast Day ${d}`}
            />
          );
        })}
      </div>
    </div>
  );
}
