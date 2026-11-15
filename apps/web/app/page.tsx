"use client";

import React, { useState, useEffect } from "react";
import HealthBadge from "@/components/HealthBadge";
import LessonForm from "@/components/LessonForm";
import AgentPipelineTracker from "@/components/AgentPipelineTracker";
import LessonViewer from "@/components/LessonViewer";
import {
  listLessons,
  getLessonVersions,
  type GenerateResponse,
  type LessonSummary,
  type LessonVersion,
} from "@/lib/api";
import {
  SparklesIcon,
  BookOpenIcon,
  HistoryIcon,
  ClockIcon,
} from "@/components/Icons";

export default function Home() {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [currentGen, setCurrentGen] = useState<GenerateResponse | null>(null);
  const [activeLesson, setActiveLesson] = useState<LessonVersion | null>(null);
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Recent lessons drawer state
  const [showHistory, setShowHistory] = useState(false);
  const [recentLessons, setRecentLessons] = useState<LessonSummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const handleStarted = (token: string, res: GenerateResponse) => {
    setSessionToken(token);
    setCurrentGen(res);
    setActiveLesson(null);
    setActiveLessonId(res.lesson_id);
    setError(null);
  };

  const handleCompleted = (version: LessonVersion) => {
    setActiveLesson(version);
    setCurrentGen(null);
    setError(null);
  };

  const handlePipelineError = (err: string) => {
    setError(err);
    setCurrentGen(null);
  };

  const handleReset = () => {
    setCurrentGen(null);
    setActiveLesson(null);
    setActiveLessonId(null);
    setError(null);
  };

  const openHistory = async () => {
    setShowHistory(true);
    if (!sessionToken) return;
    setLoadingHistory(true);
    try {
      const list = await listLessons(sessionToken);
      setRecentLessons(list);
    } catch {
      // Non-fatal if no lessons yet or unauthenticated
    } finally {
      setLoadingHistory(false);
    }
  };

  const loadPastLesson = async (lessonId: string) => {
    if (!sessionToken) return;
    try {
      const versions = await getLessonVersions(sessionToken, lessonId);
      if (versions.length > 0) {
        setActiveLesson(versions[0]);
        setActiveLessonId(lessonId);
        setCurrentGen(null);
        setShowHistory(false);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-forge-100 selection:text-forge-900">
      {/* Top Navigation */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur-md no-print">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
          <div
            onClick={handleReset}
            className="flex items-center gap-2.5 cursor-pointer select-none group"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-forge-700 to-forge-500 text-white shadow-sm shadow-forge-500/30 transition group-hover:scale-105">
              <SparklesIcon className="h-5 w-5" />
            </div>
            <div>
              <span className="font-extrabold tracking-tight text-slate-900 text-lg">
                Lesson<span className="text-forge-600">Forge</span>
              </span>
              <span className="hidden sm:inline-block ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                Educator Studio
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {sessionToken && (
              <button
                onClick={openHistory}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50"
              >
                <HistoryIcon className="h-3.5 w-3.5 text-slate-500" />
                History
              </button>
            )}
            <HealthBadge />
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        {/* State 1: Active Generation Pipeline Tracker */}
        {currentGen && sessionToken && (
          <AgentPipelineTracker
            token={sessionToken}
            generationId={currentGen.generation_id}
            lessonId={currentGen.lesson_id}
            onCompleted={handleCompleted}
            onError={handlePipelineError}
          />
        )}

        {/* State 2: Generated Lesson Plan Viewer */}
        {activeLesson && (
          <LessonViewer
            version={activeLesson}
            lessonId={activeLessonId || undefined}
            token={sessionToken || undefined}
            onReset={handleReset}
          />
        )}

        {/* State 3: Lesson Form / Creator */}
        {!currentGen && !activeLesson && (
          <div className="space-y-8">
            <div className="text-center max-w-2xl mx-auto">
              <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 border border-amber-200/80 px-3.5 py-1 text-xs font-semibold text-amber-800 mb-4">
                <SparklesIcon className="h-3.5 w-3.5 text-amber-600" />
                Multi-Agent LangGraph Architecture
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
                Design Grounded, Differentiated Lesson Plans in Seconds
              </h1>
              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                LessonForge coordinates autonomous agents for Curriculum Retrieval (RAG),
                Pedagogical Design, Universal Accommodations, and Validator Quality Gates.
              </p>
            </div>

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                <p className="font-bold">Generation Error:</p>
                <p className="mt-1">{error}</p>
              </div>
            )}

            <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
              <LessonForm onStarted={handleStarted} />
            </div>
          </div>
        )}
      </main>

      {/* History Slide-over Drawer */}
      {showHistory && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs">
          <div className="w-full max-w-md bg-white p-6 shadow-2xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <h3 className="font-bold text-slate-900 text-lg flex items-center gap-2">
                  <HistoryIcon className="h-5 w-5 text-forge-600" />
                  Your Generated Lessons
                </h3>
                <button
                  onClick={() => setShowHistory(false)}
                  className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                >
                  ✕
                </button>
              </div>

              <div className="mt-4 space-y-3 overflow-y-auto max-h-[70vh]">
                {loadingHistory ? (
                  <p className="text-sm text-slate-500 italic">Loading past lessons…</p>
                ) : recentLessons.length === 0 ? (
                  <p className="text-sm text-slate-500 italic">No past lessons recorded yet.</p>
                ) : (
                  recentLessons.map((l) => (
                    <div
                      key={l.id}
                      onClick={() => loadPastLesson(l.id)}
                      className="rounded-xl border border-slate-200 p-4 transition cursor-pointer hover:border-forge-400 hover:bg-forge-50/40"
                    >
                      <h4 className="font-bold text-sm text-slate-900">
                        {l.title || "Untitled Lesson"}
                      </h4>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                        {l.grade && (
                          <span className="rounded bg-slate-100 px-2 py-0.5 font-medium">
                            Grade {l.grade}
                          </span>
                        )}
                        {l.subject && (
                          <span className="rounded bg-amber-50 text-amber-800 px-2 py-0.5 font-medium">
                            {l.subject}
                          </span>
                        )}
                        {l.duration_minutes && (
                          <span className="inline-flex items-center gap-1">
                            <ClockIcon className="h-3 w-3" />
                            {l.duration_minutes}m
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <button
              onClick={() => setShowHistory(false)}
              className="mt-6 w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-100"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-200 py-6 text-center text-xs text-slate-400 no-print">
        <p>
          LessonForge Studio • API Documentation available at{" "}
          <a
            className="underline hover:text-slate-600 font-medium"
            href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            /docs
          </a>
        </p>
      </footer>
    </div>
  );
}
