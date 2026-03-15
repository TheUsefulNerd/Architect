/**
 * WorkspaceShell
 * Resizable dual-pane layout host.
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { Layers, ArrowLeft, Loader2 } from "lucide-react";
import { projectsApi, sessionsApi } from "@/lib/api";
import { useProjectStore } from "@/stores/useProjectStore";
import { FlowPanel } from "@/components/workspace/flow/FlowPanel";
import { ChatPanel } from "@/components/workspace/chat/ChatPanel";
import { PhaseIndicator } from "@/components/workspace/PhaseIndicator";

interface WorkspaceShellProps {
  projectId: string;
}

export function WorkspaceShell({ projectId }: WorkspaceShellProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  const { setActiveProject, setActiveSession, setMessages, activeProject } =
    useProjectStore();

  useEffect(() => {
    async function init() {
      try {
        const project = await projectsApi.get(projectId);
        setActiveProject(project);

        let session;
        try {
          session = await sessionsApi.getByProject(projectId);
        } catch {
          session = await sessionsApi.create({ project_id: projectId });
        }
        setActiveSession(session);

        const messages = await sessionsApi.getMessages(session.id);
        setMessages(messages);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load workspace");
      } finally {
        setLoading(false);
      }
    }

    init();
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#080c14]">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 h-8 w-8 animate-spin text-indigo-400" />
          <p className="text-sm text-slate-500">Loading workspace…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#080c14] p-8">
        <div className="max-w-md rounded-2xl border border-white/10 bg-[#0d1220] p-8 text-center">
          <p className="mb-4 text-sm text-red-400">{error}</p>
          <Link
            href="/dashboard"
            className="text-sm text-indigo-400 hover:text-indigo-300"
          >
            ← Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#080c14]">

      {/* Top bar */}
      <header className="glass z-50 flex h-14 shrink-0 items-center justify-between border-b border-white/5 px-5">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-slate-500 transition hover:bg-white/5 hover:text-slate-300"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Dashboard
          </Link>

          <div className="h-4 w-px bg-white/10" />

          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-500/20 ring-1 ring-indigo-500/30">
              <Layers className="h-3 w-3 text-indigo-400" />
            </div>
            <span
              className="text-sm text-slate-200"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {activeProject?.name ?? "Workspace"}
            </span>
          </div>
        </div>

        <PhaseIndicator />
      </header>

      {/* Resizable dual-pane */}
      <PanelGroup direction="horizontal" className="flex-1 overflow-hidden">
        <Panel defaultSize={40} minSize={25} maxSize={70}>
          <FlowPanel />
        </Panel>

        <PanelResizeHandle />

        <Panel defaultSize={60} minSize={30} maxSize={75}>
          <ChatPanel />
        </Panel>
      </PanelGroup>

    </div>
  );
}