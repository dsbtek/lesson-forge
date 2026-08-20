"use client";

import { useEffect, useState } from "react";
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
    ok === null ? "checking API…" : ok ? "API online" : "API unreachable";
  const color =
    ok === null ? "bg-gray-400" : ok ? "bg-green-500" : "bg-red-500";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-sm text-gray-700 shadow-sm">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      {label}
    </span>
  );
}
