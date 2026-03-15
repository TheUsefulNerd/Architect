/**
 * Project Store (Zustand)
 * Global state for the active project, session, and phase.
 */
import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  ProjectResponse,
  SessionResponse,
  Phase,
  MessageResponse,
} from "@/types";

interface ProjectState {
  // Active project & session
  activeProject: ProjectResponse | null;
  activeSession: SessionResponse | null;
  currentPhase: Phase;

  // Chat messages for the active session
  messages: MessageResponse[];
  isStreaming: boolean;
  streamingContent: string;

  // Actions
  setActiveProject: (project: ProjectResponse | null) => void;
  setActiveSession: (session: SessionResponse | null) => void;
  setCurrentPhase: (phase: Phase) => void;
  setMessages: (messages: MessageResponse[]) => void;
  appendMessage: (message: MessageResponse) => void;
  setStreaming: (streaming: boolean) => void;
  appendStreamChunk: (chunk: string) => void;
  clearStreamingContent: () => void;
  reset: () => void;
}

const initialState = {
  activeProject:    null,
  activeSession:    null,
  currentPhase:     "planner" as Phase,
  messages:         [],
  isStreaming:      false,
  streamingContent: "",
};

export const useProjectStore = create<ProjectState>()(
  devtools(
    (set) => ({
      ...initialState,

      setActiveProject: (project) =>
        set({ activeProject: project }, false, "setActiveProject"),

      setActiveSession: (session) =>
        set(
          {
            activeSession: session,
            currentPhase: session?.current_phase ?? "planner",
          },
          false,
          "setActiveSession"
        ),

      setCurrentPhase: (phase) =>
        set({ currentPhase: phase }, false, "setCurrentPhase"),

      setMessages: (messages) =>
        set({ messages }, false, "setMessages"),

      appendMessage: (message) =>
        set(
          (state) => ({ messages: [...state.messages, message] }),
          false,
          "appendMessage"
        ),

      setStreaming: (streaming) =>
        set({ isStreaming: streaming }, false, "setStreaming"),

      appendStreamChunk: (chunk) =>
        set(
          (state) => ({ streamingContent: state.streamingContent + chunk }),
          false,
          "appendStreamChunk"
        ),

      clearStreamingContent: () =>
        set({ streamingContent: "" }, false, "clearStreamingContent"),

      reset: () => set(initialState, false, "reset"),
    }),
    { name: "ArchitectProjectStore" }
  )
);