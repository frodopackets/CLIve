/**
 * Integration tests for frontend-backend connection
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WebSocketService } from '../services/websocketService';
import { knowledgeBaseService } from '../services/knowledgeBaseService';
import { sessionService } from '../services/sessionService';
import { WebSocketMessage, KnowledgeBase, Session } from '../types';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 100);
  }

  send(data: string) {
    // Simulate echo response for testing
    setTimeout(() => {
      if (this.onmessage) {
        const message = JSON.parse(data);
        const response: WebSocketMessage = {
          type: 'response',
          content: `Echo: ${message.content}`,
          sessionId: message.sessionId,
          timestamp: new Date().toISOString(),
        };
        this.onmessage(new MessageEvent('message', { data: JSON.stringify(response) }));
      }
    }, 50);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Mock fetch for API calls
const mockFetch = vi.fn();

describe('Frontend-Backend Integration', () => {
  beforeEach(() => {
    // Mock WebSocket
    global.WebSocket = MockWebSocket as any;
    
    // Mock fetch
    global.fetch = mockFetch;
    
    // Reset mocks
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('WebSocket Service', () => {
    it('should connect and send messages', async () => {
      const onMessage = vi.fn();
      const onConnectionChange = vi.fn();

      const wsService = new WebSocketService(
        { url: 'ws://localhost:8000/ws/chat/test-session' },
        { onMessage, onConnectionChange }
      );

      await wsService.connect();

      // Wait for connection
      await waitFor(() => {
        expect(onConnectionChange).toHaveBeenCalledWith('connected');
      });

      // Send a message
      const message: WebSocketMessage = {
        type: 'command',
        content: 'Hello, AI!',
        sessionId: 'test-session',
        timestamp: new Date().toISOString(),
      };

      const success = wsService.sendMessage(message);
      expect(success).toBe(true);

      // Wait for response
      await waitFor(() => {
        expect(onMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'response',
            content: 'Echo: Hello, AI!',
            sessionId: 'test-session',
          })
        );
      });

      wsService.disconnect();
    });

    it('should handle connection errors and reconnect', async () => {
      const onConnectionChange = vi.fn();
      const onError = vi.fn();

      const wsService = new WebSocketService(
        { 
          url: 'ws://localhost:8000/ws/chat/test-session',
          maxReconnectAttempts: 2,
          reconnectInterval: 100,
        },
        { onConnectionChange, onError }
      );

      // Mock WebSocket that fails to connect
      global.WebSocket = class extends MockWebSocket {
        constructor(url: string) {
          super(url);
          setTimeout(() => {
            this.readyState = MockWebSocket.CLOSED;
            if (this.onerror) {
              this.onerror(new Event('error'));
            }
          }, 50);
        }
      } as any;

      await wsService.connect();

      // Should attempt to reconnect
      await waitFor(() => {
        expect(onConnectionChange).toHaveBeenCalledWith('disconnected');
      }, { timeout: 1000 });

      wsService.disconnect();
    });
  });

  describe('Knowledge Base Service', () => {
    it('should fetch knowledge bases from API', async () => {
      const mockKnowledgeBases: KnowledgeBase[] = [
        {
          id: 'kb-1',
          name: 'Test KB 1',
          description: 'Test knowledge base 1',
          status: 'ACTIVE',
        },
        {
          id: 'kb-2',
          name: 'Test KB 2',
          description: 'Test knowledge base 2',
          status: 'ACTIVE',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ knowledge_bases: mockKnowledgeBases }),
      });

      const knowledgeBases = await knowledgeBaseService.listKnowledgeBases();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/knowledge-bases',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(knowledgeBases).toEqual(mockKnowledgeBases);
    });

    it('should return default knowledge bases on API failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const knowledgeBases = await knowledgeBaseService.listKnowledgeBases();

      expect(knowledgeBases).toHaveLength(3); // Default knowledge bases
      expect(knowledgeBases[0]).toEqual(
        expect.objectContaining({
          id: 'general',
          name: 'General Knowledge',
          status: 'ACTIVE',
        })
      );
    });

    it('should fetch individual knowledge base', async () => {
      const mockKnowledgeBase: KnowledgeBase = {
        id: 'kb-1',
        name: 'Test KB 1',
        description: 'Test knowledge base 1',
        status: 'ACTIVE',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ knowledge_base: mockKnowledgeBase }),
      });

      const knowledgeBase = await knowledgeBaseService.getKnowledgeBase('kb-1');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/knowledge-bases/kb-1',
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(knowledgeBase).toEqual(mockKnowledgeBase);
    });
  });

  describe('Session Service', () => {
    it('should create a new session', async () => {
      const mockSession: Session = {
        sessionId: 'session-123',
        userId: 'user-123',
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        knowledgeBaseId: 'kb-1',
        status: 'ACTIVE',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session: mockSession }),
      });

      const session = await sessionService.createSession('kb-1');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sessions',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify({
            knowledge_base_id: 'kb-1',
          }),
        })
      );

      expect(session).toEqual(mockSession);
    });

    it('should return fallback session on API failure', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const session = await sessionService.createSession('kb-1');

      expect(session).toEqual(
        expect.objectContaining({
          sessionId: expect.stringMatching(/^session_/),
          userId: 'current-user',
          knowledgeBaseId: 'kb-1',
          status: 'ACTIVE',
        })
      );
    });

    it('should list user sessions', async () => {
      const mockSessions: Session[] = [
        {
          sessionId: 'session-1',
          userId: 'user-123',
          createdAt: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          status: 'ACTIVE',
        },
        {
          sessionId: 'session-2',
          userId: 'user-123',
          createdAt: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          status: 'ACTIVE',
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: mockSessions }),
      });

      const sessions = await sessionService.listSessions();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/sessions',
        expect.objectContaining({
          method: 'GET',
        })
      );

      expect(sessions).toEqual(mockSessions);
    });
  });

  describe('Message Flow Integration', () => {
    it('should handle complete message flow from command to response', async () => {
      const messages: WebSocketMessage[] = [];
      
      // Mock WebSocket that simulates backend integration service responses
      global.WebSocket = class extends MockWebSocket {
        send(data: string) {
          const message = JSON.parse(data);
          
          // Simulate integration service response flow
          setTimeout(() => {
            if (this.onmessage) {
              // Status message
              const statusResponse: WebSocketMessage = {
                type: 'status',
                content: 'Processing your request...',
                sessionId: message.sessionId,
                timestamp: new Date().toISOString(),
              };
              this.onmessage(new MessageEvent('message', { data: JSON.stringify(statusResponse) }));
              
              // Streaming response
              setTimeout(() => {
                const streamResponse: WebSocketMessage = {
                  type: 'response',
                  content: 'This is a streaming response from the AI.',
                  sessionId: message.sessionId,
                  timestamp: new Date().toISOString(),
                  streaming: true,
                };
                this.onmessage(new MessageEvent('message', { data: JSON.stringify(streamResponse) }));
              }, 100);
            }
          }, 50);
        }
      } as any;

      const wsService = new WebSocketService(
        { url: 'ws://localhost:8000/ws/chat/test-session' },
        { 
          onMessage: (msg) => messages.push(msg),
        }
      );

      await wsService.connect();

      // Send command
      const command: WebSocketMessage = {
        type: 'command',
        content: 'Tell me about AI',
        sessionId: 'test-session',
        timestamp: new Date().toISOString(),
      };

      wsService.sendMessage(command);

      // Wait for responses
      await waitFor(() => {
        expect(messages).toHaveLength(2);
      });

      expect(messages[0]).toEqual(
        expect.objectContaining({
          type: 'status',
          content: 'Processing your request...',
        })
      );

      expect(messages[1]).toEqual(
        expect.objectContaining({
          type: 'response',
          content: 'This is a streaming response from the AI.',
          streaming: true,
        })
      );

      wsService.disconnect();
    });

    it('should handle agent command responses', async () => {
      const messages: WebSocketMessage[] = [];
      
      // Mock WebSocket that simulates agent responses
      global.WebSocket = class extends MockWebSocket {
        send(data: string) {
          const message = JSON.parse(data);
          
          if (message.content.includes('time')) {
            setTimeout(() => {
              if (this.onmessage) {
                const agentResponse: WebSocketMessage = {
                  type: 'agent_response',
                  content: 'Current time in Birmingham, Alabama: 2:30 PM (CST)',
                  sessionId: message.sessionId,
                  timestamp: new Date().toISOString(),
                  metadata: {
                    agent_id: 'birmingham_agent',
                    response_type: 'TIME',
                  },
                };
                this.onmessage(new MessageEvent('message', { data: JSON.stringify(agentResponse) }));
              }
            }, 50);
          }
        }
      } as any;

      const wsService = new WebSocketService(
        { url: 'ws://localhost:8000/ws/chat/test-session' },
        { onMessage: (msg) => messages.push(msg) }
      );

      await wsService.connect();

      // Send agent command
      const command: WebSocketMessage = {
        type: 'command',
        content: 'what time is it',
        sessionId: 'test-session',
        timestamp: new Date().toISOString(),
      };

      wsService.sendMessage(command);

      // Wait for agent response
      await waitFor(() => {
        expect(messages).toHaveLength(1);
      });

      expect(messages[0]).toEqual(
        expect.objectContaining({
          type: 'agent_response',
          content: 'Current time in Birmingham, Alabama: 2:30 PM (CST)',
          metadata: expect.objectContaining({
            agent_id: 'birmingham_agent',
            response_type: 'TIME',
          }),
        })
      );

      wsService.disconnect();
    });

    it('should handle knowledge base switching', async () => {
      const messages: WebSocketMessage[] = [];
      
      // Mock WebSocket that simulates knowledge base switching
      global.WebSocket = class extends MockWebSocket {
        send(data: string) {
          const message = JSON.parse(data);
          
          if (message.type === 'knowledge_base_switch') {
            setTimeout(() => {
              if (this.onmessage) {
                const switchResponse: WebSocketMessage = {
                  type: 'status',
                  content: `Switched to knowledge base: ${message.knowledgeBaseId}`,
                  sessionId: message.sessionId,
                  timestamp: new Date().toISOString(),
                  metadata: {
                    knowledge_base_id: message.knowledgeBaseId,
                    action: 'knowledge_base_switch',
                  },
                };
                this.onmessage(new MessageEvent('message', { data: JSON.stringify(switchResponse) }));
              }
            }, 50);
          }
        }
      } as any;

      const wsService = new WebSocketService(
        { url: 'ws://localhost:8000/ws/chat/test-session' },
        { onMessage: (msg) => messages.push(msg) }
      );

      await wsService.connect();

      // Send knowledge base switch
      const switchMessage: WebSocketMessage = {
        type: 'knowledge_base_switch',
        content: '',
        sessionId: 'test-session',
        knowledgeBaseId: 'technical',
        timestamp: new Date().toISOString(),
      };

      wsService.sendMessage(switchMessage);

      // Wait for switch confirmation
      await waitFor(() => {
        expect(messages).toHaveLength(1);
      });

      expect(messages[0]).toEqual(
        expect.objectContaining({
          type: 'status',
          content: 'Switched to knowledge base: technical',
          metadata: expect.objectContaining({
            knowledge_base_id: 'technical',
            action: 'knowledge_base_switch',
          }),
        })
      );

      wsService.disconnect();
    });
  });
});