/**
 * CreateProjectDialog
 * Modal for creating a new project.
 * Can render as an icon button, full button, or card.
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X, AlertCircle, FolderPlus } from "lucide-react";
import { projectsApi } from "@/lib/api";

interface CreateProjectDialogProps {
  trigger?: "icon" | "button" | "card";
}

export function CreateProjectDialog({
  trigger = "icon",
}: CreateProjectDialogProps) {
  const router = useRouter();
  const [open, setOpen]             = useState(false);
  const [name, setName]             = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const project = await projectsApi.create({ name, description });
      setOpen(false);
      setName("");
      setDescription("");
      router.push(`/workspace/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  const triggerEl = {
    icon: (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
      >
        <Plus className="h-4 w-4" />
        New project
      </button>
    ),
    button: (
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
      >
        <Plus className="h-4 w-4" />
        Create first project
      </button>
    ),
    card: (
      <button
        onClick={() => setOpen(true)}
        className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/8 p-6 text-center transition hover:border-indigo-500/30 hover:bg-white/2"
      >
        <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-white/5">
          <FolderPlus className="h-4 w-4 text-slate-500" />
        </div>
        <span className="text-sm text-slate-600">New project</span>
      </button>
    ),
  }[trigger];

  return (
    <>
      {triggerEl}

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={(e) => e.target === e.currentTarget && setOpen(false)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          {/* Dialog */}
          <div className="glass-raised relative w-full max-w-md rounded-2xl p-7">
            <div className="mb-6 flex items-start justify-between">
            <div className="flex-1 text-center">
              <h2
                className="text-xl text-slate-50"
                style={{ fontFamily: "var(--font-display)" }}
              >
                New project
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Give your idea a name to get started.
              </p>
            </div>
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/8 hover:text-slate-300"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {error && (
              <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-3.5 text-sm text-red-400">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-400">
                  Project name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  maxLength={255}
                  placeholder="e.g. Real-time collaborative whiteboard"
                  autoFocus
                  className="w-full rounded-xl border border-white/8 bg-white/4 px-4 py-2.5 text-sm text-black placeholder-black outline-none transition focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium text-slate-400">
                  Description{" "}
                  <span className="text-slate-600">(optional)</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="Briefly describe what you want to build..."
                  className="w-full resize-none rounded-xl border border-white/8 bg-white/4 px-4 py-2.5 text-sm text-black placeholder-black outline-none transition focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="flex-1 rounded-xl border border-white/8 py-2.5 text-sm text-slate-400 transition hover:bg-white/5 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !name.trim()}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      Create project
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}