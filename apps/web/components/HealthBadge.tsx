"use client";

import React, { useEffect, useState } from "react";
import { getHealth, type HealthInfo } from "@/lib/api";

export default function HealthBadge() {
  const [info, setInfo] = useState<HealthInfo | null>(null);

  useEffect(() => {
    let active = true;
    const check = async () => {
      const h = await getHealth();
      if (active) setInfo(h);
    };
    check();
    const id = setInterval(check, 10000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  const ok = info?.ok ?? null;
  const label =
    ok === null ? "Checking API…" : ok ? "API Live" : "API Offline";
  const dotColor =
    ok === null
      ? "bg-slate-400"
      : ok
      ? "bg-emerald-500 shadow-sm shadow-emerald-400"
      : "bg-rose-500 shadow-sm shadow-rose-400";
  const badgeBorder =
    ok === null
      ? "border-slate-200 bg-white text-slate-600"
      : ok
      ? "border-emerald-200 bg-emerald-50/60 text-emerald-900"
      : "border-rose-200 bg-rose-50/60 text-rose-900";

  return (
    <div className="flex items-center gap-2">
      {info?.ok && (
        <span
          title={
            info.llmEnabled
              ? `Using ${info.llmProvider} (${info.llmModel})${info.ragEnabled ? " + Hybrid RAG" : ""}`
              : "LLM_ENABLED=false — running deterministic fallback stubs"
          }
          className={`hidden sm:inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${
            info.llmEnabled
              ? "border-forge-200 bg-forge-50 text-forge-800"
              : "border-amber-200 bg-amber-50 text-amber-800"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              info.llmEnabled ? "bg-forge-600" : "bg-amber-500"
            }`}
          />
          {info.llmEnabled ? `AI: ${info.llmModel}` : "Fallback Mode"}
        </span>
      )}

      <div
        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold shadow-xs transition-colors duration-200 ${badgeBorder}`}
      >
        <span className="relative flex h-2 w-2">
          {ok && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          )}
          <span className={`relative inline-flex h-2 w-2 rounded-full ${dotColor}`} />
        </span>
        <span>{label}</span>
      </div>
    </div>
  );
}
