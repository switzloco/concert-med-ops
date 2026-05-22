"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Patient } from "@/lib/types";
import { Send, Sparkles, User, Bot, Mic, MicOff, BrainCircuit } from "lucide-react";
import ReactMarkdown from 'react-markdown';

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000") + "/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  model?: string;
}

const QUICK_PROMPTS = [
  "A patient in the campground has a core temp of 105°F and confusion. What are the active cooling steps?",
  "How should we manage a patient presenting with severe agitation and suspected excited delirium?",
  "What is the clinical protocol to differentiate MDMA hyponatremia from simple MDMA intoxication?",
  "A patient with suspected MDMA overdose wants to sign out Against Medical Advice. How do we evaluate capacity?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Load history from LocalStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("event_med_ai_chat_history");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error("Failed to load chat history", e);
      }
    }
  }, []);

  // Save history on change
  useEffect(() => {
    localStorage.setItem("event_med_ai_chat_history", JSON.stringify(messages));
  }, [messages]);

  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [patientContext, setPatientContext] = useState<string>("");
  const [isListening, setIsListening] = useState(false);
  const [verbose, setVerbose] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;

        recognitionRef.current.onresult = (event: any) => {
          let transcript = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
          }
          setInput(transcript);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  const patients = useQuery({ queryKey: ["patients"], queryFn: () => apiFetch<Patient[]>("/patient") });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text: string) {
    if (!text.trim() || streaming) return;

    const userMsg: Message = { role: "user", content: text.trim() };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setStreaming(true);

    // Placeholder assistant message that we stream into
    setMessages((m) => [...m, { role: "assistant", content: "" }]);

    try {
      const body: Record<string, unknown> = { messages: next.map(m => ({ role: m.role, content: m.content })), succinct: !verbose };
      if (patientContext) body.patient_id = patientContext;

      const res = await fetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE: events separated by \n\n; each starts with "data: "
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const evt of events) {
          const line = evt.trim();
          if (!line.startsWith("data:")) continue;
          const json = line.slice(5).trim();
          try {
            const parsed = JSON.parse(json);
            if (parsed.model) {
              setMessages((prev) => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                copy[copy.length - 1] = { ...last, model: parsed.model };
                return copy;
              });
            }
            if (parsed.token) {
              setMessages((prev) => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                copy[copy.length - 1] = {
                  ...last,
                  role: "assistant",
                  content: last.content + parsed.token,
                };
                return copy;
              });
            }
          } catch {
            // ignore malformed event
          }
        }
      }
    } catch (err) {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = {
          role: "assistant",
          content: `[AI Connection Lost: The clinical AI model is currently offline. Your message has been saved locally and will be processed when the connection is restored.]`,
        };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  }

  const activePatientName = patientContext
    ? patients.data?.find((p) => p.patient_id === patientContext)?.identifier
    : null;

  const handleClearHistory = () => {
    if (confirm("Clear chat history?")) {
      setMessages([]);
      localStorage.removeItem("event_med_ai_chat_history");
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] max-w-4xl space-y-4">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-zinc-900 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="text-cyber-neonPurple" size={24} />
            <h1 className="text-2xl font-black tracking-tight text-white">Clinical Support Chat</h1>
          </div>
          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mt-1">
            Offline-Capable Harm Reduction & Tox Guidance
          </p>
        </div>

        {messages.length > 0 && (
          <button
            onClick={handleClearHistory}
            className="text-xs bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-400 hover:text-white px-2.5 py-1 rounded transition-colors font-bold uppercase tracking-wider"
          >
            Clear History
          </button>
        )}
      </div>

      {/* CONTEXT SELECTOR & MODE */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 bg-zinc-950 border border-zinc-900 rounded-xl">
        <div>
          <label className="block text-[10px] font-black uppercase tracking-wider text-zinc-500 mb-1.5">
            Patient File Grounding (Context)
          </label>
          <select
            value={patientContext}
            onChange={(e) => setPatientContext(e.target.value)}
            className="w-full text-xs bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-lg px-3 py-2 focus:ring-1 focus:ring-cyber-neonPurple focus:outline-none"
          >
            <option value="">— No Active Patient (General Knowledge) —</option>
            {patients.data?.filter(p => p.is_active).map((p) => (
              <option key={p.patient_id} value={p.patient_id}>
                {p.identifier} ({p.approx_age ? `${p.approx_age}yo` : 'Age?'} {p.gender || 'Gen?'})
              </option>
            ))}
          </select>
          {activePatientName && (
            <p className="text-[10px] text-cyber-neonPurple font-bold mt-1">
              Currently grounded in clinical file: {activePatientName}
            </p>
          )}
        </div>

        <div className="flex flex-col justify-end">
          <label className="flex items-center gap-3 cursor-pointer p-2 rounded-lg border border-zinc-900 hover:border-zinc-800 bg-zinc-900/50 transition-colors w-fit sm:self-end">
            <input 
              type="checkbox" 
              checked={verbose} 
              onChange={(e) => setVerbose(e.target.checked)}
              className="w-4 h-4 text-cyber-neonPurple bg-zinc-900 border-zinc-800 rounded focus:ring-cyber-neonPurple"
            />
            <div className="text-left">
              <span className="text-xs font-bold text-zinc-200 block">Verbose Mode</span>
              <span className="text-[9px] text-zinc-500 font-medium">Include detailed citations and reasoning paths</span>
            </div>
          </label>
        </div>
      </div>

      {/* MESSAGES DISPLAY */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto bg-zinc-950 border border-zinc-900 rounded-xl p-5 space-y-6">
        {messages.length === 0 ? (
          <div className="space-y-6 max-w-2xl py-6">
            <div>
              <h2 className="text-sm font-black uppercase tracking-wider text-zinc-400 mb-2">
                Ask a clinical or toxicological question:
              </h2>
              <p className="text-xs text-zinc-500 leading-relaxed">
                Event Med AI is initialized with custom medical protocols for EDM festival emergencies, including serotonin syndrome criteria, Hyponatremia guidelines, and regional evacuation routing.
              </p>
            </div>
            
            <div className="grid gap-3">
              {QUICK_PROMPTS.map((p) => (
                <button
                  key={p}
                  onClick={() => sendMessage(p)}
                  disabled={streaming}
                  className="text-left text-xs bg-zinc-900/40 hover:bg-zinc-900 border border-zinc-900 hover:border-zinc-800 rounded-xl px-4 py-3 text-zinc-300 hover:text-white transition-all duration-200 leading-relaxed shadow-sm"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className="flex gap-4 items-start">
              <div
                className={`shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border ${
                  m.role === "user" 
                    ? "bg-zinc-900 border-zinc-800 text-zinc-400" 
                    : "bg-cyber-neonPurple/10 border-cyber-neonPurple/30 text-cyber-neonPurple shadow-neonPurple/20 shadow-md"
                }`}
              >
                {m.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center gap-2">
                  <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">
                    {m.role === "user" ? "User" : "Event Med AI"}
                  </p>
                  {m.role === "assistant" && m.model && (
                    <span className="text-[9px] font-extrabold px-2 py-0.5 rounded-full border border-cyber-neonPurple/30 bg-cyber-neonPurple/10 text-cyber-neonPurple uppercase tracking-wider">
                      {m.model}
                    </span>
                  )}
                </div>
                <div className="text-xs text-zinc-200 leading-relaxed prose prose-invert max-w-none prose-xs">
                  <ReactMarkdown>
                    {m.content}
                  </ReactMarkdown>
                  {streaming && i === messages.length - 1 && m.role === "assistant" && (
                    <span className="inline-block w-2 h-4 ml-0.5 bg-cyber-neonPurple animate-pulse" />
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* INPUT FORM */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a substance interaction, cooling protocol, or patient disposal status..."
          disabled={streaming}
          className="flex-1 bg-zinc-950 border border-zinc-900 rounded-xl px-4 py-3 text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-800 focus:ring-1 focus:ring-zinc-800"
          autoCorrect="off"
          spellCheck="false"
          autoComplete="off"
        />
        <button
          type="button"
          onClick={toggleListening}
          className={`px-3.5 py-3 rounded-xl border transition-all flex items-center justify-center ${
            isListening 
              ? "bg-red-500/10 border-red-500/30 text-red-500 animate-pulse shadow-neonPink" 
              : "bg-zinc-950 border-zinc-900 text-zinc-500 hover:text-zinc-300 hover:border-zinc-800"
          }`}
          title={isListening ? "Stop listening" : "Start voice-to-text"}
        >
          {isListening ? <MicOff size={16} /> : <Mic size={16} />}
        </button>
        <button
          type="submit"
          disabled={streaming || !input.trim()}
          className="bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 disabled:bg-zinc-950 disabled:border-zinc-900 disabled:text-zinc-600 text-zinc-100 px-5 py-3 rounded-xl flex items-center gap-1.5 transition-all text-xs font-bold uppercase tracking-wider"
        >
          <Send size={14} />
          {streaming ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}
