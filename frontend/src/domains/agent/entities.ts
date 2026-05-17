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
}
