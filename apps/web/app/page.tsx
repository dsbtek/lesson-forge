import HealthBadge from "@/components/HealthBadge";
import LessonForm from "@/components/LessonForm";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-forge-700">
            LessonForge
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            Multi-agent lesson-plan generation. This is the Phase 1 scaffold —
            the agent pipeline runs as deterministic stubs (no LLM calls yet).
          </p>
        </div>
        <HealthBadge />
      </header>

      <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <LessonForm />
      </section>

      <footer className="mt-8 text-center text-xs text-gray-400">
        API docs at{" "}
        <a
          className="underline hover:text-gray-600"
          href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`}
          target="_blank"
          rel="noreferrer"
        >
          /docs
        </a>
      </footer>
    </main>
  );
}
