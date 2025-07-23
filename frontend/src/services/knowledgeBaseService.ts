import { KnowledgeBase } from '../types';

export interface KnowledgeBaseServiceConfig {
  baseUrl: string;
  getAccessToken?: () => Promise<string | null>;
}

export class KnowledgeBaseService {
  private config: KnowledgeBaseServiceConfig;

  constructor(config: KnowledgeBaseServiceConfig) {
    this.config = config;
  }

  async listKnowledgeBases(): Promise<KnowledgeBase[]> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Add authorization header if token is available
      if (this.config.getAccessToken) {
        const token = await this.config.getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(`${this.config.baseUrl}/api/v1/knowledge-bases`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch knowledge bases: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.knowledge_bases || [];
    } catch (error) {
      console.error('Error fetching knowledge bases:', error);
      // Return default knowledge bases for development
      return [
        {
          id: 'general',
          name: 'General Knowledge',
          description: 'General purpose knowledge base',
          status: 'ACTIVE' as const,
        },
        {
          id: 'technical',
          name: 'Technical Documentation',
          description: 'Technical documentation and guides',
          status: 'ACTIVE' as const,
        },
        {
          id: 'company',
          name: 'Company Knowledge',
          description: 'Company-specific information',
          status: 'ACTIVE' as const,
        },
      ];
    }
  }

  async getKnowledgeBase(id: string): Promise<KnowledgeBase | null> {
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

      const response = await fetch(`${this.config.baseUrl}/api/v1/knowledge-bases/${id}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`Failed to fetch knowledge base: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.knowledge_base || null;
    } catch (error) {
      console.error(`Error fetching knowledge base ${id}:`, error);
      return null;
    }
  }
}

// Create service instance
const baseUrl = import.meta.env.VITE_API_URL || 
  (import.meta.env.MODE === 'production' 
    ? `https://${window.location.host}`
    : 'http://localhost:8000');

export const knowledgeBaseService = new KnowledgeBaseService({
  baseUrl,
  getAccessToken: async () => {
    // This would integrate with the auth service
    // For now, return null to use default knowledge bases
    return null;
  },
});