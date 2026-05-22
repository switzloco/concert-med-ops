"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { IncidentQueue, Patient, StaffMember } from "@/lib/types";
import { TrackingRow } from "@/components/TrackingRow";
import { ClipboardList, Plus, AlertCircle, RefreshCw, UserPlus } from "lucide-react";

export default function TriageBoard() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>("active"); // "active" | "all" | "cleared"

  // Form states for creating incident
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedStaffId, setSelectedStaffId] = useState("");
  const [location, setLocation] = useState("medical_tent");
  const [priority, setPriority] = useState("green");
  const [radioNotes, setRadioNotes] = useState("");

  // Queries
  const { data: incidents, isLoading, isError, refetch } = useQuery<IncidentQueue[]>({
    queryKey: ["incidents"],
    queryFn: () => apiFetch<IncidentQueue[]>("/tracking"),
  });

  const { data: patients } = useQuery<Patient[]>({
    queryKey: ["patients"],
    queryFn: () => apiFetch<Patient[]>("/patient"),
  });

  const { data: staff } = useQuery<StaffMember[]>({
    queryKey: ["staff"],
    queryFn: () => apiFetch<StaffMember[]>("/staff"),
  });

  // Mutations
  const updateStatusMutation = useMutation({
    mutationFn: ({ incidentId, status }: { incidentId: string; status: string }) =>
      apiFetch(`/tracking/${incidentId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
    },
  });

  const createIncidentMutation = useMutation({
    mutationFn: (newIncident: any) =>
      apiFetch("/tracking", {
        method: "POST",
        body: JSON.stringify(newIncident),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      setShowAddModal(false);
      // Reset form
      setSelectedPatientId("");
      setSelectedStaffId("");
      setLocation("medical_tent");
      setPriority("green");
      setRadioNotes("");
    },
    onError: (err: any) => {
      alert(`Error creating incident: ${err.message}`);
    },
  });

  const handleUpdateStatus = (incidentId: string, status: string) => {
    updateStatusMutation.mutate({ incidentId, status });
  };

  const handleCreateIncident = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !selectedStaffId) {
      alert("Please select a patient and staff member.");
      return;
    }
    
    // Find active event ID
    const activePatient = patients?.find((p) => p.patient_id === selectedPatientId);
    if (!activePatient) return;

    createIncidentMutation.mutate({
      event_id: activePatient.event_id,
      patient_id: selectedPatientId,
      assigned_to: selectedStaffId,
      location,
      priority,
      radio_notes: radioNotes,
    });
  };

  // Filter and sort incidents
  // Sort priority: red -> yellow -> green -> black
  const priorityWeight = (p: string) => {
    switch (p) {
      case "red": return 4;
      case "yellow": return 3;
      case "green": return 2;
      case "black": return 1;
      default: return 0;
    }
  };

  const filteredIncidents = incidents
    ?.filter((inc) => {
      if (filterStatus === "active") return inc.status !== "cleared";
      if (filterStatus === "cleared") return inc.status === "cleared";
      return true;
    })
    .sort((a, b) => {
      // Sort cleared to the bottom
      if (a.status === "cleared" && b.status !== "cleared") return 1;
      if (a.status !== "cleared" && b.status === "cleared") return -1;
      
      // Sort by priority weight descending
      const weightA = priorityWeight(a.priority);
      const weightB = priorityWeight(b.priority);
      if (weightA !== weightB) return weightB - weightA;
      
      // Otherwise sort by dispatch time descending (newest first)
      return new Date(b.dispatch_time).getTime() - new Date(a.dispatch_time).getTime();
    });

  // Active roster (on shift)
  const onShiftStaff = staff?.filter((s) => s.is_on_shift) ?? [];

  return (
    <div className="space-y-6 max-w-6xl">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-5">
        <div className="flex items-center gap-3">
          <div className="bg-cyber-neonBlue/15 p-2 rounded-lg border border-cyber-neonBlue/40 text-cyber-neonBlue shadow-neonBlue">
            <ClipboardList size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide uppercase">ER Triage Whiteboard</h1>
            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
              Active incident queue • Sorted by priority status
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="p-2 border border-zinc-800 bg-zinc-950 text-zinc-400 hover:text-white rounded-lg hover:border-zinc-700 transition-all"
            aria-label="Refresh board"
          >
            <RefreshCw size={16} />
          </button>
          
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 bg-cyber-neonBlue text-black hover:bg-cyber-neonBlue/90 border border-cyber-neonBlue/50 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-neonBlue hover:scale-105"
          >
            <Plus size={14} />
            Dispatch Incident
          </button>
        </div>
      </div>

      {/* FILTER BUTTONS & STAFF SUMMARY */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-zinc-950 border border-zinc-900 p-4 rounded-xl shadow-lg">
        <div className="flex gap-2">
          {[
            { id: "active", label: "Active Queue" },
            { id: "all", label: "All Logs" },
            { id: "cleared", label: "Cleared" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterStatus(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                filterStatus === tab.id
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Shift roster indicators */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Active Roster:</span>
          <div className="flex flex-wrap gap-1.5">
            {onShiftStaff.length > 0 ? (
              onShiftStaff.map((s) => (
                <span
                  key={s.staff_id}
                  className="px-2 py-0.5 bg-zinc-900 border border-zinc-800 text-zinc-300 text-[10px] font-bold rounded-lg"
                  title={`${s.name} (${s.role.toUpperCase()})`}
                >
                  {s.call_sign}
                </span>
              ))
            ) : (
              <span className="text-[10px] text-red-400 italic">No staff logged on shift</span>
            )}
          </div>
        </div>
      </div>

      {/* WHITEBOARD GRID */}
      {isLoading ? (
        <div className="h-64 flex items-center justify-center text-zinc-500 text-sm">
          Loading whiteboard incidents...
        </div>
      ) : isError ? (
        <div className="h-64 border border-dashed border-red-500/20 bg-red-500/5 rounded-xl flex flex-col items-center justify-center text-red-400 p-6 text-center">
          <AlertCircle size={24} className="mb-2" />
          <p className="font-bold text-sm">Failed to connect to database</p>
          <p className="text-xs text-zinc-500 mt-1">Start the backend server on 127.0.0.1:8000</p>
        </div>
      ) : filteredIncidents && filteredIncidents.length > 0 ? (
        <div className="overflow-x-auto border border-zinc-900 rounded-xl shadow-2xl">
          <table className="min-w-full divide-y divide-zinc-900 text-left">
            <thead className="bg-zinc-950 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
              <tr>
                <th className="px-6 py-3">Triage</th>
                <th className="px-6 py-3">Patient Ref</th>
                <th className="px-6 py-3">Location</th>
                <th className="px-6 py-3">Assigned Staff</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Elapsed</th>
                <th className="px-6 py-3">Radio Log</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900">
              {filteredIncidents.map((inc) => (
                <TrackingRow
                  key={inc.incident_id}
                  incident={inc}
                  onUpdateStatus={handleUpdateStatus}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="h-64 border border-dashed border-zinc-900 rounded-xl flex flex-col items-center justify-center text-zinc-500 text-sm">
          <ClipboardList size={24} className="text-zinc-700 mb-2" />
          <p className="font-semibold text-zinc-400">All quiet on the board</p>
          <p className="text-xs text-zinc-600 mt-0.5">No incidents currently match the filters</p>
        </div>
      )}

      {/* DISPATCH INCIDENT MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="w-full max-w-md bg-zinc-950 border border-zinc-900 rounded-2xl shadow-2xl p-6 overflow-hidden">
            <h2 className="text-base font-black text-white tracking-wide uppercase mb-4 border-b border-zinc-900 pb-3 flex items-center gap-2">
              <UserPlus size={18} className="text-cyber-neonBlue" />
              <span>Dispatch Medical Rover</span>
            </h2>

            <form onSubmit={handleCreateIncident} className="space-y-4">
              {/* SELECT PATIENT */}
              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Patient Wristband/Identifier</label>
                <select
                  required
                  className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                >
                  <option value="">-- Choose Patient --</option>
                  {patients
                    ?.filter((p) => p.is_active)
                    .map((p) => (
                      <option key={p.patient_id} value={p.patient_id}>
                        {p.identifier}
                      </option>
                    ))}
                </select>
              </div>

              {/* SELECT STAFF */}
              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Assign Responder</label>
                <select
                  required
                  className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={selectedStaffId}
                  onChange={(e) => setSelectedStaffId(e.target.value)}
                >
                  <option value="">-- Assign Staff --</option>
                  {staff
                    ?.filter((s) => s.is_on_shift)
                    .map((s) => (
                      <option key={s.staff_id} value={s.staff_id}>
                        {s.name} ({s.call_sign} - {s.role.toUpperCase()})
                      </option>
                    ))}
                </select>
              </div>

              {/* PRIORITY & LOCATION */}
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Initial Triage Priority</label>
                  <select
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    <option value="green">Green - Minor</option>
                    <option value="yellow">Yellow - Delayed</option>
                    <option value="red">Red - Immediate</option>
                    <option value="black">Black - Deceased</option>
                  </select>
                </div>
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Dispatch Location</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. stage_left, camp_a"
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>
              </div>

              {/* RADIO NOTES */}
              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Radio Dispatch Notes</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Found slumped near rails, breathing shallow, rover-2 dispatched..."
                  className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={radioNotes}
                  onChange={(e) => setRadioNotes(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-zinc-900">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-zinc-800 hover:bg-zinc-900 text-zinc-400 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-cyber-neonBlue text-black hover:bg-cyber-neonBlue/90 px-4 py-2 border border-cyber-neonBlue/50 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-neonBlue"
                >
                  Dispatch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
