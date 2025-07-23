import { useRef, useState } from 'react';
import Terminal from './components/Terminal';
import TerminalLayout from './components/TerminalLayout';
import WebSocketClient, { WebSocketClientRef } from './components/WebSocketClient';
import ProtectedRoute from './components/ProtectedRoute';
import AuthErrorBoundary from './components/AuthErrorBoundary';
import { useCommandHistory } from './hooks/useCommandHistory';
import { commandProcessor, CommandResult } from './services/commandProcessor';
import { TerminalRef, ConnectionStatus } from './types';

function App() {
  const terminalRef = useRef<TerminalRef>(null);
  const webSocketRef = useRef<WebSocketClientRef>(null);
  const { addCommand } = useCommandHistory();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<string>('general');
  const [sessionId] = useState<string>(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

  const handleCommand = async (command: string) => {
    try {
      // Process the command
      const result: CommandResult = commandProcessor.processCommand(command);
      
      if (result.output === 'CLEAR_SCREEN') {
        // Special case for clear command
        if (terminalRef.current) {
          terminalRef.current.clear();
        }
        addCommand(command);
        return;
      }

      if (result.output) {
        if (result.type === 'error') {
          if (terminalRef.current) {
            terminalRef.current.writeError(result.output);
          }
        } else {
          if (terminalRef.current) {
            terminalRef.current.writeOutput(result.output);
          }
        }
      }

      // Add to history
      addCommand(command, result.output, result.error);

      // If it's not a built-in command, it should be sent to AI
      if (result.output?.startsWith('Sending to AI:')) {
        // Send command via WebSocket to AI backend
        if (webSocketRef.current && connectionStatus === 'connected') {
          webSocketRef.current.sendCommand(command);
        } else {
          if (terminalRef.current) {
            terminalRef.current.writeError('Not connected to AI server. Please wait for connection.');
          }
        }
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      if (terminalRef.current) {
        terminalRef.current.writeError(`Error: ${errorMessage}`);
      }
      addCommand(command, undefined, errorMessage);
    }
  };

  const handleKnowledgeBaseChange = (knowledgeBaseId: string) => {
    setSelectedKnowledgeBase(knowledgeBaseId);
    
    // Send knowledge base switch message via WebSocket
    if (webSocketRef.current && connectionStatus === 'connected') {
      webSocketRef.current.switchKnowledgeBase(knowledgeBaseId);
    } else {
      // Fallback for when not connected
      if (terminalRef.current) {
        terminalRef.current.writeOutput(`📚 Switched to knowledge base: ${knowledgeBaseId} (offline)`);
      }
    }
  };

  return (
    <AuthErrorBoundary>
      <ProtectedRoute>
        <TerminalLayout
          title="AI Assistant CLI"
          status={connectionStatus}
          knowledgeBase={selectedKnowledgeBase}
          onKnowledgeBaseChange={handleKnowledgeBaseChange}
        >
          <WebSocketClient
            ref={webSocketRef}
            terminalRef={terminalRef}
            sessionId={sessionId}
            knowledgeBaseId={selectedKnowledgeBase}
            onConnectionStatusChange={setConnectionStatus}
          />
          <Terminal
            ref={terminalRef}
            onCommand={handleCommand}
            className="h-full"
          />
        </TerminalLayout>
      </ProtectedRoute>
    </AuthErrorBoundary>
  );
}

export default App;