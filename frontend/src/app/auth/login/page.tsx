/**
 * Login Page — "/auth/login"
 */
"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Layers, Github, Chrome, ArrowRight, AlertCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

// ─── Inner component that uses useSearchParams ────────────────────────────────
// Must be a separate component so it can be wrapped in <Suspense>
function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirectTo") || "/dashboard";

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const supabase = createClient();

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    router.push(redirectTo);
    router.refresh();
  };

  const handleOAuth = async (provider: "google" | "github") => {
    setError(null);
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback?next=${redirectTo}`,
      },
    });
    if (error) setError(error.message);
  };

  return (
    <div className="rounded-2xl border border-white/10 bg-[#0d1220] p-8">
      <h1
        className="mb-1 text-2xl text-slate-50"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Welcome back
      </h1>
      <p className="mb-8 text-sm text-slate-500">
        Sign in to continue building with Architect.
      </p>

      {/* Error */}
      {error && (
        <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-3.5 text-sm text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* OAuth */}
      <div className="mb-6 grid grid-cols-2 gap-3">
        <button
          onClick={() => handleOAuth("google")}
          className="flex items-center justify-center gap-2 rounded-xl border border-white/8 bg-white/4 py-2.5 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
        >
          <Chrome className="h-4 w-4" />
          Google
        </button>
        <button
          onClick={() => handleOAuth("github")}
          className="flex items-center justify-center gap-2 rounded-xl border border-white/8 bg-white/4 py-2.5 text-sm text-slate-300 transition hover:bg-white/8 hover:text-white"
        >
          <Github className="h-4 w-4" />
          GitHub
        </button>
      </div>

      {/* Divider */}
      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/6" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-[#0d1220] px-3 text-xs text-slate-600">
            or continue with email
          </span>
        </div>
      </div>

      {/* Email form */}
      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-slate-400">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
            className="w-full rounded-xl border border-white/8 bg-white/4 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-100 outline-none transition focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 [color-scheme:dark]"
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-slate-400">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
            className="w-full rounded-xl border border-white/8 bg-white/4 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 outline-none transition focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 [color-scheme:dark]"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="group flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-semibold text-white transition-all hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          ) : (
            <>
              Sign in
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </>
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-slate-600">
        Don&apos;t have an account?{" "}
        <Link
          href="/auth/register"
          className="text-indigo-400 transition hover:text-indigo-300"
        >
          Sign up
        </Link>
      </p>
    </div>
  );
}

// ─── Page shell — handles layout, wraps LoginForm in Suspense ─────────────────
export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#080c14] px-4">

      {/* Background glow */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 40% at 50% 0%, rgba(99,102,241,0.15), transparent)",
        }}
      />

      <div className="relative w-full max-w-md">

        {/* Logo */}
        <Link href="/" className="mb-8 flex items-center justify-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/20 ring-1 ring-indigo-500/40">
            <Layers className="h-5 w-5 text-indigo-400" />
          </div>
          <span
            className="text-xl text-slate-100"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Architect
          </span>
        </Link>

        {/* Suspense required because LoginForm uses useSearchParams() */}
        <Suspense fallback={
          <div className="rounded-2xl border border-white/10 bg-[#0d1220] p-8 text-center text-sm text-slate-500">
            Loading...
          </div>
        }>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}