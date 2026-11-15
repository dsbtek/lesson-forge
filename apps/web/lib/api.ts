// Typed client for the LessonForge API.
//
// The base URL comes from NEXT_PUBLIC_API_URL (baked at build time in the browser
// bundle). In docker-compose the browser talks to the api on localhost:8000.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_V1 = `${API_BASE}/api/v1`;

export interface LessonRequest {
  grade: string;
  subject: string;
  topic: string;
  duration_minutes: number;
  standards: string[];
  instructional_strategy?: string | null;
  learner_profiles: string[];
  assessment_type?: string | null;
}

export interface GenerateResponse {
  generation_id: string;
  lesson_id: string;
  status: string;
}

export interface GenerationStatus {
  id: string;
  lesson_id: string;
  status: string;
  revision: number;
  quality_score?: number | null;
  error?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface StandardRef {
  code: string;
  description?: string | null;
  evidence: string[];
}

export interface Objective {
  id: string;
  text: string;
  assessment_ids: string[];
}

export interface LessonSection {
  id: string;
  title: string;
  duration_minutes: number;
  teacher_actions: string[];
  student_actions: string[];
  materials: string[];
}

export interface Differentiation {
  ell: string[];
  iep: string[];
  gifted: string[];
}

export interface Assessment {
  id: string;
  type: string;
  questions: string[];
  success_criteria: string[];
}

export interface ReviewIssue {
  severity: "low" | "medium" | "high";
  field?: string | null;
  issue: string;
  recommendation?: string | null;
}

export interface ReviewResult {
  review_passed: boolean;
  score: number;
  issues: ReviewIssue[];
}

export interface LessonContent {
  title: string;
  grade: string;
  subject: string;
  duration_minutes: number;
  standards: StandardRef[];
  objectives: Objective[];
  sections: LessonSection[];
  differentiation: Differentiation;
  assessments: Assessment[];
  vocabulary: string[];
  materials: string[];
  review: ReviewResult;
}

export interface LessonVersion {
  id: string;
  version: number;
  status: string;
  content: LessonContent;
  created_at: string;
}

export interface LessonSummary {
  id: string;
  title: string;
  subject?: string | null;
  grade?: string | null;
  duration_minutes?: number | null;
  created_at: string;
}

export interface StreamEvent {
  event: string;
  generation_id: string;
  agent?: string | null;
  message?: string | null;
  progress?: number | null;
  data?: Record<string, unknown>;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    return JSON.stringify(body.detail ?? body);
  } catch {
    return res.statusText;
  }
}

export async function getHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

export async function register(
  email: string,
  password: string,
  fullName?: string,
): Promise<void> {
  const res = await fetch(`${API_V1}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName || null }),
  });
  // 400 = already registered; treat as non-fatal so demo login can proceed.
  if (!res.ok && res.status !== 400) {
    throw new ApiError(res.status, await parseError(res));
  }
}

export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const res = await fetch(`${API_V1}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  const data = await res.json();
  return data.access_token as string;
}

export async function generateLesson(
  token: string,
  req: LessonRequest,
): Promise<GenerateResponse> {
  const res = await fetch(`${API_V1}/lessons/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return (await res.json()) as GenerateResponse;
}

export async function getGenerationStatus(
  token: string,
  generationId: string,
): Promise<GenerationStatus> {
  const res = await fetch(`${API_V1}/generations/${generationId}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return (await res.json()) as GenerationStatus;
}

export async function getLessonVersions(
  token: string,
  lessonId: string,
): Promise<LessonVersion[]> {
  const res = await fetch(`${API_V1}/lessons/${lessonId}/versions`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return (await res.json()) as LessonVersion[];
}

export async function listLessons(token: string): Promise<LessonSummary[]> {
  const res = await fetch(`${API_V1}/lessons`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return (await res.json()) as LessonSummary[];
}

export interface ExportResult {
  id: string;
  lesson_version_id: string;
  format: string;
  status: string;
  storage_url?: string | null;
}

export async function createExport(
  token: string,
  lessonId: string,
  format: "markdown" | "pdf" | "json" | "docx" = "markdown",
  versionId?: string,
): Promise<ExportResult> {
  const res = await fetch(`${API_V1}/lessons/${lessonId}/exports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ format, version_id: versionId || null }),
  });
  if (!res.ok) throw new ApiError(res.status, await parseError(res));
  return (await res.json()) as ExportResult;
}

/**
 * Connect to SSE generation events stream with automatic reconnect/cleanup.
 */
export function streamGenerationEvents(
  token: string,
  generationId: string,
  onEvent: (ev: StreamEvent) => void,
  onError: (err: Error) => void,
): () => void {
  const controller = new AbortController();

  const run = async () => {
    try {
      const res = await fetch(`${API_V1}/generations/${generationId}/events`, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "text/event-stream",
        },
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new Error(`SSE failed with status ${res.status}`);
      }

      if (!res.body) {
        throw new Error("No response body for SSE");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const block of lines) {
          const match = block.match(/data:\s*(.*)/);
          if (match && match[1]) {
            try {
              const data = JSON.parse(match[1]) as StreamEvent;
              onEvent(data);
            } catch {
              // Ignore keep-alive comments or invalid JSON blocks
            }
          }
        }
      }
    } catch (err: unknown) {
      if ((err as Error)?.name !== "AbortError") {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    }
  };

  run();

  return () => {
    controller.abort();
  };
}
