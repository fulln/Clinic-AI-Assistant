'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import apiClient from '@/shared/api/client';
import { type StreamProgress, useSSEStream } from './useSSEStream';
import { ConversationDomainService } from '@/domains/conversation/services';
import type { Conversation, Locale, Message } from '@/domains/conversation/entities';
import { DEFAULT_LOCALE, normalizeLocale } from '@/shared/i18n/conversation';
import { useLocaleStore } from '@/shared/store/localeStore';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface StreamingState {
  isStreaming: boolean;
  streamingContent: string;
  streamingMessageId: string | null;
}

export function useConversation(initialConversationId?: string) {
  const siteLocale = useLocaleStore((state) => state.locale);
  const setSiteLocale = useLocaleStore((state) => state.setLocale);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [locale, setLocale] = useState<Locale>(siteLocale);
  const [streaming, setStreaming] = useState<StreamingState>({
    isStreaming: false,
    streamingContent: '',
    streamingMessageId: null,
  });
  const [progressSteps, setProgressSteps] = useState<StreamProgress[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { stream, abort } = useSSEStream(BASE_URL);
  const conversationIdRef = useRef<string | null>(initialConversationId ?? null);
  const streamingContentRef = useRef('');
  const progressStepsRef = useRef<StreamProgress[]>([]);
  const localeRef = useRef<Locale>(siteLocale);
  const sendingRef = useRef(false);

  const createConversation = useCallback(async (agentId?: string, nextLocale: Locale = localeRef.current) => {
    const { data } = await apiClient.post<any>('/api/v1/conversations', {
      agent_id: agentId ?? null,
      locale: nextLocale,
    });
    conversationIdRef.current = data.id;
    const resolvedLocale = normalizeLocale(data.locale ?? data.session?.locale ?? nextLocale);
    localeRef.current = resolvedLocale;
    setLocale(resolvedLocale);
    setSiteLocale(resolvedLocale);
    setConversation({
      id: data.id,
      title: data.title,
      session: {
        id: data.session?.id ?? data.session_id,
        activeAgentId: data.session?.activeAgentId ?? data.active_agent_id ?? undefined,
        ragEnabled: data.session?.ragEnabled ?? data.rag_enabled ?? false,
        locale: resolvedLocale,
      },
      messages: [],
    });
    return data;
  }, [setSiteLocale]);

  const loadConversation = useCallback(async (conversationId: string) => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<any>(`/api/v1/conversations/${conversationId}`);
      conversationIdRef.current = conversationId;
      const resolvedLocale = normalizeLocale(data.session?.locale);
      localeRef.current = resolvedLocale;
      setLocale(resolvedLocale);
      setSiteLocale(resolvedLocale);
      setConversation({
        id: data.id,
        title: data.title,
        session: {
          id: data.session.id,
          activeAgentId: data.session.active_agent_id ?? undefined,
          ragEnabled: data.session.rag_enabled ?? false,
          locale: resolvedLocale,
        },
        messages: [],
      });
      setMessages(
        data.messages.map((m: any) => ({
          id: m.id, role: m.role, content: m.content,
          agentId: m.agent_id,
          hasDisclaimer: m.has_disclaimer,
          createdAt: m.created_at,
          metadata: m.metadata ?? {},
          progressSteps: m.progress_steps ?? [],
        }))
      );
    } finally {
      setLoading(false);
    }
  }, [setSiteLocale]);

  const sendMessage = useCallback(
    async (content: string, agentId?: string, ragEnabled?: boolean) => {
      if (sendingRef.current) return;

      const activeLocale = localeRef.current;
      const validationError = ConversationDomainService.validateMessageContent(content, activeLocale);
      if (validationError) { setError(validationError); return; }
      setError(null);
      sendingRef.current = true;

      try {
        let convId = conversationIdRef.current;
        if (!convId) {
          const conv = await createConversation(agentId, activeLocale);
          convId = conv.id;
        }
        if (!convId) return;

        const userMsg: Message = {
          id: `temp-${Date.now()}`, role: 'user', content,
          hasDisclaimer: false,
          createdAt: new Date().toISOString(),
          metadata: { locale: activeLocale },
        };
        setMessages((prev) => [...prev, userMsg]);
        streamingContentRef.current = '';
        progressStepsRef.current = [];
        setProgressSteps([]);
        setStreaming({ isStreaming: true, streamingContent: '', streamingMessageId: null });

        await stream(convId, content, agentId ?? null, ragEnabled ?? null, activeLocale, {
          onStart: (messageId, _agentId, startLocale) => {
            localeRef.current = startLocale;
            setLocale(startLocale);
            setSiteLocale(startLocale);
            setStreaming((s) => ({ ...s, streamingMessageId: messageId }));
          },
          onToken: (token) => {
            streamingContentRef.current += token;
            setStreaming((s) => ({ ...s, streamingContent: s.streamingContent + token }));
          },
          onDisclaimer: (_text, disclaimerLocale) => {
            localeRef.current = disclaimerLocale;
            setLocale(disclaimerLocale);
            setSiteLocale(disclaimerLocale);
          },
          onProgress: (progress) => {
            progressStepsRef.current = [...progressStepsRef.current, progress];
            setProgressSteps(progressStepsRef.current);
          },
          onEnd: (messageId, _latencyMs, endLocale) => {
            const content = streamingContentRef.current;
            const assistantMsg: Message = {
              id: messageId, role: 'assistant', content,
              hasDisclaimer: true,
              createdAt: new Date().toISOString(),
              metadata: { locale: endLocale, disclaimer_locale: endLocale },
              progressSteps: progressStepsRef.current,
            };
            setMessages((prev) => {
              if (prev.some((msg) => msg.id === messageId)) return prev;
              return [...prev, assistantMsg];
            });
            localeRef.current = endLocale;
            setLocale(endLocale);
            setSiteLocale(endLocale);
            setConversation((current) => current ? {
              ...current,
              session: current.session ? { ...current.session, locale: endLocale } : undefined,
            } : current);
            streamingContentRef.current = '';
            progressStepsRef.current = [];
            setStreaming({ isStreaming: false, streamingContent: '', streamingMessageId: null });
          },
          onError: (_code, message, errorLocale) => {
            localeRef.current = errorLocale;
            setLocale(errorLocale);
            setSiteLocale(errorLocale);
            setError(message);
            progressStepsRef.current = [];
            setProgressSteps([]);
            setStreaming({ isStreaming: false, streamingContent: '', streamingMessageId: null });
          },
        });
      } finally {
        sendingRef.current = false;
      }
    },
    [stream, createConversation, setSiteLocale]
  );

  const switchAgent = useCallback(async (agentId: string) => {
    if (!conversationIdRef.current) return;
    await apiClient.patch(`/api/v1/conversations/${conversationIdRef.current}/session`, {
      active_agent_id: agentId,
    });
    setConversation((c) => c ? { ...c, session: { ...c.session!, activeAgentId: agentId } } : c);
  }, []);

  const switchLocale = useCallback(async (nextLocale: Locale) => {
    localeRef.current = nextLocale;
    setLocale(nextLocale);
    setSiteLocale(nextLocale);
    if (!conversationIdRef.current) {
      setConversation((current) => current ? {
        ...current,
        session: current.session ? { ...current.session, locale: nextLocale } : current.session,
      } : current);
      return;
    }
    const { data } = await apiClient.patch(`/api/v1/conversations/${conversationIdRef.current}/session`, {
      locale: nextLocale,
    });
    const resolvedLocale = normalizeLocale(data.locale ?? nextLocale);
    localeRef.current = resolvedLocale;
    setLocale(resolvedLocale);
    setSiteLocale(resolvedLocale);
    setConversation((current) => current ? {
      ...current,
      session: {
        ...(current.session ?? { id: data.id, ragEnabled: false, locale: resolvedLocale }),
        locale: resolvedLocale,
      },
    } : current);
  }, [setSiteLocale]);

  useEffect(() => {
    if (initialConversationId) loadConversation(initialConversationId);
  }, [initialConversationId, loadConversation]);

  useEffect(() => {
    if (!conversationIdRef.current) {
      localeRef.current = siteLocale;
      setLocale(siteLocale);
    }
  }, [siteLocale]);

  return {
    conversation,
    messages,
    locale,
    streaming,
    progressSteps,
    error,
    loading,
    sendMessage,
    switchAgent,
    switchLocale,
    abort,
    createConversation,
  };
}
