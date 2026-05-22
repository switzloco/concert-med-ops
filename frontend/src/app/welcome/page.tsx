"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { fetchSetupStatus, setMode } from "@/lib/setup";
import { isTauri, tauriInvoke } from "@/lib/platform";
import Link from "next/link";
import { Globe, Shield, Activity, Rocket, FolderOpen } from "lucide-react";
import { useState, useEffect } from "react";

export default function WelcomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [serverIsLocal, setServerIsLocal] = useState<boolean | null>(null);
  const [tauri, setTauri] = useState(false);

  useEffect(() => {
    setTauri(isTauri());
    fetchSetupStatus()
      .then(s => setServerIsLocal(s.server_is_local))
      .catch(() => setServerIsLocal(false));
  }, []);

  const handleTryCloud = async () => {
    setLoading("cloud");
    try {
      await apiFetch("/setup/mode", {
        method: "POST",
        body: JSON.stringify({ mode: "cloud" }),
      });
      localStorage.setItem("vessel_ops_onboarded", "true");
      router.push("/");
    } catch (err) {
      console.error(err);
      alert("Cloud mode requires a GOOGLE_API_KEY. Please use 'Get Started' for local setup.");
      setLoading(null);
    }
  };

  // Tauri-only: skip the wizard, set local mode, go straight to the app.
  const handleRunOfflineNow = async () => {
    setLoading("local");
    try {
      await setMode("local");
    } catch (err) {
      console.warn("setMode('local') failed, continuing anyway:", err);
    }
    localStorage.setItem("vessel_ops_onboarded", "true");
    router.push("/");
  };

  const handleOpenLogs = async () => {
    try {
      await tauriInvoke("open_logs_dir");
    } catch (err) {
      console.error("Failed to open logs folder:", err);
      alert("Could not open the logs folder. Look in %APPDATA%\\EventMedAI\\logs\\ manually.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 font-sans">
      <div className="max-w-4xl w-full bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200">
        {/* Hero Section */}
        <div className="relative h-64 w-full">
          <Image
            src="/images/hero-festival.png"
            alt="Festival Medical Operations"
            fill
            className="object-cover"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />
          
          <div className="absolute bottom-6 left-8 flex items-center gap-3 text-white">
            <div className="bg-rose-600 p-2 rounded-xl shadow-lg">
              <Activity size={32} />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Event Med AI</h1>
              <p className="text-rose-100 text-sm md:text-base font-medium">Precision Crisis Response for Mass Gatherings</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-10 text-center">
          <p className="text-slate-600 text-base md:text-lg leading-relaxed mb-10 max-w-2xl mx-auto">
            Your offline-first AI decision support tool for music festivals and mass gatherings. Grounded in 
            <strong> CrowdRx festival medical guidelines</strong>, substance safety protocols, and emergency triage frameworks. 
            Built to coordinate care and save lives.
          </p>

          {tauri ? (
            <div className="flex flex-col items-center gap-4 mb-12">
              <button
                onClick={handleRunOfflineNow}
                disabled={!!loading}
                className="w-full max-w-md flex items-center justify-center gap-3 px-8 py-5 bg-rose-600 hover:bg-rose-700 disabled:opacity-60 text-white rounded-2xl font-bold text-lg shadow-xl shadow-rose-200 transition-all"
              >
                <Rocket size={22} />
                {loading === "local" ? "Launching…" : "Run Offline Now →"}
              </button>
              <button
                onClick={() => router.push("/welcome/setup")}
                disabled={!!loading}
                className="text-sm text-slate-500 hover:text-slate-800 underline underline-offset-4 transition-colors"
              >
                I need to set up Ollama first
              </button>
              <button
                onClick={handleOpenLogs}
                className="mt-2 inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-700 transition-colors"
              >
                <FolderOpen size={12} /> Trouble? Open log folder
              </button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6 mb-12">
              <button
                onClick={handleTryCloud}
                disabled={!!loading}
                className="group p-6 bg-slate-50 border border-slate-200 rounded-2xl hover:border-rose-300 hover:bg-rose-50 transition-all text-left"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-blue-100 text-blue-600 p-2 rounded-lg group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    <Globe size={24} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">Cloud Access</h2>
                </div>
                <p className="text-sm text-slate-500 mb-4 leading-relaxed">
                  Always available with an active internet connection. High-performance cloud
                  processing with persistent storage for your logs and data.
                </p>
                <span className="text-rose-600 text-sm font-semibold flex items-center gap-1">
                  {loading === "cloud" ? "Connecting..." : "Launch Online Mode →"}
                </span>
              </button>

              <button
                onClick={() => {
                  if (serverIsLocal === false) {
                    const proceed = confirm(
                      "You're using the hosted web version.\n\n" +
                      "Running offline in the field requires installing Event Med AI on your own laptop — a one-time ~1 hour setup (mostly downloading the AI model).\n\n" +
                      "The next page shows exactly what to download. Continue?"
                    );
                    if (!proceed) return;
                  }
                  router.push("/welcome/setup");
                }}
                disabled={!!loading}
                className="group p-6 bg-slate-50 border border-slate-200 rounded-2xl hover:border-green-300 hover:bg-green-50 transition-all text-left"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-green-100 text-green-600 p-2 rounded-lg group-hover:bg-green-600 group-hover:text-white transition-colors">
                    <Shield size={24} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">Offline Setup</h2>
                </div>
                <p className="text-sm text-slate-500 mb-4 leading-relaxed">
                  Requires ~1 hour setup (mainly for downloading the 8 GB Gemma 4 model) and installation of Ollama. Run Gemma 4
                  entirely on your hardware for 100% privacy and mission-critical reliability in the field.
                </p>
                <span className="text-green-600 text-sm font-semibold">
                  Begin Local Onboarding →
                </span>
              </button>
            </div>
          )}

          {/* Credits & Info */}
          <div className="border-t border-slate-100 pt-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4 text-left">
              <div className="bg-rose-50 text-rose-600 p-3 rounded-xl border border-rose-100">
                <Activity size={24} />
              </div>
              <p className="text-xs text-slate-400 leading-tight max-w-[200px]">
                Powered by the <span className="font-semibold text-slate-600">CrowdRx Mass Gathering Medical Guidelines</span> and harm reduction databases.
              </p>
            </div>
            <div className="text-xs text-slate-400 text-center md:text-right">
              <p>Built for Griztronics 2026 Operations by</p>
              <p className="font-semibold text-slate-600">CrowdRx Medical Team</p>
            </div>
          </div>
        </div>
      </div>
      <p className="mt-8 text-slate-400 text-sm">
        When using the local setup (via Ollama), Event Med AI runs entirely in your browser and on your local machine.
      </p>
      <div className="mt-4 flex items-center justify-center gap-4 text-xs text-slate-400">
        <Link href="/terms" className="hover:text-rose-600 transition-colors">Terms of Use</Link>
        <span>·</span>
        <Link href="/privacy" className="hover:text-rose-600 transition-colors">Privacy Policy</Link>
      </div>
    </div>
  );
}
