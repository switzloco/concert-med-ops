"use client";

import React from "react";
import type { IncidentQueue } from "@/lib/types";
import { TriageBadge } from "./TriageBadge";
import { MapPin, User, Clock, Radio, ChevronRight } from "lucide-react";
import Link from "next/link";

interface TrackingRowProps {
  incident: IncidentQueue;
  onUpdateStatus: (incidentId: string, status: string) => void;
}

export function TrackingRow({ incident, onUpdateStatus }: TrackingRowProps) {
  const elapsedMinutes = () => {
    if (!incident.dispatch_time) return "";
    const start = new Date(incident.dispatch_time).getTime();
    const end = incident.cleared_time ? new Date(incident.cleared_time).getTime() : Date.now();
    const diff = Math.floor((end - start) / 60000);
    return `${diff}m`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "dispatched": return "bg-red-500/10 text-red-400 border border-red-500/20";
      case "en_route": return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
      case "on_scene": return "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 animate-pulse";
      case "in_tent": return "bg-cyber-neonBlue/10 text-cyber-neonBlue border border-cyber-neonBlue/20 shadow-neonBlue";
      case "observation": return "bg-cyber-neonPurple/10 text-cyber-neonPurple border border-cyber-neonPurple/20 shadow-neonPurple";
      case "cleared": return "bg-green-500/10 text-green-400 border border-green-500/20";
      default: return "bg-zinc-800 text-zinc-400";
    }
  };

  return (
    <tr className="border-b border-zinc-900 bg-zinc-950 hover:bg-zinc-900/60 transition-all duration-200">
      {/* PRIORITY */}
      <td className="px-6 py-4 whitespace-nowrap">
        <TriageBadge level={incident.priority} short />
      </td>

      {/* PATIENT IDENTIFIER */}
      <td className="px-6 py-4">
        <div className="text-sm font-bold text-zinc-200 truncate max-w-[200px]" title={incident.patient?.identifier}>
          {incident.patient?.identifier ?? "Wristband / Anonymous ID"}
        </div>
        {incident.patient?.substances_reported && incident.patient.substances_reported.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {incident.patient.substances_reported.map((sub, idx) => (
              <span key={idx} className="text-[10px] bg-zinc-900 text-zinc-400 px-1.5 py-0.5 rounded font-mono">
                {sub.name}
              </span>
            ))}
          </div>
        )}
      </td>

      {/* LOCATION */}
      <td className="px-6 py-4 whitespace-nowrap text-zinc-300">
        <div className="flex items-center gap-1.5 text-sm">
          <MapPin size={14} className="text-zinc-500" />
          <span>{incident.location}</span>
        </div>
      </td>

      {/* ASSIGNED STAFF */}
      <td className="px-6 py-4 whitespace-nowrap text-zinc-300">
        <div className="flex items-center gap-1.5 text-sm">
          <User size={14} className="text-zinc-500" />
          <span>{incident.assigned_staff?.name ? `${incident.assigned_staff.name} (${incident.assigned_staff.call_sign})` : "Unassigned"}</span>
        </div>
      </td>

      {/* STATUS SELECT */}
      <td className="px-6 py-4 whitespace-nowrap">
        <select
          value={incident.status}
          onChange={(e) => onUpdateStatus(incident.incident_id, e.target.value)}
          className={`px-2.5 py-1 text-xs rounded-full outline-none font-bold uppercase tracking-wider transition-all duration-300 cursor-pointer ${getStatusColor(incident.status)}`}
        >
          <option value="dispatched" className="bg-zinc-950 text-red-400">Dispatched</option>
          <option value="en_route" className="bg-zinc-950 text-amber-400">En Route</option>
          <option value="on_scene" className="bg-zinc-950 text-yellow-400">On Scene</option>
          <option value="in_tent" className="bg-zinc-950 text-cyber-neonBlue">In Tent</option>
          <option value="observation" className="bg-zinc-950 text-cyber-neonPurple">Observation</option>
          <option value="cleared" className="bg-zinc-950 text-green-400">Cleared</option>
        </select>
      </td>

      {/* ELAPSED TIME */}
      <td className="px-6 py-4 whitespace-nowrap text-zinc-400 text-sm">
        <div className="flex items-center gap-1.5">
          <Clock size={14} className="text-zinc-600" />
          <span>{elapsedMinutes()}</span>
        </div>
      </td>

      {/* RADIO NOTES / COMMS */}
      <td className="px-6 py-4 max-w-[200px] truncate text-zinc-500 text-xs italic">
        <div className="flex items-center gap-1">
          <Radio size={12} className="text-zinc-600 shrink-0" />
          <span className="truncate">{incident.radio_notes ?? "No radio log"}</span>
        </div>
      </td>

      {/* ACTIONS */}
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <Link
          href={`/encounter?patient_id=${incident.patient_id}&incident_id=${incident.incident_id}`}
          className="inline-flex items-center gap-1 bg-cyber-neonBlue/10 text-cyber-neonBlue hover:bg-cyber-neonBlue/20 border border-cyber-neonBlue/30 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-300 shadow-neonBlue"
        >
          <span>Evaluate</span>
          <ChevronRight size={14} />
        </Link>
      </td>
    </tr>
  );
}
