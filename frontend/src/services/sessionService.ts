import { Session } from '../types';

export interface SessionServiceConfig {
  baseUrl: string;
  getAccessToken?: () => Promise<string | null>;
}

export class SessionService {
  private config: SessionServiceConfig;

  constructor(config: SessionServiceConfig) {
    this.config = config;
  }

  async createSession(knowledgeBaseId?: string): Promise<Session> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (this.config.getAccessToken) {
        const token = await this.config.getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${this.config.baseUrl}/api/v1/sessions`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          knowledge_base_id: knowledgeBaseId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.session;
    } catch (error) {
      console.error('Error creating session:', error);
      // Return a fallback session for development
      return {
        sessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        userId: 'current-user',
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        knowledgeBaseId,
        status: 'ACTIVE' as const,
      };
    }
  }

  async getSession(sessionId: string): Promise<Session | null> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (this.config.getAccessToken) {
        const token = await this.config.getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${this.config.baseUrl}/api/v1/sessions/${sessionId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to get session: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.session;
    } catch (error) {
      console.error(`Error getting session ${sessionId}:`, error);
      return null;
    }
  }

  async listSessions(): Promise<Session[]> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (this.config.getAccessToken) {
        const token = await this.config.getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${this.config.baseUrl}/api/v1/sessions`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to list sessions: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.sessions || [];
    } catch (error) {
      console.error('Error listing sessions:', error);
      return [];
    }
  }

  async deleteSession(sessionId: string): Promise<boolean> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (this.config.getAccessToken) {
        const token = await this.config.getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${this.config.baseUrl}/api/v1/sessions/${sessionId}`, {
        method: 'DELETE',
        headers,
      });

      return response.ok;
    } catch (error) {
      console.error(`Error deleting session ${sessionId}:`, error);
      return false;
    }
  }
}

// Create service instance
const baseUrl = import.meta.env.VITE_API_URL || 
  (import.meta.env.MODE === 'production' 
    ? `https://${window.location.host}`
    : 'http://localhost:8000');

export const sessionService = new SessionService({
  baseUrl,
  getAccessToken: async () => {
    // This would integrate with the auth service
    // For now, return null to use fallback sessions
    return null;
  },
});