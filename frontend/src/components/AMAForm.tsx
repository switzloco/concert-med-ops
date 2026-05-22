"use client";

import React from "react";
import { AlertOctagon, CheckSquare, Square } from "lucide-react";

interface AMAFormProps {
  amaCapacityAssessment: string;
  onAssessmentChange: (val: string) => void;
  checkboxes: {
    oriented: boolean;
    noGrossImpairment: boolean;
    understandsRisks: boolean;
    noSelfHarm: boolean;
    noPsychosis: boolean;
  };
  onCheckboxChange: (key: string, val: boolean) => void;
}

export function AMAForm({
  amaCapacityAssessment,
  onAssessmentChange,
  checkboxes,
  onCheckboxChange,
}: AMAFormProps) {
  const toggleCheckbox = (key: string) => {
    onCheckboxChange(key, !checkboxes[key as keyof typeof checkboxes]);
  };

  const allChecked = Object.values(checkboxes).every((v) => v);

  return (
    <div className="bg-red-950/20 border border-red-900/50 p-5 rounded-xl space-y-4 shadow-xl">
      <div className="flex items-center gap-2 text-red-400">
        <AlertOctagon size={20} className="animate-pulse" />
        <h3 className="font-bold text-sm uppercase tracking-wider">Against Medical Advice (AMA) Refusal of Care</h3>
      </div>
      <p className="text-xs text-zinc-400 leading-relaxed">
        <strong>IMPORTANT CYA PROTOCOL:</strong> Patients refusing care when presenting with moderate-to-severe symptoms MUST have their decision-making capacity explicitly assessed. If a patient does NOT have capacity (due to drugs, head trauma, or altered mental status), you cannot legally discharge them AMA.
      </p>

      <div className="space-y-2.5">
        <p className="text-xs font-bold text-zinc-300 uppercase tracking-widest">Capacity Assessment Checklist</p>
        
        {[
          { key: "oriented", label: "Patient is Alert & Oriented to Person, Place, Time, and Situation (A&O x 4)" },
          { key: "noGrossImpairment", label: "No gross impairment from substances (slurred speech, severe ataxia, inability to focus)" },
          { key: "understandsRisks", label: "Patient verbalizes understanding of their clinical condition and risks of refusal (e.g. death, organ failure)" },
          { key: "noSelfHarm", label: "Patient denies suicidal or homicidal intent, and shows no self-harm ideation" },
          { key: "noPsychosis", label: "Patient has no visible hallucinations, severe paranoia, or excited delirium indicators" },
        ].map((item) => (
          <div
            key={item.key}
            onClick={() => toggleCheckbox(item.key)}
            className="flex items-start gap-3 cursor-pointer select-none group"
          >
            {checkboxes[item.key as keyof typeof checkboxes] ? (
              <CheckSquare className="text-red-400 mt-0.5 shrink-0" size={16} />
            ) : (
              <Square className="text-zinc-600 group-hover:text-zinc-400 mt-0.5 shrink-0" size={16} />
            )}
            <span className={`text-xs ${checkboxes[item.key as keyof typeof checkboxes] ? "text-zinc-300 font-medium" : "text-zinc-500"}`}>
              {item.label}
            </span>
          </div>
        ))}
      </div>

      <div className="flex flex-col">
        <label className="text-xs font-semibold text-zinc-400 mb-1.5 uppercase tracking-wide">
          Clinical Capacity Note / Details of Refusal
        </label>
        <textarea
          rows={3}
          placeholder="Describe how patient demonstrated capacity (e.g., 'Patient states they know they took MDMA and their temp was 101F. They refuse IV fluids and state they will sit in the shade. They repeat that they understand the risk of heat stroke...')"
          className="w-full px-3 py-2 bg-zinc-900/50 border border-zinc-800 rounded-lg text-xs text-zinc-300 outline-none focus:border-red-500 min-h-[80px]"
          value={amaCapacityAssessment}
          onChange={(e) => onAssessmentChange(e.target.value)}
        />
      </div>

      {!allChecked && (
        <div className="p-3 bg-red-950/40 border border-red-800/20 rounded-lg text-[11px] text-red-300">
          <strong>WARNING:</strong> One or more capacity checkboxes are unchecked. Clinical documentation must demonstrate why the patient possesses decision-making capacity, or active efforts must be taken to detain/treat under medical hold if they present an immediate danger to self.
        </div>
      )}
    </div>
  );
}
