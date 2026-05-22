"use client";

import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { ReagentLog, Patient, StaffMember } from "@/lib/types";
import { CYADisclaimer } from "@/components/CYADisclaimer";
import { 
  FlaskConical, Sparkles, Check, FileText, UploadCloud, 
  HelpCircle, ChevronRight, AlertTriangle, Info, Camera, RefreshCw 
} from "lucide-react";

const REAGENT_CHARTS = {
  marquis: [
    { substance: "MDMA / MDA / MDE", color: "Purple to Black", hex: "bg-purple-950 border-purple-500 shadow-[0_0_10px_#a855f7]" },
    { substance: "Amphetamine / Methamphetamine", color: "Orange to Brown", hex: "bg-orange-850 border-orange-500 shadow-[0_0_10px_#f97316]" },
    { substance: "2C-B", color: "Yellow to Green", hex: "bg-yellow-850 border-green-500 shadow-[0_0_10px_#22c55e]" },
    { substance: "Heroin / Morphine", color: "Purple / Pink", hex: "bg-fuchsia-900 border-fuchsia-400" },
    { substance: "DXM", color: "Yellow to Orange", hex: "bg-yellow-600 border-amber-500" },
    { substance: "Cocaine / Ketamine", color: "No reaction", hex: "bg-zinc-800 border-zinc-700" }
  ],
  mecke: [
    { substance: "MDMA / MDA / MDE", color: "Green to Blue/Black", hex: "bg-blue-950 border-emerald-500 shadow-[0_0_10px_#06b6d4]" },
    { substance: "Heroin / Morphine", color: "Deep Green to Blue", hex: "bg-emerald-950 border-blue-500" },
    { substance: "DXM", color: "Yellow", hex: "bg-yellow-400 border-yellow-300 text-black" },
    { substance: "Ketamine / Cocaine", color: "No reaction", hex: "bg-zinc-800 border-zinc-700" }
  ]
};

