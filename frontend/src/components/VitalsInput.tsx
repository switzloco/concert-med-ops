"use client";

import React from "react";
import type { VitalSigns } from "@/lib/types";

interface VitalsInputProps {
  vitals: VitalSigns;
  onChange: (vitals: VitalSigns) => void;
}

export function VitalsInput({ vitals, onChange }: VitalsInputProps) {
  const handleNumChange = (field: keyof VitalSigns, valStr: string) => {
    const val = valStr === "" ? undefined : parseFloat(valStr);
    onChange({
      ...vitals,
      [field]: val,
    });
  };

  const handleStrChange = (field: keyof VitalSigns, val: string) => {
    onChange({
      ...vitals,
      [field]: val === "" ? undefined : val,
    });
  };

  // Status highlights
  const getHrClass = (hr?: number) => {
    if (!hr) return "border-zinc-800 bg-zinc-900/50 text-zinc-300 focus:border-cyber-neonBlue";
    if (hr > 120 || hr < 50) return "border-red-500 bg-red-500/10 text-red-400 focus:border-red-400";
    if (hr > 100 || hr < 60) return "border-yellow-500 bg-yellow-500/10 text-yellow-400 focus:border-yellow-400";
    return "border-green-500/50 bg-green-500/5 text-green-300 focus:border-green-400";
  };

  const getTempClass = (temp?: number) => {
    if (!temp) return "border-zinc-800 bg-zinc-900/50 text-zinc-300 focus:border-cyber-neonBlue";
    if (temp >= 103.0 || temp < 95.0) return "border-red-500 bg-red-500/10 text-red-400 focus:border-red-400 animate-pulse";
    if (temp >= 100.4 || temp < 96.8) return "border-yellow-500 bg-yellow-500/10 text-yellow-400 focus:border-yellow-400";
    return "border-green-500/50 bg-green-500/5 text-green-300 focus:border-green-400";
  };

  const getSpo2Class = (spo2?: number) => {
    if (!spo2) return "border-zinc-800 bg-zinc-900/50 text-zinc-300 focus:border-cyber-neonBlue";
    if (spo2 < 90) return "border-red-500 bg-red-500/10 text-red-400 focus:border-red-400 animate-pulse";
    if (spo2 < 95) return "border-yellow-500 bg-yellow-500/10 text-yellow-400 focus:border-yellow-400";
    return "border-green-500/50 bg-green-500/5 text-green-300 focus:border-green-400";
  };

  const getRrClass = (rr?: number) => {
    if (!rr) return "border-zinc-800 bg-zinc-900/50 text-zinc-300 focus:border-cyber-neonBlue";
    if (rr > 24 || rr < 8) return "border-red-500 bg-red-500/10 text-red-400 focus:border-red-400 animate-pulse";
    if (rr > 20 || rr < 10) return "border-yellow-500 bg-yellow-500/10 text-yellow-400 focus:border-yellow-400";
    return "border-green-500/50 bg-green-500/5 text-green-300 focus:border-green-400";
  };

  const getGcsClass = (gcs?: number) => {
    if (!gcs) return "border-zinc-800 bg-zinc-900/50 text-zinc-300 focus:border-cyber-neonBlue";
    if (gcs <= 8) return "border-red-500 bg-red-500/10 text-red-400 focus:border-red-400 animate-pulse";
    if (gcs <= 13) return "border-yellow-500 bg-yellow-500/10 text-yellow-400 focus:border-yellow-400";
    return "border-green-500/50 bg-green-500/5 text-green-300 focus:border-green-400";
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-zinc-950 p-5 rounded-xl border border-zinc-900 shadow-xl">
      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">Heart Rate (BPM)</label>
        <input
          type="number"
          placeholder="e.g. 72"
          className={`px-3 py-2 rounded-lg border text-sm outline-none transition-all ${getHrClass(vitals.hr)}`}
          value={vitals.hr ?? ""}
          onChange={(e) => handleNumChange("hr", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">Blood Pressure</label>
        <input
          type="text"
          placeholder="e.g. 120/80"
          className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 outline-none focus:border-cyber-neonBlue text-sm transition-all"
          value={vitals.bp ?? ""}
          onChange={(e) => handleStrChange("bp", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">Temp (°F)</label>
        <input
          type="number"
          step="0.1"
          placeholder="e.g. 98.6"
          className={`px-3 py-2 rounded-lg border text-sm outline-none transition-all ${getTempClass(vitals.temp_f)}`}
          value={vitals.temp_f ?? ""}
          onChange={(e) => handleNumChange("temp_f", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">SpO2 (%)</label>
        <input
          type="number"
          placeholder="e.g. 98"
          className={`px-3 py-2 rounded-lg border text-sm outline-none transition-all ${getSpo2Class(vitals.spo2)}`}
          value={vitals.spo2 ?? ""}
          onChange={(e) => handleNumChange("spo2", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">Resp Rate (RR)</label>
        <input
          type="number"
          placeholder="e.g. 16"
          className={`px-3 py-2 rounded-lg border text-sm outline-none transition-all ${getRrClass(vitals.rr)}`}
          value={vitals.rr ?? ""}
          onChange={(e) => handleNumChange("rr", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">GCS (3-15)</label>
        <input
          type="number"
          min="3"
          max="15"
          placeholder="e.g. 15"
          className={`px-3 py-2 rounded-lg border text-sm outline-none transition-all ${getGcsClass(vitals.gcs)}`}
          value={vitals.gcs ?? ""}
          onChange={(e) => handleNumChange("gcs", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">Pupils</label>
        <input
          type="text"
          placeholder="e.g. PERRL, pinpoint, dilated"
          className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 outline-none focus:border-cyber-neonBlue text-sm transition-all"
          value={vitals.pupils ?? ""}
          onChange={(e) => handleStrChange("pupils", e.target.value)}
        />
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">Skin</label>
        <input
          type="text"
          placeholder="e.g. warm & dry, diaphoretic"
          className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 outline-none focus:border-cyber-neonBlue text-sm transition-all"
          value={vitals.skin_condition ?? ""}
          onChange={(e) => handleStrChange("skin_condition", e.target.value)}
        />
      </div>
    </div>
  );
}
