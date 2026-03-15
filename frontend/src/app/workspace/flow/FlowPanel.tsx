/**
 * FlowPanel
 * Left pane — React Flow workflow visualization.
 */
"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
} from "reactflow";
import "reactflow/dist/style.css";
import { Cpu, BookOpen, Code2, Check } from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";
import { cn } from "@/lib/utils";
import type { Phase } from "@/types";

// ─── Phase config ─────────────────────────────────────────────────────────────

const phaseConfig: Record
  Phase,
  { icon: React.ElementType; color: string; description: string }
> = {
  planner: {
    icon: Cpu,
    color: "indigo",
    description: "Deconstructs your idea into a Technical Specification",
  },
  librarian: {
    icon: BookOpen,
    color: "cyan",
    description: "Gathers documentation and deep-links official resources",
  },
  mentor: {
    icon: Code2,
    color: "violet",
    description: "Generates scaffolds and guides your implementation",
  },
};

const colorMap = {
  indigo: {
    ring:   "ring-indigo-500/50",
    bg:     "bg-indigo-500/15",
    text:   "text-indigo-400",
    glow:   "shadow-[0_0_20px_rgba(99,102,241,0.4)]",
    border: "border-indigo-500/40",
  },
  cyan: {
    ring:   "ring-cyan-500/50",
    bg:     "bg-cyan-500/15",
    text:   "text-cyan-400",
    glow:   "shadow-[0_0_20px_rgba(6,182,212,0.4)]",
    border: "border-cyan-500/40",
  },
  violet: {
    ring:   "ring-violet-500/50",
    bg:     "bg-violet-500/15",
    text:   "text-violet-400",
    glow:   "shadow-[0_0_20px_rgba(139,92,246,0.4)]",
    border: "border-violet-500/40",
  },
};

// ─── Custom node ──────────────────────────────────────────────────────────────

function PhaseNode({ data }: NodeProps) {
  const { phase, status } = data as {
    phase: Phase;
    status: "idle" | "active" | "completed";
  };

  const cfg   = phaseConfig[phase];
  const Icon  = cfg.icon;
  const color = colorMap[cfg.color as keyof typeof colorMap];

  return (
    <div
      className={cn(
        "relative w-52 rounded-2xl border bg-[#0d1220] p-5 transition-all",
        status === "active"    && `${color.border} ${color.glow}`,
        status === "completed" && "border-emerald-500/30",
        status === "idle"      && "border-white/8"
      )}
    >
      <Handle type="target" position={Position.Top}    style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />

      <div className="mb-3 flex items-center justify-between">
        <div
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl ring-1",
            status === "active"    && `${color.bg} ${color.ring}`,
            status === "completed" && "bg-emerald-500/15 ring-emerald-500/30",
            status === "idle"      && "bg-white/5 ring-white/10"
          )}
        >
          {status === "completed" ? (
            <Check className="h-4 w-4 text-emerald-400" />
          ) : (
            <Icon
              className={cn(
                "h-4 w-4",
                status === "active" ? color.text : "text-slate-600"
              )}
            />
          )}
        </div>

        <div
          className={cn(
            "flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium",
            status === "active"    && `${color.bg} ${color.text}`,
            status === "completed" && "bg-emerald-500/15 text-emerald-400",
            status === "idle"      && "bg-white/5 text-slate-600"
          )}
        >
          {status === "active" && (
            <span className={`h-1.5 w-1.5 animate-pulse rounded-full bg-current`} />
          )}
          {status === "active" ? "Active" : status === "completed" ? "Done" : "Waiting"}
        </div>
      </div>

      <h3
        className={cn(
          "mb-1 text-sm font-medium capitalize",
          status === "idle" ? "text-slate-600" : "text-slate-100"
        )}
        style={{ fontFamily: "var(--font-display)" }}
      >
        {phase}
      </h3>

      <p className="text-[11px] leading-relaxed text-slate-600">
        {cfg.description}
      </p>
    </div>
  );
}

const nodeTypes = { phaseNode: PhaseNode };

// ─── Flow Panel ───────────────────────────────────────────────────────────────

export function FlowPanel() {
  const currentPhase = useProjectStore((s) => s.currentPhase);
  const phaseOrder: Phase[] = ["planner", "librarian", "mentor"];
  const currentIdx = phaseOrder.indexOf(currentPhase);

  const nodes: Node[] = useMemo(
    () =>
      phaseOrder.map((phase, i) => ({
        id:       phase,
        type:     "phaseNode",
        position: { x: 80, y: 60 + i * 180 },
        data: {
          phase,
          status:
            i < currentIdx  ? "completed" :
            i === currentIdx ? "active"    : "idle",
        },
      })),
    [currentIdx] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const edges: Edge[] = useMemo(
    () => [
      {
        id:       "planner-librarian",
        source:   "planner",
        target:   "librarian",
        animated: currentIdx >= 1,
        style: {
          stroke: currentIdx >= 1
            ? "rgba(99,102,241,0.6)"
            : "rgba(255,255,255,0.06)",
        },
      },
      {
        id:       "librarian-mentor",
        source:   "librarian",
        target:   "mentor",
        animated: currentIdx >= 2,
        style: {
          stroke: currentIdx >= 2
            ? "rgba(99,102,241,0.6)"
            : "rgba(255,255,255,0.06)",
        },
      },
    ],
    [currentIdx]
  );

  return (
    <div className="relative h-full bg-[#080c14]">
      <div className="absolute left-4 top-4 z-10 flex items-center gap-1.5 rounded-lg bg-black/40 px-3 py-1.5 text-xs text-slate-500 backdrop-blur">
        Workflow
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        zoomOnScroll={true}
        panOnScroll={false}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="rgba(59,130,246,0.08)"
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}