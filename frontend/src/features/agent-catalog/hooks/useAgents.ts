'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import type { Agent, AgentType } from '@/domains/agent/entities';

interface RawAgent {
  id: string;
  name: string;
  slug: string;
  description: string;
  agent_type: AgentType;
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

interface UseAgentsOptions {
  type?: 'formal' | 'demo';
}

export function useAgents({ type }: UseAgentsOptions = {}) {
  const { data, isLoading, error } = useQuery<Agent[]>({
    queryKey: ['agents', type],
    queryFn: async () => {
      const params = type ? { agent_type: type } : {};
      const { data: raw } = await apiClient.get<RawAgent[]>('/api/v1/agents', { params });
      return raw.map(mapAgent);
    },
  });

  return {
    agents: data ?? [],
    isLoading,
    error,
  };
}
