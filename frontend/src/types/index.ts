export interface WebSocketMessage {
  type: 'command' | 'response' | 'error' | 'status' | 'agent_response' | 'knowledge_base_switch';
  content: string;
  sessionId: string;
  knowledgeBaseId?: string;
  timestamp: string;
  streaming?: boolean;
  metadata?: {
    [key: string]: any;
  };
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  status: 'ACTIVE' | 'INACTIVE';
}

export interface Session {
  sessionId: string;
  userId: string;
  createdAt: string;
  lastActivity: string;
  knowledgeBaseId?: string;
  status: 'ACTIVE' | 'INACTIVE';
}

export interface TerminalRef {
  writeOutput: (text: string) => void;
  writeError: (text: string) => void;
  writeStream: (text: string) => void;
  writePrompt: () => void;
  clear: () => void;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
}

export interface AuthConfig {
  authority: string;
  clientId: string;
  redirectUri: string;
  postLogoutRedirectUri: string;
  scope: string;
}