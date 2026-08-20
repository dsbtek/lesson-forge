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

class ApiError extends Error {
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
  // 400 = already registered; treat as non-fatal so the demo login can proceed.
  if (!res.ok && res.status !== 400) {
    throw new ApiError(res.status, await parseError(res));
  }
}

export async function login(email: string, password: string): Promise<string> {
  // The API uses an OAuth2 password form: field name is `username` (= email).
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
