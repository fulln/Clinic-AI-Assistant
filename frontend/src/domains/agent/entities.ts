export type AgentStatus = 'draft' | 'published' | 'archived';
export type AgentType = 'formal' | 'demo';

export interface Agent {
  id: string;
  name: string;
  slug: string;
  description: string;
  agentType: AgentType;
  capabilities: string[];
  allowedRoles: string[];
  status: AgentStatus;
  version?: string;
  systemPromptEn?: string | null;
  systemPromptZh?: string | null;
  tools: string[];
  maxToolTurns: number;
  llmModel?: string | null;
  llmTemperature?: number | null;
  llmMaxTokens?: number | null;
}

export interface AgentEditPayload {
  name: string;
  description: string;
  agentType: AgentType;
  allowedRoles: string[];
  systemPromptEn: string | null;
  systemPromptZh: string | null;
  tools: string[];
  maxToolTurns: number;
  llmModel: string | null;
  llmTemperature: number | null;
  llmMaxTokens: number | null;
}
