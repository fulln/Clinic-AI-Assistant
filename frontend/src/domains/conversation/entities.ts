export type MessageRole = 'user' | 'assistant' | 'system';
export type Locale = 'zh-CN' | 'en-US';

export interface MessageMetadata {
  locale?: Locale;
  disclaimer_locale?: Locale;
  latency_ms?: number;
  orchestra?: boolean;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  agentId?: string;
  hasDisclaimer: boolean;
  createdAt: string;
  metadata?: MessageMetadata;
  progressSteps?: MessageProgress[];
}

export interface MessageProgress {
  stage: string;
  message: string;
  locale?: Locale;
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
  locale: Locale;
}

export interface Conversation {
  id: string;
  title: string;
  session?: ConversationSession;
  messages: Message[];
}
