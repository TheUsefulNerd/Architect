/**
 * Landing Page — "/" route
 */
import Link from "next/link";
import {
  ArrowRight,
  Cpu,
  BookOpen,
  Code2,
  Zap,
  GitBranch,
  Layers,
} from "lucide-react";

const features = [
  {
    icon: Cpu,
    title: "Phase I — Planner",
    description:
      "Deconstructs your idea into a formal Technical Specification: requirements, architecture, and a curated tech stack.",
  },
  {
    icon: BookOpen,
    title: "Phase II — Librarian",
    description:
      "Identifies knowledge gaps and crawls official documentation, returning deep-linked citations — never hallucinated links.",
  },
  {
    icon: Code2,
    title: "Phase III — Mentor",
    description:
      "Generates code scaffolds with intentional gaps and Socratic hints, so you build the solution — not the AI.",
  },
];

const stats = [
  { value: "3",  label: "Agent Phases"      },
  { value: "∞",  label: "Project Types"     },
  { value: "0",  label: "Lines Written For You" },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#080c14]">

      {/* Background grid */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(59,130,246,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.04) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Hero glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,0.25), transparent)",
        }}
      />

      {/* Nav */}
      <header className="relative z-10 flex items-center justify-between px-8 py-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 ring-1 ring-indigo-500/40">
            <Layers className="h-4 w-4 text-indigo-400" />
          </div>
          <span
            className="text-lg tracking-wide text-slate-100"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Architect
          </span>
        </div>

        <nav className="flex items-center gap-6">
          <Link
            href="/auth/login"
            className="text-sm text-slate-400 transition hover:text-slate-100"
          >
            Sign in
          </Link>
          <Link
            href="/auth/register"
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
          >
            Get started <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <main className="relative z-10 mx-auto max-w-5xl px-8 pb-16 pt-24 text-center">

        {/* Badge */}
        <div className="animate-in stagger-1 mb-8 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-xs text-indigo-400">
          <Zap className="h-3 w-3" />
          Multi-agent AI orchestration · Socratic methodology
        </div>

        {/* Headline */}
        <h1
          className="animate-in stagger-2 mb-6 text-6xl leading-tight text-slate-50 md:text-7xl"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Transform ideas into
          <br />
          <span className="gradient-text italic">engineering reality</span>
        </h1>

        {/* Subheadline */}
        <p className="animate-in stagger-3 mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-slate-400">
          Architect guides you through system design and documentation research
          using the Socratic Loop — so you{" "}
          <em className="text-slate-300">understand</em> every decision, not
          just receive generated code.
        </p>

        {/* CTAs */}
        <div className="animate-in stagger-4 flex items-center justify-center gap-4">
          <Link
            href="/auth/register"
            className="group inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-7 py-3.5 text-sm font-semibold text-white transition-all hover:bg-indigo-500 hover:-translate-y-0.5"
          >
            Start building
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/auth/login"
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-3.5 text-sm font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
          >
            Sign in
          </Link>
        </div>

        {/* Stats */}
        <div className="animate-in stagger-5 mt-20 grid grid-cols-3 divide-x divide-white/5 rounded-2xl border border-white/6 bg-white/[0.02] py-8">
          {stats.map((s) => (
            <div key={s.label} className="px-8 text-center">
              <div
                className="gradient-text mb-1 text-4xl"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {s.value}
              </div>
              <div className="text-sm text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      </main>

      {/* Features */}
      <section className="relative z-10 mx-auto max-w-5xl px-8 pb-24">
        <div className="mb-12 text-center">
          <h2
            className="mb-3 text-3xl text-slate-100"
            style={{ fontFamily: "var(--font-display)" }}
          >
            The three-phase Socratic Loop
          </h2>
          <p className="text-slate-500">
            Each phase builds on the last, guided by your active participation.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {features.map((f, i) => (
            <div
              key={f.title}
              className="animate-in glass rounded-2xl p-6"
              style={{ animationDelay: `${0.1 + i * 0.1}s` }}
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/15 ring-1 ring-indigo-500/25">
                <f.icon className="h-5 w-5 text-indigo-400" />
              </div>
              <h3
                className="mb-2 text-lg text-slate-100"
                style={{ fontFamily: "var(--font-display)" }}
              >
                {f.title}
              </h3>
              <p className="text-sm leading-relaxed text-slate-400">
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 px-8 py-6">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-slate-600" />
            <span className="text-xs text-slate-600">
              Built with FastAPI · LangGraph · Next.js 15
            </span>
          </div>
          <span className="text-xs text-slate-700">
            Architect © {new Date().getFullYear()}
          </span>
        </div>
      </footer>

    </div>
  );
}