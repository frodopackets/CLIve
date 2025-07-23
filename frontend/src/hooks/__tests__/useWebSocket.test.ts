import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import { WebSocketMessage } from '../../types';

// Mock the WebSocketService
vi.mock('../../services/websocketService', () => {
  const mockService = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendMessage: vi.fn().mockReturnValue(true),
    getConnectionStatus: vi.fn().mockReturnValue('disconnected'),
  };

  return {
    WebSocketService: vi.fn().mockImplementation((_config, _callbacks) => {
      return mockService;
    }),
  };
});

describe('useWebSocket', () => {
  const mockConfig = {
    url: 'ws://localhost:8000/test',
    sessionId: 'test-session',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useWebSocket(mockConfig));

    expect(result.current.connectionStatus).toBe('disconnected');
    expect(result.current.lastMessage).toBeNull();
    expect(result.current.streamBuffer).toBe('');
  });

  it('should auto-connect by default', () => {
    const { WebSocketService } = require('../../services/websocketService');
    
    renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;
    expect(serviceInstance.connect).toHaveBeenCalled();
  });

  it('should not auto-connect when disabled', () => {
    const { WebSocketService } = require('../../services/websocketService');
    
    renderHook(() => useWebSocket({ ...mockConfig, autoConnect: false }));

    const serviceInstance = WebSocketService.mock.results[0].value;
    expect(serviceInstance.connect).not.toHaveBeenCalled();
  });

  it('should send messages with timestamp', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const message = {
      type: 'command' as const,
      content: 'test command',
      sessionId: 'test-session',
    };

    act(() => {
      result.current.sendMessage(message);
    });

    const serviceInstance = WebSocketService.mock.results[0].value;
    expect(serviceInstance.sendMessage).toHaveBeenCalledWith({
      ...message,
      timestamp: expect.any(String),
    });
  });

  it('should use provided sessionId in messages', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const message = {
      type: 'command' as const,
      content: 'test command',
      sessionId: '', // Empty sessionId should be replaced
    };

    act(() => {
      result.current.sendMessage(message);
    });

    const serviceInstance = WebSocketService.mock.results[0].value;
    expect(serviceInstance.sendMessage).toHaveBeenCalledWith({
      ...message,
      sessionId: 'test-session', // Should use hook's sessionId
      timestamp: expect.any(String),
    });
  });

  it('should handle connection status changes', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;
    const callbacks = serviceInstance.callbacks;

    act(() => {
      callbacks.onConnectionChange('connected');
    });

    expect(result.current.connectionStatus).toBe('connected');
  });

  it('should handle incoming messages', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;
    const callbacks = serviceInstance.callbacks;

    const testMessage: WebSocketMessage = {
      type: 'response',
      content: 'test response',
      sessionId: 'test-session',
      timestamp: new Date().toISOString(),
    };

    act(() => {
      callbacks.onMessage(testMessage);
    });

    expect(result.current.lastMessage).toEqual(testMessage);
  });

  it('should handle stream chunks', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;
    const callbacks = serviceInstance.callbacks;

    act(() => {
      callbacks.onStreamChunk('chunk1');
    });

    expect(result.current.streamBuffer).toBe('chunk1');

    act(() => {
      callbacks.onStreamChunk('chunk2');
    });

    expect(result.current.streamBuffer).toBe('chunk1chunk2');
  });

  it('should clear stream buffer', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;
    const callbacks = serviceInstance.callbacks;

    act(() => {
      callbacks.onStreamChunk('test chunk');
    });

    expect(result.current.streamBuffer).toBe('test chunk');

    act(() => {
      result.current.clearStreamBuffer();
    });

    expect(result.current.streamBuffer).toBe('');
  });

  it('should expose connect and disconnect methods', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { result } = renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;

    act(() => {
      result.current.connect();
    });

    expect(serviceInstance.connect).toHaveBeenCalledTimes(2); // Once for auto-connect, once manual

    act(() => {
      result.current.disconnect();
    });

    expect(serviceInstance.disconnect).toHaveBeenCalled();
  });

  it('should call custom callbacks', () => {
    const mockCallbacks = {
      onMessage: vi.fn(),
      onError: vi.fn(),
      onStreamChunk: vi.fn(),
    };

    const { WebSocketService } = require('../../services/websocketService');
    renderHook(() => useWebSocket(mockConfig, mockCallbacks));

    const serviceInstance = WebSocketService.mock.results[0].value;
    const callbacks = serviceInstance.callbacks;

    const testMessage: WebSocketMessage = {
      type: 'response',
      content: 'test',
      sessionId: 'test',
      timestamp: new Date().toISOString(),
    };

    act(() => {
      callbacks.onMessage(testMessage);
    });

    expect(mockCallbacks.onMessage).toHaveBeenCalledWith(testMessage);

    act(() => {
      callbacks.onStreamChunk('chunk');
    });

    expect(mockCallbacks.onStreamChunk).toHaveBeenCalledWith('chunk');

    const errorEvent = new Event('error');
    act(() => {
      callbacks.onError(errorEvent);
    });

    expect(mockCallbacks.onError).toHaveBeenCalledWith(errorEvent);
  });

  it('should cleanup on unmount', () => {
    const { WebSocketService } = require('../../services/websocketService');
    const { unmount } = renderHook(() => useWebSocket(mockConfig));

    const serviceInstance = WebSocketService.mock.results[0].value;

    unmount();

    expect(serviceInstance.disconnect).toHaveBeenCalled();
  });
});