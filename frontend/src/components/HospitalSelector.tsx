"use client";

import React from "react";
import type { HospitalDirectory } from "@/lib/types";
import { AlertTriangle, Clock, MapPin, Phone } from "lucide-react";

interface HospitalSelectorProps {
  hospitals: HospitalDirectory[];
  selectedHospital?: string;
  onSelect: (hospitalName: string) => void;
}

export function HospitalSelector({
  hospitals,
  selectedHospital,
  onSelect,
}: HospitalSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {hospitals.map((h) => {
          const isSelected = selectedHospital === h.name;
          const diversion = h.is_on_diversion;
          
          return (
            <div
              key={h.hospital_id}
              onClick={() => onSelect(h.name)}
              className={`p-4 rounded-xl border cursor-pointer transition-all duration-300 ${
                isSelected
                  ? "bg-cyber-neonBlue/10 border-cyber-neonBlue text-white shadow-neonBlue"
                  : diversion
                  ? "bg-red-500/5 border-red-500/30 text-zinc-400 hover:border-red-500/50"
                  : "bg-zinc-950 border-zinc-900 text-zinc-300 hover:border-zinc-800"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-bold text-sm tracking-wide text-zinc-100">{h.name}</h4>
                  <div className="flex items-center gap-1.5 text-xs text-zinc-500 mt-1">
                    <MapPin size={12} />
                    <span className="truncate max-w-[200px]">{h.address}</span>
                  </div>
                </div>
                {h.trauma_level ? (
                  <span className="px-2 py-0.5 bg-zinc-900 text-zinc-400 border border-zinc-800 rounded text-[10px] font-bold uppercase tracking-wider">
                    Level {h.trauma_level} Trauma
                  </span>
                ) : (
                  <span className="px-2 py-0.5 bg-zinc-900/40 text-zinc-500 border border-zinc-900/60 rounded text-[10px] uppercase">
                    Non-Trauma
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-zinc-900/60 text-xs">
                <div className="flex items-center gap-2">
                  <Clock size={14} className="text-cyber-neonBlue" />
                  <div>
                    <p className="text-[10px] text-zinc-500 uppercase leading-none mb-0.5">Drive Time</p>
                    <p className="font-bold text-zinc-200">{h.drive_time_min} mins</p>
                  </div>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase leading-none mb-0.5">Distance</p>
                  <p className="font-semibold text-zinc-300">{h.distance_miles} miles</p>
                </div>
              </div>

              {h.capabilities && h.capabilities.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {h.capabilities.map((c) => (
                    <span
                      key={c}
                      className="px-1.5 py-0.5 bg-zinc-900 text-[10px] font-mono text-zinc-400 rounded"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              )}

              {diversion && (
                <div className="flex items-center gap-1.5 mt-3 text-red-400 text-xs font-bold bg-red-500/10 border border-red-500/20 px-2 py-1 rounded-lg">
                  <AlertTriangle size={12} className="animate-bounce" />
                  <span>ON DIVERSION: Avoid transport if possible</span>
                </div>
              )}

              {h.notes && (
                <p className="text-[11px] text-zinc-500 mt-2.5 italic border-l-2 border-zinc-800 pl-2 leading-relaxed">
                  {h.notes}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
