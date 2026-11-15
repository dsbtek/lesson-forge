"use client";

import React, { useState } from "react";
import {
  generateLesson,
  getMe,
  login,
  register,
  type GenerateResponse,
  type LessonRequest,
  type UserProfile,
} from "@/lib/api";
import { BookOpenIcon, ClockIcon, SparklesIcon, UsersIcon } from "./Icons";

interface Props {
  token?: string | null;
  onAutoAuth?: (token: string, user: UserProfile) => void;
  onStarted: (token: string, response: GenerateResponse) => void;
}

interface Preset {
  title: string;
  grade: string;
  subject: string;
  topic: string;
  duration: number;
  standards: string;
  strategy: string;
  profiles: string;
  assessmentType: string;
}

const PRESETS: Preset[] = [
  {
    title: "5th Grade Science",
    grade: "5",
    subject: "Science",
    topic: "Earth Systems & Water Cycle",
    duration: 60,
    standards: "NGSS 5-ESS2-1",
    strategy: "Inquiry-based 5E Model",
    profiles: "ELL, Gifted",
    assessmentType: "Formative + Exit Ticket",
  },
  {
    title: "8th Grade Math",
    grade: "8",
    subject: "Mathematics",
    topic: "Linear Equations & Slope",
    duration: 45,
    standards: "CCSS.MATH.8.EE.B.5",
    strategy: "Worked Examples & Peer Problem Solving",
    profiles: "IEP (Visual Learner), General",
    assessmentType: "Diagnostic Warm-up + Mid-check Quiz",
  },
  {
    title: "10th Grade English",
    grade: "10",
    subject: "English Language Arts",
    topic: "Rhetorical Devices & Persuasive Writing",
    duration: 60,
    standards: "CCSS.ELA-LITERACY.RI.9-10.6",
    strategy: "Socratic Seminar & Textual Annotation",
    profiles: "ELL (Level 3), Advanced",
    assessmentType: "Peer Feedback Rubric",
  },
];

const FIELD =
  "w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm text-slate-800 placeholder-slate-400 transition focus:border-forge-500 focus:outline-none focus:ring-2 focus:ring-forge-500/20";
const LABEL = "block text-xs font-semibold text-slate-700 mb-1.5 uppercase tracking-wider";

