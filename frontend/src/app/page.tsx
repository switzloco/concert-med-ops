"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Event, Patient, IncidentQueue, Encounter, Supply, HospitalDirectory } from "@/lib/types";
import { WeatherBanner } from "@/components/WeatherBanner";
import { HospitalSelector } from "@/components/HospitalSelector";
import Link from "next/link";
import { 
  Users, Activity, ClipboardList, ShieldAlert, Sparkles, 
  FlaskConical, Package, RefreshCw, AlertTriangle 
} from "lucide-react";

function StatCard({
  label,
  value,
  href,
  icon: Icon,
  accent,
  glow,
}: {
  label: string;
  value: number | string;
  href: string;
  icon: React.ElementType;
  accent: string;
  glow?: string;
}) {
  return (
    <Link
      href={href}
      className={`bg-zinc-950 border border-zinc-900 rounded-xl p-5 flex items-center gap-4 hover:border-zinc-800 transition-all duration-300 ${glow ?? ""}`}
    >
      <div className={`p-3 rounded-lg ${accent}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-black text-zinc-100">{value}</p>
        <p className="text-xs text-zinc-500 font-bold uppercase tracking-wider mt-0.5">{label}</p>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const eventInfo = useQuery({ queryKey: ["event-info"], queryFn: () => apiFetch<Event>("/setup/event-info") });
  const patients = useQuery({ queryKey: ["patients"], queryFn: () => apiFetch<Patient[]>("/patient") });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: () => apiFetch<IncidentQueue[]>("/tracking") });
  const encounters = useQuery({ queryKey: ["encounters"], queryFn: () => apiFetch<Encounter[]>("/encounter") });
  const supplies = useQuery({ queryKey: ["supplies"], queryFn: () => apiFetch<Supply[]>("/supplies") });
  const hospitals = useQuery({ queryKey: ["hospitals"], queryFn: () => apiFetch<HospitalDirectory[]>("/hospitals") });

  const activePatients = patients.data?.filter((p) => p.is_active).length ?? 0;
  const activeIncidents = incidents.data?.filter((i) => i.status !== "cleared").length ?? 0;
  const totalEncounters = encounters.data?.length ?? 0;
  
  // Count low supplies (remaining < 30% of start, or narcan < 10)
  const lowSupplies = supplies.data?.filter((s) => {
    if (s.category === "narcan" && s.quantity_remaining < 20) return true;
    return s.quantity_remaining < (s.quantity_start * 0.3);
  }).length ?? 0;

  const isDemoData = patients.data?.some((p) => p.identifier.includes("wristband #"));

  const handleResetData = async () => {
    if (confirm("Reset database to initial Griztronics 2026 festival demo dataset? This deletes all current patients, encounters, and logs.")) {
      await apiFetch("/setup/reset-demo-data", { method: "POST" });
      window.location.reload();
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-5">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white">{eventInfo.data?.name ?? "Event Med AI"}</h1>
          <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
            {eventInfo.data?.venue ?? "Incident Command Dashboard"} • Lead: {eventInfo.data?.medical_lead ?? "Supervisor"}
          </p>
        </div>
        
        <button
          onClick={handleResetData}
          className="flex items-center gap-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
        >
          <RefreshCw size={12} />
          Reset Demo Data
        </button>
      </div>

      {/* HEAT ALERT BANNER */}
      {eventInfo.data && (
        <WeatherBanner
          highTemp={eventInfo.data.weather_high_f}
          humidity={eventInfo.data.weather_humidity}
        />
      )}

      {/* STATS MATRIX */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Active Incidents"
          value={activeIncidents}
          href="/board"
          icon={ClipboardList}
          accent="bg-red-500/10 text-red-400 border border-red-500/30"
          glow="hover:shadow-neonPink"
        />
        <StatCard
          label="Logged Patients"
          value={activePatients}
          href="/patients"
          icon={Users}
          accent="bg-cyber-neonBlue/10 text-cyber-neonBlue border border-cyber-neonBlue/30"
          glow="hover:shadow-neonBlue"
        />
        <StatCard
          label="Encounters PCR/OTC"
          value={totalEncounters}
          href="/board"
          icon={Activity}
          accent="bg-cyber-neonPurple/10 text-cyber-neonPurple border border-cyber-neonPurple/30"
          glow="hover:shadow-neonPurple"
        />
        <StatCard
          label="Supply Warnings"
          value={lowSupplies}
          href="/supplies"
          icon={Package}
          accent={lowSupplies > 0 ? "bg-amber-500/10 text-amber-400 border border-amber-500/30" : "bg-zinc-900 text-zinc-500"}
          glow={lowSupplies > 0 ? "hover:shadow-neonGreen" : ""}
        />
      </div>

      {/* ACTION HERO CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/chat"
          className="md:col-span-2 p-6 bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 border border-zinc-900 rounded-2xl text-white hover:border-cyber-neonPurple/40 transition-all duration-300 relative overflow-hidden group hover:shadow-neonPurple"
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 text-cyber-neonPurple group-hover:scale-110 transition-transform duration-500">
            <Sparkles size={180} />
          </div>
          
          <div className="relative z-10 flex flex-col justify-between h-full min-h-[140px]">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="bg-cyber-neonPurple/10 border border-cyber-neonPurple/30 p-2 rounded-lg text-cyber-neonPurple shadow-neonPurple">
                    <Sparkles size={20} />
                  </div>
                  <h2 className="text-lg font-black tracking-wide">Ask Clinical Assistant</h2>
                </div>
                <div className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 px-2.5 py-0.5 rounded-full">
                  <div className="w-1.5 h-1.5 bg-cyber-neonGreen rounded-full animate-pulse" />
                  <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-400">Offline-first RAG Ready</span>
                </div>
              </div>
              
              <p className="text-xs text-zinc-400 leading-relaxed max-w-xl">
                Differential triage checklist (e.g. serotonin syndrome vs. heat stroke), polydrug toxicity warnings, 
                Gorge hospital capacities, and harm reduction protocol guidelines.
              </p>
            </div>
            
            <p className="text-[10px] font-extrabold text-cyber-neonPurple uppercase tracking-widest mt-4 group-hover:translate-x-1 transition-transform">
              Launch Chat Assistant &rarr;
            </p>
          </div>
        </Link>

        <Link
          href="/reagent"
          className="p-6 bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 border border-zinc-900 rounded-2xl text-white hover:border-cyber-neonPink/40 transition-all duration-300 relative overflow-hidden group hover:shadow-neonPink"
        >
          <div className="absolute top-0 right-0 p-4 opacity-5 text-cyber-neonPink group-hover:scale-110 transition-transform duration-500">
            <FlaskConical size={140} />
          </div>
          
          <div className="relative z-10 flex flex-col justify-between h-full min-h-[140px]">
            <div>
              <div className="bg-cyber-neonPink/10 border border-cyber-neonPink/30 p-2 rounded-lg text-cyber-neonPink shadow-neonPink w-fit mb-4">
                <FlaskConical size={20} />
              </div>
              <h2 className="text-lg font-black tracking-wide">Reagent & Pill ID</h2>
              <p className="text-xs text-zinc-400 mt-1.5 leading-relaxed">
                Log pill descriptions, fentanyl strip testing, Marquis/Mecke presumptive changes, with visual AI camera matching.
              </p>
            </div>
            
            <p className="text-[10px] font-extrabold text-cyber-neonPink uppercase tracking-widest mt-4 group-hover:translate-x-1 transition-transform">
              Open Reagent Logs &rarr;
            </p>
          </div>
        </Link>
      </div>

      {/* HOSPITAL DIRECTORY SECTION */}
      <div className="bg-zinc-950 border border-zinc-900 rounded-2xl p-5 shadow-xl space-y-4">
        <div>
          <h3 className="text-sm font-black uppercase tracking-wider text-zinc-200">Gorge Region Evacuation Routing</h3>
          <p className="text-xs text-zinc-500 leading-relaxed mt-0.5">
            Closest hospitals and diversion controls. Select a facility to display details. Use this matrix to manage ambulance routing decisions.
          </p>
        </div>

        {hospitals.data ? (
          <HospitalSelector
            hospitals={hospitals.data}
            onSelect={() => {}}
          />
        ) : (
          <div className="h-28 border border-dashed border-zinc-900 rounded-xl flex items-center justify-center text-xs text-zinc-600">
            Loading hospital matrices...
          </div>
        )}
      </div>
    </div>
  );
}
