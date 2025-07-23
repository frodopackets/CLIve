import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { WebSocketMessage, TerminalRef, ConnectionStatus } from '../types';
import { useAuth } from '../contexts/AuthContext';

interface WebSocketClientProps {
  terminalRef: React.RefObject<TerminalRef>;
  sessionId: string;
  knowledgeBaseId?: string;
  onConnectionStatusChange?: (status: ConnectionStatus) => void;
}

export interface WebSocketClientRef {
  sendCommand: (command: string) => void;
  switchKnowledgeBase: (knowledgeBaseId: string) => void;
  connect: () => void;
  disconnect: () => void;
  connectionStatus: ConnectionStatus;
}

export const WebSocketClient = forwardRef<WebSocketClientRef, WebSocketClientProps>(({
  terminalRef,
  sessionId,
  knowledgeBaseId,
  onConnectionStatusChange,
}, ref) => {
  const { getAccessToken } = useAuth();
  const [isStreaming, setIsStreaming] = useState(false);
  const streamingLineRef = useRef<string>('');
  
  // WebSocket configuration - in production this would come from environment variables
  const wsUrl = import.meta.env.VITE_WEBSOCKET_URL || 
    (import.meta.env.MODE === 'production' 
      ? `wss://${window.location.host}/ws/chat/${sessionId}`
      : `ws://localhost:8000/ws/chat/${sessionId}`);

  const {
    connectionStatus,
    sendMessage,
    connect,
    disconnect,
  } = useWebSocket(
    {
      url: wsUrl,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      sessionId,
      getAccessToken,
    },
    {
      onMessage: handleMessage,
      onError: handleError,
      onStreamChunk: handleStreamChunk,
    }
  );

  // Notify parent component of connection status changes
  useEffect(() => {
    if (onConnectionStatusChange) {
      onConnectionStatusChange(connectionStatus);
    }
  }, [connectionStatus, onConnectionStatusChange]);

  // Handle incoming messages
  function handleMessage(message: WebSocketMessage) {
    if (!terminalRef.current) return;

    switch (message.type) {
      case 'response':
        if (message.streaming) {
          // Handle streaming response chunks
          if (!isStreaming) {
            setIsStreaming(true);
            streamingLineRef.current = '';
          }
          streamingLineRef.current += message.content;
          terminalRef.current.writeStream(message.content);
        } else {
          // Handle complete response
          if (isStreaming) {
            setIsStreaming(false);
            terminalRef.current.writeStream('\n');
            terminalRef.current.writePrompt();
            streamingLineRef.current = '';
          } else {
            terminalRef.current.writeOutput(message.content);
          }
        }
        break;
        
      case 'agent_response':
        // Handle agent-specific responses
        if (isStreaming) {
          setIsStreaming(false);
          terminalRef.current.writeStream('\n');
        }
        terminalRef.current.writeOutput(`🤖 ${message.content}`);
        break;
        
      case 'error':
        if (isStreaming) {
          setIsStreaming(false);
          terminalRef.current.writeStream('\n');
        }
        terminalRef.current.writeError(`❌ ${message.content}`);
        break;
        
      case 'status':
        // Handle status messages
        if (message.content.includes('Processing') || message.content.includes('Thinking') || 
            message.content.includes('Searching') || message.content.includes('Contacting')) {
          terminalRef.current.writeOutput(`⏳ ${message.content}`);
        } else if (message.content.includes('Switched to knowledge base')) {
          terminalRef.current.writeOutput(`📚 ${message.content}`);
        } else {
          terminalRef.current.writeOutput(`ℹ️  ${message.content}`);
        }
        break;
        
      case 'knowledge_base_switch':
        // Handle knowledge base switching confirmation
        terminalRef.current.writeOutput(`📚 ${message.content}`);
        break;
    }
  }

  // Handle streaming chunks
  function handleStreamChunk(chunk: string) {
    if (!terminalRef.current || !isStreaming) return;

    // For streaming, we want to display text as it comes in
    // This simulates the real-time typing effect
    streamingLineRef.current += chunk;
    
    // Write the chunk directly to terminal using writeStream method
    terminalRef.current.writeStream(chunk);
  }

  // Handle WebSocket errors
  function handleError(error: Event) {
    console.error('WebSocket error:', error);
    if (terminalRef.current) {
      terminalRef.current.writeError('Connection error occurred. Attempting to reconnect...');
    }
  }

  // Send command to backend
  const sendCommand = (command: string) => {
    if (connectionStatus !== 'connected') {
      if (terminalRef.current) {
        terminalRef.current.writeError('Not connected to server. Please wait for reconnection.');
      }
      return;
    }

    const message: Omit<WebSocketMessage, 'timestamp'> = {
      type: 'command',
      content: command,
      sessionId,
      knowledgeBaseId,
      metadata: {
        user_id: 'current-user' // This would come from auth context in production
      }
    };

    const success = sendMessage(message);
    if (!success && terminalRef.current) {
      terminalRef.current.writeError('Failed to send command. Please try again.');
    }
  };

  // Send knowledge base switch message
  const switchKnowledgeBase = (newKnowledgeBaseId: string) => {
    if (connectionStatus !== 'connected') {
      if (terminalRef.current) {
        terminalRef.current.writeError('Not connected to server. Please wait for reconnection.');
      }
      return;
    }

    const message: Omit<WebSocketMessage, 'timestamp'> = {
      type: 'knowledge_base_switch',
      content: '',
      sessionId,
      knowledgeBaseId: newKnowledgeBaseId,
      metadata: {
        user_id: 'current-user'
      }
    };

    const success = sendMessage(message);
    if (!success && terminalRef.current) {
      terminalRef.current.writeError('Failed to switch knowledge base. Please try again.');
    }
  };

  // Connection status indicator
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-400';
      case 'connecting': return 'text-yellow-400';
      case 'disconnected': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'disconnected': return 'Disconnected';
      default: return 'Unknown';
    }
  };

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    sendCommand,
    switchKnowledgeBase,
    connect,
    disconnect,
    connectionStatus,
  }));

  return (
    <div className="websocket-client">
      {/* Connection Status Indicator */}
      <div className="flex items-center justify-between p-2 bg-gray-800 text-sm">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-400' : 
            connectionStatus === 'connecting' ? 'bg-yellow-400' : 'bg-red-400'
          }`} />
          <span className={getStatusColor()}>{getStatusText()}</span>
          {sessionId && (
            <span className="text-gray-400">Session: {sessionId.slice(0, 8)}...</span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {connectionStatus === 'disconnected' && (
            <button
              onClick={connect}
              className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded"
            >
              Reconnect
            </button>
          )}
          {knowledgeBaseId && (
            <span className="text-gray-400 text-xs">KB: {knowledgeBaseId.slice(0, 8)}...</span>
          )}
        </div>
      </div>
    </div>
  );
});

export default WebSocketClient;