export default function ReagentPage() {
  const queryClient = useQueryClient();
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
  const [activeTab, setActiveTab] = useState<"log" | "history">("log");

  // Form state
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [selectedStaffId, setSelectedStaffId] = useState("");
  const [sampleDescription, setSampleDescription] = useState("");
  const [testType, setTestType] = useState<"fent_strip" | "marquis" | "mecke" | "mandelin" | "folin" | "ehhrlich" | "ftir">("marquis");
  const [testResult, setTestResult] = useState<"positive" | "negative" | "color_change_verified" | "inconclusive">("color_change_verified");
  const [colorObserved, setColorObserved] = useState("");
  const [predictedSubstance, setPredictedSubstance] = useState("");

  // AI photo identification state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [isIdentifying, setIsIdentifying] = useState(false);
  const [aiAnalysisResult, setAiAnalysisResult] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load disclaimer state from localStorage
  useEffect(() => {
    const accepted = localStorage.getItem("event_med_disclaimer_accepted") === "true";
    if (accepted) setDisclaimerAccepted(true);
  }, []);

  const handleAgreeDisclaimer = () => {
    localStorage.setItem("event_med_disclaimer_accepted", "true");
    setDisclaimerAccepted(true);
  };

  // Queries
  const { data: logs, isLoading: logsLoading } = useQuery<ReagentLog[]>({
    queryKey: ["reagent-logs"],
    queryFn: () => apiFetch<ReagentLog[]>("/reagent"),
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
  const createLogMutation = useMutation({
    mutationFn: (newLog: any) =>
      apiFetch("/reagent", {
        method: "POST",
        body: JSON.stringify(newLog),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reagent-logs"] });
      // Reset form
      setSampleDescription("");
      setColorObserved("");
      setPredictedSubstance("");
      setSelectedPatientId("");
      setActiveTab("history");
    },
    onError: (err: any) => {
      alert(`Error logging result: ${err.message}`);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPhotoPreview(URL.createObjectURL(file));
      setAiAnalysisResult(null);
    }
  };

  const handleRunPhotoAnalysis = async () => {
    if (!selectedFile) return;
    setIsIdentifying(true);
    setAiAnalysisResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("test_type", testType);
    formData.append("disclaimer_agreed", "true");

    try {
      const getApiBase = () => {
        if (process.env.NEXT_PUBLIC_API_BASE) return process.env.NEXT_PUBLIC_API_BASE;
        if (typeof window !== "undefined") {
          if ("__TAURI_INTERNALS__" in window) return "http://127.0.0.1:8000";
          return window.location.origin;
        }
        return "http://localhost:8000";
      };
      const response = await fetch(`${getApiBase()}/api/reagent/identify-photo`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Analysis request failed");
      }

      const res = await response.json();
      setAiAnalysisResult(res.analysis);
      
      // Auto fill predicted substance if the response looks clear
      if (res.analysis && res.status === "success") {
        // Simple search for probable matches
        if (res.analysis.toLowerCase().includes("mdma")) {
          setPredictedSubstance("MDMA / Ecstasy");
          setColorObserved("Purple/Black");
          setTestResult("color_change_verified");
        } else if (res.analysis.toLowerCase().includes("fentanyl positive")) {
          setTestResult("positive");
          setPredictedSubstance("Fentanyl Contaminated");
        }
      }
    } catch (err: any) {
      console.error(err);
      alert("Error identifying photo. Falling back to manual entry.");
    } finally {
      setIsIdentifying(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStaffId) {
      alert("Please select the tester Staff Member.");
      return;
    }
    if (!sampleDescription.trim()) {
      alert("Please provide a description of the sample.");
      return;
    }

    const activeEventId = patients?.[0]?.event_id || "griztronics-2026";

    createLogMutation.mutate({
      event_id: activeEventId,
      patient_id: selectedPatientId || undefined,
      sample_description: sampleDescription.trim(),
      test_type: testType,
      test_result: testResult,
      color_observed: colorObserved.trim() || undefined,
      predicted_substance: predictedSubstance.trim() || undefined,
      disclaimer_agreed: true,
      tester_staff_id: selectedStaffId,
    });
  };

  const activePatients = patients?.filter((p) => p.is_active) ?? [];
  const onShiftStaff = staff?.filter((s) => s.is_on_shift) ?? [];

  return (
    <div className="space-y-6 max-w-5xl pb-16">
      {/* CYA DISCLAIMER SHIELD */}
      {!disclaimerAccepted && (
        <CYADisclaimer onAgree={handleAgreeDisclaimer} />
      )}

      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-5">
        <div className="flex items-center gap-3">
          <div className="bg-cyber-neonPink/15 p-2 rounded-lg border border-cyber-neonPink/40 text-cyber-neonPink shadow-neonPink">
            <FlaskConical size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide uppercase">Presumptive Reagent Logs</h1>
            <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest mt-1">
              presumptive drug checking • Marquis/Mecke visualizer • Fent strip logs
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab("log")}
            className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
              activeTab === "log"
                ? "bg-zinc-800 text-white"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Log New Test
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
              activeTab === "history"
                ? "bg-zinc-800 text-white"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            History ({logs?.length ?? 0})
          </button>
        </div>
      </div>

      {activeTab === "log" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LOGGING FORM */}
          <div className="lg:col-span-2 space-y-6">
            <form onSubmit={handleSubmit} className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 shadow-xl space-y-4">
              <h2 className="text-xs font-black uppercase tracking-widest text-zinc-200 border-b border-zinc-900 pb-3 flex items-center gap-2">
                <FileText size={14} className="text-cyber-neonPink" />
                Presumptive Test Details
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* STAFF TESTER */}
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Tested By (Staff)</label>
                  <select
                    required
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                    value={selectedStaffId}
                    onChange={(e) => setSelectedStaffId(e.target.value)}
                  >
                    <option value="">-- Select Tester --</option>
                    {onShiftStaff.map((s) => (
                      <option key={s.staff_id} value={s.staff_id}>
                        {s.name} ({s.call_sign})
                      </option>
                    ))}
                  </select>
                </div>

                {/* ASSOCIATED PATIENT */}
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Patient Wristband (Optional)</label>
                  <select
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                  >
                    <option value="">-- Anonymous / Not Linked --</option>
                    {activePatients.map((p) => (
                      <option key={p.patient_id} value={p.patient_id}>
                        {p.identifier}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* SAMPLE DESCRIPTION */}
              <div className="flex flex-col">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Sample Description</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Pink Tesla tablet, white crystalline powder..."
                  className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                  value={sampleDescription}
                  onChange={(e) => setSampleDescription(e.target.value)}
                />
              </div>

              {/* TEST TYPE & RESULT */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Testing Method</label>
                  <select
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                    value={testType}
                    onChange={(e) => setTestType(e.target.value as any)}
                  >
                    <option value="fent_strip">Fentanyl Test Strip</option>
                    <option value="marquis">Marquis Reagent</option>
                    <option value="mecke">Mecke Reagent</option>
                    <option value="mandelin">Mandelin Reagent</option>
                    <option value="folin">Folin Reagent</option>
                    <option value="ehhrlich">Ehrlich Reagent</option>
                    <option value="ftir">FTIR Spectrometry</option>
                  </select>
                </div>

                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Outcome Result</label>
                  <select
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                    value={testResult}
                    onChange={(e) => setTestResult(e.target.value as any)}
                  >
                    <option value="color_change_verified">Reaction Color Change Verified</option>
                    <option value="negative">Negative (e.g. Fent Strip Neg)</option>
                    <option value="positive">Positive (e.g. Fent Strip Pos)</option>
                    <option value="inconclusive">Inconclusive / No Change</option>
                  </select>
                </div>
              </div>

              {/* REACTION COLORS & PREDICTED SUBSTANCE */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Reaction Color Observed</label>
                  <input
                    type="text"
                    placeholder="e.g. Quick purple to black, Orange-brown..."
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                    value={colorObserved}
                    onChange={(e) => setColorObserved(e.target.value)}
                  />
                </div>

                <div className="flex flex-col">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1.5">Presumptive Predicted Substance</label>
                  <input
                    type="text"
                    placeholder="e.g. MDMA, Amphetamine, Ketamine..."
                    className="px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-900/50 text-zinc-300 text-xs outline-none focus:border-cyber-neonPink"
                    value={predictedSubstance}
                    onChange={(e) => setPredictedSubstance(e.target.value)}
                  />
                </div>
              </div>

              {/* SUBMIT */}
              <div className="flex items-center justify-between pt-4 border-t border-zinc-900">
                <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                  <Info size={12} className="text-zinc-600" />
                  <span>Checking disclaimer_agreed=True on save</span>
                </div>
                <button
                  type="submit"
                  disabled={createLogMutation.isPending}
                  className="bg-cyber-neonPink text-white hover:bg-cyber-neonPink/90 px-6 py-2 border border-cyber-neonPink/50 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-neonPink hover:scale-105"
                >
                  {createLogMutation.isPending ? "Saving..." : "Log Reagent Result"}
                </button>
              </div>
            </form>

            {/* QUICK IMAGE ASSISTANT */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-6 shadow-xl space-y-4">
              <h2 className="text-xs font-black uppercase tracking-widest text-zinc-200 flex items-center gap-2">
                <Camera size={14} className="text-cyber-neonPink" />
                AI Visual Drug Checking Assistant
              </h2>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Take or upload a clear photo of the test strip or reagent reaction spot. The offline-ready multimodal engine will analyze the image, estimate the reaction colors, and compare it with the reference charts.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 items-start">
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="flex flex-col items-center justify-center border border-dashed border-zinc-800 hover:border-cyber-neonPink hover:bg-zinc-900/30 text-zinc-500 hover:text-zinc-300 w-32 h-32 rounded-xl transition-all"
                    >
                      <UploadCloud size={24} />
                      <span className="text-[10px] mt-2 font-bold uppercase">Add Photo</span>
                    </button>
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      accept="image/*"
                      className="hidden"
                    />

                    {photoPreview && (
                      <div className="relative w-32 h-32 rounded-xl border border-zinc-800 overflow-hidden">
                        <img src={photoPreview} alt="reagent spot" className="w-full h-full object-cover" />
                      </div>
                    )}
                  </div>

                  {selectedFile && (
                    <button
                      type="button"
                      onClick={handleRunPhotoAnalysis}
                      disabled={isIdentifying}
                      className="w-full bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-1.5"
                    >
                      {isIdentifying ? (
                        <>
                          <RefreshCw size={12} className="animate-spin" />
                          Analyzing reaction...
                        </>
                      ) : (
                        <>
                          <Sparkles size={12} className="text-cyber-neonPink" />
                          Run Photo Analysis
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* AI OUTPUT */}
                {aiAnalysisResult ? (
                  <div className="flex-1 bg-zinc-900/20 border border-zinc-900 rounded-xl p-4 space-y-2 text-xs">
                    <div className="flex items-center gap-1.5 text-cyber-neonPink mb-1 font-bold">
                      <Sparkles size={12} />
                      <span>Gemini Evaluation Report</span>
                    </div>
                    <div className="text-zinc-300 leading-relaxed max-h-[140px] overflow-y-auto whitespace-pre-line font-mono text-[10px]">
                      {aiAnalysisResult}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 border border-dashed border-zinc-900 rounded-xl p-6 h-32 flex items-center justify-center text-xs text-zinc-600 text-center">
                    Upload spot reaction photo to see AI predictions
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* VISUAL CHARTS PANELS */}
          <div className="space-y-6">
            {/* MARQUIS CHART */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-3">
              <div className="flex items-center gap-2">
                <FlaskConical size={14} className="text-purple-400" />
                <h3 className="text-[11px] font-black uppercase tracking-wider text-zinc-300">Marquis Color Reference</h3>
              </div>
              <div className="space-y-2">
                {REAGENT_CHARTS.marquis.map((m) => (
                  <div key={m.substance} className="flex items-center justify-between text-xs p-1.5 rounded bg-zinc-900/40 border border-zinc-900/60">
                    <span className="font-semibold text-zinc-400 text-[10px]">{m.substance}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-zinc-500 font-mono">{m.color}</span>
                      <div className={`w-3.5 h-3.5 rounded border border-zinc-800 ${m.hex}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* MECKE CHART */}
            <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl space-y-3">
              <div className="flex items-center gap-2">
                <FlaskConical size={14} className="text-emerald-400" />
                <h3 className="text-[11px] font-black uppercase tracking-wider text-zinc-300">Mecke Color Reference</h3>
              </div>
              <div className="space-y-2">
                {REAGENT_CHARTS.mecke.map((m) => (
                  <div key={m.substance} className="flex items-center justify-between text-xs p-1.5 rounded bg-zinc-900/40 border border-zinc-900/60">
                    <span className="font-semibold text-zinc-400 text-[10px]">{m.substance}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-zinc-500 font-mono">{m.color}</span>
                      <div className={`w-3.5 h-3.5 rounded border border-zinc-800 ${m.hex}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* SAFETY NOTICE */}
            <div className="bg-red-950/10 border border-red-900/40 p-4 rounded-xl space-y-2 text-xs">
              <div className="flex items-center gap-1.5 text-red-400 font-bold uppercase tracking-wider">
                <AlertTriangle size={14} />
                <span>Fentanyl Dilution Rule</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Dilute 10mg of powder in 10mL of water before testing. MDMA/Stimulants require higher dilution (10mg in 50mL) to prevent false positives.
              </p>
            </div>
          </div>
        </div>
      ) : (
        /* HISTORY TAB */
        <div className="bg-zinc-950 border border-zinc-900 rounded-xl p-5 shadow-xl">
          <h2 className="text-xs font-black uppercase tracking-widest text-zinc-200 border-b border-zinc-900 pb-3 mb-4">
            Harm Reduction Log History
          </h2>

          {logsLoading ? (
            <p className="text-xs text-zinc-500 italic">Retrieving reagent database records...</p>
          ) : logs && logs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-zinc-900 text-left text-xs">
                <thead>
                  <tr className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest bg-zinc-950">
                    <th className="px-4 py-2.5">Date</th>
                    <th className="px-4 py-2.5">Sample</th>
                    <th className="px-4 py-2.5">Method</th>
                    <th className="px-4 py-2.5">Result</th>
                    <th className="px-4 py-2.5">Color Observed</th>
                    <th className="px-4 py-2.5">Presumptive Predicted</th>
                    <th className="px-4 py-2.5">Tester</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900">
                  {logs.map((log) => {
                    const isFentPos = log.test_type === "fent_strip" && log.test_result === "positive";
                    return (
                      <tr key={log.log_id} className={`hover:bg-zinc-900/30 transition-all ${isFentPos ? "bg-red-500/5 text-red-200" : ""}`}>
                        <td className="px-4 py-3 text-zinc-500 font-mono">
                          {new Date(log.created_at || "").toLocaleDateString()} {new Date(log.created_at || "").toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </td>
                        <td className="px-4 py-3 font-semibold text-zinc-200">{log.sample_description}</td>
                        <td className="px-4 py-3 text-zinc-400 uppercase font-bold text-[10px]">{log.test_type.replace("_", " ")}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            log.test_result === "positive"
                              ? "bg-red-500/20 text-red-400 border border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.2)] animate-pulse"
                              : log.test_result === "negative"
                              ? "bg-green-500/20 text-green-400 border border-green-500/30"
                              : "bg-zinc-800 text-zinc-400"
                          }`}>
                            {log.test_result.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-semibold text-zinc-300">{log.color_observed ?? "—"}</td>
                        <td className="px-4 py-3 font-extrabold text-cyber-neonPink">{log.predicted_substance ?? "—"}</td>
                        <td className="px-4 py-3 text-zinc-500">
                          {staff?.find((s) => s.staff_id === log.tester_staff_id)?.call_sign ?? log.tester_staff_id}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-40 border border-dashed border-zinc-900 rounded-lg flex items-center justify-center text-zinc-500">
              No reagent spot testing logs recorded yet
            </div>
          )}
        </div>
      )}
    </div>
  );
}
