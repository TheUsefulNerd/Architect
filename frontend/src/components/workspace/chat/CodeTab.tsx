/**
 * CodeTab
 * Displays Mentor-generated code scaffolds as a file browser.
 */
"use client";

import { useState } from "react";
import { Code2, FileCode, ChevronRight, RefreshCw } from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";
import { sessionsApi } from "@/lib/api";
import { SyntaxHighlighter } from "@/components/workspace/chat/SyntaxHighlighter";

export function CodeTab() {
  const scaffolds     = useProjectStore((s) => s.scaffolds);
  const activeSession = useProjectStore((s) => s.activeSession);
  const [activeFile, setActiveFile] = useState<number>(0);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!activeSession) return;
    setRefreshing(true);
    try {
      const data = await sessionsApi.getScaffolds(activeSession.id);
      if (data.length > 0) useProjectStore.getState().setScaffolds(data);
    } finally {
      setRefreshing(false);
    }
  };

  if (scaffolds.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-500/10 ring-1 ring-violet-500/20">
          <Code2 className="h-7 w-7 text-violet-500/60" />
        </div>
        <h3
          className="mb-2 text-lg text-slate-300"
          style={{ fontFamily: "var(--font-display)" }}
        >
          No code yet
        </h3>
        <p className="max-w-xs text-sm text-slate-600">
          Scaffolds will appear here once the Mentor phase completes.
        </p>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="mt-4 flex items-center gap-2 rounded-lg border border-violet-500/20 bg-violet-500/10 px-3 py-1.5 text-xs text-violet-400 transition hover:bg-violet-500/20 disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Loading…" : "Load scaffolds"}
        </button>
      </div>
    );
  }

  const active = scaffolds[activeFile];
  const fileExt = active?.file_path?.split(".").pop() ?? "text";

  const langMap: Record<string, string> = {
    ts:   "typescript",
    tsx:  "typescript",
    js:   "javascript",
    jsx:  "javascript",
    py:   "python",
    css:  "css",
    html: "html",
    json: "json",
    md:   "markdown",
    sh:   "bash",
    yml:  "yaml",
    yaml: "yaml",
  };
  const language = langMap[fileExt] ?? "text";

  return (
    <div className="flex h-full flex-col">
      {/* File browser sidebar + content */}
      <div className="flex flex-1 overflow-hidden">

        {/* File list */}
        <div className="w-44 shrink-0 border-r border-white/5 overflow-y-auto bg-[#080c14]">
          <div className="px-3 py-2 text-[10px] font-medium uppercase tracking-widest text-slate-600">
            Files
          </div>
          {scaffolds.map((scaffold, i) => {
            const fileName = scaffold.file_path?.split("/").pop() ?? scaffold.file_path;
            const isActive = i === activeFile;
            return (
              <button
                key={i}
                onClick={() => setActiveFile(i)}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition ${
                  isActive
                    ? "bg-violet-500/10 text-violet-400"
                    : "text-slate-500 hover:bg-white/4 hover:text-slate-300"
                }`}
              >
                <FileCode className="h-3 w-3 shrink-0" />
                <span className="truncate">{fileName}</span>
                {isActive && (
                  <ChevronRight className="ml-auto h-3 w-3 shrink-0" />
                )}
              </button>
            );
          })}
        </div>

        {/* File content */}
        <div className="flex-1 overflow-y-auto">
          {active && (
            <div>
              {/* File header */}
              <div className="flex items-center gap-2 border-b border-white/5 bg-[#080c14] px-4 py-2.5">
                <FileCode className="h-3.5 w-3.5 text-violet-400" />
                <span className="text-xs text-slate-400">{active.file_path}</span>
              </div>

              {/* Code */}
              <div className="p-4">
                <SyntaxHighlighter language={language}>
                  {active.content}
                </SyntaxHighlighter>
              </div>

              {/* Hints */}
              {active.hints && active.hints.length > 0 && (
                <div className="mx-4 mb-4 rounded-xl border border-violet-500/15 bg-violet-500/5 p-4">
                  <p className="mb-2 text-[10px] font-medium uppercase tracking-widest text-violet-400">
                    Hints for this file
                  </p>
                  <ul className="space-y-1.5">
                    {active.hints.map((hint, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-500">
                        <span className="mt-0.5 shrink-0 text-violet-400">🤔</span>
                        {hint}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}