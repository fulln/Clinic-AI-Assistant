'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/shared/api/client';
import type { Agent, AgentEditPayload, AgentStatus } from '@/domains/agent/entities';

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
  system_prompt_en?: string | null;
  system_prompt_zh?: string | null;
  tools?: string[];
  max_tool_turns?: number;
  llm_model?: string | null;
  llm_temperature?: number | null;
  llm_max_tokens?: number | null;
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
    systemPromptEn: raw.system_prompt_en ?? null,
    systemPromptZh: raw.system_prompt_zh ?? null,
    tools: raw.tools ?? [],
    maxToolTurns: raw.max_tool_turns ?? 3,
    llmModel: raw.llm_model ?? null,
    llmTemperature: raw.llm_temperature ?? null,
    llmMaxTokens: raw.llm_max_tokens ?? null,
  };
}

function toApiPayload(agent: Agent, edits: AgentEditPayload) {
  return {
    name: edits.name,
    slug: agent.slug,
    description: edits.description,
    agent_type: edits.agentType,
    capabilities: agent.capabilities,
    allowed_roles: edits.allowedRoles,
    workflow_config: {},
    system_prompt_en: edits.systemPromptEn,
    system_prompt_zh: edits.systemPromptZh,
    tools: edits.tools,
    max_tool_turns: edits.maxToolTurns,
    llm_model: edits.llmModel,
    llm_temperature: edits.llmTemperature,
    llm_max_tokens: edits.llmMaxTokens,
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

  const restoreMutation = useMutation({
    mutationFn: async (agentId: string) => {
      const { data } = await apiClient.post<RawAgent>(`/api/v1/agents/${agentId}/restore`);
      return mapAgent(data);
    },
    onSuccess: refresh,
  });

  const updateMutation = useMutation({
    mutationFn: async ({ agent, edits }: { agent: Agent; edits: AgentEditPayload }) => {
      const { data } = await apiClient.patch<RawAgent>(
        `/api/v1/agents/${agent.id}`,
        toApiPayload(agent, edits),
      );
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
    restoreAgent: restoreMutation.mutateAsync,
    updateAgent: updateMutation.mutateAsync,
    isPublishing: publishMutation.isPending,
    isArchiving: archiveMutation.isPending,
    isRestoring: restoreMutation.isPending,
    isUpdating: updateMutation.isPending,
  };
}
