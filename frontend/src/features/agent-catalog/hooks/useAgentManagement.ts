'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import type { Agent, AgentStatus } from '@/domains/agent/entities';

interface RawAgent {
  id: string;
  name: string;
  slug: string;
  description: string;
  agent_type: Agent['agentType'];
  capabilities: string[];
  allowed_roles: string[];
  status: AgentStatus;
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

export function useAgentManagement() {
  const queryClient = useQueryClient();

  const query = useQuery<Agent[]>({
    queryKey: ['agent-management'],
    queryFn: async () => {
      const { data } = await apiClient.get<RawAgent[]>('/api/v1/agents', {
        params: { include_all: true },
      });
      return data.map(mapAgent);
    },
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['agent-management'] });

  const publishMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const { data } = await apiClient.post<RawAgent>(`/api/v1/agents/${agentId}/publish`);
      return mapAgent(data);
    },
    onSuccess: refresh,
  });

  const archiveMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const { data } = await apiClient.post<RawAgent>(`/api/v1/agents/${agentId}/archive`);
      return mapAgent(data);
    },
    onSuccess: refresh,
  });

  return {
    agents: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    publishAgent: publishMutation.mutateAsync,
    archiveAgent: archiveMutation.mutateAsync,
    isPublishing: publishMutation.isPending,
    isArchiving: archiveMutation.isPending,
  };
}
