export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  agentId?: string;
  hasDisclaimer: boolean;
  createdAt: string;
  progressSteps?: MessageProgress[];
}

export interface MessageProgress {
  stage: string;
  message: string;
  agent_id?: string | null;
  agent_name?: string | null;
  workflow_type?: string | null;
  artifacts?: MessageProgressArtifact[];
}

export interface MessageProgressArtifact {
  type: string;
  title: string;
  subtitle?: string | null;
  score?: number | null;
  content: string;
  document_id?: string | null;
  chunk_id?: string | null;
}

export interface ConversationSession {
  id: string;
  activeAgentId?: string;
  ragEnabled: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  session?: ConversationSession;
  messages: Message[];
}
