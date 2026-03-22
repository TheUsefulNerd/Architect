/**
 * PhaseIndicator
 * Shows the current agent phase as a progress stepper in the header.
 */
"use client";

import { Cpu, BookOpen, Code2, Check } from "lucide-react";
import { useProjectStore } from "@/stores/useProjectStore";
import { cn } from "@/lib/utils";
import type { Phase } from "@/types";

const phases: { id: Phase; label: string; icon: React.ElementType }[] = [
  { id: "planner",   label: "Planner",   icon: Cpu      },
  { id: "librarian", label: "Librarian", icon: BookOpen },
  { id: "mentor",    label: "Mentor",    icon: Code2    },
];

export function PhaseIndicator() {
  const currentPhase = useProjectStore((s) => s.currentPhase);
  const currentIdx   = phases.findIndex((p) => p.id === currentPhase);

  return (
    <div className="flex items-center gap-1">
      {phases.map((phase, i) => {
        const isCompleted = i < currentIdx;
        const isActive    = i === currentIdx;
        const Icon        = phase.icon;

        return (
          <div key={phase.id} className="flex items-center gap-1">
            <div
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs transition",
                isActive    && "bg-indigo-500/15 text-indigo-400 ring-1 ring-indigo-500/30",
                isCompleted && "text-emerald-400",
                !isActive && !isCompleted && "text-slate-600"
              )}
            >
              {isCompleted ? (
                <Check className="h-3 w-3" />
              ) : (
                <Icon className="h-3 w-3" />
              )}
              <span className="hidden sm:inline">{phase.label}</span>
            </div>

            {i < phases.length - 1 && (
              <div
                className={cn(
                  "h-px w-4 transition",
                  i < currentIdx ? "bg-emerald-400/40" : "bg-white/8"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}