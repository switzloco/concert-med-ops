"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Event } from "@/lib/types";
import {
  Settings as SettingsIcon,
  Activity,
  Trash2,
  Cpu,
  Database,
  FileText,
  Save,
  RotateCcw,
  Cloud,
  HardDrive,
  ExternalLink,
  CheckCircle2,
  ChevronDown,
  FlaskConical,
  Calendar,
  Users
} from "lucide-react";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useToast } from "@/components/ui/Toast";
import { LocalSetupGuide } from "@/components/ui/LocalSetupGuide";
import { fetchSetupStatus, type SetupStatus } from "@/lib/setup";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  
  const { data: eventInfo, isLoading: eventLoading } = useQuery({ 
    queryKey: ["event-info"], 
    queryFn: () => apiFetch<Event>("/setup/event-info") 
  });
  const { data: stats } = useQuery({ 
    queryKey: ["knowledge-stats"], 
    queryFn: () => apiFetch<Record<string, number>>("/ai/knowledge-stats") 
  });
  const { data: modeInfo } = useQuery({ 
    queryKey: ["ai-mode"], 
    queryFn: () => apiFetch<{ mode: string }>("/setup/mode") 
  });
  const { data: status } = useQuery({ 
    queryKey: ["setup-status"], 
    queryFn: () => fetchSetupStatus() 
  });

  // Event Edit State
  const [formState, setFormState] = useState<Partial<Event>>({});
  const [showGuide, setShowGuide] = useState(false);
  const [showNerdInfo, setShowNerdInfo] = useState(false);

  useEffect(() => {
    if (eventInfo) {
      setFormState({
        name: eventInfo.name,
        venue: eventInfo.venue || "",
        expected_attendance: eventInfo.expected_attendance || 0,
        medical_lead: eventInfo.medical_lead || "",
        contact_info: eventInfo.contact_info || "",
        weather_high_f: eventInfo.weather_high_f || 80,
        weather_humidity: eventInfo.weather_humidity || 30,
        notes: eventInfo.notes || ""
      });
    }
  }, [eventInfo]);

  const updateEvent = useMutation({
    mutationFn: (payload: Partial<Event>) => 
      apiFetch<Event>("/setup/event-info", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      showToast("Event configuration updated.", "success");
      queryClient.invalidateQueries({ queryKey: ["event-info"] });
    },
    onError: (err: any) => {
      showToast(err.message || "Failed to update event details.", "error");
    }
  });

  const toggleMode = useMutation({
    mutationFn: (mode: string) => 
      apiFetch("/setup/mode", { method: "POST", body: JSON.stringify({ mode }) }),
    onSuccess: () => {
      showToast("AI Intelligence mode updated.", "success");
      queryClient.invalidateQueries({ queryKey: ["ai-mode"] });
    },
    onError: (err: any) => {
      showToast(err.message, "error");
      setShowGuide(true);
    }
  });

  const clearDemoData = async () => {
    if (!confirm("Are you sure you want to reset the database? This deletes all current patients, encounters, and reagent logs.")) return;
    try {
      await apiFetch("/setup/reset-demo-data", { method: "POST" });
      showToast("Demo data reset successfully.", "success");
      window.location.reload();
    } catch (err) {
      showToast("Failed to reset data.", "error");
    }
  };

  const handleSaveEvent = () => {
    updateEvent.mutate(formState);
  };

  return (
    <div className="max-w-5xl space-y-6 pb-16">
      {/* HEADER */}
      <div className="flex items-center gap-3 border-b border-zinc-900 pb-5">
        <div className="bg-cyber-neonPurple/10 p-2 rounded-lg border border-cyber-neonPurple/30 text-cyber-neonPurple shadow-neonPurple">
          <SettingsIcon size={22} />
        </div>
        <div>
          <h1 className="text-2xl font-black text-white tracking-wide uppercase">System Settings</h1>
          <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
            Configure Event parameters and local RAG models
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Event Identity Card */}
        <section className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <Calendar className="text-cyber-neonBlue" size={16} />
            <h2 className="font-extrabold text-sm text-zinc-200 uppercase tracking-wider">Event Parameters</h2>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="space-y-1 sm:col-span-2">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Event Name</label>
              <input 
                type="text" 
                value={formState.name || ""}
                onChange={(e) => setFormState({ ...formState, name: e.target.value })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>
            
            <div className="space-y-1 sm:col-span-2">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Venue / Site Details</label>
              <input 
                type="text" 
                value={formState.venue || ""}
                onChange={(e) => setFormState({ ...formState, venue: e.target.value })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Expected Attendance</label>
              <input 
                type="number" 
                value={formState.expected_attendance || 0}
                onChange={(e) => setFormState({ ...formState, expected_attendance: parseInt(e.target.value) || 0 })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Medical Lead Physician</label>
              <input 
                type="text" 
                value={formState.medical_lead || ""}
                onChange={(e) => setFormState({ ...formState, medical_lead: e.target.value })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>

            <div className="space-y-1 sm:col-span-2">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Radio Dispatch / Contact</label>
              <input 
                type="text" 
                value={formState.contact_info || ""}
                onChange={(e) => setFormState({ ...formState, contact_info: e.target.value })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Weather High (°F)</label>
              <input 
                type="number" 
                step="0.1"
                value={formState.weather_high_f || 0}
                onChange={(e) => setFormState({ ...formState, weather_high_f: parseFloat(e.target.value) || 0 })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-wider">Weather Humidity (%)</label>
              <input 
                type="number" 
                step="0.1"
                value={formState.weather_humidity || 0}
                onChange={(e) => setFormState({ ...formState, weather_humidity: parseFloat(e.target.value) || 0 })}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 outline-none focus:border-cyber-neonBlue"
              />
            </div>
          </div>

          <button 
            onClick={handleSaveEvent}
            disabled={updateEvent.isPending}
            className="w-full py-2 bg-cyber-neonBlue hover:bg-cyber-neonBlue/90 text-black rounded-lg text-xs font-black uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-neonBlue transition-all"
          >
            <Save size={14} /> {updateEvent.isPending ? "Saving..." : "Save Event Parameters"}
          </button>
        </section>

        {/* AI Engine Card */}
        <section className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <Cpu className="text-cyber-neonPurple" size={16} />
            <h2 className="font-extrabold text-sm text-zinc-200 uppercase tracking-wider">AI Intelligence Mode</h2>
          </div>
          <div className="space-y-4">
            <div className="flex p-1 bg-zinc-900 border border-zinc-800 rounded-xl">
              <button 
                onClick={() => toggleMode.mutate("local")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all uppercase tracking-wider ${
                  modeInfo?.mode === "local" ? "bg-zinc-850 text-cyber-neonPurple shadow-neonPurple/20 shadow-md" : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <HardDrive size={14} /> Local (Ollama)
              </button>
              <button 
                onClick={() => toggleMode.mutate("cloud")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all uppercase tracking-wider ${
                  modeInfo?.mode === "cloud" ? "bg-zinc-850 text-cyber-neonBlue shadow-neonBlue/20 shadow-md" : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <Cloud size={14} /> Cloud (Gemini)
              </button>
            </div>
            <p className="text-[10px] text-zinc-500 leading-relaxed italic">
              Local mode runs Gemma locally on this laptop for 100% offline coverage during severe festival network outages. Cloud mode routes to Google AI Studio (Gemini) for high-speed triage.
            </p>
            <div className="pt-2 border-t border-zinc-900">
              <button 
                onClick={() => setShowGuide(true)}
                className="text-[10px] text-cyber-neonPurple font-bold hover:underline flex items-center gap-1"
              >
                Local AI Setup Guide <ExternalLink size={10} />
              </button>
            </div>
          </div>
        </section>

        {status && (
          <LocalSetupGuide 
            isOpen={showGuide} 
            onClose={() => setShowGuide(false)} 
            status={status} 
          />
        )}

        {/* RAG Knowledge Base Card */}
        <section className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <Database className="text-cyber-neonGreen" size={16} />
            <h2 className="font-extrabold text-sm text-zinc-200 uppercase tracking-wider">RAG Knowledge Base</h2>
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 border border-zinc-900 rounded-xl">
              <div className="flex items-center gap-3">
                <FileText className="text-zinc-500" size={16} />
                <span className="font-bold text-zinc-300">Harm Reduction Protocols</span>
              </div>
              <span className="text-[10px] font-black text-cyber-neonGreen px-2 py-0.5 border border-cyber-neonGreen/30 bg-cyber-neonGreen/10 rounded">
                {stats?.harm_reduction_protocols ?? 0} Chunks
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 border border-zinc-900 rounded-xl">
              <div className="flex items-center gap-3">
                <FileText className="text-zinc-500" size={16} />
                <span className="font-bold text-zinc-300">Substance Profile Index</span>
              </div>
              <span className="text-[10px] font-black text-cyber-neonGreen px-2 py-0.5 border border-cyber-neonGreen/30 bg-cyber-neonGreen/10 rounded">
                {stats?.substance_database ?? 0} Chunks
              </span>
            </div>
            <p className="text-[10px] text-zinc-500 leading-relaxed italic">
              Knowledge base chunks are synced from SQLite FTS5 database. Search occurs instantly during chat or encounter intakes.
            </p>
          </div>
        </section>

        {/* Reset & Maintenance Card */}
        <section className="bg-zinc-950 border border-red-950 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
            <RotateCcw className="text-red-400" size={16} />
            <h2 className="font-extrabold text-sm text-zinc-200 uppercase tracking-wider">Maintenance & Reset</h2>
          </div>
          <div className="space-y-3">
            <button 
              onClick={() => {
                localStorage.removeItem("event_med_ai_onboarded");
                window.location.href = "/welcome";
              }}
              className="w-full py-2 bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white rounded-lg text-xs font-bold hover:bg-zinc-800 transition-colors flex items-center justify-center gap-1.5"
            >
              <CheckCircle2 size={12} className="text-cyber-neonPurple" /> Run Initial Setup Wizard
            </button>
            <button 
              onClick={clearDemoData}
              className="w-full py-2 border border-red-900/30 hover:border-red-900/60 bg-red-950/10 text-red-400 rounded-lg text-xs font-bold hover:bg-red-950/20 transition-all flex items-center justify-center gap-1.5"
            >
              <Trash2 size={12} /> Reset to Griztronics Demo Data
            </button>
          </div>
        </section>

        {/* Under the Hood (For Nerds) */}
        <section className="bg-zinc-950 border border-zinc-900 rounded-xl shadow-xl md:col-span-2">
          <button
            onClick={() => setShowNerdInfo(v => !v)}
            className="w-full flex items-center justify-between p-5 text-left"
          >
            <div className="flex items-center gap-2.5">
              <FlaskConical className="text-cyber-neonPink shadow-neonPink/20" size={18} />
              <h2 className="font-black text-sm text-zinc-200 uppercase tracking-wider">Under the Hood</h2>
              <span className="text-[8px] font-black bg-cyber-neonPink/10 border border-cyber-neonPink/30 text-cyber-neonPink px-2 py-0.5 rounded-full uppercase tracking-widest">for nerds</span>
            </div>
            <ChevronDown
              size={16}
              className={`text-zinc-500 transition-transform duration-200 ${showNerdInfo ? "rotate-180" : ""}`}
            />
          </button>

          {showNerdInfo && (
            <div className="px-5 pb-5 space-y-6 border-t border-zinc-900 pt-4 text-xs">
              {/* FAQ grid */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-zinc-900/30 border border-zinc-900 rounded-xl p-4 space-y-1.5">
                  <p className="text-[10px] font-black text-zinc-550 uppercase tracking-wider">Why Offline-First RAG?</p>
                  <p className="text-zinc-400 leading-relaxed">
                    Cell towers at massive outdoor festivals (especially locations like The Gorge) routinely collapse due to congestion. Event Med AI uses a fully local SQLite FTS5 search index to query clinical guides and substance information even when completely disconnected from the WAN.
                  </p>
                </div>

                <div className="bg-zinc-900/30 border border-zinc-900 rounded-xl p-4 space-y-1.5">
                  <p className="text-[10px] font-black text-zinc-550 uppercase tracking-wider">Reagent testing liability?</p>
                  <p className="text-zinc-400 leading-relaxed">
                    Color-reagent checks are only presumptive and cannot guarantee substance safety. The app enforces a mandatory 3-point clinical check disclaimer (`disclaimer_agreed=True`) which is logged to the SQLite database to legally mitigate organization liability.
                  </p>
                </div>

                <div className="bg-zinc-900/30 border border-zinc-900 rounded-xl p-4 space-y-1.5">
                  <p className="text-[10px] font-black text-zinc-550 uppercase tracking-wider">Triage Whiteboard Priority?</p>
                  <p className="text-zinc-400 leading-relaxed">
                    Encounters are triaged using standard color-coded tags (Red for emergent cardiorespiratory threats or severe hyperthermia, Yellow for urgent/unstable, Green for stable minor trauma or hydration needs, and Black for deceased).
                  </p>
                </div>

                <div className="bg-zinc-900/30 border border-zinc-900 rounded-xl p-4 space-y-1.5">
                  <p className="text-[10px] font-black text-zinc-550 uppercase tracking-wider">Gemini Cloud Mode?</p>
                  <p className="text-zinc-400 leading-relaxed">
                    In cloud mode, Event Med AI communicates with Google AI Studio (Gemini 2.5 Flash) via a developer api key. This allows ultra-fast processing speeds, visual image recognition of drug packaging, and does not require local GPU/Ollama setup.
                  </p>
                </div>
              </div>

              {/* Stack summary */}
              <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-4 font-mono text-[10px] space-y-1 text-zinc-400">
                <p className="text-zinc-650 mb-2"># model configuration & data pipelines</p>
                <p><span className="text-cyber-neonPurple font-bold">clinical chat</span>  →  <span className="text-zinc-200">Gemini Cloud (2.5 Flash)</span> or <span className="text-zinc-200">Local Ollama</span></p>
                <p><span className="text-cyber-neonPurple font-bold">RAG search index</span>  →  <span className="text-zinc-200">SQLite FTS5 Porter Tokenizer</span></p>
                <p><span className="text-cyber-neonPurple font-bold">liability logs</span>  →  <span className="text-zinc-200">SQLite WAL WAL-journal mode</span></p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
