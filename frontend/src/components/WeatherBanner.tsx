"use client";

import React from "react";
import { Sun, AlertTriangle } from "lucide-react";

interface WeatherBannerProps {
  highTemp?: number;
  humidity?: number;
}

export function WeatherBanner({ highTemp, humidity }: WeatherBannerProps) {
  if (!highTemp) return null;

  const isHot = highTemp >= 82;
  const isDangerous = highTemp >= 90;

  if (!isHot) return null;

  return (
    <div className={`px-4 py-3 rounded-xl border flex items-center justify-between gap-3 shadow-lg ${
      isDangerous
        ? "bg-red-500/10 border-red-500/30 text-red-400"
        : "bg-amber-500/10 border-amber-500/30 text-amber-400"
    }`}>
      <div className="flex items-center gap-3">
        <div className={`p-1.5 rounded-lg ${isDangerous ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"}`}>
          <Sun size={18} className="animate-spin-slow" />
        </div>
        <div>
          <h4 className="font-bold text-xs uppercase tracking-wider">
            {isDangerous ? "CRITICAL HEAT ADVISORY" : "ELEVATED HEAT EXHAUSTION RISK"}
          </h4>
          <p className="text-[11px] opacity-90 leading-tight mt-0.5">
            Active Event Weather: {highTemp}°F with {humidity ?? 20}% humidity. Monitor all MDMA/stimulant presentation patients for hyperthermia. 
            Initiate aggressive active cooling (cold packs/mist/fans) if core temp exceeds 101.5°F.
          </p>
        </div>
      </div>
      <div className="hidden sm:block shrink-0">
        <AlertTriangle size={18} className="animate-bounce" />
      </div>
    </div>
  );
}
