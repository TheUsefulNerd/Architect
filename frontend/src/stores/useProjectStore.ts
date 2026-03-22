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

import type {
  ProjectResponse,
  SessionResponse,
  Phase,
  MessageResponse,
  RoadmapStep,
  WorkspaceTab,
} from "@/types";
import type {
  DocumentationLinkResponse,
  CodeScaffoldResponse,
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
  // Roadmap
  roadmap: RoadmapStep[];

  // Docs from Librarian
  docLinks: DocumentationLinkResponse[];

  // Code scaffolds from Mentor
  scaffolds: CodeScaffoldResponse[];

  // Active workspace tab
  activeTab: WorkspaceTab;

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
  setRoadmap:    (roadmap: RoadmapStep[]) => void;
  setDocLinks:   (docs: DocumentationLinkResponse[]) => void;
  setScaffolds:  (scaffolds: CodeScaffoldResponse[]) => void;
  setActiveTab:  (tab: WorkspaceTab) => void;
}

const initialState = {
  activeProject:    null,
  activeSession:    null,
  currentPhase:     "planner" as Phase,
  messages:         [],
  isStreaming:      false,
  streamingContent: "",
  roadmap:    [],
  docLinks:   [],
  scaffolds:  [],
  activeTab:  "chat" as WorkspaceTab,
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

      setRoadmap: (roadmap) =>
        set({ roadmap }, false, "setRoadmap"),

      setDocLinks: (docs) =>
        set({ docLinks: docs }, false, "setDocLinks"),

      setScaffolds: (scaffolds) =>
        set({ scaffolds }, false, "setScaffolds"),

      setActiveTab: (tab) =>
        set({ activeTab: tab }, false, "setActiveTab"),
    }),
    {
      name: "ArchitectProjectStore",
      // Disable devtools history in production to prevent memory buildup
      // Also limit history in dev to prevent crashes from high-frequency updates (streaming)
      enabled: process.env.NODE_ENV === "development",
      limit: process.env.NODE_ENV === "development" ? 25 : 1, // Keep only recent actions
    }
  )
);