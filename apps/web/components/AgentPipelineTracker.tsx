"use client";

import React, { useEffect, useState } from "react";
import {
  getGenerationStatus,
  getLessonVersions,
  streamGenerationEvents,
  type GenerationStatus,
  type LessonVersion,
  type StreamEvent,
} from "@/lib/api";
import { CheckCircleIcon, SparklesIcon, RefreshIcon } from "./Icons";

interface Props {
  token: string;
  generationId: string;
  lessonId: string;
  onCompleted: (lesson: LessonVersion) => void;
  onError: (err: string) => void;
}

interface PipelineStep {
  id: string;
  name: string;
  role: string;
  description: string;
}

const STEPS: PipelineStep[] = [
  {
    id: "researcher",
    name: "Curriculum Researcher",
    role: "Hybrid RAG",
    description: "Aligns state standards and retrieves curriculum evidence",
  },
  {
    id: "designer",
    name: "Lesson Designer",
    role: "Core Architecture",
    description: "Architects pedagogical flow, timing, and learning activities",
  },
  {
    id: "differentiation",
    name: "Differentiation & Assessment",
    role: "Inclusion & Rubrics",
    description: "Generates ELL/IEP/Gifted accommodations and criteria",
  },
  {
    id: "critic",
    name: "Critic & Validator",
    role: "Quality Gate",
    description: "Audits pedagogical alignment and triggers repair loops",
  },
  {
    id: "finalizer",
    name: "Lesson Finalizer",
    role: "Artifact Synthesis",
    description: "Synthesizes canonical lesson version and outputs metadata",
  },
];

