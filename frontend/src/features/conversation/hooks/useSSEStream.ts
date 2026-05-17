'use client';

import { useCallback, useRef } from 'react';

interface SSECallbacks {
  onToken: (token: string) => void;
  onDisclaimer: (text: string) => void;
  onProgress: (progress: StreamProgress) => void;
  onEnd: (messageId: string, latencyMs: number) => void;
  onError: (code: string, message: string) => void;
  onStart: (messageId: string, agentId: string | null) => void;
}

export interface StreamProgress {
  stage: string;
  message: string;
  agent_id?: string | null;
  agent_name?: string | null;
  workflow_type?: string | null;
  artifacts?: StreamProgressArtifact[];
}

export interface StreamProgressArtifact {
  type: string;
  title: string;
  subtitle?: string | null;
  score?: number | null;
  content: string;
  document_id?: string | null;
  chunk_id?: string | null;
}

export function useSSEStream(baseUrl: string) {
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(
    async (
      conversationId: string,
      content: string,
      agentId: string | null,
      ragEnabled: boolean | null,
      callbacks: SSECallbacks
    ) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const token = typeof window !== 'undefined' ? window.__authToken : undefined;

      try {
        const response = await fetch(
          `${baseUrl}/api/v1/conversations/${conversationId}/messages`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              content,
              agent_id: agentId ?? undefined,
              rag_enabled: ragEnabled ?? undefined,
            }),
            signal: controller.signal,
            credentials: 'include',
          }
        );

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          callbacks.onError('http_error', err?.detail ?? `HTTP ${response.status}`);
          return;
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() ?? '';

          for (const part of parts) {
            const lines = part.trim().split('\n');
            let eventType = 'message';
            let data = '';
            for (const line of lines) {
              if (line.startsWith('event:')) eventType = line.slice(6).trim();
              if (line.startsWith('data:')) data = line.slice(5).trim();
            }
            if (!data) continue;
            try {
              const parsed = JSON.parse(data);
              if (eventType === 'start') callbacks.onStart(parsed.message_id, parsed.agent_id);
              else if (eventType === 'token') callbacks.onToken(parsed.token);
              else if (eventType === 'progress') callbacks.onProgress(parsed);
              else if (eventType === 'disclaimer') callbacks.onDisclaimer(parsed.text);
              else if (eventType === 'end') callbacks.onEnd(parsed.message_id, parsed.latency_ms);
              else if (eventType === 'error') callbacks.onError(parsed.code, parsed.message);
            } catch {
              // ignore malformed SSE data
            }
          }
        }
      } catch (err: any) {
        if (err?.name !== 'AbortError') {
          callbacks.onError('network_error', err?.message ?? '网络连接失败，请检查网络后重试');
        }
      }
    },
    [baseUrl]
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { stream, abort };
}
