"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { Patient, StaffMember, HospitalDirectory, SubstanceReported, VitalSigns, Intervention } from "@/lib/types";
import { VitalsInput } from "@/components/VitalsInput";
import { SubstanceLogger } from "@/components/SubstanceLogger";
import { HospitalSelector } from "@/components/HospitalSelector";
import { AMAForm } from "@/components/AMAForm";
import { 
  ClipboardPlus, ArrowLeft, UserPlus, Sparkles, Activity, 
  AlertTriangle, ShieldAlert, Plus, Trash2, CheckCircle2 
} from "lucide-react";

export default function NewEncounterPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Mode: PCR vs OTC
  const [docType, setDocType] = useState<"pcr" | "otc">("pcr");

  // Core metadata
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedStaffId, setSelectedStaffId] = useState("");
  const [triageLevel, setTriageLevel] = useState<"green" | "yellow" | "red" | "black">("green");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [notes, setNotes] = useState("");

  // Patient Creation state (if adding new patient inline)
  const [isNewPatient, setIsNewPatient] = useState(false);
  const [newIdentifier, setNewIdentifier] = useState("");
  const [newAge, setNewAge] = useState<number | "">("");
  const [newGender, setNewGender] = useState("");
  const [newLocationFound, setNewLocationFound] = useState<"venue_tent" | "campground" | "gate" | "field" | "other">("venue_tent");

  // AI Autofill description
  const [rawIntakeText, setRawIntakeText] = useState("");
  const [isExtracting, setIsExtracting] = useState(false);

  // Symptoms
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const commonSymptoms = [
    "Nausea", "Vomiting", "Hyperthermia", "Agitation", "Hallucinations",
    "Trauma/Laceration", "Headache", "Anxiety", "Dyspnea", "Chest Pain",
    "Tachycardia", "Seizure", "Confusion", "Dehydration"
  ];

  const handleSymptomToggle = (symptom: string) => {
    setSymptoms((prev) =>
      prev.includes(symptom) ? prev.filter((s) => s !== symptom) : [...prev, symptom]
    );
  };

  // Vitals
  const [vitals, setVitals] = useState<VitalSigns>({
    hr: undefined,
    bp: "",
    temp_f: undefined,
    spo2: undefined,
    rr: undefined,
    gcs: undefined,
    pupils: "",
    skin_condition: ""
  });

  // Substances
  const [substances, setSubstances] = useState<SubstanceReported[]>([]);

  // Interventions
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [customAction, setCustomAction] = useState("");
  const [customActionNotes, setCustomActionNotes] = useState("");

  const handleAddIntervention = (actionName: string, detailNotes: string = "") => {
    setInterventions((prev) => [
      ...prev,
      {
        action: actionName,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        by_whom: selectedStaffId || "Staff",
        notes: detailNotes || undefined
      }
    ]);
  };

  const handleRemoveIntervention = (idx: number) => {
    setInterventions((prev) => prev.filter((_, i) => i !== idx));
  };

  // Disposition
  const [disposition, setDisposition] = useState<"released" | "observation" | "transport" | "ama" | "deceased">("released");
  const [transportHospital, setTransportHospital] = useState("");
  const [transportUnit, setTransportUnit] = useState("");

  // AMA capacity checkboxes
  const [amaCheckboxes, setAmaCheckboxes] = useState({
    oriented: false,
    noGrossImpairment: false,
    understandsRisks: false,
    noSelfHarm: false,
    noPsychosis: false,
  });
  const [amaCapacityNote, setAmaCapacityNote] = useState("");
  const [pendingPrefillPatientId, setPendingPrefillPatientId] = useState<string | null>(null);

  // Prefill check on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const prefillChat = sessionStorage.getItem("encounter_prefill_chat");
      const prefillPatientId = sessionStorage.getItem("encounter_prefill_patient_id");
      
      if (prefillChat) {
        setRawIntakeText(prefillChat);
        sessionStorage.removeItem("encounter_prefill_chat");
        
        if (prefillPatientId) {
          setSelectedPatientId(prefillPatientId);
          setIsNewPatient(false);
          setPendingPrefillPatientId(prefillPatientId);
        } else {
          setIsNewPatient(true);
        }
        
        // Trigger auto-extraction
        handleAIExtract(prefillChat);
      }
    }
  }, []);

  // Fetch lists
  const { data: patients } = useQuery<Patient[]>({
    queryKey: ["patients"],
    queryFn: () => apiFetch<Patient[]>("/patient"),
  });

  const { data: staff } = useQuery<StaffMember[]>({
    queryKey: ["staff"],
    queryFn: () => apiFetch<StaffMember[]>("/staff"),
  });

  const { data: hospitals } = useQuery<HospitalDirectory[]>({
    queryKey: ["hospitals"],
    queryFn: () => apiFetch<HospitalDirectory[]>("/hospitals"),
  });

  // Update substances from patient when patient data finishes loading
  useEffect(() => {
    if (pendingPrefillPatientId && patients) {
      const pat = patients.find(p => p.patient_id === pendingPrefillPatientId);
      if (pat?.substances_reported) {
        setSubstances(pat.substances_reported);
      }
      setPendingPrefillPatientId(null);
    }
  }, [patients, pendingPrefillPatientId]);

  // Mutation to create a patient
  const createPatientMutation = useMutation({
    mutationFn: (newPatient: any) => apiFetch<Patient>("/patient", {
      method: "POST",
      body: JSON.stringify(newPatient)
    }),
  });

  // Mutation to create an encounter
  const createEncounterMutation = useMutation({
    mutationFn: (encounterPayload: any) => apiFetch("/encounter", {
      method: "POST",
      body: JSON.stringify(encounterPayload),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["encounters"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      router.push("/board");
    },
    onError: (err: any) => {
      alert(`Failed to save encounter: ${err.message}`);
    }
  });

  // AI Extract intake note
  const handleAIExtract = async (textOverride?: string) => {
    const textToExtract = textOverride !== undefined ? textOverride : rawIntakeText;
    if (!textToExtract.trim()) return;
    setIsExtracting(true);
    try {
      const activeEventId = patients?.[0]?.event_id || "griztronics-2026";
      const res = await apiFetch<any>("/ai/extract-encounter-info", {
        method: "POST",
        body: JSON.stringify({
          text: textToExtract,
          event_id: activeEventId
        })
      });

      if (res) {
        if (res.chief_complaint) setChiefComplaint(res.chief_complaint);
        if (res.triage_level) setTriageLevel(res.triage_level);
        if (res.disposition) setDisposition(res.disposition);
        
        // Match symptoms
        if (res.symptoms && Array.isArray(res.symptoms)) {
          const matchedSymptoms = res.symptoms.map((s: string) => {
            const match = commonSymptoms.find(cs => cs.toLowerCase() === s.toLowerCase());
            return match || s;
          });
          setSymptoms(prev => Array.from(new Set([...prev, ...matchedSymptoms])));
        }

        // Vitals
        setVitals({
          hr: res.hr || undefined,
          bp: res.bp || "",
          temp_f: res.temp_f || undefined,
          spo2: res.spo2 || undefined,
          rr: res.rr || undefined,
          gcs: res.gcs || undefined,
          pupils: vitals.pupils,
          skin_condition: vitals.skin_condition
        });

        // Substances
        if (res.substances_involved && Array.isArray(res.substances_involved)) {
          const newSubs: SubstanceReported[] = res.substances_involved.map((sub: string) => ({
            name: sub,
            route: "Oral",
            time_taken: "Unknown",
            amount: "Unknown"
          }));
          setSubstances(prev => {
            const existingNames = new Set(prev.map(s => s.name.toLowerCase()));
            const filteredNew = newSubs.filter(s => !existingNames.has(s.name.toLowerCase()));
            return [...prev, ...filteredNew];
          });
        }
      }
    } catch (error) {
      console.error(error);
      alert("AI extraction failed. Please fill manually.");
    } finally {
      setIsExtracting(false);
    }
  };

  // Submit Handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedStaffId) {
      alert("Please select the logged-by Staff Member.");
      return;
    }

    let patientId = selectedPatientId;
    const activeEventId = patients?.[0]?.event_id || "griztronics-2026";

    // If new patient mode is toggled, create patient first
    if (isNewPatient) {
      if (!newIdentifier.trim()) {
        alert("Please provide an anonymous wristband ID or physical description for the patient.");
        return;
      }
      try {
        const freshPatient = await createPatientMutation.mutateAsync({
          event_id: activeEventId,
          identifier: newIdentifier.trim(),
          approx_age: newAge ? Number(newAge) : undefined,
          gender: newGender || undefined,
          location_found: newLocationFound,
          substances_reported: substances,
        });
        patientId = freshPatient.patient_id;
      } catch (err: any) {
        alert(`Failed to create patient: ${err.message}`);
        return;
      }
    }

    if (!patientId) {
      alert("Please select a patient or toggle 'New Patient'.");
      return;
    }

    // Assemble payload
    const payload: any = {
      event_id: activeEventId,
      patient_id: patientId,
      doc_type: docType,
      logged_by: selectedStaffId,
      chief_complaint: chiefComplaint || undefined,
      symptoms: docType === "pcr" ? symptoms : [],
      vital_signs: docType === "pcr" ? vitals : {},
      substances_involved: substances.map(s => s.name),
      triage_level: docType === "pcr" ? triageLevel : "green",
      interventions: interventions,
      disposition: disposition,
      notes: notes || undefined
    };

    if (disposition === "transport") {
      payload.transport_hospital = transportHospital || undefined;
      payload.transport_unit = transportUnit || undefined;
      payload.transport_time = new Date().toISOString();
    } else if (disposition === "ama") {
      payload.ama_documented = true;
      payload.ama_capacity_assessment = JSON.stringify({
        checkboxes: amaCheckboxes,
        note: amaCapacityNote
      });
    }

    createEncounterMutation.mutate(payload);
  };

  const onShiftStaff = staff?.filter((s) => s.is_on_shift) ?? [];

  return (
    <div className="space-y-6 max-w-4xl pb-16">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-5">
        <div className="flex items-center gap-3">
          <div className="bg-cyber-neonPurple/15 p-2 rounded-lg border border-cyber-neonPurple/40 text-cyber-neonPurple shadow-neonPurple">
            <ClipboardPlus size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide uppercase">New Encounter Log</h1>
            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
              Document patient treatments, OTC distribution, or transport decisions
            </p>
          </div>
        </div>

        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
        >
          <ArrowLeft size={14} />
          Back
        </button>
      </div>

      {/* AI AUTOFILL EXTRACTOR */}
      <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl relative overflow-hidden group hover:border-cyber-neonPurple/30 transition-all duration-300">
        <div className="absolute top-0 right-0 p-3 opacity-5 text-cyber-neonPurple group-hover:scale-110 transition-transform">
          <Sparkles size={100} />
        </div>
        <div className="flex items-center gap-2 mb-3">
          <Sparkles size={16} className="text-cyber-neonPurple" />
          <h2 className="text-xs font-black uppercase tracking-wider text-zinc-200">AI Intake Autofill</h2>
        </div>
        <p className="text-xs text-zinc-500 mb-4 leading-relaxed">
          Paste a quick verbal description or Rover radio dispatch note below (e.g. <i>&quot;Wristband #302, 22yo female, rapid pulse, hyperthermic at campgrounds, suspected MDMA. Cool towels applied.&quot;</i>). The offline assistant will parse symptoms, vitals, and triage status into the fields below automatically.
        </p>
        <div className="flex gap-2">
          <textarea
            rows={2}
            placeholder="Paste raw transcript or radio logs..."
            className="flex-1 px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/40 text-zinc-300 text-xs outline-none focus:border-cyber-neonPurple min-h-[50px]"
            value={rawIntakeText}
            onChange={(e) => setRawIntakeText(e.target.value)}
          />
          <button
            type="button"
            onClick={handleAIExtract}
            disabled={isExtracting || !rawIntakeText.trim()}
            className="bg-cyber-neonPurple text-white hover:bg-cyber-neonPurple/95 disabled:opacity-50 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1 shadow-neonPurple shrink-0"
          >
            {isExtracting ? "Extracting..." : "Autofill"}
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* LOG METADATA ROW */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* DOC TYPE */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-lg space-y-3">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Encounter Type</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDocType("pcr")}
                className={`py-2 text-xs font-bold uppercase tracking-wider border rounded-lg transition-all ${
                  docType === "pcr"
                    ? "bg-cyber-neonPurple/25 border-cyber-neonPurple text-cyber-neonPurple shadow-neonPurple"
                    : "bg-zinc-900/50 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-white"
                }`}
              >
                Full PCR
              </button>
              <button
                type="button"
                onClick={() => setDocType("otc")}
                className={`py-2 text-xs font-bold uppercase tracking-wider border rounded-lg transition-all ${
                  docType === "otc"
                    ? "bg-cyber-neonGreen/25 border-cyber-neonGreen text-cyber-neonGreen shadow-neonGreen"
                    : "bg-zinc-900/50 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-white"
                }`}
              >
                OTC Given
              </button>
            </div>
            <p className="text-[10px] text-zinc-500 leading-relaxed italic">
              {docType === "pcr" 
                ? "Full Patient Care Report: requires vitals, triage level, and disposition." 
                : "Quick OTC medication record: minimal info required, defaults to green triage."}
            </p>
          </div>

          {/* STAFF LOGGER */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-lg flex flex-col justify-between">
            <div className="flex flex-col">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2">Logged By (Staff)</label>
              <select
                required
                className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPurple"
                value={selectedStaffId}
                onChange={(e) => setSelectedStaffId(e.target.value)}
              >
                <option value="">-- Choose Roster Sign-In --</option>
                {onShiftStaff.map((s) => (
                  <option key={s.staff_id} value={s.staff_id}>
                    {s.name} ({s.call_sign} - {s.role.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>
            <p className="text-[10px] text-zinc-500 italic mt-3">
              Only shift-active medical personnel listed. Adjust roster in Settings.
            </p>
          </div>

          {/* TRIAGE LEVEL (PCR Only) */}
          {docType === "pcr" && (
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-lg space-y-3">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Triage Level</label>
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { val: "green", bg: "bg-green-500/20 text-green-300 border-green-500/40 focus:ring-green-500" },
                  { val: "yellow", bg: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40 focus:ring-yellow-500" },
                  { val: "red", bg: "bg-red-500/20 text-red-300 border-red-500/40 focus:ring-red-500 animate-pulse" },
                  { val: "black", bg: "bg-zinc-800 text-zinc-200 border-zinc-700 focus:ring-zinc-600" }
                ].map((item) => (
                  <button
                    key={item.val}
                    type="button"
                    onClick={() => setTriageLevel(item.val as any)}
                    className={`py-2 text-[10px] font-bold uppercase tracking-wider border rounded-lg transition-all ${
                      triageLevel === item.val
                        ? `${item.bg} border-current ring-1 ring-white`
                        : "bg-zinc-900/50 border-zinc-800 text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    {item.val}
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-zinc-500 leading-relaxed italic">
                Red indicates immediate life threats (unstable vitals). Green indicates minor/walking wounded.
              </p>
            </div>
          )}
        </div>

        {/* PATIENT PROFILE */}
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
          <div className="flex justify-between items-center border-b border-zinc-900 pb-3">
            <h3 className="text-xs font-black uppercase tracking-wider text-zinc-200 flex items-center gap-2">
              <Activity size={14} className="text-cyber-neonBlue" />
              Patient Association
            </h3>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isNewPatient}
                onChange={(e) => setIsNewPatient(e.target.checked)}
                className="w-4 h-4 text-cyber-neonBlue bg-zinc-900 border-zinc-800 rounded focus:ring-cyber-neonBlue"
              />
              <span className="text-xs font-bold text-cyber-neonBlue uppercase tracking-wider">New Patient</span>
            </label>
          </div>

          {isNewPatient ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Wristband # or Description</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Wristband #912 / Green Tanktop"
                  className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={newIdentifier}
                  onChange={(e) => setNewIdentifier(e.target.value)}
                />
              </div>

              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Approx. Age</label>
                <input
                  type="number"
                  placeholder="e.g. 23"
                  className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={newAge}
                  onChange={(e) => setNewAge(e.target.value ? Number(e.target.value) : "")}
                />
              </div>

              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Gender</label>
                <input
                  type="text"
                  placeholder="e.g. Male / Female"
                  className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={newGender}
                  onChange={(e) => setNewGender(e.target.value)}
                />
              </div>

              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Location Found</label>
                <select
                  className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                  value={newLocationFound}
                  onChange={(e) => setNewLocationFound(e.target.value as any)}
                >
                  <option value="venue_tent">Venue Main Tent</option>
                  <option value="campground">Campground Area</option>
                  <option value="gate">Entrance / Gate</option>
                  <option value="field">Outdoor Fields</option>
                  <option value="other">Other location</option>
                </select>
              </div>
            </div>
          ) : (
            <div className="flex flex-col">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Select Active Patient</label>
              <select
                required={!isNewPatient}
                className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                value={selectedPatientId}
                onChange={(e) => {
                  setSelectedPatientId(e.target.value);
                  // Autofill suspected substances from patient file if any
                  const pat = patients?.find(p => p.patient_id === e.target.value);
                  if (pat?.substances_reported) {
                    setSubstances(pat.substances_reported);
                  }
                }}
              >
                <option value="">-- Choose Patient Wristband --</option>
                {patients
                  ?.filter((p) => p.is_active)
                  .map((p) => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.identifier} ({p.location_found})
                    </option>
                  ))}
              </select>
            </div>
          )}
        </div>

        {/* CLINICAL LOGS (PCR ONLY) */}
        {docType === "pcr" && (
          <>
            {/* VITALS SECTION */}
            <div className="space-y-2">
              <h3 className="text-xs font-black uppercase tracking-wider text-zinc-400">Physiological Vitals</h3>
              <VitalsInput vitals={vitals} onChange={setVitals} />
            </div>

            {/* SYMPTOMS CHECKLIST */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Observed Symptoms Checklist</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {commonSymptoms.map((sym) => {
                  const active = symptoms.includes(sym);
                  return (
                    <button
                      key={sym}
                      type="button"
                      onClick={() => handleSymptomToggle(sym)}
                      className={`flex items-center gap-2 p-2 border rounded-lg text-left text-xs transition-all ${
                        active
                          ? "bg-cyber-neonPurple/15 border-cyber-neonPurple text-zinc-200"
                          : "bg-zinc-900/30 border-zinc-900 text-zinc-500 hover:border-zinc-800 hover:text-zinc-400"
                      }`}
                    >
                      <div className={`w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0 ${
                        active ? "border-cyber-neonPurple bg-cyber-neonPurple text-black" : "border-zinc-700"
                      }`}>
                        {active && <CheckCircle2 size={10} />}
                      </div>
                      <span>{sym}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* SUBSTANCE INVOLVEMENT */}
        <div className="space-y-2">
          <h3 className="text-xs font-black uppercase tracking-wider text-zinc-400">Substances Involvement</h3>
          <SubstanceLogger substances={substances} onChange={setSubstances} />
        </div>

        {/* INTERVENTIONS (PCR & OTC) */}
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
          <h3 className="text-xs font-black uppercase tracking-wider text-zinc-200 flex items-center gap-2 border-b border-zinc-900 pb-3">
            <Activity size={14} className="text-cyber-neonGreen" />
            Medical Interventions Logged
          </h3>

          {interventions.length > 0 ? (
            <div className="divide-y divide-zinc-900 border border-zinc-900 rounded-lg overflow-hidden bg-zinc-950">
              {interventions.map((intv, idx) => (
                <div key={idx} className="flex justify-between items-start p-3 text-xs">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-zinc-200 uppercase tracking-wide">{intv.action}</span>
                      <span className="text-[10px] text-zinc-500 font-mono">@{intv.time} by {intv.by_whom}</span>
                    </div>
                    {intv.notes && <p className="text-zinc-400 mt-1">{intv.notes}</p>}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveIntervention(idx)}
                    className="text-zinc-600 hover:text-red-400 p-1"
                    aria-label="Remove intervention"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-zinc-500 italic">No interventions logged. Select quick items below or write custom.</p>
          )}

          {/* QUICK INTERVENTIONS */}
          <div className="space-y-3">
            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Quick Interventions</p>
            <div className="flex flex-wrap gap-2">
              {[
                { name: "Administered Narcan (Naloxone)", notes: "4mg Intranasal spray" },
                { name: "IV Hydration Started", notes: "1L Normal Saline" },
                { name: "Active cooling applied", notes: "Ice packs to groin/axilla & wet towels" },
                { name: "Wound debridement & bandage", notes: "Cleaned with saline, gauze dress" },
                { name: "OTC Pain Relief given", notes: "Acetaminophen 650mg PO" },
                { name: "OTC Antihistamine given", notes: "Diphenhydramine 25mg PO" },
                { name: "Oral Electrolytes administered", notes: "500mL Gatorade PO" },
                { name: "De-escalation / Quiet room rest", notes: "Placed in dark tent with supervisor" },
              ].map((item) => (
                <button
                  key={item.name}
                  type="button"
                  onClick={() => handleAddIntervention(item.name, item.notes)}
                  className="px-3 py-1 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 rounded-lg text-xs transition-all"
                >
                  + {item.name}
                </button>
              ))}
            </div>
          </div>

          {/* CUSTOM INTERVENTION ADDER */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-zinc-900 items-end">
            <div className="flex flex-col col-span-1">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Custom Action</label>
              <input
                type="text"
                placeholder="e.g. Splint applied"
                className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonGreen"
                value={customAction}
                onChange={(e) => setCustomAction(e.target.value)}
              />
            </div>
            <div className="flex flex-col col-span-1">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1">Intervention Notes</label>
              <input
                type="text"
                placeholder="e.g. Rigid splint to left wrist"
                className="px-3 py-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonGreen"
                value={customActionNotes}
                onChange={(e) => setCustomActionNotes(e.target.value)}
              />
            </div>
            <button
              type="button"
              onClick={() => {
                if (customAction.trim()) {
                  handleAddIntervention(customAction.trim(), customActionNotes.trim());
                  setCustomAction("");
                  setCustomActionNotes("");
                }
              }}
              disabled={!customAction.trim()}
              className="bg-cyber-neonGreen/20 text-cyber-neonGreen hover:bg-cyber-neonGreen/30 disabled:opacity-50 border border-cyber-neonGreen/40 py-1.5 px-3 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1"
            >
              <Plus size={14} />
              Add Custom
            </button>
          </div>
        </div>

        {/* DISPOSITION SECTION */}
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-4">
          <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Encounter Outcome / Disposition</label>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[
              { val: "released", label: "Released / Rested" },
              { val: "observation", label: "Tent Observation" },
              { val: "transport", label: "ER Evacuation" },
              { val: "ama", label: "AMA Refusal" },
              { val: "deceased", label: "Deceased" },
            ].map((d) => (
              <button
                key={d.val}
                type="button"
                onClick={() => setDisposition(d.val as any)}
                className={`py-2 text-xs font-bold border rounded-lg transition-all ${
                  disposition === d.val
                    ? "bg-cyber-neonBlue/20 border-cyber-neonBlue text-white shadow-neonBlue"
                    : "bg-zinc-900/50 border-zinc-800 text-zinc-400 hover:border-zinc-700"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>

          {/* CONDITIONAL DISPOSITION SUBFORMS */}
          {disposition === "transport" && (
            <div className="border border-zinc-800 rounded-xl p-4 bg-zinc-950 space-y-4 mt-3 animate-fade-in">
              <h4 className="text-xs font-extrabold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle size={14} />
                Emergency Evacuation Hospital Selection
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Transport Transporting Unit</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Med-Rover 1 / AMR Ambulance #3"
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonBlue"
                    value={transportUnit}
                    onChange={(e) => setTransportUnit(e.target.value)}
                  />
                </div>
              </div>

              {hospitals ? (
                <HospitalSelector
                  hospitals={hospitals}
                  selectedHospital={transportHospital}
                  onSelect={setTransportHospital}
                />
              ) : (
                <p className="text-xs text-zinc-500 italic">Loading regional hospitals list...</p>
              )}
            </div>
          )}

          {disposition === "ama" && (
            <div className="mt-3 animate-fade-in">
              <AMAForm
                amaCapacityAssessment={amaCapacityNote}
                onAssessmentChange={setAmaCapacityNote}
                checkboxes={amaCheckboxes}
                onCheckboxChange={(key, val) => {
                  setAmaCheckboxes(prev => ({ ...prev, [key]: val }));
                }}
              />
            </div>
          )}
        </div>

        {/* CLINICAL NOTES */}
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-3">
          <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wide">
            Clinical Notes & Differential Remarks
          </label>
          <textarea
            rows={4}
            placeholder="Document general clinical narrative details..."
            className="w-full px-3 py-2 bg-zinc-900/50 border border-zinc-800 rounded-lg text-xs text-zinc-300 outline-none focus:border-cyber-neonPurple min-h-[100px]"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* SUBMIT */}
        <div className="flex justify-end gap-3 border-t border-zinc-900 pt-5">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-5 py-2.5 border border-zinc-800 hover:bg-zinc-900 text-zinc-400 rounded-lg text-xs font-bold uppercase tracking-wider transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createEncounterMutation.isPending || createPatientMutation.isPending}
            className="bg-cyber-neonPurple text-white hover:bg-cyber-neonPurple/90 px-6 py-2.5 border border-cyber-neonPurple/50 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-neonPurple font-black hover:scale-105"
          >
            {createEncounterMutation.isPending || createPatientMutation.isPending ? "Saving log..." : "Save Encounter"}
          </button>
        </div>
      </form>
    </div>
  );
}