export default function LessonForm({ token, onAutoAuth, onStarted }: Props) {
  const [grade, setGrade] = useState("5");
  const [subject, setSubject] = useState("Science");
  const [topic, setTopic] = useState("Earth Systems & Water Cycle");
  const [duration, setDuration] = useState(60);
  const [standards, setStandards] = useState("NGSS 5-ESS2-1");
  const [strategy, setStrategy] = useState("Inquiry-based 5E Model");
  const [profiles, setProfiles] = useState("ELL, Gifted");
  const [assessmentType, setAssessmentType] = useState("Formative + Exit Ticket");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const applyPreset = (p: Preset) => {
    setGrade(p.grade);
    setSubject(p.subject);
    setTopic(p.topic);
    setDuration(p.duration);
    setStandards(p.standards);
    setStrategy(p.strategy);
    setProfiles(p.profiles);
    setAssessmentType(p.assessmentType);
  };

  const csv = (s: string) =>
    s.split(",").map((x) => x.trim()).filter(Boolean);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      let activeToken = token;
      if (!activeToken) {
        const demoEmail = "teacher@example.com";
        const demoPass = "changeme-please";
        await register(demoEmail, demoPass, "Demo Educator");
        activeToken = await login(demoEmail, demoPass);
        const profile = await getMe(activeToken);
        onAutoAuth?.(activeToken, profile);
      }

      const req: LessonRequest = {
        grade,
        subject,
        topic,
        duration_minutes: Number(duration),
        standards: csv(standards),
        instructional_strategy: strategy || null,
        learner_profiles: csv(profiles),
        assessment_type: assessmentType || null,
      };

      const resp = await generateLesson(activeToken, req);
      onStarted(activeToken, resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  };

  const standardsList = csv(standards);
  const profilesList = csv(profiles);

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
      {/* Left: Studio Form */}
      <form onSubmit={onSubmit} className="lg:col-span-8 space-y-6">
        {/* Quick Template Selector */}
        <div className="rounded-xl border border-forge-100 bg-forge-50/60 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-forge-800 flex items-center gap-1.5">
              <SparklesIcon className="h-4 w-4 text-forge-600" />
              Quick Curriculum Presets
            </span>
            <span className="text-[11px] text-slate-500">1-click prefill</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p, i) => (
              <button
                key={i}
                type="button"
                onClick={() => applyPreset(p)}
                className="rounded-lg border border-forge-200 bg-white px-3 py-1.5 text-xs font-medium text-forge-700 shadow-2xs transition hover:bg-forge-100/70 hover:border-forge-300"
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        {/* Primary Details */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
            1. Core Curriculum Scope
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={LABEL}>Grade Level</label>
              <input
                className={FIELD}
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                placeholder="e.g. 5, 8th Grade, High School"
                required
              />
            </div>
            <div>
              <label className={LABEL}>Subject / Discipline</label>
              <input
                className={FIELD}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Science, Mathematics, World History"
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className={LABEL}>Lesson Topic & Focus</label>
              <input
                className={FIELD}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. Earth Systems, Photosynthesis, Quadratic Equations"
                required
              />
            </div>
            <div>
              <label className={LABEL}>Duration (Minutes)</label>
              <input
                className={FIELD}
                type="number"
                min={15}
                max={360}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                required
              />
            </div>
            <div>
              <label className={LABEL}>Target Standards (Codes)</label>
              <input
                className={FIELD}
                value={standards}
                onChange={(e) => setStandards(e.target.value)}
                placeholder="e.g. NGSS 5-ESS2-1, CCSS.MATH.8.EE.B.5"
              />
            </div>
          </div>
        </div>

        {/* Pedagogy & Inclusion */}
        <div className="space-y-4">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
            2. Pedagogy & Inclusion Strategy
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className={LABEL}>Instructional Strategy</label>
              <input
                className={FIELD}
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                placeholder="e.g. Inquiry-based 5E Model, Socratic, Project-based"
              />
            </div>
            <div>
              <label className={LABEL}>Assessment Measures</label>
              <input
                className={FIELD}
                value={assessmentType}
                onChange={(e) => setAssessmentType(e.target.value)}
                placeholder="e.g. Formative + Exit Ticket, Rubric"
              />
            </div>
            <div className="sm:col-span-2">
              <label className={LABEL}>Learner Profiles & Accommodations (comma-separated)</label>
              <input
                className={FIELD}
                value={profiles}
                onChange={(e) => setProfiles(e.target.value)}
                placeholder="e.g. ELL, IEP, Gifted, Visual Learners"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
            <span className="font-bold">Error: </span>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-forge-600 to-forge-700 py-3.5 px-6 font-semibold text-white shadow-md shadow-forge-500/20 transition hover:from-forge-700 hover:to-forge-800 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
        >
          <SparklesIcon className="h-5 w-5" />
          {busy ? "Queuing LangGraph Pipeline…" : "Launch Lesson Forge Agent"}
        </button>
      </form>

      {/* Right: Live Blueprint Preview */}
      <aside className="lg:col-span-4">
        <div className="sticky top-20 rounded-2xl border border-slate-200 bg-slate-50/70 p-5 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Live Blueprint Preview
            </span>
            <span className="rounded-full bg-forge-100 px-2 py-0.5 text-[10px] font-bold text-forge-700">
              5E Pipeline
            </span>
          </div>

          <div>
            <div className="flex flex-wrap gap-1.5 mb-2">
              <span className="rounded-full bg-forge-50 border border-forge-200 px-2.5 py-0.5 text-[11px] font-semibold text-forge-700">
                Grade {grade || "—"}
              </span>
              <span className="rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-[11px] font-semibold text-amber-800">
                {subject || "Subject"}
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-white border border-slate-200 px-2.5 py-0.5 text-[11px] font-medium text-slate-600">
                <ClockIcon className="h-3 w-3" />
                {duration || 0}m
              </span>
            </div>
            <h4 className="text-base font-bold text-slate-900 leading-snug">
              {topic || "Untitled Lesson Topic"}
            </h4>
            {strategy && (
              <p className="mt-1 text-xs text-slate-600">
                Strategy: <span className="font-medium text-slate-800">{strategy}</span>
              </p>
            )}
          </div>

          <div className="space-y-2 border-t border-slate-200/80 pt-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
              <BookOpenIcon className="h-3.5 w-3.5 text-forge-600" />
              Standards ({standardsList.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {standardsList.length > 0 ? (
                standardsList.map((s, idx) => (
                  <span
                    key={idx}
                    className="rounded bg-white border border-slate-200 px-2 py-0.5 font-mono text-[11px] text-slate-700"
                  >
                    {s}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400 italic">None specified</span>
              )}
            </div>
          </div>

          <div className="space-y-2 border-t border-slate-200/80 pt-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
              <UsersIcon className="h-3.5 w-3.5 text-emerald-600" />
              Learner Accommodations ({profilesList.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {profilesList.length > 0 ? (
                profilesList.map((p, idx) => (
                  <span
                    key={idx}
                    className="rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-[11px] font-medium text-emerald-800"
                  >
                    {p}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400 italic">General classroom</span>
              )}
            </div>
          </div>

          {assessmentType && (
            <div className="border-t border-slate-200/80 pt-3 text-xs text-slate-600">
              <span className="font-semibold text-slate-700">Assessment: </span>
              {assessmentType}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
