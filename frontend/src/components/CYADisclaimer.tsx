"use client";

import React, { useState } from "react";
import { ShieldAlert, Check } from "lucide-react";

interface CYADisclaimerProps {
  onAgree: () => void;
}

export function CYADisclaimer({ onAgree }: CYADisclaimerProps) {
  const [agreedCheck1, setAgreedCheck1] = useState(false);
  const [agreedCheck2, setAgreedCheck2] = useState(false);
  const [agreedCheck3, setAgreedCheck3] = useState(false);

  const canSubmit = agreedCheck1 && agreedCheck2 && agreedCheck3;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-zinc-950 border border-zinc-900 rounded-2xl shadow-2xl p-6 overflow-hidden">
        <div className="flex items-center gap-3 text-cyber-neonPink mb-4 border-b border-zinc-900 pb-3">
          <ShieldAlert size={24} className="animate-pulse shrink-0" />
          <h2 className="font-extrabold text-base uppercase tracking-wider">LIABILITY DISCLAIMER & HARM REDUCTION TERMS</h2>
        </div>

        <div className="space-y-4 text-xs text-zinc-400 leading-relaxed max-h-[300px] overflow-y-auto pr-1">
          <p>
            <strong>Presumptive Drug Checking (Reagents & Test Strips)</strong> is an information-only harm reduction service. It does not provide absolute confirmation of sample safety, purity, or contents.
          </p>
          <p>
            Read and verify each statement below to proceed with reagent log access:
          </p>

          <div className="space-y-3 pt-2">
            <div 
              onClick={() => setAgreedCheck1(!agreedCheck1)}
              className="flex items-start gap-3 cursor-pointer select-none group p-2.5 rounded-lg border border-zinc-900 bg-zinc-900/20 hover:border-zinc-800"
            >
              <input
                type="checkbox"
                checked={agreedCheck1}
                onChange={() => {}}
                className="mt-0.5 shrink-0 accent-cyber-neonPink cursor-pointer"
              />
              <span className="text-[11px] leading-snug text-zinc-300">
                I understand reagent color changes are <strong>presumptive only</strong>. They cannot detect all cutting agents, and color matches can be subjective.
              </span>
            </div>

            <div 
              onClick={() => setAgreedCheck2(!agreedCheck2)}
              className="flex items-start gap-3 cursor-pointer select-none group p-2.5 rounded-lg border border-zinc-900 bg-zinc-900/20 hover:border-zinc-800"
            >
              <input
                type="checkbox"
                checked={agreedCheck2}
                onChange={() => {}}
                className="mt-0.5 shrink-0 accent-cyber-neonPink cursor-pointer"
              />
              <span className="text-[11px] leading-snug text-zinc-300">
                I understand fentanyl test strips have a <strong>limit of detection</strong> and can yield false negatives (especially for novel analogues) or false positives if diluted incorrectly.
              </span>
            </div>

            <div 
              onClick={() => setAgreedCheck3(!agreedCheck3)}
              className="flex items-start gap-3 cursor-pointer select-none group p-2.5 rounded-lg border border-zinc-900 bg-zinc-900/20 hover:border-zinc-800"
            >
              <input
                type="checkbox"
                checked={agreedCheck3}
                onChange={() => {}}
                className="mt-0.5 shrink-0 accent-cyber-neonPink cursor-pointer"
              />
              <span className="text-[11px] leading-snug text-zinc-300">
                I agree that logging drug checking results does <strong>NOT endorse consumption</strong>. Event Med AI and staff are not liable for any poisoning, overdose, or adverse event following substance use.
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-zinc-900">
          <button
            onClick={onAgree}
            disabled={!canSubmit}
            className="flex items-center justify-center gap-1.5 w-full bg-cyber-neonPink text-white hover:bg-cyber-neonPink/90 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:border-transparent border border-cyber-neonPink/50 py-2.5 px-4 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-300 shadow-neonPink disabled:shadow-none"
          >
            <Check size={16} />
            <span>I Agree, Unlock Log</span>
          </button>
        </div>
      </div>
    </div>
  );
}
