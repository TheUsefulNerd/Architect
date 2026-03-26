/**
 * useChat Hook
 * Manages chat state and message sending via SSE streaming.
 * Each agent node produces a separate message bubble immediately.
 */
"use client";

import { useCallback } from "react";
import { chatApi, sessionsApi } from "@/lib/api";
import { useProjectStore } from "@/stores/useProjectStore";
import type { MessageResponse, Phase, RoadmapStep } from "@/types";

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

    // Per-node tracking
    let currentNode = "";
    let currentNodeContent = "";
    let currentPhase: Phase = activeSession.current_phase;

    const finaliseCurrentNode = () => {
      if (currentNodeContent.trim()) {
        const msg: MessageResponse = {
          id:         crypto.randomUUID(),
          session_id: activeSession.id,
          role:       "assistant",
          content:    currentNodeContent,
          phase:      currentPhase,
          metadata:   {},
          created_at: new Date().toISOString(),
        };
        useProjectStore.getState().appendMessage(msg);
        useProjectStore.getState().clearStreamingContent();
        currentNodeContent = "";
      }
    };

    try {
      await chatApi.stream(
        { session_id: activeSession.id, message: content },

        // onChunk
        async (chunk, phase, node) => {
          const normPhase = normalisePhase(phase);
          if (normPhase) {
            currentPhase = normPhase;
            useProjectStore.getState().setCurrentPhase(normPhase);
          }

          // Node changed — finalise previous node's message
          // Set currentNode on first chunk if not set
          if (!currentNode && node) {
            currentNode = node;
          }

          // Node changed — finalise previous node's message
          if (node && node !== currentNode && node !== "done") {
            finaliseCurrentNode();
            currentNode = node;
          }

          // Accumulate content and update streaming bubble
          if (chunk) {
            currentNodeContent += chunk;
            useProjectStore.getState().clearStreamingContent();
            useProjectStore.getState().appendStreamChunk(currentNodeContent);
          }
        },

        // onDone
        async () => {
          // Finalise the last node's message
          finaliseCurrentNode();
          useProjectStore.getState().setStreaming(false);

          // After everything completes — fetch roadmap and any remaining data
          if (activeSession) {
            try {
              await new Promise(resolve => setTimeout(resolve, 800));

              const [sessionData, docs, scaffolds] = await Promise.all([
                sessionsApi.getById(activeSession.id),
                sessionsApi.getDocLinks(activeSession.id),
                sessionsApi.getScaffolds(activeSession.id),
              ]);

              // Update roadmap
              const graphState = sessionData?.metadata?.graph_state as Record<string, unknown> | undefined;
              const roadmap = (graphState?.roadmap as RoadmapStep[]) ?? [];
              if (roadmap.length > 0) {
                useProjectStore.getState().setRoadmap(roadmap);
              }

              // Update docs if not already set
              if (docs.length > 0) {
                useProjectStore.getState().setDocLinks(docs);
              }

              // Update scaffolds if not already set
              if (scaffolds.length > 0) {
                useProjectStore.getState().setScaffolds(scaffolds);
              }
            } catch {
              // silently fail
            }
          }
        }
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