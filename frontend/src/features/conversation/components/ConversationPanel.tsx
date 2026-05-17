'use client';

import { useState } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { AgentSelector } from './AgentSelector';
import { useConversation } from '@/features/conversation/hooks/useConversation';

interface ConversationPanelProps {
  /** Pre-bind to a specific agent (demo mode). */
  agentId?: string;
  conversationId?: string;
}

export function ConversationPanel({ agentId: initialAgentId, conversationId }: ConversationPanelProps) {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(initialAgentId ?? null);

  const { messages, streaming, progressSteps, error, sendMessage, switchAgent } = useConversation(conversationId);

  const handleAgentChange = async (id: string) => {
    setSelectedAgentId(id);
    if (conversationId) await switchAgent(id);
  };

  const handleSend = (content: string) => {
    sendMessage(content, selectedAgentId ?? undefined);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-gray-200 bg-white px-4 py-3">
        <span className="text-sm font-medium text-gray-700">当前智能体</span>
        <AgentSelector
          value={selectedAgentId}
          onChange={handleAgentChange}
          disabled={streaming.isStreaming || !!initialAgentId}
        />
      </div>

      <MessageList
        messages={messages}
        streamingContent={streaming.isStreaming ? streaming.streamingContent : undefined}
        isStreaming={streaming.isStreaming}
        progressSteps={progressSteps}
      />

      {error && (
        <div className="mx-4 mb-2 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      )}

      <MessageInput onSend={handleSend} disabled={streaming.isStreaming} />
    </div>
  );
}
