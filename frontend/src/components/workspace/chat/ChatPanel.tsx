/**
 * ChatPanel — tabbed right pane
 * Tabs: Chat | Docs | Code
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Cpu, User, BookOpen, Code2, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SyntaxHighlighter } from "@/components/workspace/chat/SyntaxHighlighter";
import { DocsTab } from "@/components/workspace/chat/DocsTab";
import { CodeTab } from "@/components/workspace/chat/CodeTab";
import { useProjectStore } from "@/stores/useProjectStore";
import { useChat } from "@/hooks/useChat";
import { cn, phaseLabels } from "@/lib/utils";
import type { Phase, WorkspaceTab } from "@/types";

// ─── Phase icon map ───────────────────────────────────────────────────────────

const phaseIconMap: Record<Phase, React.ElementType> = {
  planner:   Cpu,
  librarian: BookOpen,
  mentor:    Code2,
};

// ─── Tab config ───────────────────────────────────────────────────────────────

const tabs: { id: WorkspaceTab; label: string; icon: React.ElementType }[] = [
  { id: "chat", label: "Chat",  icon: Cpu      },
  { id: "docs", label: "Docs",  icon: BookOpen },
  { id: "code", label: "Code",  icon: Code2    },
];

// ─── Message bubble ───────────────────────────────────────────────────────────

function MessageBubble({
  role,
  content,
  phase,
}: {
  role: "user" | "assistant" | "system";
  content: string;
  phase?: Phase;
}) {
  const isUser    = role === "user";
  const PhaseIcon = phase ? phaseIconMap[phase] : Cpu;

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ring-1",
          isUser
            ? "bg-slate-700/50 ring-white/10"
            : "bg-indigo-500/15 ring-indigo-500/30"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-slate-400" />
        ) : (
          <PhaseIcon className="h-4 w-4 text-indigo-400" />
        )}
      </div>

      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-white/6 text-slate-200"
            : "border border-white/8 bg-[#0d1220] text-slate-200"
        )}
      >
        {!isUser && phase && (
          <div className="mb-2 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-widest text-slate-600">
            <PhaseIcon className="h-2.5 w-2.5" />
            {phaseLabels[phase]}
          </div>
        )}

        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children }) {
              const match = /language-(\w+)/.exec(className || "");
              return match ? (
                <SyntaxHighlighter language={match[1]}>
                  {String(children).replace(/\n$/, "")}
                </SyntaxHighlighter>
              ) : (
                <code className="rounded bg-white/8 px-1.5 py-0.5 font-mono text-xs text-slate-300">
                  {children}
                </code>
              );
            },
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            ul: ({ children }) => <ul className="mb-2 list-disc pl-5 last:mb-0">{children}</ul>,
            ol: ({ children }) => <ol className="mb-2 list-decimal pl-5 last:mb-0">{children}</ol>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-indigo-500/40 pl-4 italic text-slate-400">
                {children}
              </blockquote>
            ),
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 underline underline-offset-2 hover:text-indigo-300"
              >
                {children}
              </a>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

// ─── Streaming bubble ─────────────────────────────────────────────────────────

function StreamingBubble({ content }: { content: string }) {
  return (
    <div className="flex gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-500/15 ring-1 ring-indigo-500/30">
        <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
      </div>
      <div className="max-w-[80%] rounded-2xl border border-white/8 bg-[#0d1220] px-4 py-3 text-sm text-slate-200">
        {content || (
          <div className="flex items-center gap-1.5 text-slate-600">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-600 [animation-delay:0ms]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-600 [animation-delay:150ms]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-600 [animation-delay:300ms]" />
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Empty chat state ─────────────────────────────────────────────────────────

function EmptyChat() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 ring-1 ring-indigo-500/20">
        <Cpu className="h-7 w-7 text-indigo-500/60" />
      </div>
      <h3
        className="mb-2 text-lg text-slate-300"
        style={{ fontFamily: "var(--font-display)" }}
      >
        Start the Socratic Loop
      </h3>
      <p className="max-w-xs text-sm text-slate-600">
        Describe your idea below. The Planner will guide you through
        the first phase.
      </p>
    </div>
  );
}

// ─── Main ChatPanel ───────────────────────────────────────────────────────────

export function ChatPanel() {
  const [input, setInput] = useState("");
  const bottomRef         = useRef<HTMLDivElement>(null);

  const messages         = useProjectStore((s) => s.messages);
  const isStreaming      = useProjectStore((s) => s.isStreaming);
  const streamingContent = useProjectStore((s) => s.streamingContent);
  const activeSession    = useProjectStore((s) => s.activeSession);
  const activeTab        = useProjectStore((s) => s.activeTab);
  const setActiveTab     = useProjectStore((s) => s.setActiveTab);
  const docLinks         = useProjectStore((s) => s.docLinks);
  const scaffolds        = useProjectStore((s) => s.scaffolds);

  const { sendMessage } = useChat();

  // Auto-scroll on new messages
  useEffect(() => {
    if (activeTab === "chat") {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, streamingContent, activeTab]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const text = input.trim();
    if (!text || isStreaming || !activeSession) return;
    setInput("");
    try {
      await sendMessage(text);
    } catch (err) {
      console.error("Chat error:", err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-full flex-col bg-[#080c14]">

      {/* Tab bar */}
      <div className="flex items-center border-b border-white/5 px-4">
        {tabs.map((tab) => {
          const Icon      = tab.icon;
          const isActive  = activeTab === tab.id;
          const hasBadge  = (tab.id === "docs" && docLinks.length > 0) ||
                            (tab.id === "code" && scaffolds.length > 0);

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "relative flex items-center gap-1.5 px-4 py-3 text-xs font-medium transition border-b-2",
                isActive
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-600 hover:text-slate-400"
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
              {hasBadge && !isActive && (
                <span className="ml-1 h-1.5 w-1.5 rounded-full bg-indigo-500" />
              )}
            </button>
          );
        })}

        {/* Session indicator */}
        <div className="ml-auto flex items-center gap-1.5 pr-2">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-400" />
          <span className="text-[10px] text-slate-600">
            {activeSession?.current_phase ?? "connecting"}
          </span>
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "chat" && (
        <>
          <div className="flex-1 overflow-y-auto px-5 py-6">
            {messages.length === 0 && !isStreaming ? (
              <EmptyChat />
            ) : (
              <div className="space-y-5">
                {messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    role={msg.role as "user" | "assistant" | "system"}
                    content={msg.content}
                    phase={msg.phase}
                  />
                ))}
                {isStreaming && <StreamingBubble content={streamingContent} />}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          <div className="border-t border-white/5 p-4">
            <form onSubmit={handleSubmit} className="relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isStreaming || !activeSession}
                rows={1}
                placeholder={
                  isStreaming
                    ? "Architect is thinking…"
                    : "Describe your idea or respond to the agent…"
                }
                style={{ resize: "none" }}
                className="w-full rounded-2xl border border-white/8 bg-white/4 py-3.5 pl-4 pr-14 text-sm text-slate-100 placeholder-slate-600 outline-none transition focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/15 disabled:cursor-not-allowed disabled:opacity-50 [color-scheme:dark]"
                onInput={(e) => {
                  const el = e.currentTarget;
                  el.style.height = "auto";
                  el.style.height = Math.min(el.scrollHeight, 160) + "px";
                }}
              />
              <button
                type="submit"
                disabled={!input.trim() || isStreaming || !activeSession}
                className="absolute bottom-3 right-3 flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600 text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
              </button>
            </form>
            <p className="mt-2 text-center text-[10px] text-slate-700">
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        </>
      )}

      {activeTab === "docs" && (
        <div className="flex flex-1 flex-col overflow-hidden">
          <DocsTab />
        </div>
      )}

      {activeTab === "code" && (
        <div className="flex flex-1 flex-col overflow-hidden">
          <CodeTab />
        </div>
      )}

    </div>
  );
}