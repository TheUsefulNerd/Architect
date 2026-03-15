/**
 * Dashboard Page — "/dashboard"
 * Lists user projects and allows creating new ones.
 */
import { redirect } from "next/navigation";
import Link from "next/link";
import {
  FolderOpen,
  Clock,
  CheckCircle2,
  Circle,
  Layers,
  LogOut,
  User,
} from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { formatDate, statusColors, statusLabels } from "@/lib/utils";
import { CreateProjectDialog } from "@/components/dashboard/CreateProjectDialog";
import type { ProjectResponse } from "@/types";

export const metadata = { title: "Dashboard" };

export default async function DashboardPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/auth/login");

  // Projects will be fetched client-side via CreateProjectDialog
  // For now we start with empty — the list will load once backend is connected
  const projects: ProjectResponse[] = [];

  const statusIcon = {
    draft:       <Circle       className="h-3.5 w-3.5" />,
    in_progress: <Clock        className="h-3.5 w-3.5" />,
    completed:   <CheckCircle2 className="h-3.5 w-3.5" />,
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#080c14]">

      {/* Topbar */}
      <header className="glass sticky top-0 z-50 border-b border-white/5 px-8 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">

          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 ring-1 ring-indigo-500/40">
              <Layers className="h-3.5 w-3.5 text-indigo-400" />
            </div>
            <span
              className="text-base text-slate-100"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Architect
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl border border-white/8 bg-white/4 px-3 py-1.5">
              <User className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-xs text-slate-400">{user.email}</span>
            </div>
            <form action="/auth/signout" method="post">
              <button className="flex items-center gap-1.5 rounded-xl border border-white/8 bg-white/4 px-3 py-1.5 text-xs text-slate-400 transition hover:bg-white/8 hover:text-slate-200">
                <LogOut className="h-3 w-3" />
                Sign out
              </button>
            </form>
          </div>

        </div>
      </header>

      {/* Main */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-12">

        {/* Page header */}
        <div className="mb-10 flex items-end justify-between">
          <div>
            <h1
              className="mb-1 text-3xl text-slate-50"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Projects
            </h1>
            <p className="text-sm text-slate-500">
              {projects.length === 0
                ? "No projects yet — create your first one below."
                : `${projects.length} project${projects.length !== 1 ? "s" : ""}`}
            </p>
          </div>
          <CreateProjectDialog trigger="icon" />
        </div>

        {/* Empty state */}
        {projects.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/8 py-24 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 ring-1 ring-indigo-500/20">
              <FolderOpen className="h-6 w-6 text-indigo-500/60" />
            </div>
            <h3
              className="mb-2 text-lg text-slate-300"
              style={{ fontFamily: "var(--font-display)" }}
            >
              No projects yet
            </h3>
            <p className="mb-6 max-w-xs text-sm text-slate-600">
              Create a project to start the Socratic Loop and transform your
              idea into an engineered system.
            </p>
            <CreateProjectDialog trigger="button" />
          </div>
        )}

        {/* Projects grid */}
        {projects.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/workspace/${project.id}`}
                className="glass group rounded-2xl p-6 transition-all hover:border-indigo-500/25"
              >
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 ring-1 ring-indigo-500/20 transition group-hover:bg-indigo-500/20">
                    <FolderOpen className="h-4 w-4 text-indigo-400" />
                  </div>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${statusColors[project.status]}`}
                  >
                    {statusIcon[project.status]}
                    {statusLabels[project.status]}
                  </span>
                </div>

                <h3
                  className="mb-1.5 text-base font-medium text-slate-100 group-hover:text-white"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  {project.name}
                </h3>

                {project.description && (
                  <p className="mb-4 line-clamp-2 text-xs leading-relaxed text-slate-500">
                    {project.description}
                  </p>
                )}

                <div className="flex items-center gap-1 text-xs text-slate-600">
                  <Clock className="h-3 w-3" />
                  {formatDate(project.created_at)}
                </div>
              </Link>
            ))}

            <CreateProjectDialog trigger="card" />
          </div>
        )}

      </main>
    </div>
  );
}