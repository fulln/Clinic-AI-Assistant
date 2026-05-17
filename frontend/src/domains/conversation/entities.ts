export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  agentId?: string;
  hasDisclaimer: boolean;
  createdAt: string;
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
