"use client";

import React, { useState } from "react";
import {
  createExport,
  regenerateSection,
  updateLesson,
  type GenerateResponse,
  type LessonVersion,
} from "@/lib/api";
import {
  ArrowLeftIcon,
  BookOpenIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentDuplicateIcon,
  PrintIcon,
  RefreshIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UsersIcon,
} from "./Icons";

interface Props {
  version: LessonVersion;
  versions?: LessonVersion[];
  lessonId?: string;
  token?: string;
  onSelectVersion?: (v: LessonVersion) => void;
  onRegenerated?: (resp: GenerateResponse) => void;
  onLessonUpdated?: () => void;
  onReset: () => void;
}

export default function LessonViewer({
  version,
  versions = [],
  lessonId,
  token,
  onSelectVersion,
  onRegenerated,
  onLessonUpdated,
  onReset,
}: Props) {
  const [tab, setTab] = useState<"plan" | "objectives" | "diff" | "assessment" | "quality">("plan");
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [regenSectionId, setRegenSectionId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Inline title/metadata edit
  const content = version.content;
  const [editingTitle, setEditingTitle] = useState(false);
  const [draftTitle, setDraftTitle] = useState(content.title || "");
  const [savingTitle, setSavingTitle] = useState(false);

  const copyMarkdown = () => {
    let md = `# ${content.title || "Lesson Plan"}\n\n`;
    md += `**Subject:** ${content.subject} | **Grade:** ${content.grade} | **Duration:** ${content.duration_minutes} mins\n\n`;

    if (content.objectives?.length) {
      md += `## Learning Objectives\n`;
      content.objectives.forEach((obj) => (md += `- ${obj.text}\n`));
      md += `\n`;
    }

    if (content.standards?.length) {
      md += `## Standards Alignment\n`;
      content.standards.forEach((std) => (md += `- **${std.code}**: ${std.description || ""}\n`));
      md += `\n`;
    }

    if (content.sections?.length) {
      md += `## Lesson Plan Timeline\n`;
      content.sections.forEach((sec, idx) => {
        md += `### ${idx + 1}. ${sec.title} (${sec.duration_minutes} min)\n`;
        if (sec.teacher_actions?.length) {
          md += `**Teacher Actions:**\n` + sec.teacher_actions.map((a) => `  - ${a}`).join("\n") + "\n";
        }
        if (sec.student_actions?.length) {
          md += `**Student Actions:**\n` + sec.student_actions.map((a) => `  - ${a}`).join("\n") + "\n";
        }
        if (sec.materials?.length) {
          md += `**Materials:** ${sec.materials.join(", ")}\n`;
        }
        md += `\n`;
      });
    }

    if (content.differentiation) {
      md += `## Differentiation\n`;
      if (content.differentiation.ell?.length) {
        md += `### English Language Learners (ELL)\n` + content.differentiation.ell.map((x) => `- ${x}`).join("\n") + "\n";
      }
      if (content.differentiation.iep?.length) {
        md += `### IEP / Accommodations\n` + content.differentiation.iep.map((x) => `- ${x}`).join("\n") + "\n";
      }
      if (content.differentiation.gifted?.length) {
        md += `### Gifted & Talented\n` + content.differentiation.gifted.map((x) => `- ${x}`).join("\n") + "\n";
      }
      md += `\n`;
    }

    if (content.assessments?.length) {
      md += `## Assessments\n`;
      content.assessments.forEach((ass) => {
        md += `### ${ass.type}\n`;
        if (ass.questions?.length) {
          md += `**Questions/Prompts:**\n` + ass.questions.map((q) => `- ${q}`).join("\n") + "\n";
        }
        if (ass.success_criteria?.length) {
          md += `**Success Criteria:**\n` + ass.success_criteria.map((c) => `- ${c}`).join("\n") + "\n";
        }
      });
    }

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleExport = async (format: "markdown" | "pdf" | "json") => {
    if (!token || !lessonId) {
      copyMarkdown();
      return;
    }
    setExporting(format);
    setActionError(null);
    try {
      const res = await createExport(token, lessonId, format, version.id);
      if (res.storage_url) {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const resp = await fetch(`${apiBase}${res.storage_url}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!resp.ok) throw new Error(`Export download failed (${resp.status})`);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `lesson_${format === "pdf" ? "printable.html" : format === "markdown" ? "plan.md" : "plan.json"}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setExporting(null);
    }
  };

  const handleSaveTitle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !lessonId || !draftTitle.trim()) return;
    setSavingTitle(true);
    setActionError(null);
    try {
      await updateLesson(token, lessonId, { title: draftTitle.trim() });
      content.title = draftTitle.trim();
      setEditingTitle(false);
      onLessonUpdated?.();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingTitle(false);
    }
  };

  const handleRegenerateSection = async (sectionId: string) => {
    if (!token || !lessonId || !onRegenerated) return;
    setRegenSectionId(sectionId);
    setActionError(null);
    try {
      const resp = await regenerateSection(token, lessonId, sectionId);
      onRegenerated(resp);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
      setRegenSectionId(null);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const score = content.review?.score ?? 0;
  const passed = content.review?.review_passed ?? true;

  return (
    <div className="space-y-6">
      {/* Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 no-print border-b border-slate-200 pb-4">
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          New Lesson
        </button>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={copyMarkdown}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50"
          >
            <DocumentDuplicateIcon className="h-4 w-4 text-slate-500" />
            {copied ? "Copied!" : "Copy MD"}
          </button>

          <button
            onClick={() => handleExport("markdown")}
            disabled={exporting !== null}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50 disabled:opacity-50"
          >
            {exporting === "markdown" ? "Exporting…" : "Download .md"}
          </button>

          <button
            onClick={() => handleExport("pdf")}
            disabled={exporting !== null}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50 disabled:opacity-50"
          >
            {exporting === "pdf" ? "Exporting…" : "Download .html"}
          </button>

          <button
            onClick={() => handleExport("json")}
            disabled={exporting !== null}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition hover:bg-slate-50 disabled:opacity-50"
          >
            {exporting === "json" ? "Exporting…" : "Download .json"}
          </button>

          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 rounded-lg bg-forge-600 px-3.5 py-2 text-xs font-semibold text-white shadow-2xs transition hover:bg-forge-700"
          >
            <PrintIcon className="h-4 w-4" />
            Print / PDF
          </button>
        </div>
      </div>

      {actionError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 no-print">
          {actionError}
        </div>
      )}

      {/* Hero Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="rounded-full bg-forge-50 border border-forge-200 px-3 py-1 text-xs font-semibold text-forge-700">
                Grade {content.grade}
              </span>
              <span className="rounded-full bg-amber-50 border border-amber-200 px-3 py-1 text-xs font-semibold text-amber-800">
                {content.subject}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                <ClockIcon className="h-3.5 w-3.5 text-slate-500" />
                {content.duration_minutes} minutes
              </span>

              {/* Version Switcher */}
              {versions.length > 1 && onSelectVersion ? (
                <select
                  aria-label="Lesson version"
                  value={version.id}
                  onChange={(e) => {
                    const found = versions.find((v) => v.id === e.target.value);
                    if (found) onSelectVersion(found);
                  }}
                  className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 focus:border-forge-500 focus:outline-none no-print"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.id}>
                      v{v.version} ({v.status})
                    </option>
                  ))}
                </select>
              ) : (
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-500">
                  v{version.version}
                </span>
              )}
            </div>

            {editingTitle ? (
              <form onSubmit={handleSaveTitle} className="flex items-center gap-2 no-print">
                <input
                  type="text"
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  className="flex-1 rounded-lg border border-forge-400 px-3 py-1.5 text-xl font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-forge-500/20"
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={savingTitle}
                  className="rounded-lg bg-forge-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-forge-700"
                >
                  {savingTitle ? "Saving…" : "Save"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setEditingTitle(false);
                    setDraftTitle(content.title || "");
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </form>
            ) : (
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
                  {content.title || "Curriculum Lesson Plan"}
                </h1>
                {token && lessonId && (
                  <button
                    type="button"
                    onClick={() => {
                      setDraftTitle(content.title || "");
                      setEditingTitle(true);
                    }}
                    className="no-print rounded-md border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                  >
                    Rename
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Quality Audit Meter */}
          <div className="flex items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/80 p-3 sm:p-4 shrink-0">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-xl font-bold text-lg ${
                score >= 0.8
                  ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  : "bg-amber-100 text-amber-800 border border-amber-300"
              }`}
            >
              {Math.round(score * 100)}%
            </div>
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                <ShieldCheckIcon className="h-4 w-4 text-emerald-600" />
                Critic Quality Score
              </div>
              <div className="text-xs text-slate-500">
                {passed ? "Quality Threshold Met" : "Revision Suggested"}
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mt-8 flex border-b border-slate-200 no-print overflow-x-auto space-x-1">
          <button
            onClick={() => setTab("plan")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition ${
              tab === "plan"
                ? "border-forge-600 text-forge-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <ClockIcon className="h-4 w-4" />
            Timeline Pacing ({content.sections?.length || 0})
          </button>
          <button
            onClick={() => setTab("objectives")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition ${
              tab === "objectives"
                ? "border-forge-600 text-forge-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <BookOpenIcon className="h-4 w-4" />
            Objectives & Standards
          </button>
          <button
            onClick={() => setTab("diff")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition ${
              tab === "diff"
                ? "border-forge-600 text-forge-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <UsersIcon className="h-4 w-4" />
            Differentiation Studio
          </button>
          <button
            onClick={() => setTab("assessment")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition ${
              tab === "assessment"
                ? "border-forge-600 text-forge-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <CheckCircleIcon className="h-4 w-4" />
            Assessments
          </button>
          <button
            onClick={() => setTab("quality")}
            className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition ${
              tab === "quality"
                ? "border-forge-600 text-forge-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <ShieldCheckIcon className="h-4 w-4" />
            Critic Audit
          </button>
        </div>
      </div>

      {/* Section 1: Lesson Plan Timeline (always rendered in print) */}
      <div className={`${tab === "plan" ? "block" : "hidden print:block"} space-y-4`}>
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <ClockIcon className="h-5 w-5 text-forge-600" />
          Instructional Timeline & Pacing
        </h2>

        <div className="space-y-4">
          {content.sections && content.sections.length > 0 ? (
            content.sections.map((sec, idx) => (
              <div
                key={sec.id || idx}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-forge-600 text-xs font-bold text-white">
                      {idx + 1}
                    </span>
                    <h3 className="font-bold text-slate-900 text-base">
                      {sec.title}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                      <ClockIcon className="h-3 w-3 text-slate-400" />
                      {sec.duration_minutes} min
                    </span>
                    {token && lessonId && onRegenerated && (
                      <button
                        type="button"
                        disabled={regenSectionId !== null}
                        onClick={() => handleRegenerateSection(sec.id || `sec-${idx}`)}
                        title="Regenerate lesson with updated section"
                        className="no-print inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:border-forge-300 hover:text-forge-700 disabled:opacity-50"
                      >
                        <RefreshIcon
                          className={`h-3 w-3 ${
                            regenSectionId === (sec.id || `sec-${idx}`) ? "animate-spin" : ""
                          }`}
                        />
                        Regenerate
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="rounded-lg bg-forge-50/50 p-4 border border-forge-100">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-forge-900 mb-2">
                      Teacher Actions & Facilitation
                    </h4>
                    <ul className="space-y-1.5 text-sm text-slate-700">
                      {sec.teacher_actions?.map((act, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-forge-600 font-bold">•</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-lg bg-emerald-50/40 p-4 border border-emerald-100">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-900 mb-2">
                      Student Engagement & Tasks
                    </h4>
                    <ul className="space-y-1.5 text-sm text-slate-700">
                      {sec.student_actions?.map((act, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-emerald-600 font-bold">•</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {sec.materials && sec.materials.length > 0 && (
                  <div className="mt-3 flex flex-wrap items-center gap-2 pt-2 text-xs text-slate-600">
                    <span className="font-semibold text-slate-500">Materials:</span>
                    {sec.materials.map((m, i) => (
                      <span
                        key={i}
                        className="rounded bg-slate-100 px-2 py-0.5 text-slate-700"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <p className="text-slate-500 italic">No timeline sections generated.</p>
          )}
        </div>
      </div>

      {/* Section 2: Objectives & Standards (always rendered in print) */}
      <div className={`${tab === "objectives" ? "grid" : "hidden print:grid"} grid-cols-1 md:grid-cols-2 gap-6`}>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <BookOpenIcon className="h-5 w-5 text-forge-600" />
            Target Learning Objectives
          </h3>
          <ul className="space-y-3">
            {content.objectives?.map((obj, i) => (
              <li key={obj.id || i} className="flex items-start gap-3 text-sm text-slate-700">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-forge-100 text-forge-700 text-xs font-bold">
                  {i + 1}
                </span>
                <span>{obj.text}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <ShieldCheckIcon className="h-5 w-5 text-amber-600" />
            Standards Alignment & Evidence
          </h3>
          <div className="space-y-4">
            {content.standards?.map((std, i) => (
              <div key={i} className="rounded-lg border border-slate-100 bg-slate-50 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-bold text-slate-900">
                    {std.code}
                  </span>
                  <span className="rounded bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                    Grounded
                  </span>
                </div>
                {std.description && (
                  <p className="mt-1 text-xs text-slate-600">{std.description}</p>
                )}
                {std.evidence?.length > 0 && (
                  <div className="mt-2 text-xs text-slate-500">
                    <span className="font-semibold text-slate-600">Curriculum Grounding: </span>
                    {std.evidence.join("; ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Section 3: Differentiation Studio (always rendered in print) */}
      <div className={`${tab === "diff" ? "space-y-4" : "hidden print:block print:space-y-4"}`}>
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <UsersIcon className="h-5 w-5 text-forge-600" />
          Universal Design & Differentiated Instruction
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-xl border border-forge-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 pb-3 border-b border-forge-100">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-forge-100 text-forge-700 text-xs font-bold">
                EN
              </span>
              <h3 className="font-bold text-slate-900 text-sm">
                English Language Learners (ELL)
              </h3>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              {content.differentiation?.ell?.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-forge-600">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-amber-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 pb-3 border-b border-amber-100">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-amber-800 text-xs font-bold">
                IEP
              </span>
              <h3 className="font-bold text-slate-900 text-sm">
                Special Education & Accommodations
              </h3>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              {content.differentiation?.iep?.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-amber-600">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 pb-3 border-b border-emerald-100">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                GT
              </span>
              <h3 className="font-bold text-slate-900 text-sm">
                Advanced / Gifted Extensions
              </h3>
            </div>
            <ul className="mt-4 space-y-2 text-sm text-slate-700">
              {content.differentiation?.gifted?.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-emerald-600">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Section 4: Assessments (always rendered in print) */}
      <div className={`${tab === "assessment" ? "space-y-4" : "hidden print:block print:space-y-4"}`}>
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <CheckCircleIcon className="h-5 w-5 text-emerald-600" />
          Formative, Summative & Diagnostic Measures
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {content.assessments?.map((ass, i) => (
            <div key={ass.id || i} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <span className="inline-block rounded bg-forge-100 px-2.5 py-1 text-xs font-bold text-forge-800 uppercase">
                {ass.type}
              </span>

              <div className="mt-4 space-y-3">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                    Assessment Prompts / Questions
                  </h4>
                  <ul className="space-y-1 text-sm text-slate-800">
                    {ass.questions?.map((q, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-forge-600 font-bold">Q{idx + 1}:</span>
                        <span>{q}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {ass.success_criteria?.length > 0 && (
                  <div className="pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-700 mb-1.5">
                      Success Criteria (Mastery)
                    </h4>
                    <ul className="space-y-1 text-xs text-slate-600">
                      {ass.success_criteria.map((crit, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-600">✓</span>
                          <span>{crit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 5: Critic Audit */}
      {tab === "quality" && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-6 no-print">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-lg">
                Critic & Validator Reflection Audit
              </h3>
              <p className="text-sm text-slate-500">
                Automated pedagogical quality score and schema validation report.
              </p>
            </div>
            <span
              className={`rounded-full px-4 py-1 text-sm font-bold ${
                passed
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              {passed ? "Quality Check Passed" : "Needs Review"}
            </span>
          </div>

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
              Identified Issues & Repair Recommendations
            </h4>
            {content.review?.issues && content.review.issues.length > 0 ? (
              <div className="space-y-3">
                {content.review.issues.map((iss, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm"
                  >
                    <div className="flex items-center gap-2 font-semibold text-slate-800">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] uppercase font-bold ${
                          iss.severity === "high"
                            ? "bg-red-100 text-red-700"
                            : iss.severity === "medium"
                            ? "bg-amber-100 text-amber-700"
                            : "bg-slate-200 text-slate-700"
                        }`}
                      >
                        {iss.severity}
                      </span>
                      <span>{iss.issue}</span>
                    </div>
                    {iss.recommendation && (
                      <p className="mt-1.5 text-xs text-slate-600 pl-2 border-l-2 border-forge-500">
                        {iss.recommendation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-emerald-700 text-sm font-medium flex items-center gap-2">
                <CheckCircleIcon className="h-4 w-4" />
                No pedagogical issues or standard misalignments detected.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
