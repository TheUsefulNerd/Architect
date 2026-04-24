/**
 * ProjectsList
 * Client component — fetches and displays the projects list.
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderOpen, Clock, CheckCircle2, Circle, Trash2 } from "lucide-react";
import { formatDate, statusColors, statusLabels } from "@/lib/utils";
import { CreateProjectDialog } from "@/components/dashboard/CreateProjectDialog";
import { projectsApi } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { ProjectResponse, ProjectStatus } from "@/types";

const statusIcon: Record<ProjectStatus, React.ReactNode> = {
  draft:       <Circle       className="h-3.5 w-3.5" />,
  in_progress: <Clock        className="h-3.5 w-3.5" />,
  completed:   <CheckCircle2 className="h-3.5 w-3.5" />,
};

export function ProjectsList() {
  const { user, loading: authLoading } = useAuth();
  const [projects, setProjects]     = useState<ProjectResponse[]>([]);
  const [loading, setLoading]       = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmId, setConfirmId]   = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) { setLoading(false); return; }

    async function fetchProjects() {
      try {
        // Uses axios interceptor — attaches Authorization + X-User-Id automatically
        const data = await projectsApi.list();
        setProjects(data);
      } catch {
        setProjects([]);
      } finally {
        setLoading(false);
      }
    }
    fetchProjects();
  }, [authLoading, user]);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await projectsApi.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error("Failed to delete project:", err);
    } finally {
      setDeletingId(null);
      setConfirmId(null);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="shimmer h-40 rounded-2xl border border-white/8 bg-white/2"
          />
        ))}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
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
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <div key={project.id} className="relative group">
          <Link
            href={`/workspace/${project.id}`}
            className="glass block rounded-2xl p-6 transition-all hover:border-indigo-500/25"
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

          {/* Delete button — shown on hover */}
          <div className="absolute right-3 top-3">
            {confirmId === project.id ? (
              <div className="flex items-center gap-1.5 rounded-xl border border-red-500/20 bg-[#0d1220] p-1.5">
                <span className="text-[10px] text-red-400">Delete?</span>
                <button
                  onClick={() => handleDelete(project.id)}
                  disabled={deletingId === project.id}
                  className="rounded-lg bg-red-500/20 px-2 py-0.5 text-[10px] text-red-400 transition hover:bg-red-500/30"
                >
                  {deletingId === project.id ? "..." : "Yes"}
                </button>
                <button
                  onClick={() => setConfirmId(null)}
                  className="rounded-lg px-2 py-0.5 text-[10px] text-slate-500 transition hover:text-slate-300"
                >
                  No
                </button>
              </div>
            ) : (
              <button
                onClick={(e) => {
                  e.preventDefault();
                  setConfirmId(project.id);
                }}
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/8 bg-[#0d1220] text-slate-600 opacity-0 transition hover:border-red-500/30 hover:text-red-400 group-hover:opacity-100"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      ))}

      <CreateProjectDialog trigger="card" />
    </div>
  );
}