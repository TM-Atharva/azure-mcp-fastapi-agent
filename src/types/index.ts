export interface User {
  id: string;
  azure_id: string;
  email: string;
  name: string;
  avatar_url?: string;
  created_at: string;
  last_login: string;
}

export interface Agent {
  id: string;
  azure_agent_id: string;
  name: string;
  description?: string;
  capabilities: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  agent_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface CreateSessionRequest {
  agent_id: string;
  title?: string;
}

export interface SendMessageRequest {
  session_id: string;
  content: string;
  metadata?: Record<string, any>;
}

export interface AgentResponse {
  agents: Agent[];
  count: number;
}

export interface MessageResponse {
  message: ChatMessage;
}

export interface SessionResponse {
  session: ChatSession;
}

export interface ChatHistoryResponse {
  session: ChatSession;
  messages: ChatMessage[];
}
