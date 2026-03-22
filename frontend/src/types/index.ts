/**
 * Architect Frontend - Core Type Definitions
 * Mirrors the Pydantic schemas from the FastAPI backend (schemas.py)
 */

// ─── Enums ────────────────────────────────────────────────────────────────────

export type ProjectStatus = "draft" | "in_progress" | "completed";
export type Phase = "planner" | "librarian" | "mentor";
export type MessageRole = "user" | "assistant" | "system";
export type LLMProvider = "gemini" | "groq";

// ─── API Request Types ────────────────────────────────────────────────────────

export interface ProjectCreateRequest {
  name: string;
  description?: string;
}

export interface SessionCreateRequest {
  project_id: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  phase?: Phase;
}

// ─── API Response Types ───────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectResponse {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface SessionResponse {
  id: string;
  project_id: string;
  current_phase: Phase;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  phase?: Phase;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface TechnicalSpecResponse {
  id: string;
  session_id: string;
  requirements?: string;
  architecture?: string;
  tech_stack: Record<string, string[]>;
  version: number;
  created_at: string;
}

export interface DocumentationLinkResponse {
  id: string;
  session_id: string;
  tech_name: string;
  doc_url: string;
  scraped_content?: string;
  relevance_score?: number;
  created_at: string;
}

export interface CodeScaffoldResponse {
  id: string;
  session_id: string;
  file_path: string;
  content: string;
  hints: string[];
  completed: boolean;
  created_at: string;
}

// ─── Agent Output Types ───────────────────────────────────────────────────────

export interface PlannerOutput {
  requirements: string;
  architecture: string;
  tech_stack: Record<string, string[]>;
  success: boolean;
  error_message?: string;
}

export interface LibrarianOutput {
  documentation_links: Array<Record<string, unknown>>;
  tech_identified: string[];
  success: boolean;
  error_message?: string;
}

export interface MentorOutput {
  scaffolds: Array<Record<string, unknown>>;
  implementation_hints: string[];
  success: boolean;
  error_message?: string;
}

export interface ChatResponse {
  session_id: string;
  message_id: string;
  response: string;
  phase: Phase;
  metadata: Record<string, unknown>;
  planner_output?: PlannerOutput;
  librarian_output?: LibrarianOutput;
  mentor_output?: MentorOutput;
}

// ─── Streaming Types ──────────────────────────────────────────────────────────

export type StreamChunkType = "text" | "phase_change" | "metadata" | "error" | "done";

export interface StreamChunk {
  type: StreamChunkType;
  content: unknown;
  timestamp: string;
}

// ─── React Flow Node Types ────────────────────────────────────────────────────

export type WorkflowNodeType = "phase" | "agent" | "output";

export interface WorkflowNodeData {
  label: string;
  phase: Phase;
  status: "idle" | "active" | "completed" | "error";
  description?: string;
  icon?: string;
}

// ─── UI / App State ───────────────────────────────────────────────────────────

export interface AppUser {
  id: string;
  email: string;
  avatarUrl?: string;
  fullName?: string;
}

// ─── Roadmap Types ────────────────────────────────────────────────────────────

export type RoadmapComplexity = "simple" | "medium" | "complex";

export interface RoadmapStep {
  title: string;
  complexity: RoadmapComplexity;
  completed?: boolean;
}

// ─── Tab Types ────────────────────────────────────────────────────────────────

export type WorkspaceTab = "chat" | "docs" | "code";