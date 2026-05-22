"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Patient, Encounter, StaffMember, IncidentQueue } from "@/lib/types";
import { 
  Users, Search, UserPlus, Heart, AlertTriangle, Plus, 
  MapPin, Calendar, Clock, Activity, FileText, Pill, Info 
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function PatientsPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);

  // Queries
  const { data: patients, isLoading: patientsLoading } = useQuery<Patient[]>({
    queryKey: ["patients", activeOnly],
    queryFn: () => apiFetch<Patient[]>(`/patient?active_only=${activeOnly}`),
  });

  const { data: encounters } = useQuery<Encounter[]>({
    queryKey: ["encounters"],
    queryFn: () => apiFetch<Encounter[]>("/encounter"),
  });

  const { data: staff } = useQuery<StaffMember[]>({
    queryKey: ["staff"],
    queryFn: () => apiFetch<StaffMember[]>("/staff"),
  });

  // Toggle patient active state mutation
  const toggleActiveMutation = useMutation({
    mutationFn: ({ patientId, isActive }: { patientId: string; isActive: boolean }) =>
      apiFetch(`/patient/${patientId}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: isActive }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });

  const handleToggleActive = (patientId: string, currentStatus: boolean) => {
    toggleActiveMutation.mutate({ patientId, isActive: !currentStatus });
  };

  // Find patient detail
  const selectedPatient = patients?.find((p) => p.patient_id === selectedPatientId);
  const patientEncounters = encounters?.filter((e) => e.patient_id === selectedPatientId) ?? [];

  // Filter patients by search term
  const filteredPatients = patients?.filter((p) =>
    p.identifier.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.location_found && p.location_found.toLowerCase().includes(searchTerm.toLowerCase()))
  ) ?? [];

  return (
    <div className="space-y-6 max-w-6xl pb-16">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-5">
        <div className="flex items-center gap-3">
          <div className="bg-cyber-neonBlue/15 p-2 rounded-lg border border-cyber-neonBlue/40 text-cyber-neonBlue shadow-neonBlue">
            <Users size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide uppercase">Patient Directory</h1>
            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
              Active wristbands & medical histories
            </p>
          </div>
        </div>

        <Link
          href="/encounter"
          className="flex items-center gap-1.5 bg-cyber-neonPurple text-white hover:bg-cyber-neonPurple/90 border border-cyber-neonPurple/50 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-neonPurple hover:scale-105"
        >
          <UserPlus size={14} />
          New Intake PCR
        </Link>
      </div>

      {/* FILTER & SEARCH ROW */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-zinc-950 border border-zinc-900 p-4 rounded-xl shadow-lg">
        <div className="relative w-full md:w-80">
          <input
            type="text"
            placeholder="Search wristband #, location found..."
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Search size={14} className="absolute left-3 top-2.5 text-zinc-500" />
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="w-4 h-4 text-cyber-neonBlue bg-zinc-900 border-zinc-800 rounded focus:ring-cyber-neonBlue"
            />
            <span className="text-xs text-zinc-400 font-bold uppercase tracking-wider">Active Board Cases Only</span>
          </label>
        </div>
      </div>

      {/* DIRECTORY SPLIT GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PATIENTS TABLE */}
        <div className="lg:col-span-2 bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden shadow-xl">
          {patientsLoading ? (
            <div className="h-64 flex items-center justify-center text-zinc-500 text-sm">
              Loading patients...
            </div>
          ) : filteredPatients.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-zinc-900 text-left text-xs">
                <thead>
                  <tr className="bg-zinc-950 text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                    <th className="px-5 py-3">Wristband / Identifier</th>
                    <th className="px-5 py-3">Location Found</th>
                    <th className="px-5 py-3">Details</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900">
                  {filteredPatients.map((p) => {
                    const isSelected = p.patient_id === selectedPatientId;
                    return (
                      <tr
                        key={p.patient_id}
                        onClick={() => setSelectedPatientId(p.patient_id)}
                        className={`cursor-pointer transition-all ${
                          isSelected
                            ? "bg-cyber-neonBlue/10 border-l-2 border-cyber-neonBlue"
                            : "hover:bg-zinc-900/30"
                        }`}
                      >
                        <td className="px-5 py-4">
                          <span className="font-extrabold text-zinc-200 text-sm tracking-wide block">{p.identifier}</span>
                          <span className="text-[10px] text-zinc-500 block font-mono mt-0.5">ID: {p.patient_id.substring(0, 8)}</span>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-1 text-zinc-400">
                            <MapPin size={12} className="text-zinc-650" />
                            <span className="capitalize">{p.location_found.replace("_", " ")}</span>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-zinc-450 block">Age: {p.approx_age ?? "Unknown"} • {p.gender ?? "Unknown"}</span>
                          {p.substances_reported && p.substances_reported.length > 0 && (
                            <span className="text-[10px] text-cyber-neonPink mt-1 block truncate max-w-[150px]">
                              {p.substances_reported.map(s => s.name).join(", ")}
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-4">
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
                            p.is_active
                              ? "bg-green-500/20 text-green-400 border-green-500/30"
                              : "bg-zinc-800 text-zinc-550 border-zinc-700"
                          }`}>
                            {p.is_active ? "Active" : "Archived"}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleToggleActive(p.patient_id, p.is_active);
                            }}
                            className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider transition-all border ${
                              p.is_active
                                ? "bg-zinc-900 border-zinc-800 text-zinc-450 hover:bg-zinc-800"
                                : "bg-cyber-neonBlue text-black border-cyber-neonBlue/50 hover:bg-cyber-neonBlue/90 shadow-neonBlue"
                            }`}
                          >
                            {p.is_active ? "Archive" : "Activate"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-zinc-500 text-sm">
              No patients found matching the criteria
            </div>
          )}
        </div>

        {/* DETAILS SIDEBAR PANEL */}
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-6">
          {selectedPatient ? (
            <div className="space-y-6 animate-fade-in">
              {/* TOP HEADER */}
              <div className="border-b border-zinc-900 pb-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-base font-black text-white tracking-wide uppercase">Patient Clinical File</h3>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                    selectedPatient.is_active
                      ? "bg-green-500/20 text-green-400 border border-green-500/30"
                      : "bg-zinc-800 text-zinc-500 border border-zinc-700"
                  }`}>
                    {selectedPatient.is_active ? "Active Board File" : "Archived Case"}
                  </span>
                </div>
                <p className="text-xl font-extrabold text-cyber-neonBlue mt-2">{selectedPatient.identifier}</p>
                <div className="flex items-center gap-4 text-xs text-zinc-500 mt-2">
                  <span>Age: <strong>{selectedPatient.approx_age ?? "U/K"}</strong></span>
                  <span>Gender: <strong>{selectedPatient.gender ?? "U/K"}</strong></span>
                  <span>Weight: <strong>{selectedPatient.weight_kg ? `${selectedPatient.weight_kg} kg` : "U/K"}</strong></span>
                </div>
              </div>

              {/* ENCOUNTER LOGS LIST */}
              <div className="space-y-3">
                <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Encounter Timeline</h4>
                {patientEncounters.length > 0 ? (
                  <div className="space-y-3">
                    {patientEncounters.map((enc) => {
                      const staffCall = staff?.find((s) => s.staff_id === enc.logged_by)?.call_sign ?? "Medic";
                      return (
                        <div key={enc.encounter_id} className="p-3 bg-zinc-900/40 border border-zinc-900 rounded-lg space-y-2">
                          <div className="flex justify-between items-center">
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                              enc.doc_type === "pcr" ? "bg-cyber-neonPurple/20 text-cyber-neonPurple" : "bg-cyber-neonGreen/20 text-cyber-neonGreen"
                            }`}>
                              {enc.doc_type.toUpperCase()}
                            </span>
                            <span className="text-[10px] text-zinc-500">
                              {new Date(enc.encounter_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>

                          <p className="text-xs text-zinc-200">
                            <strong>Chief Complaint:</strong> {enc.chief_complaint ?? "None"}
                          </p>

                          {enc.symptoms && enc.symptoms.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {enc.symptoms.map(s => (
                                <span key={s} className="px-1.5 py-0.5 bg-zinc-950 text-zinc-450 border border-zinc-900 rounded text-[9px]">
                                  {s}
                                </span>
                              ))}
                            </div>
                          )}

                          {enc.vital_signs && Object.keys(enc.vital_signs).length > 0 && (
                            <div className="grid grid-cols-3 gap-1 pt-1.5 border-t border-zinc-950 text-[10px] text-zinc-500">
                              <span>HR: <strong className="text-zinc-300">{enc.vital_signs.hr ?? "—"}</strong></span>
                              <span>BP: <strong className="text-zinc-300">{enc.vital_signs.bp ?? "—"}</strong></span>
                              <span>Temp: <strong className="text-zinc-300">{enc.vital_signs.temp_f ?? "—"}°F</strong></span>
                            </div>
                          )}

                          <div className="flex justify-between items-center text-[10px] text-zinc-500 pt-1.5 border-t border-zinc-950">
                            <span>Logged by: <strong>{staffCall}</strong></span>
                            <span className="capitalize text-cyber-neonBlue">Disp: <strong>{enc.disposition}</strong></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-zinc-500 italic">No clinical encounters recorded yet.</p>
                )}
              </div>

              {/* ACTION SHORTCUTS */}
              <div className="pt-4 border-t border-zinc-900 space-y-2">
                <Link
                  href={`/encounter?patient_id=${selectedPatient.patient_id}`}
                  className="w-full flex items-center justify-center gap-1.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all text-zinc-300"
                >
                  <Plus size={14} className="text-cyber-neonPurple" />
                  Add Encounter Log
                </Link>
              </div>
            </div>
          ) : (
            <div className="h-64 flex flex-col items-center justify-center text-zinc-600 text-xs border border-dashed border-zinc-900 rounded-lg text-center p-4">
              <Info size={18} className="mb-2 text-zinc-750" />
              Select a patient from the directory to review clinical summaries and vitals timelines
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
