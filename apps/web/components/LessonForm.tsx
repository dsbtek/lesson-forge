"use client";

import React, { useState } from "react";
import {
  generateLesson,
  login,
  register,
  type GenerateResponse,
  type LessonRequest,
} from "@/lib/api";
import { SparklesIcon } from "./Icons";

interface Props {
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

export default function LessonForm({ onStarted }: Props) {
  // Demo auth (Phase 1).
  const [email, setEmail] = useState("teacher@example.com");
  const [password, setPassword] = useState("changeme-please");
  const [showAuth, setShowAuth] = useState(false);

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
      await register(email, password);
      const token = await login(email, password);

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

      const resp = await generateLesson(token, req);
      onStarted(token, resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Quick Template Selector */}
      <div className="rounded-xl border border-forge-100 bg-forge-50/50 p-4">
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

      {/* Demo Credentials Accordion */}
      <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-3">
        <button
          type="button"
          onClick={() => setShowAuth(!showAuth)}
          className="flex w-full items-center justify-between text-xs font-semibold text-slate-600 hover:text-slate-900"
        >
          <span>Teacher Session Credentials</span>
          <span className="text-[11px] text-forge-600 underline">
            {showAuth ? "Hide" : "Customize"}
          </span>
        </button>

        {showAuth && (
          <div className="mt-3 grid grid-cols-1 gap-3 pt-3 border-t border-slate-200 sm:grid-cols-2">
            <div>
              <label className={LABEL}>Teacher Email</label>
              <input
                className={FIELD}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className={LABEL}>Password (min 8 chars)</label>
              <input
                className={FIELD}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>
          </div>
        )}
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
  );
}
