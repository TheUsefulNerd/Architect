/**
 * FlowPanel
 * Left pane — Dynamic roadmap visualization using React Flow.
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
import { Check } from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";
import { cn } from "@/lib/utils";

// ─── Complexity styles ────────────────────────────────────────────────────────

type ComplexityStyle = {
  color: string;
  bg: string;
  ring: string;
  dot: string;
};

const complexityStyles: { [key: string]: ComplexityStyle } = {
  simple: {
    color: "text-emerald-400",
    bg:    "bg-emerald-500/10",
    ring:  "ring-emerald-500/30",
    dot:   "bg-emerald-400",
  },
  medium: {
    color: "text-amber-400",
    bg:    "bg-amber-500/10",
    ring:  "ring-amber-500/30",
    dot:   "bg-amber-400",
  },
  complex: {
    color: "text-red-400",
    bg:    "bg-red-500/10",
    ring:  "ring-red-500/30",
    dot:   "bg-red-400",
  },
};

function getStyle(complexity: string): ComplexityStyle {
  return complexityStyles[complexity] ?? complexityStyles.simple;
}

// ─── Roadmap Node ─────────────────────────────────────────────────────────────

function RoadmapNode({ data }: NodeProps) {
  const title      = data.title as string;
  const complexity = data.complexity as string;
  const status     = data.status as "idle" | "active" | "completed";
  const stepNumber = data.stepNumber as number;

  const cfg = getStyle(complexity);

  return (
    <div
      className={cn(
        "relative w-56 rounded-2xl border bg-[#0d1220] px-4 py-3.5 transition-all",
        status === "active"    && "border-indigo-500/40 shadow-[0_0_20px_rgba(99,102,241,0.3)]",
        status === "completed" && "border-emerald-500/25",
        status === "idle"      && "border-white/8"
      )}
    >
      <Handle type="target" position={Position.Top}    style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />

      <div className="flex items-center gap-3">
        {/* Step number / check */}
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-medium ring-1",
            status === "completed" && "bg-emerald-500/15 ring-emerald-500/30 text-emerald-400",
            status === "active"    && "bg-indigo-500/15 ring-indigo-500/30 text-indigo-400",
            status === "idle"      && "bg-white/5 ring-white/10 text-slate-600"
          )}
        >
          {status === "completed" ? (
            <Check className="h-3.5 w-3.5" />
          ) : (
            <span>{stepNumber}</span>
          )}
        </div>

        {/* Title */}
        <p
          className={cn(
            "flex-1 text-xs leading-snug",
            status === "idle" ? "text-slate-600" : "text-slate-200"
          )}
        >
          {title}
        </p>

        {/* Complexity dot */}
        <div
          className={cn("h-2 w-2 shrink-0 rounded-full", cfg.dot)}
          title={complexity}
        />
      </div>
    </div>
  );
}

// ─── Default nodes shown before Planner completes ────────────────────────────

const defaultSteps = [
  { title: "Planning your project",        complexity: "simple"  },
  { title: "Gathering documentation",      complexity: "simple"  },
  { title: "Generating code scaffolds",    complexity: "medium"  },
];

// ─── nodeTypes defined at module level to prevent React Flow warning ──────────

const nodeTypes = Object.freeze({ roadmapNode: RoadmapNode });

// ─── Flow Panel ───────────────────────────────────────────────────────────────

export function FlowPanel() {
  const roadmap      = useProjectStore((s) => s.roadmap);
  const currentPhase = useProjectStore((s) => s.currentPhase);

  const steps = roadmap.length > 0 ? roadmap : defaultSteps;
  const usingDefault = roadmap.length === 0;

  const nodes: Node[] = useMemo(
    () =>
      steps.map((step, i) => {
        let status: "idle" | "active" | "completed" = "idle";

        if (usingDefault) {
          if (currentPhase === "planner"   && i === 0) status = "active";
          if (currentPhase === "librarian" && i === 1) status = "active";
          if (currentPhase === "mentor"    && i === 2) status = "active";
          if (currentPhase === "librarian" && i === 0) status = "completed";
          if (currentPhase === "mentor"    && i  <  2) status = "completed";
        }

        return {
          id:       `step-${i}`,
          type:     "roadmapNode",
          position: { x: 60, y: 40 + i * 110 },
          data: {
            title:      step.title,
            complexity: step.complexity,
            stepNumber: i + 1,
            status,
          },
        };
      }),
    [steps, currentPhase, usingDefault] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const edges: Edge[] = useMemo(
    () =>
      steps.slice(0, -1).map((_, i) => ({
        id:     `edge-${i}`,
        source: `step-${i}`,
        target: `step-${i + 1}`,
        style:  { stroke: "rgba(99,102,241,0.2)", strokeWidth: 1.5 },
      })),
    [steps.length] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <div className="relative h-full bg-[#080c14]">
      {/* Labels */}
      <div className="absolute left-4 top-4 z-10 flex flex-col gap-2">
        <div className="flex items-center gap-1.5 rounded-lg bg-black/40 px-3 py-1.5 text-xs text-slate-500 backdrop-blur">
          Roadmap
        </div>
        <div className="flex flex-col gap-1 rounded-lg bg-black/40 px-3 py-2 backdrop-blur">
          {["simple", "medium", "complex"].map((c) => (
            <div key={c} className="flex items-center gap-1.5">
              <div className={cn("h-1.5 w-1.5 rounded-full", getStyle(c).dot)} />
              <span className="text-[10px] capitalize text-slate-600">{c}</span>
            </div>
          ))}
        </div>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
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
          color="rgba(59,130,246,0.06)"
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}