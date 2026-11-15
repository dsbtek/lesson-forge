"use client";

import React, { useMemo, useState } from "react";
import type { LessonSummary, UserProfile } from "@/lib/api";
import { BookOpenIcon, ClockIcon, SparklesIcon } from "./Icons";

interface Props {
  open: boolean;
  onClose: () => void;
  lessons: LessonSummary[];
  loadingLessons: boolean;
  activeLessonId: string | null;
  user: UserProfile | null;
  onNewLesson: () => void;
  onSelectLesson: (lessonId: string) => void;
  onOpenAuth: () => void;
  onSignOut: () => void;
}

export default function Sidebar({
  open,
  onClose,
  lessons,
  loadingLessons,
  activeLessonId,
  user,
  onNewLesson,
  onSelectLesson,
  onOpenAuth,
  onSignOut,
}: Props) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return lessons;
    return lessons.filter(
      (l) =>
        (l.title || "").toLowerCase().includes(q) ||
        (l.subject || "").toLowerCase().includes(q) ||
        (l.grade || "").toLowerCase().includes(q),
    );
  }, [lessons, query]);

  const content = (
    <aside className="flex h-full w-72 flex-col border-r border-slate-200 bg-white">
      {/* Brand */}
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3.5">
        <div
          onClick={() => {
            onNewLesson();
            onClose();
          }}
          className="flex items-center gap-2.5 cursor-pointer select-none"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-forge-700 to-forge-500 text-white shadow-sm shadow-forge-500/25">
            <SparklesIcon className="h-4 w-4" />
          </div>
          <div>
            <span className="font-extrabold tracking-tight text-slate-900 text-base">
              Lesson<span className="text-forge-600">Forge</span>
            </span>
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Educator Studio
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 lg:hidden"
          aria-label="Close sidebar"
        >
          ✕
        </button>
      </div>

      {/* Primary CTA */}
      <div className="p-3">
        <button
          type="button"
          onClick={() => {
            onNewLesson();
            onClose();
          }}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-forge-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-forge-700"
        >
          <SparklesIcon className="h-4 w-4" />
          + New Lesson Plan
        </button>
      </div>

      {/* Search & Lessons List */}
      <div className="flex-1 overflow-hidden flex flex-col px-3">
        <div className="mb-2">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter lessons by topic, grade…"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-forge-500 focus:bg-white focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-between px-1 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          <span>My Lessons</span>
          <span>{lessons.length}</span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 pb-4">
          {!user ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4 text-center">
              <BookOpenIcon className="mx-auto h-6 w-6 text-slate-400" />
              <p className="mt-2 text-xs text-slate-600">
                Sign in to access your saved lesson library.
              </p>
              <button
                type="button"
                onClick={onOpenAuth}
                className="mt-2.5 text-xs font-semibold text-forge-600 hover:underline"
              >
                Sign In / Register →
              </button>
            </div>
          ) : loadingLessons ? (
            <p className="px-2 py-4 text-xs text-slate-400 italic">Loading lessons…</p>
          ) : filtered.length === 0 ? (
            <p className="px-2 py-4 text-xs text-slate-400 italic">
              {lessons.length === 0 ? "No lessons created yet." : "No matching lessons."}
            </p>
          ) : (
            filtered.map((lesson) => {
              const active = lesson.id === activeLessonId;
              return (
                <button
                  key={lesson.id}
                  type="button"
                  onClick={() => {
                    onSelectLesson(lesson.id);
                    onClose();
                  }}
                  className={`w-full rounded-xl border p-3 text-left transition ${
                    active
                      ? "border-forge-300 bg-forge-50/70 shadow-2xs"
                      : "border-transparent hover:border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  <div className="line-clamp-2 text-xs font-semibold text-slate-900">
                    {lesson.title || "Untitled Lesson"}
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-500">
                    {lesson.grade && (
                      <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium text-slate-700">
                        Gr {lesson.grade}
                      </span>
                    )}
                    {lesson.subject && (
                      <span className="rounded bg-amber-50 px-1.5 py-0.5 font-medium text-amber-800">
                        {lesson.subject}
                      </span>
                    )}
                    {lesson.duration_minutes && (
                      <span className="inline-flex items-center gap-0.5">
                        <ClockIcon className="h-2.5 w-2.5" />
                        {lesson.duration_minutes}m
                      </span>
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Teacher Profile Footer */}
      <div className="border-t border-slate-200 bg-slate-50/70 p-3">
        {user ? (
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-xs font-bold text-slate-900">
                {user.full_name || "Teacher"}
              </p>
              <p className="truncate text-[11px] text-slate-500">{user.email}</p>
            </div>
            <button
              type="button"
              onClick={onSignOut}
              className="shrink-0 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:bg-slate-100"
            >
              Sign Out
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={onOpenAuth}
            className="w-full rounded-xl border border-slate-300 bg-white py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50"
          >
            Teacher Sign In / Register
          </button>
        )}
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop persistent sidebar */}
      <div className="hidden lg:block lg:shrink-0 no-print">{content}</div>

      {/* Mobile slide-over */}
      {open && (
        <div className="fixed inset-0 z-40 flex lg:hidden no-print">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
            onClick={onClose}
          />
          <div className="relative z-10 h-full">{content}</div>
        </div>
      )}
    </>
  );
}
