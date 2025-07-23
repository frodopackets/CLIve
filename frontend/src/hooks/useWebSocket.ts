import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketService, WebSocketConfig, WebSocketCallbacks } from '../services/websocketService';
import { WebSocketMessage, ConnectionStatus } from '../types';

export interface UseWebSocketOptions extends WebSocketConfig {
  autoConnect?: boolean;
  sessionId?: string;
}

export interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  sendMessage: (message: Omit<WebSocketMessage, 'timestamp'>) => boolean;
  connect: () => void;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
  streamBuffer: string;
  clearStreamBuffer: () => void;
}

export const useWebSocket = (
  options: UseWebSocketOptions,
  callbacks: Omit<WebSocketCallbacks, 'onConnectionChange'> = {}
): UseWebSocketReturn => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [streamBuffer, setStreamBuffer] = useState<string>('');
  
  const wsServiceRef = useRef<WebSocketService | null>(null);
  const { autoConnect = true, sessionId, ...wsConfig } = options;

  // Initialize WebSocket service
  useEffect(() => {
    const wsCallbacks: WebSocketCallbacks = {
      onConnectionChange: setConnectionStatus,
      onMessage: (message: WebSocketMessage) => {
        setLastMessage(message);
        if (callbacks.onMessage) {
          callbacks.onMessage(message);
        }
      },
      onError: callbacks.onError,
      onStreamChunk: (chunk: string) => {
        setStreamBuffer(prev => prev + chunk);
        if (callbacks.onStreamChunk) {
          callbacks.onStreamChunk(chunk);
        }
      },
    };

    wsServiceRef.current = new WebSocketService(wsConfig, wsCallbacks);

    if (autoConnect) {
      wsServiceRef.current.connect();
    }

    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect();
      }
    };
  }, [wsConfig.url, autoConnect]);

  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'timestamp'>): boolean => {
    if (!wsServiceRef.current) return false;

    const fullMessage: WebSocketMessage = {
      ...message,
      sessionId: message.sessionId || sessionId || '',
      timestamp: new Date().toISOString(),
    };

    return wsServiceRef.current.sendMessage(fullMessage);
  }, [sessionId]);

  const connect = useCallback(async () => {
    if (wsServiceRef.current) {
      await wsServiceRef.current.connect();
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsServiceRef.current) {
      wsServiceRef.current.disconnect();
    }
  }, []);

  const clearStreamBuffer = useCallback(() => {
    setStreamBuffer('');
  }, []);

  return {
    connectionStatus,
    sendMessage,
    connect,
    disconnect,
    lastMessage,
    streamBuffer,
    clearStreamBuffer,
  };
};