'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient } from '@/shared/api/client';
import type { Agent } from '@/domains/agent/entities';
import { AgentTypeBadge } from '@/features/agent-catalog/components/AgentTypeBadge';
import { ConversationPanel } from '@/features/conversation/components/ConversationPanel';

interface RawAgent {
  id: string;
  name: string;
  slug: string;
  description: string;
  agent_type: Agent['agentType'];
  capabilities: string[];
  allowed_roles: string[];
  status: Agent['status'];
  version?: string;
}

function mapAgent(raw: RawAgent): Agent {
  return {
    id: raw.id,
    name: raw.name,
    slug: raw.slug,
    description: raw.description,
    agentType: raw.agent_type,
    capabilities: raw.capabilities,
    allowedRoles: raw.allowed_roles,
    status: raw.status,
    version: raw.version,
  };
}

export default function AgentDetailPage() {
  const params = useParams<{ agentId: string }>();
  const agentId = params.agentId;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loadingAgent, setLoadingAgent] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;

    let cancelled = false;

    async function init() {
      try {
        const [agentRes, convRes] = await Promise.all([
          apiClient.get<RawAgent>(`/api/v1/agents/${agentId}`),
          apiClient.post<{ id: string }>('/api/v1/conversations', { agent_id: agentId }),
        ]);

        if (!cancelled) {
          setAgent(mapAgent(agentRes.data));
          setConversationId(convRes.data.id);
        }
      } catch {
        if (!cancelled) setError('加载智能体信息失败，请稍后重试。');
      } finally {
        if (!cancelled) setLoadingAgent(false);
      }
    }

    init();

    return () => {
      cancelled = true;
    };
  }, [agentId]);

  if (loadingAgent) {
    return (
      <div className="flex h-full items-center justify-center py-20">
        <svg
          className="h-8 w-8 animate-spin text-blue-500"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-label="加载中"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? '智能体不存在。'}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Agent header */}
      <div className="border-b border-gray-200 bg-white px-6 py-5">
        <div className="flex flex-wrap items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900 truncate">{agent.name}</h1>
              <AgentTypeBadge agentType={agent.agentType} />
              {agent.version && (
                <span className="text-xs text-gray-400">v{agent.version}</span>
              )}
            </div>
            <p className="mt-1 text-sm text-gray-500">{agent.description}</p>
          </div>
        </div>

        {agent.capabilities.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {agent.capabilities.map((cap) => (
              <span
                key={cap}
                className="inline-block rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
              >
                {cap}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Conversation panel */}
      <div className="min-h-0 flex-1">
        {conversationId ? (
          <ConversationPanel agentId={agentId} conversationId={conversationId} />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            正在初始化对话…
          </div>
        )}
      </div>
    </div>
  );
}
