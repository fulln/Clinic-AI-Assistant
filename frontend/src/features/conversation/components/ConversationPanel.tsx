'use client';

import { useEffect, useState } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { AgentSelector } from './AgentSelector';
import { useConversation } from '@/features/conversation/hooks/useConversation';
import { t } from '@/shared/i18n/conversation';
import { useLocaleStore } from '@/shared/store/localeStore';

interface ConversationPanelProps {
  /** Pre-bind to a specific agent (demo mode). */
  agentId?: string;
  conversationId?: string;
}

export function ConversationPanel({ agentId: initialAgentId, conversationId }: ConversationPanelProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(initialAgentId ?? null);
  const siteLocale = useLocaleStore((state) => state.locale);

  const {
    conversation,
    messages,
    locale,
    streaming,
    progressSteps,
    error,
    sendMessage,
    switchAgent,
    switchLocale,
  } = useConversation(conversationId);
  const copy = t(locale);

  useEffect(() => {
    if (!initialAgentId && conversation?.session?.activeAgentId) {
      setSelectedAgentId(conversation.session.activeAgentId);
    }
  }, [conversation?.session?.activeAgentId, initialAgentId]);

  const handleAgentChange = async (id: string) => {
    setSelectedAgentId(id);
    await switchAgent(id);
  };

  const handleSend = (content: string) => {
    sendMessage(content, selectedAgentId ?? undefined);
  };

  useEffect(() => {
    if (siteLocale !== locale && !streaming.isStreaming) {
      void switchLocale(siteLocale);
    }
  }, [locale, siteLocale, streaming.isStreaming, switchLocale]);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-3 border-b border-slate-200 bg-white/80 px-5 py-4">
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{copy.currentAgent}</span>
        <AgentSelector
          value={selectedAgentId}
          onChange={handleAgentChange}
          disabled={streaming.isStreaming || !!initialAgentId}
          locale={locale}
        />
      </div>

      <MessageList
        locale={locale}
        messages={messages}
        streamingContent={streaming.isStreaming ? streaming.streamingContent : undefined}
        isStreaming={streaming.isStreaming}
        progressSteps={progressSteps}
      />

      {error && (
        <div className="mx-5 mb-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
          {error}
        </div>
      )}

      <MessageInput onSend={handleSend} locale={locale} />
    </div>
  );
}