export default function AgentPipelineTracker({
  token,
  generationId,
  lessonId,
  onCompleted,
  onError,
}: Props) {
  const [activeAgent, setActiveAgent] = useState<string>("researcher");
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [progress, setProgress] = useState<number>(15);
  const [logs, setLogs] = useState<string[]>([]);
  const [revisions, setRevisions] = useState<number>(0);
  const [isFinishing, setIsFinishing] = useState(false);

  const appendLog = (msg: string) => {
    setLogs((prev) => [msg, ...prev.slice(0, 15)]);
  };

  const fetchAndComplete = async () => {
    if (isFinishing) return;
    setIsFinishing(true);
    try {
      const versions = await getLessonVersions(token, lessonId);
      if (versions.length > 0) {
        onCompleted(versions[0]);
      } else {
        // Retry shortly if DB transaction is committing
        setTimeout(async () => {
          const retried = await getLessonVersions(token, lessonId);
          if (retried.length > 0) {
            onCompleted(retried[0]);
          } else {
            onError("Lesson generated, but could not load version content.");
          }
        }, 1500);
      }
    } catch (err: unknown) {
      onError(err instanceof Error ? err.message : String(err));
    }
  };

  useEffect(() => {
    let unmounted = false;
    appendLog(`Generation started (ID: ${generationId.slice(0, 8)}…)`);

    // Fallback poller to ensure completion even if SSE stream drops
    const pollInterval = setInterval(async () => {
      if (unmounted) return;
      try {
        const st: GenerationStatus = await getGenerationStatus(token, generationId);
        if (st.revision) setRevisions(st.revision);
        if (st.status === "completed") {
          clearInterval(pollInterval);
          setProgress(100);
          fetchAndComplete();
        } else if (st.status === "failed") {
          clearInterval(pollInterval);
          onError(st.error || "Generation reported failure.");
        }
      } catch {
        // Non-fatal poll error
      }
    }, 4000);

    // Primary SSE Event Stream
    const cleanupSSE = streamGenerationEvents(
      token,
      generationId,
      (ev: StreamEvent) => {
        if (unmounted) return;

        const timestamp = new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });

        if (ev.agent) {
          setActiveAgent(ev.agent);
        }

        if (ev.progress !== null && ev.progress !== undefined) {
          setProgress(ev.progress);
        }

        switch (ev.event) {
          case "agent.started":
            appendLog(`[${timestamp}] 🤖 ${ev.agent || "Agent"} started work`);
            break;
          case "agent.completed":
            if (ev.agent) {
              setCompletedSteps((prev) => new Set([...prev, ev.agent!]));
            }
            appendLog(`[${timestamp}] ✓ ${ev.agent || "Agent"} completed`);
            break;
          case "retrieval.started":
            appendLog(`[${timestamp}] 📚 Querying hybrid RAG standards knowledge base…`);
            break;
          case "retrieval.completed":
            appendLog(`[${timestamp}] 🎯 RAG retrieval returned grounded curriculum evidence`);
            break;
          case "repair.started":
            setRevisions((r) => r + 1);
            appendLog(`[${timestamp}] 🔄 Quality reflection: initiating revision loop…`);
            break;
          case "generation.completed":
            setProgress(100);
            appendLog(`[${timestamp}] ✨ LessonForge completed generation successfully!`);
            fetchAndComplete();
            break;
          case "generation.failed":
            onError(ev.message || "Generation pipeline failed.");
            break;
          default:
            if (ev.message) {
              appendLog(`[${timestamp}] ${ev.message}`);
            }
        }
      },
      (err: Error) => {
        appendLog(`⚠️ Stream sync note: ${err.message}. Polling active.`);
      }
    );

    return () => {
      unmounted = true;
      clearInterval(pollInterval);
      cleanupSSE();
    };
  }, [generationId, lessonId, token]);

  const stepStatus = (stepId: string, index: number) => {
    if (completedSteps.has(stepId)) return "done";
    if (activeAgent.toLowerCase().includes(stepId)) return "active";
    const activeIndex = STEPS.findIndex((s) =>
      activeAgent.toLowerCase().includes(s.id)
    );
    if (activeIndex > index) return "done";
    return "pending";
  };

  return (
    <div className="space-y-8 py-2">
      {/* Header & Progress Bar */}
      <div className="rounded-2xl border border-forge-100 bg-gradient-to-br from-forge-50/80 via-white to-amber-50/30 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-forge-600 text-white shadow-md shadow-forge-500/20">
              <SparklesIcon className="h-6 w-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Forging Your Lesson Plan
              </h2>
              <p className="text-sm text-slate-600">
                Multi-agent LangGraph workflow running autonomous pedagogical agents.
              </p>
            </div>
          </div>
          {revisions > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
              <RefreshIcon className="h-3.5 w-3.5 animate-spin" />
              Revision Loop #{revisions}
            </span>
          )}
        </div>

        {/* Global Progress Bar */}
        <div className="mt-6 space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-700">
            <span>Synthesis Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200/80">
            <div
              className="h-full rounded-full bg-gradient-to-r from-forge-600 to-amber-500 transition-all duration-500 ease-out"
              style={{ width: `${Math.max(progress, 8)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Agents Stepper Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-5">
        {STEPS.map((step, idx) => {
          const status = stepStatus(step.id, idx);
          return (
            <div
              key={step.id}
              className={`relative flex flex-col justify-between rounded-xl border p-4 transition-all duration-300 ${
                status === "active"
                  ? "border-forge-500 bg-white shadow-md ring-2 ring-forge-500/20"
                  : status === "done"
                  ? "border-emerald-200 bg-emerald-50/40 text-slate-800"
                  : "border-slate-200 bg-slate-50/60 opacity-60"
              }`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Step {idx + 1}
                  </span>
                  {status === "done" ? (
                    <CheckCircleIcon className="h-4 w-4 text-emerald-600" />
                  ) : status === "active" ? (
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-forge-400 opacity-75" />
                      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-forge-600" />
                    </span>
                  ) : null}
                </div>

                <h3 className="mt-2 text-sm font-semibold text-slate-900 leading-snug">
                  {step.name}
                </h3>
                <span className="mt-1 inline-block rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
                  {step.role}
                </span>
                <p className="mt-2 text-xs text-slate-500 leading-relaxed">
                  {step.description}
                </p>
              </div>

              {status === "active" && (
                <div className="mt-3 text-[11px] font-semibold text-forge-600 animate-pulse">
                  ● Working…
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Live Stream Activity Log */}
      <div className="rounded-xl border border-slate-200 bg-slate-900 p-4 text-slate-200 shadow-inner">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Live Agent Event Log
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Redis Stream SSE
          </span>
        </div>
        <div className="mt-3 h-32 overflow-y-auto space-y-1.5 font-mono text-xs text-slate-300">
          {logs.length === 0 ? (
            <p className="text-slate-500 italic">Connecting to event stream…</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="leading-relaxed">
                {log}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
