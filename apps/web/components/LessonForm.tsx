"use client";

import { useState } from "react";
import {
  generateLesson,
  login,
  register,
  type GenerateResponse,
  type LessonRequest,
} from "@/lib/api";

const FIELD =
  "w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500";
const LABEL = "block text-sm font-medium text-gray-700 mb-1";

export default function LessonForm() {
  // Demo auth (Phase 1). A real sign-in / session UI is Phase 4.
  const [email, setEmail] = useState("teacher@example.com");
  const [password, setPassword] = useState("changeme-please");

  const [grade, setGrade] = useState("5");
  const [subject, setSubject] = useState("Science");
  const [topic, setTopic] = useState("Earth Systems");
  const [duration, setDuration] = useState(60);
  const [standards, setStandards] = useState("NGSS 5-ESS2-1");
  const [strategy, setStrategy] = useState("Inquiry-based learning");
  const [profiles, setProfiles] = useState("ELL, Gifted");
  const [assessmentType, setAssessmentType] = useState("Formative + Exit Ticket");

  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const csv = (s: string) =>
    s.split(",").map((x) => x.trim()).filter(Boolean);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      // Demo convenience: register (ignored if the account exists) then log in.
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
      setResult(await generateLesson(token, req));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <fieldset className="rounded-lg border border-gray-200 p-4">
        <legend className="px-2 text-sm font-semibold text-gray-500">
          Demo account
        </legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className={LABEL}>Email</label>
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
      </fieldset>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className={LABEL}>Grade</label>
          <input className={FIELD} value={grade} onChange={(e) => setGrade(e.target.value)} required />
        </div>
        <div>
          <label className={LABEL}>Subject</label>
          <input className={FIELD} value={subject} onChange={(e) => setSubject(e.target.value)} required />
        </div>
        <div className="sm:col-span-2">
          <label className={LABEL}>Topic</label>
          <input className={FIELD} value={topic} onChange={(e) => setTopic(e.target.value)} required />
        </div>
        <div>
          <label className={LABEL}>Duration (minutes)</label>
          <input
            className={FIELD}
            type="number"
            min={1}
            max={600}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            required
          />
        </div>
        <div>
          <label className={LABEL}>Assessment type</label>
          <input className={FIELD} value={assessmentType} onChange={(e) => setAssessmentType(e.target.value)} />
        </div>
        <div>
          <label className={LABEL}>Standards (comma-separated)</label>
          <input className={FIELD} value={standards} onChange={(e) => setStandards(e.target.value)} />
        </div>
        <div>
          <label className={LABEL}>Learner profiles (comma-separated)</label>
          <input className={FIELD} value={profiles} onChange={(e) => setProfiles(e.target.value)} />
        </div>
        <div className="sm:col-span-2">
          <label className={LABEL}>Instructional strategy</label>
          <input className={FIELD} value={strategy} onChange={(e) => setStrategy(e.target.value)} />
        </div>
      </div>

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-md bg-forge-600 px-4 py-2.5 font-medium text-white transition hover:bg-forge-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? "Submitting…" : "Generate lesson plan"}
      </button>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="rounded-md border border-green-200 bg-green-50 p-4 text-sm">
          <p className="font-medium text-green-800">Generation queued.</p>
          <dl className="mt-2 space-y-1 font-mono text-xs text-gray-700">
            <div>
              <dt className="inline text-gray-500">generation_id: </dt>
              <dd className="inline">{result.generation_id}</dd>
            </div>
            <div>
              <dt className="inline text-gray-500">lesson_id: </dt>
              <dd className="inline">{result.lesson_id}</dd>
            </div>
            <div>
              <dt className="inline text-gray-500">status: </dt>
              <dd className="inline">{result.status}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs text-gray-500">
            Live progress streaming (SSE) and the lesson editor are Phase 4. Track
            events at{" "}
            <code className="rounded bg-white px-1">
              GET /api/v1/generations/{result.generation_id}/events
            </code>
            .
          </p>
        </div>
      )}
    </form>
  );
}
