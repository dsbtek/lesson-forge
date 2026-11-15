"use client";

import React, { useState } from "react";
import { getMe, login, register, type UserProfile } from "@/lib/api";
import { SparklesIcon } from "./Icons";

interface Props {
  open: boolean;
  onClose: () => void;
  onAuthenticated: (token: string, user: UserProfile) => void;
}

export default function AuthModal({ open, onClose, onAuthenticated }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const completeLogin = async (userEmail: string, userPassword: string) => {
    const token = await login(userEmail, userPassword);
    const profile = await getMe(token);
    onAuthenticated(token, profile);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await register(email, password, fullName || undefined);
      }
      await completeLogin(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleDemoLogin = async () => {
    setBusy(true);
    setError(null);
    const demoEmail = "teacher@example.com";
    const demoPass = "changeme-please";
    try {
      await register(demoEmail, demoPass, "Demo Educator");
      await completeLogin(demoEmail, demoPass);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forge-600 text-white">
              <SparklesIcon className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                {mode === "login" ? "Teacher Sign In" : "Create Teacher Account"}
              </h2>
              <p className="text-xs text-slate-500">
                Save lessons, track versions & export plans
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            ✕
          </button>
        </div>

        {/* Mode Tabs */}
        <div className="mt-4 grid grid-cols-2 rounded-lg bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`rounded-md py-1.5 text-xs font-semibold transition ${
              mode === "login"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`rounded-md py-1.5 text-xs font-semibold transition ${
              mode === "register"
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {mode === "register" && (
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Sarah Smith"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-forge-500 focus:outline-none focus:ring-2 focus:ring-forge-500/20"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teacher@school.org"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-forge-500 focus:outline-none focus:ring-2 focus:ring-forge-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
              Password (min 8 chars)
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-forge-500 focus:outline-none focus:ring-2 focus:ring-forge-500/20"
            />
          </div>

          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-forge-600 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-forge-700 disabled:opacity-60"
          >
            {busy
              ? "Please wait…"
              : mode === "login"
              ? "Sign In"
              : "Register & Sign In"}
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-slate-100">
          <button
            type="button"
            disabled={busy}
            onClick={handleDemoLogin}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-60"
          >
            Continue with Demo Teacher (teacher@example.com)
          </button>
        </div>
      </div>
    </div>
  );
}
