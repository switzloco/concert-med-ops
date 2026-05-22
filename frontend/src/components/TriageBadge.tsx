"use client";

const TRIAGE_COLORS: Record<string, string> = {
  green: "bg-green-500/10 text-green-400 border border-green-500/30 shadow-[0_0_8px_rgba(34,197,94,0.2)]",
  yellow: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 shadow-[0_0_8px_rgba(234,179,8,0.2)]",
  red: "bg-red-500/10 text-red-400 border border-red-500/30 shadow-[0_0_8px_rgba(239,68,68,0.2)] animate-pulse",
  black: "bg-zinc-800 text-zinc-400 border border-zinc-700 shadow-none",
};

const TRIAGE_LABELS: Record<string, string> = {
  green: "Green - Minor",
  yellow: "Yellow - Delayed",
  red: "Red - Immediate",
  black: "Black - Deceased",
};

export function TriageBadge({
  level,
  short = false,
}: {
  level: string;
  short?: boolean;
}) {
  const normalizedLevel = level?.toLowerCase() || "green";
  const colorClass = TRIAGE_COLORS[normalizedLevel] ?? TRIAGE_COLORS.green;
  const label = short ? (normalizedLevel.toUpperCase()) : (TRIAGE_LABELS[normalizedLevel] ?? level);

  return (
    <span
      className={`inline-block px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wide transition-all duration-300 ${colorClass}`}
    >
      {label}
    </span>
  );
}
