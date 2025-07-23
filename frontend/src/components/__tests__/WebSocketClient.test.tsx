import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import WebSocketClient from '../WebSocketClient';
import { TerminalRef } from '../../types';

// Mock the useWebSocket hook
const mockUseWebSocket = {
  connectionStatus: 'disconnected' as 'connected' | 'disconnected' | 'connecting',
  sendMessage: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
  lastMessage: null,
  streamBuffer: '',
  clearStreamBuffer: vi.fn(),
};

vi.mock('../../hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => mockUseWebSocket),
}));

describe('WebSocketClient Component', () => {
  const mockTerminalRef = {
    current: {
      writeOutput: vi.fn(),
      writeError: vi.fn(),
      writeStream: vi.fn(),
      writePrompt: vi.fn(),
      clear: vi.fn(),
    } as TerminalRef,
  };

  const defaultProps = {
    terminalRef: mockTerminalRef,
    sessionId: 'test-session-123',
    knowledgeBaseId: 'test-kb-456',
    onConnectionStatusChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseWebSocket.connectionStatus = 'disconnected';
  });

  it('renders connection status indicator', () => {
    render(<WebSocketClient {...defaultProps} />);
    
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    expect(screen.getByText(/Session:/)).toBeInTheDocument();
    expect(screen.getByText(/KB:/)).toBeInTheDocument();
  });

  it('shows reconnect button when disconnected', () => {
    render(<WebSocketClient {...defaultProps} />);
    
    const reconnectButton = screen.getByText('Reconnect');
    expect(reconnectButton).toBeInTheDocument();
  });

  it('displays correct status colors for different connection states', () => {
    const { rerender } = render(<WebSocketClient {...defaultProps} />);
    
    // Test disconnected state
    expect(screen.getByText('Disconnected')).toHaveClass('text-red-400');
    
    // Test connecting state
    mockUseWebSocket.connectionStatus = 'connecting';
    rerender(<WebSocketClient {...defaultProps} />);
    expect(screen.getByText('Connecting...')).toHaveClass('text-yellow-400');
    
    // Test connected state
    mockUseWebSocket.connectionStatus = 'connected';
    rerender(<WebSocketClient {...defaultProps} />);
    expect(screen.getByText('Connected')).toHaveClass('text-green-400');
  });

  it('calls onConnectionStatusChange when status changes', () => {
    const onConnectionStatusChange = vi.fn();
    render(<WebSocketClient {...defaultProps} onConnectionStatusChange={onConnectionStatusChange} />);
    
    expect(onConnectionStatusChange).toHaveBeenCalledWith('disconnected');
  });
});