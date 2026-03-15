/**
 * Utility helpers
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { formatDistanceToNow, format } from "date-fns";
import type { Phase, ProjectStatus } from "@/types";

/** Merge Tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format ISO date string to relative time ("3 hours ago") */
export function timeAgo(dateString: string): string {
  return formatDistanceToNow(new Date(dateString), { addSuffix: true });
}

/** Format ISO date string to readable date ("Feb 23, 2026") */
export function formatDate(dateString: string): string {
  return format(new Date(dateString), "MMM d, yyyy");
}

/** Map Phase enum to display label */
export const phaseLabels: Record<Phase, string> = {
  planner:   "Planner",
  librarian: "Librarian",
  mentor:    "Mentor",
};

/** Map Phase enum to description */
export const phaseDescriptions: Record<Phase, string> = {
  planner:   "Deconstructing your idea into a Technical Specification",
  librarian: "Gathering documentation and deep-linking official resources",
  mentor:    "Generating code scaffolds and guiding your implementation",
};

/** Map ProjectStatus to display label */
export const statusLabels: Record<ProjectStatus, string> = {
  draft:       "Draft",
  in_progress: "In Progress",
  completed:   "Completed",
};

/** Map ProjectStatus to Tailwind color classes */
export const statusColors: Record<ProjectStatus, string> = {
  draft:       "text-slate-400 bg-slate-400/10 border-slate-400/20",
  in_progress: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  completed:   "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
};

/** Phase order for workflow visualization */
export const phaseOrder: Phase[] = ["planner", "librarian", "mentor"];

/** Get the next phase in the workflow */
export function nextPhase(current: Phase): Phase | null {
  const idx = phaseOrder.indexOf(current);
  return idx < phaseOrder.length - 1 ? phaseOrder[idx + 1] : null;
}