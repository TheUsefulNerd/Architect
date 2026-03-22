/**
 * useChat Hook
 * Manages chat state and message sending via SSE streaming.
 * Populates docs and scaffolds store when respective agents complete.
 */
"use client";

import { useCallback } from "react";
import { chatApi, sessionsApi } from "@/lib/api";
import { useProjectStore } from "@/stores/useProjectStore";
import type { MessageResponse, Phase, RoadmapStep} from "@/types";

function normalisePhase(raw: string | undefined): Phase | null {
  if (!raw) return null;
  const val = raw.toLowerCase();
  if (val.includes("planner"))   return "planner";
  if (val.includes("librarian")) return "librarian";
  if (val.includes("mentor"))    return "mentor";
  return null;
}

export function useChat() {
  const sendMessage = useCallback(async (content: string) => {
    const { activeSession } = useProjectStore.getState();
    if (!activeSession) throw new Error("No active session");

    // Optimistically add user message
    const userMessage: MessageResponse = {
      id:         crypto.randomUUID(),
      session_id: activeSession.id,
      role:       "user",
      content,
      phase:      activeSession.current_phase,
      metadata:   {},
      created_at: new Date().toISOString(),
    };
    useProjectStore.getState().appendMessage(userMessage);
    useProjectStore.getState().setStreaming(true);
    useProjectStore.getState().clearStreamingContent();

    // Track which nodes have completed to fetch their data
    const completedNodes = new Set<string>();

    try {
      await chatApi.stream(
        { session_id: activeSession.id, message: content },

        // onChunk
        async (chunk, phase, node) => {
          useProjectStore.getState().appendStreamChunk(chunk);

          const normPhase = normalisePhase(phase);
          if (normPhase) {
            useProjectStore.getState().setCurrentPhase(normPhase);
          }

          // When a node completes, fetch its output data
          if (node && !completedNodes.has(node)) {
            completedNodes.add(node);

            if (node === "librarian") {
              // Fetch and store docs
              try {
                const docs = await sessionsApi.getDocLinks(activeSession.id);
                useProjectStore.getState().setDocLinks(docs);
                // Switch to docs tab to notify user
                useProjectStore.getState().setActiveTab("docs");
                // Switch back to chat after a moment
                setTimeout(() => {
                  useProjectStore.getState().setActiveTab("chat");
                }, 2000);
              } catch {
                // Silently fail — docs tab will just be empty
              }
            }

            if (node === "mentor") {
              // Fetch and store scaffolds
              try {
                const scaffolds = await sessionsApi.getScaffolds(activeSession.id);
                useProjectStore.getState().setScaffolds(scaffolds);
              } catch {
                // Silently fail — code tab will just be empty
              }
            }
          }
        },

        // onDone
        async () => {
          const { streamingContent, activeSession: session } =
            useProjectStore.getState();

          if (streamingContent) {
            const assistantMessage: MessageResponse = {
              id:         crypto.randomUUID(),
              session_id: session?.id ?? "",
              role:       "assistant",
              content:    streamingContent,
              phase:      session?.current_phase,
              metadata:   {},
              created_at: new Date().toISOString(),
            };
            useProjectStore.getState().appendMessage(assistantMessage);
            useProjectStore.getState().clearStreamingContent();
          }
          useProjectStore.getState().setStreaming(false);

          // After stream completes, fetch roadmap from persisted session
          if (session) {
            try {
              await new Promise(resolve => setTimeout(resolve, 500));
              const sessionData = await sessionsApi.getById(session.id);
              const graphState = sessionData?.metadata?.graph_state as Record<string, unknown> | undefined;
              const roadmap = (graphState?.roadmap as RoadmapStep[]) ?? [];
              if (roadmap.length > 0) {
                useProjectStore.getState().setRoadmap(roadmap);
              }
            } catch {
              // Silently fail
            }
          }
        },
      );
    } catch {
      try {
        const response = await chatApi.send({
          session_id: activeSession.id,
          message:    content,
        });
        const assistantMessage: MessageResponse = {
          id:         response.message_id,
          session_id: activeSession.id,
          role:       "assistant",
          content:    response.response,
          phase:      response.phase,
          metadata:   response.metadata,
          created_at: new Date().toISOString(),
        };
        useProjectStore.getState().appendMessage(assistantMessage);
        useProjectStore.getState().setCurrentPhase(response.phase);
      } finally {
        useProjectStore.getState().setStreaming(false);
      }
    }
  }, []);

  return { sendMessage };
}