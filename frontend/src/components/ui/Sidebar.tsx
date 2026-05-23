"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Activity, ClipboardList, Users, ClipboardPlus, 
  Sparkles, FlaskConical, Package, Settings, X, Share2,
  GraduationCap
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Event } from "@/lib/types";

const SHARE_TEXT = "Event Med AI — clinical decision support and whiteboard for festival medicine. Try it:";

async function handleShare() {
  const currentUrl = typeof window !== "undefined" ? window.location.origin : "";
  const payload = { title: "Event Med AI", text: SHARE_TEXT, url: currentUrl };
  if (typeof navigator !== "undefined" && "share" in navigator) {
    try {
      await navigator.share(payload);
      return;
    } catch {
      // Fall through
    }
  }
  if (typeof navigator !== "undefined" && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(`${SHARE_TEXT}\n${currentUrl}`);
      alert("Share link copied to clipboard!");
    } catch {
      window.prompt("Copy this link:", currentUrl);
    }
  } else {
    window.prompt("Copy this link:", currentUrl);
  }
}

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const path = usePathname();
  const { data: event } = useQuery({ 
    queryKey: ["event-info"], 
    queryFn: () => apiFetch<Event>("/setup/event-info") 
  });

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden" 
          onClick={onClose}
        />
      )}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-zinc-950 text-white flex flex-col border-r border-zinc-900 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0
        ${isOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="px-5 py-6 border-b border-zinc-900 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="bg-cyber-neonPurple/20 p-2 rounded-lg shrink-0 border border-cyber-neonPurple/50 shadow-neonPurple">
              <Activity className="text-cyber-neonPurple" size={20} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-zinc-500 leading-none mb-1">Event Med AI</p>
              <p className="font-bold text-sm leading-tight truncate w-32">{event?.name ?? "Griztronics 2026"}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 -mr-2 text-zinc-400 hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 py-4 space-y-6 overflow-y-auto">
          <div>
            <p className="px-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2">AI & Clinical Tools</p>
            {[
              { href: "/chat", label: "Ask AI Assistant", icon: Sparkles },
              { href: "/reagent", label: "Reagent Log", icon: FlaskConical },
              { href: "/training", label: "AI Staff Training", icon: GraduationCap },
            ].map(({ href, label, icon: Icon }) => {
              const active = path.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 px-5 py-3 text-sm font-medium transition-colors ${
                    active
                      ? "bg-zinc-900 text-cyber-neonPurple border-l-2 border-cyber-neonPurple"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                  }`}
                  onClick={() => onClose()}
                >
                  <Icon size={18} className={active ? "text-cyber-neonPurple" : ""} />
                  {label}
                </Link>
              );
            })}
          </div>

          <div>
            <p className="px-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2">Operations</p>
            {[
              { href: "/board", label: "Triage Board", icon: ClipboardList },
              { href: "/", label: "Dashboard", icon: Activity },
              { href: "/patients", label: "Patients", icon: Users },
              { href: "/encounter", label: "New Encounter", icon: ClipboardPlus },
            ].map(({ href, label, icon: Icon }) => {
              const active = href === "/" ? path === "/" : path.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 px-5 py-3 text-sm font-medium transition-colors ${
                    active
                      ? "bg-zinc-900 text-cyber-neonBlue border-l-2 border-cyber-neonBlue"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                  }`}
                  onClick={() => onClose()}
                >
                  <Icon size={18} />
                  {label}
                </Link>
              );
            })}
          </div>

          <div>
            <p className="px-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2">Resources</p>
            {[
              { href: "/supplies", label: "Supplies", icon: Package },
            ].map(({ href, label, icon: Icon }) => {
              const active = path.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 px-5 py-3 text-sm font-medium transition-colors ${
                    active
                      ? "bg-zinc-900 text-cyber-neonGreen border-l-2 border-cyber-neonGreen"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                  }`}
                  onClick={() => onClose()}
                >
                  <Icon size={18} />
                  {label}
                </Link>
              );
            })}
          </div>

          <div>
            <p className="px-5 text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-2">System</p>
            {[
              { href: "/settings", label: "Settings", icon: Settings },
            ].map(({ href, label, icon: Icon }) => {
              const active = path.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 px-5 py-3 text-sm font-medium transition-colors ${
                    active
                      ? "bg-zinc-900 text-white border-l-2 border-white"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                  }`}
                  onClick={() => onClose()}
                >
                  <Icon size={18} />
                  {label}
                </Link>
              );
            })}
            <button
              onClick={handleShare}
              className="w-full flex items-center gap-3 px-5 py-3 text-sm font-medium text-zinc-400 hover:bg-zinc-900 hover:text-white transition-colors text-left"
            >
              <Share2 size={18} />
              Share App
            </button>
          </div>
        </nav>

        <div className="px-5 py-4 border-t border-zinc-900 bg-zinc-950">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-2.5 h-2.5 rounded-full bg-cyber-neonGreen animate-pulse"></div>
            <div>
              <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest leading-none mb-1">Triage Network</p>
              <p className="text-xs font-bold text-zinc-300">Med-Tent Online</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
