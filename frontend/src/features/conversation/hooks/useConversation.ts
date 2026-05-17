'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import apiClient from '@/shared/api/client';
import { useSSEStream } from './useSSEStream';
import { ConversationDomainService } from '@/domains/conversation/services';
import type { Conversation, Message } from '@/domains/conversation/entities';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface StreamingState {
  isStreaming: boolean;
  streamingContent: string;
  streamingMessageId: string | null;
}

export function useConversation(initialConversationId?: string) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState<StreamingState>({
    isStreaming: false,
    streamingContent: '',
    streamingMessageId: null,
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { stream, abort } = useSSEStream(BASE_URL);
  const conversationIdRef = useRef<string | null>(initialConversationId ?? null);

  const createConversation = useCallback(async (agentId?: string) => {
    const { data } = await apiClient.post<Conversation>('/api/v1/conversations', {
      agent_id: agentId ?? null,
    });
    conversationIdRef.current = data.id;
    setConversation(data);
    return data;
  }, []);

  const loadConversation = useCallback(async (conversationId: string) => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<any>(`/api/v1/conversations/${conversationId}`);
      conversationIdRef.current = conversationId;
      setConversation({ id: data.id, title: data.title, session: data.session, messages: [] });
      setMessages(
        data.messages.map((m: any) => ({
          id: m.id, role: m.role, content: m.content,
          agentId: m.agent_id, hasDisclaimer: m.has_disclaimer, createdAt: m.created_at,
        }))
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, agentId?: string, ragEnabled?: boolean) => {
      const validationError = ConversationDomainService.validateMessageContent(content);
      if (validationError) { setError(validationError); return; }
      setError(null);

      let convId = conversationIdRef.current;
      if (!convId) {
        const conv = await createConversation(agentId);
        convId = conv.id;
      }

      const userMsg: Message = {
        id: `temp-${Date.now()}`, role: 'user', content,
        hasDisclaimer: false, createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setStreaming({ isStreaming: true, streamingContent: '', streamingMessageId: null });

      await stream(convId, content, agentId ?? null, ragEnabled ?? null, {
        onStart: (messageId) =>
          setStreaming((s) => ({ ...s, streamingMessageId: messageId })),
        onToken: (token) =>
          setStreaming((s) => ({ ...s, streamingContent: s.streamingContent + token })),
        onDisclaimer: () => {},
        onEnd: (messageId) => {
          setStreaming((s) => {
            const assistantMsg: Message = {
              id: messageId, role: 'assistant', content: s.streamingContent,
              hasDisclaimer: s.streamingContent.includes('本内容仅供辅助参考'),
              createdAt: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
            return { isStreaming: false, streamingContent: '', streamingMessageId: null };
          });
        },
        onError: (code, message) => {
          setError(message);
          setStreaming({ isStreaming: false, streamingContent: '', streamingMessageId: null });
        },
      });
    },
    [stream, createConversation]
  );

  const switchAgent = useCallback(async (agentId: string) => {
    if (!conversationIdRef.current) return;
    await apiClient.patch(`/api/v1/conversations/${conversationIdRef.current}/session`, {
      active_agent_id: agentId,
    });
    setConversation((c) => c ? { ...c, session: { ...c.session!, activeAgentId: agentId } } : c);
  }, []);

  useEffect(() => {
    if (initialConversationId) loadConversation(initialConversationId);
  }, [initialConversationId, loadConversation]);

  return { conversation, messages, streaming, error, loading, sendMessage, switchAgent, abort, createConversation };
}
