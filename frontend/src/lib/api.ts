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

// ─── Supabase singleton client ────────────────────────────────────────────────
let supabaseClient: ReturnType<typeof createClient> | null = null;

function getSupabaseClient() {
  if (!supabaseClient) {
    supabaseClient = createClient();
  }
  return supabaseClient;
}

// ─── Axios instance ───────────────────────────────────────────────────────────

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// Attach Supabase JWT to every request (reuse client)
// Attach Supabase JWT and user ID to every request
apiClient.interceptors.request.use(async (config) => {
  try {
    const supabase = getSupabaseClient();
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      config.headers.Authorization = `Bearer ${data.session.access_token}`;
    }
    if (data.session?.user?.id) {
      config.headers["X-User-Id"] = data.session.user.id;  // <-- add this
    }
  } catch (error) {
    console.debug("Failed to attach auth token:", error);
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
    apiClient
      .get<{ success: boolean; projects: ProjectResponse[] }>("/api/projects")
      .then((r) => r.data.projects ?? []),

  create: (data: ProjectCreateRequest) =>
    apiClient
      .post<{ success: boolean; project: ProjectResponse }>("/api/projects", data)
      .then((r) => r.data.project),

  get: (id: string) =>
    apiClient
      .get<{ success: boolean; project: ProjectResponse }>(`/api/projects/${id}`)
      .then((r) => r.data.project),

  delete: (id: string) =>
    apiClient.delete(`/api/projects/${id}`).then((r) => r.data),
};

// ─── Sessions ─────────────────────────────────────────────────────────────────

export const sessionsApi = {
  create: (data: SessionCreateRequest) =>
    apiClient
      .post<{ success: boolean; session: SessionResponse }>("/api/sessions", data)
      .then((r) => r.data.session),

  getByProject: (projectId: string) =>
    apiClient
      .get<{ success: boolean; session: SessionResponse }>(
        `/api/sessions?project_id=${projectId}`
      )
      .then((r) => r.data.session),

  getById: (sessionId: string) =>
    apiClient
      .get<{ success: boolean; session: SessionResponse }>(
        `/api/sessions/${sessionId}`
      )
      .then((r) => r.data.session),

  getMessages: (sessionId: string) =>
    apiClient
      .get<{ success: boolean; messages: MessageResponse[] }>(
        `/api/sessions/${sessionId}/messages`
      )
      .then((r) => r.data.messages ?? []),

  getTechnicalSpec: (sessionId: string) =>
    apiClient
      .get<{ success: boolean; spec: TechnicalSpecResponse }>(
        `/api/sessions/${sessionId}/spec`
      )
      .then((r) => r.data.spec),

  getDocLinks: (sessionId: string) =>
    apiClient
      .get<{ success: boolean; docs: DocumentationLinkResponse[] }>(
        `/api/sessions/${sessionId}/docs`
      )
      .then((r) => r.data.docs ?? []),

  getScaffolds: (sessionId: string) =>
    apiClient
      .get<{ success: boolean; scaffolds: CodeScaffoldResponse[] }>(
        `/api/sessions/${sessionId}/scaffolds`
      )
      .then((r) => r.data.scaffolds ?? []),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────

export const chatApi = {
  send: (data: ChatRequest) =>
    apiClient
      .post<ChatResponse>("/api/chat", data)
      .then((r) => r.data),

  stream: async (
    data: ChatRequest,
    onChunk: (chunk: string, phase?: string, node?: string) => void,    onDone: () => Promise<void> | void
  ) => {
    const supabase = getSupabaseClient();
    const { data: authData } = await supabase.auth.getSession();
    const token = authData.session?.access_token;

    const response = await fetch(
      `${BASE_URL}/api/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Stream request failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) throw new Error("No response body");

    while (true) {
      const { done, value } = await reader.read();
      if (done) { await onDone(); break; }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const parsed = JSON.parse(line.slice(6));

          if (parsed.node === "done") {
            await onDone();
            return;
          }
          if (parsed.node === "error") {
            throw new Error(parsed.content);
 }
          if (parsed.content) {
            onChunk(parsed.content, parsed.phase, parsed.node);
          }
        } catch {
          // skip malformed chunks
        }
      }
    }
  },
};