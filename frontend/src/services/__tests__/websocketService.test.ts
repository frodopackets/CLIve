import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketService } from '../websocketService';
import { WebSocketMessage } from '../../types';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(_data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  // Helper methods for testing
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateClose(code = 1000, reason = '') {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code, reason }));
    }
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any;

describe('WebSocketService', () => {
  let service: WebSocketService;
  let mockCallbacks: any;

  beforeEach(() => {
    vi.clearAllTimers();
    vi.useFakeTimers();
    
    mockCallbacks = {
      onMessage: vi.fn(),
      onConnectionChange: vi.fn(),
      onError: vi.fn(),
      onStreamChunk: vi.fn(),
    };

    service = new WebSocketService(
      {
        url: 'ws://localhost:8000/test',
        reconnectInterval: 1000,
        maxReconnectAttempts: 3,
        heartbeatInterval: 5000,
      },
      mockCallbacks
    );
  });

  afterEach(() => {
    service.disconnect();
    vi.useRealTimers();
  });

  describe('Connection Management', () => {
    it('should connect successfully', async () => {
      service.connect();
      
      expect(mockCallbacks.onConnectionChange).toHaveBeenCalledWith('connecting');
      
      // Fast-forward to simulate connection
      vi.advanceTimersByTime(20);
      
      expect(mockCallbacks.onConnectionChange).toHaveBeenCalledWith('connected');
      expect(service.getConnectionStatus()).toBe('connected');
    });

    it('should disconnect cleanly', () => {
      service.connect();
      vi.advanceTimersByTime(20); // Wait for connection
      
      service.disconnect();
      
      expect(service.getConnectionStatus()).toBe('disconnected');
    });

    it('should not connect if already connected', () => {
      service.connect();
      vi.advanceTimersByTime(20);
      
      const initialCallCount = mockCallbacks.onConnectionChange.mock.calls.length;
      service.connect(); // Try to connect again
      
      expect(mockCallbacks.onConnectionChange.mock.calls.length).toBe(initialCallCount);
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      service.connect();
      vi.advanceTimersByTime(20); // Wait for connection
    });

    it('should send messages when connected', () => {
      const message: WebSocketMessage = {
        type: 'command',
        content: 'test command',
        sessionId: 'test-session',
        timestamp: new Date().toISOString(),
      };

      const result = service.sendMessage(message);
      expect(result).toBe(true);
    });

    it('should not send messages when disconnected', () => {
      service.disconnect();
      
      const message: WebSocketMessage = {
        type: 'command',
        content: 'test command',
        sessionId: 'test-session',
        timestamp: new Date().toISOString(),
      };

      const result = service.sendMessage(message);
      expect(result).toBe(false);
    });

    it('should handle incoming messages', () => {
      const testMessage = {
        type: 'response',
        content: 'test response',
        sessionId: 'test-session',
        timestamp: new Date().toISOString(),
      };

      // Simulate receiving a message
      const ws = (service as any).ws as MockWebSocket;
      ws.simulateMessage(testMessage);

      expect(mockCallbacks.onMessage).toHaveBeenCalledWith(testMessage);
    });

    it('should handle streaming messages', () => {
      const streamMessage = {
        type: 'stream',
        content: 'chunk of text',
      };

      const ws = (service as any).ws as MockWebSocket;
      ws.simulateMessage(streamMessage);

      expect(mockCallbacks.onStreamChunk).toHaveBeenCalledWith('chunk of text');
    });

    it('should handle malformed messages gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const ws = (service as any).ws as MockWebSocket;
      if (ws.onmessage) {
        ws.onmessage(new MessageEvent('message', { data: 'invalid json' }));
      }

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('Reconnection Logic', () => {
    it('should attempt reconnection on connection loss', () => {
      service.connect();
      vi.advanceTimersByTime(20); // Wait for connection
      
      // Simulate connection loss
      const ws = (service as any).ws as MockWebSocket;
      ws.simulateClose(1006, 'Connection lost');
      
      expect(mockCallbacks.onConnectionChange).toHaveBeenCalledWith('disconnected');
      
      // Should attempt reconnection
      vi.advanceTimersByTime(1000);
      expect(mockCallbacks.onConnectionChange).toHaveBeenCalledWith('connecting');
    });

    it('should stop reconnecting after max attempts', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      service.connect();
      vi.advanceTimersByTime(20); // Initial connection
      
      // Simulate connection failures that trigger reconnection attempts
      for (let i = 0; i < 4; i++) {
        const ws = (service as any).ws as MockWebSocket;
        ws.simulateClose(1006, 'Connection lost'); // This should trigger reconnection
        vi.advanceTimersByTime(1000); // Wait for reconnection attempt
        vi.advanceTimersByTime(20); // Allow new connection to be established
      }
      
      // Check that we attempted to reconnect and eventually stopped
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Attempting to reconnect')
      );
      expect(consoleSpy).toHaveBeenCalledWith('Max reconnection attempts reached');
      
      consoleSpy.mockRestore();
      consoleLogSpy.mockRestore();
    });

    it('should not reconnect on manual disconnect', () => {
      service.connect();
      vi.advanceTimersByTime(20);
      
      service.disconnect();
      
      // Should not attempt reconnection
      vi.advanceTimersByTime(2000);
      expect(service.getConnectionStatus()).toBe('disconnected');
    });
  });

  describe('Heartbeat', () => {
    it('should send heartbeat messages', () => {
      service.connect();
      vi.advanceTimersByTime(20); // Wait for connection
      
      const sendSpy = vi.spyOn(service, 'sendMessage');
      
      // Fast-forward to heartbeat interval
      vi.advanceTimersByTime(5000);
      
      expect(sendSpy).toHaveBeenCalledWith({
        type: 'status',
        content: 'ping',
        sessionId: '',
        timestamp: expect.any(String),
      });
    });

    it('should stop heartbeat on disconnect', () => {
      service.connect();
      vi.advanceTimersByTime(20);
      
      const sendSpy = vi.spyOn(service, 'sendMessage');
      
      service.disconnect();
      vi.advanceTimersByTime(5000);
      
      // Should not send heartbeat after disconnect
      expect(sendSpy).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should handle WebSocket errors', () => {
      service.connect();
      vi.advanceTimersByTime(20);
      
      const ws = (service as any).ws as MockWebSocket;
      ws.simulateError();
      
      expect(mockCallbacks.onError).toHaveBeenCalled();
      expect(mockCallbacks.onConnectionChange).toHaveBeenCalledWith('disconnected');
    });

    it('should handle send errors gracefully', () => {
      service.connect();
      vi.advanceTimersByTime(20);
      
      // Mock send to throw error
      const ws = (service as any).ws as MockWebSocket;
      vi.spyOn(ws, 'send').mockImplementation(() => {
        throw new Error('Send failed');
      });
      
      const message: WebSocketMessage = {
        type: 'command',
        content: 'test',
        sessionId: 'test',
        timestamp: new Date().toISOString(),
      };
      
      const result = service.sendMessage(message);
      expect(result).toBe(false);
    });
  });
});