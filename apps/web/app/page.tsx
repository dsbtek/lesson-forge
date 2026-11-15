"use client";

import React, { useCallback, useEffect, useState } from "react";
import AgentPipelineTracker from "@/components/AgentPipelineTracker";
import AuthModal from "@/components/AuthModal";
import HealthBadge from "@/components/HealthBadge";
import { SparklesIcon } from "@/components/Icons";
import LessonForm from "@/components/LessonForm";
import LessonViewer from "@/components/LessonViewer";
import Sidebar from "@/components/Sidebar";
import {
  getLessonVersions,
  getMe,
  listLessons,
  type GenerateResponse,
  type LessonSummary,
  type LessonVersion,
  type UserProfile,
} from "@/lib/api";

const TOKEN_STORAGE_KEY = "lessonforge_token";

export default function Home() {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [loadingLessons, setLoadingLessons] = useState(false);

  const [currentGen, setCurrentGen] = useState<GenerateResponse | null>(null);
  const [activeLesson, setActiveLesson] = useState<LessonVersion | null>(null);
  const [activeVersions, setActiveVersions] = useState<LessonVersion[]>([]);
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshLessons = useCallback(async (token: string) => {
    setLoadingLessons(true);
    try {
      const list = await listLessons(token);
      setLessons(list);
    } catch {
      // Non-fatal
    } finally {
      setLoadingLessons(false);
    }
  }, []);

  // Restore persisted teacher session on mount
  useEffect(() => {
    const saved = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!saved) return;
    getMe(saved)
      .then((profile) => {
        setSessionToken(saved);
        setUser(profile);
        refreshLessons(saved);
      })
      .catch(() => {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      });
  }, [refreshLessons]);

  const handleAuthenticated = (token: string, profile: UserProfile) => {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    setSessionToken(token);
    setUser(profile);
    refreshLessons(token);
  };

  const handleSignOut = () => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setSessionToken(null);
    setUser(null);
    setLessons([]);
    setActiveLesson(null);
    setActiveVersions([]);
    setActiveLessonId(null);
    setCurrentGen(null);
  };

  const handleStarted = (token: string, res: GenerateResponse) => {
    setSessionToken(token);
    setCurrentGen(res);
    setActiveLesson(null);
    setActiveVersions([]);
    setActiveLessonId(res.lesson_id);
    setError(null);
    refreshLessons(token);
  };

  const handleCompleted = async (version: LessonVersion) => {
    setActiveLesson(version);
    setCurrentGen(null);
    setError(null);
    if (sessionToken && activeLessonId) {
      try {
        const all = await getLessonVersions(sessionToken, activeLessonId);
        setActiveVersions(all);
      } catch {
        setActiveVersions([version]);
      }
      refreshLessons(sessionToken);
    }
  };

  const handlePipelineError = (err: string) => {
    setError(err);
    setCurrentGen(null);
  };

  const handleReset = () => {
    setCurrentGen(null);
    setActiveLesson(null);
    setActiveVersions([]);
    setActiveLessonId(null);
    setError(null);
  };

  const loadPastLesson = async (lessonId: string) => {
    if (!sessionToken) return;
    setError(null);
    try {
      const versions = await getLessonVersions(sessionToken, lessonId);
      if (versions.length > 0) {
        setActiveVersions(versions);
        setActiveLesson(versions[0]);
        setActiveLessonId(lessonId);
        setCurrentGen(null);
      } else {
        setError("This lesson has no completed version yet.");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 selection:bg-forge-100 selection:text-forge-900">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        lessons={lessons}
        loadingLessons={loadingLessons}
        activeLessonId={activeLessonId}
        user={user}
        onNewLesson={handleReset}
        onSelectLesson={loadPastLesson}
        onOpenAuth={() => setAuthModalOpen(true)}
        onSignOut={handleSignOut}
      />

      <div className="flex flex-1 flex-col min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur-md no-print">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="rounded-lg border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 lg:hidden"
                aria-label="Open menu"
              >
                ☰
              </button>
              <span className="text-sm font-semibold text-slate-700 hidden sm:inline">
                {activeLesson
                  ? activeLesson.content.title
                  : currentGen
                  ? "Forging Lesson Plan…"
                  : "Lesson Studio"}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <HealthBadge />
              {!user && (
                <button
                  type="button"
                  onClick={() => setAuthModalOpen(true)}
                  className="rounded-lg border border-forge-200 bg-forge-50 px-3 py-1.5 text-xs font-semibold text-forge-700 hover:bg-forge-100"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Main Workspace Canvas */}
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
          {currentGen && sessionToken && (
            <AgentPipelineTracker
              token={sessionToken}
              generationId={currentGen.generation_id}
              lessonId={currentGen.lesson_id}
              onCompleted={handleCompleted}
              onError={handlePipelineError}
            />
          )}

          {activeLesson && (
            <LessonViewer
              version={activeLesson}
              versions={activeVersions}
              lessonId={activeLessonId || undefined}
              token={sessionToken || undefined}
              onSelectVersion={(v) => setActiveLesson(v)}
              onRegenerated={(resp) => {
                setCurrentGen(resp);
                setActiveLesson(null);
              }}
              onLessonUpdated={() => sessionToken && refreshLessons(sessionToken)}
              onReset={handleReset}
            />
          )}

          {!currentGen && !activeLesson && (
            <div className="space-y-8">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 border border-amber-200/80 px-3 py-1 text-xs font-semibold text-amber-800 mb-3">
                  <SparklesIcon className="h-3.5 w-3.5 text-amber-600" />
                  Multi-Agent LangGraph Architecture
                </div>
                <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
                  Design Standards-Aligned Lesson Plans in Seconds
                </h1>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                  LessonForge orchestrates specialized agents for curriculum research,
                  5E pacing design, universal accommodations, and automated quality critique.
                </p>
              </div>

              {error && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                  <p className="font-bold">Generation Error:</p>
                  <p className="mt-1">{error}</p>
                </div>
              )}

              <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
                <LessonForm
                  token={sessionToken}
                  onAutoAuth={handleAuthenticated}
                  onStarted={handleStarted}
                />
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200 py-5 text-center text-xs text-slate-400 no-print">
          LessonForge Studio • API Docs at{" "}
          <a
            className="underline hover:text-slate-600 font-medium"
            href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
            target="_blank"
            rel="noreferrer"
          >
            /docs
          </a>
        </footer>
      </div>

      <AuthModal
        open={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthenticated={handleAuthenticated}
      />
    </div>
  );
}
