/**
 * useChat Hook
 * Manages chat state, message sending, and WebSocket streaming.
 */
"use client";

import { useCallback, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { chatApi, createChatWebSocket } from "@/lib/api";
import { useProjectStore } from "@/stores/useProjectStore";
import type { ChatRequest, MessageResponse } from "@/types";

export function useChat() {
  const wsRef = useRef<WebSocket | null>(null);
  const supabase = createClient();

  const sendMessage = useCallback(async (content: string) => {
    const { activeSession } = useProjectStore.getState();
    if (!activeSession) throw new Error("No active session");

    // Optimistically add the user message
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

    try {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token;

      if (token) {
        await streamMessage(activeSession.id, content, token);
      } else {
        await restMessage({ session_id: activeSession.id, message: content });
      }
    } catch {
      // Fallback to REST if WebSocket fails
      await restMessage({ session_id: activeSession.id, message: content });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const streamMessage = async (
    sessionId: string,
    content: string,
    token: string
  ) => {
    return new Promise<void>((resolve, reject) => {
      const ws = createChatWebSocket(sessionId, token);
      wsRef.current = ws;
      useProjectStore.getState().setStreaming(true);
      useProjectStore.getState().clearStreamingContent();

      ws.onopen = () => {
        ws.send(JSON.stringify({ message: content }));
      };

      ws.onmessage = (event) => {
        try {
          const chunk = JSON.parse(event.data);
          if (chunk.type === "text") {
            useProjectStore.getState().appendStreamChunk(chunk.content as string);
          } else if (chunk.type === "phase_change") {
            useProjectStore.getState().setCurrentPhase(chunk.content as never);
          } else if (chunk.type === "done") {
            finaliseStream();
            resolve();
          } else if (chunk.type === "error") {
            reject(new Error(chunk.content as string));
          }
        } catch {
          useProjectStore.getState().appendStreamChunk(event.data as string);
        }
      };

      ws.onerror = () => reject(new Error("WebSocket error"));
      ws.onclose = () => {
        finaliseStream();
        resolve();
      };
    });
  };

  const finaliseStream = () => {
    const { streamingContent, activeSession } = useProjectStore.getState();
    if (streamingContent) {
      const assistantMessage: MessageResponse = {
        id:         crypto.randomUUID(),
        session_id: activeSession?.id ?? "",
        role:       "assistant",
        content:    streamingContent,
        phase:      activeSession?.current_phase,
        metadata:   {},
        created_at: new Date().toISOString(),
      };
      useProjectStore.getState().appendMessage(assistantMessage);
      useProjectStore.getState().clearStreamingContent();
    }
    useProjectStore.getState().setStreaming(false);
  };

  const restMessage = async (data: ChatRequest) => {
    useProjectStore.getState().setStreaming(true);
    try {
      const response = await chatApi.send(data);
      const assistantMessage: MessageResponse = {
        id:         response.message_id,
        session_id: data.session_id,
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
  };

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  return { sendMessage, disconnect };
}