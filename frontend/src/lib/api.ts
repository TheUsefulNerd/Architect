/**
 * Architect API Client
 * Axios instance pre-configured for the FastAPI backend.
 */
import axios, { AxiosError } from "axios";
import { createClient } from "@/lib/supabase/client";
import type {
  ChatRequest,
  ChatResponse,
  ProjectCreateRequest,
  ProjectResponse,
  SessionCreateRequest,
  SessionResponse,
  MessageResponse,
  TechnicalSpecResponse,
  CodeScaffoldResponse,
  DocumentationLinkResponse,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ─── Axios instance ───────────────────────────────────────────────────────────

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Attach Supabase JWT to every request
apiClient.interceptors.request.use(async (config) => {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  if (data.session?.access_token) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

// Normalise errors
apiClient.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    const message =
      (error.response?.data as { detail?: string })?.detail ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

// ─── Projects ─────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: () =>
    apiClient.get<ProjectResponse[]>("/api/projects").then((r) => r.data),

  create: (data: ProjectCreateRequest) =>
    apiClient.post<ProjectResponse>("/api/projects", data).then((r) => r.data),

  get: (id: string) =>
    apiClient.get<ProjectResponse>(`/api/projects/${id}`).then((r) => r.data),

  delete: (id: string) =>
    apiClient.delete(`/api/projects/${id}`).then((r) => r.data),
};

// ─── Sessions ─────────────────────────────────────────────────────────────────

export const sessionsApi = {
  create: (data: SessionCreateRequest) =>
    apiClient.post<SessionResponse>("/api/sessions", data).then((r) => r.data),

  getByProject: (projectId: string) =>
    apiClient
      .get<SessionResponse>(`/api/sessions?project_id=${projectId}`)
      .then((r) => r.data),

  getMessages: (sessionId: string) =>
    apiClient
      .get<MessageResponse[]>(`/api/sessions/${sessionId}/messages`)
      .then((r) => r.data),

  getTechnicalSpec: (sessionId: string) =>
    apiClient
      .get<TechnicalSpecResponse>(`/api/sessions/${sessionId}/technical-spec`)
      .then((r) => r.data),

  getDocLinks: (sessionId: string) =>
    apiClient
      .get<DocumentationLinkResponse[]>(
        `/api/sessions/${sessionId}/documentation-links`
      )
      .then((r) => r.data),

  getScaffolds: (sessionId: string) =>
    apiClient
      .get<CodeScaffoldResponse[]>(`/api/sessions/${sessionId}/scaffolds`)
      .then((r) => r.data),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────

export const chatApi = {
  send: (data: ChatRequest) =>
    apiClient.post<ChatResponse>("/api/chat", data).then((r) => r.data),
};

// ─── WebSocket ────────────────────────────────────────────────────────────────

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function createChatWebSocket(
  sessionId: string,
  token: string
): WebSocket {
  const url = `${WS_URL}/api/ws/chat/${sessionId}?token=${token}`;
  return new WebSocket(url);
}