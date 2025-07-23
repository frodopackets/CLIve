import React from 'react';
import KnowledgeBaseSelector from './KnowledgeBaseSelector';
import UserInfo from './UserInfo';

interface TerminalLayoutProps {
  children: React.ReactNode;
  title?: string;
  status?: 'connected' | 'disconnected' | 'connecting';
  knowledgeBase?: string;
  onKnowledgeBaseChange?: (knowledgeBaseId: string) => void;
}

export const TerminalLayout: React.FC<TerminalLayoutProps> = ({
  children,
  title = 'AI Assistant CLI',
  status = 'disconnected',
  knowledgeBase,
  onKnowledgeBaseChange,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'text-green-400';
      case 'connecting':
        return 'text-yellow-400';
      case 'disconnected':
      default:
        return 'text-red-400';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return '● Connected';
      case 'connecting':
        return '● Connecting...';
      case 'disconnected':
      default:
        return '● Disconnected';
    }
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-700 p-3">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold">{title}</h1>
            <span className={`text-sm ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
          
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            {onKnowledgeBaseChange && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400 whitespace-nowrap">Knowledge Base:</span>
                <KnowledgeBaseSelector
                  selectedKnowledgeBase={knowledgeBase}
                  onKnowledgeBaseChange={onKnowledgeBaseChange}
                  className="min-w-48"
                />
              </div>
            )}
            
            {knowledgeBase && !onKnowledgeBaseChange && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-400">KB:</span>
                <span className="text-blue-400">{knowledgeBase}</span>
              </div>
            )}
            
            <UserInfo />
          </div>
        </div>
      </header>

      {/* Main Terminal Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 p-4">
          <div className="h-full bg-black border border-gray-700 rounded-lg overflow-hidden">
            {children}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-gray-700 p-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-gray-400">
          <div className="flex items-center gap-4">
            <span>Use ↑↓ for command history</span>
            <span>Ctrl+C to interrupt</span>
            <span>Type 'help' for commands</span>
          </div>
          <div className="flex items-center gap-2">
            <span>v1.0.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default TerminalLayout;