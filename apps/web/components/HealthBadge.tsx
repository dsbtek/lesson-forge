"use client";

import React, { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

export default function HealthBadge() {
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    const check = async () => {
      const healthy = await getHealth();
      if (active) setOk(healthy);
    };
    check();
    const id = setInterval(check, 10000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

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
      ? "border-slate-200 bg-white"
      : ok
      ? "border-emerald-200 bg-emerald-50/50 text-emerald-900"
      : "border-rose-200 bg-rose-50/50 text-rose-900";

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold shadow-xs transition-colors duration-200 ${badgeBorder}`}>
      <span className="relative flex h-2 w-2">
        {ok && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
        )}
        <span className={`relative inline-flex h-2 w-2 rounded-full ${dotColor}`} />
      </span>
      <span>{label}</span>
    </div>
  );
}
