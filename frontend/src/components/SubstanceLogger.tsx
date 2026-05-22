"use client";

import React, { useState } from "react";
import type { SubstanceReported } from "@/lib/types";
import { Plus, Trash2, ShieldAlert } from "lucide-react";

interface SubstanceLoggerProps {
  substances: SubstanceReported[];
  onChange: (substances: SubstanceReported[]) => void;
}

const QUICK_SUBSTANCES = [
  "Alcohol", "MDMA", "Ketamine", "GHB", "Cocaine", 
  "LSD", "Fentanyl", "Psilocybin", "Xanax / Benzo", "2C-B", "Speed / Adderall"
];

const QUICK_ROUTES = ["Oral", "Insufflation (Snort)", "Inhalation (Smoke/Vape)", "Injection", "Sublingual"];

export function SubstanceLogger({ substances, onChange }: SubstanceLoggerProps) {
  const [name, setName] = useState("");
  const [route, setRoute] = useState("Oral");
  const [timeTaken, setTimeTaken] = useState("");
  const [amount, setAmount] = useState("");

  const handleAdd = () => {
    if (!name.trim()) return;
    onChange([
      ...substances,
      {
        name: name.trim(),
        route: route || undefined,
        time_taken: timeTaken.trim() || undefined,
        amount: amount.trim() || undefined,
      },
    ]);
    // reset form
    setName("");
    setTimeTaken("");
    setAmount("");
  };

  const handleRemove = (index: number) => {
    onChange(substances.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4 bg-zinc-950 p-5 rounded-xl border border-zinc-900 shadow-xl">
      <div className="flex items-center gap-2 text-cyber-neonPink mb-1">
        <ShieldAlert size={16} />
        <h4 className="text-xs font-bold uppercase tracking-wider">Substances Reported / Suspected</h4>
      </div>

      {substances.length > 0 ? (
        <div className="divide-y divide-zinc-900 bg-zinc-900/20 rounded-lg border border-zinc-900 overflow-hidden">
          {substances.map((sub, i) => (
            <div key={i} className="flex justify-between items-center px-4 py-2.5 text-sm">
              <div>
                <span className="font-bold text-zinc-200">{sub.name}</span>
                <span className="text-xs text-zinc-500 ml-2">
                  ({sub.route ?? "Unknown route"} • {sub.amount ?? "Unknown amt"} • {sub.time_taken ?? "Unknown time"})
                </span>
              </div>
              <button
                type="button"
                onClick={() => handleRemove(i)}
                className="text-zinc-600 hover:text-red-400 transition-colors p-1"
                aria-label="Remove substance"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-zinc-500 italic">No substances logged yet. Add any reported by patient/friends or suspected by rovers.</p>
      )}

      {/* Quick Select Grid */}
      <div>
        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1.5">Quick Select</p>
        <div className="flex flex-wrap gap-1.5">
          {QUICK_SUBSTANCES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setName(s)}
              className={`px-2.5 py-1 text-xs rounded-full border transition-all ${
                name === s
                  ? "bg-cyber-neonPink/20 text-cyber-neonPink border-cyber-neonPink/60 shadow-neonPink"
                  : "bg-zinc-900/60 text-zinc-400 border-zinc-800 hover:border-zinc-700 hover:text-white"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Add Form */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Substance Name</label>
          <input
            type="text"
            placeholder="e.g. Pink Tesla"
            className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>

        <div className="flex flex-col">
          <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Route</label>
          <select
            className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
            value={route}
            onChange={(e) => setRoute(e.target.value)}
          >
            {QUICK_ROUTES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Amount</label>
            <input
              type="text"
              placeholder="e.g. 2 bumps"
              className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          <div className="flex flex-col">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Time Taken</label>
            <input
              type="text"
              placeholder="e.g. 1h ago"
              className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
              value={timeTaken}
              onChange={(e) => setTimeTaken(e.target.value)}
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleAdd}
          disabled={!name.trim()}
          className="w-full flex items-center justify-center gap-1 bg-cyber-neonPink/20 text-cyber-neonPink hover:bg-cyber-neonPink/30 disabled:opacity-50 disabled:cursor-not-allowed border border-cyber-neonPink/40 py-1.5 px-3 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
        >
          <Plus size={14} />
          Add Entry
        </button>
      </div>
    </div>
  );
}
