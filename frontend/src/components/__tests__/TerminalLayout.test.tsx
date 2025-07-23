import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TerminalLayout from '../TerminalLayout';

describe('TerminalLayout Component', () => {
  it('renders with default props', () => {
    render(
      <TerminalLayout>
        <div>Test Content</div>
      </TerminalLayout>
    );
    
    expect(screen.getByText('AI Assistant CLI')).toBeTruthy();
    expect(screen.getByText('● Disconnected')).toBeTruthy();
    expect(screen.getByText('Test Content')).toBeTruthy();
  });

  it('displays custom title', () => {
    render(
      <TerminalLayout title="Custom Title">
        <div>Test Content</div>
      </TerminalLayout>
    );
    
    expect(screen.getByText('Custom Title')).toBeTruthy();
  });

  it('shows connected status', () => {
    render(
      <TerminalLayout status="connected">
        <div>Test Content</div>
      </TerminalLayout>
    );
    
    expect(screen.getByText('● Connected')).toBeTruthy();
  });

  it('shows connecting status', () => {
    render(
      <TerminalLayout status="connecting">
        <div>Test Content</div>
      </TerminalLayout>
    );
    
    expect(screen.getByText('● Connecting...')).toBeTruthy();
  });

  it('displays knowledge base when provided', () => {
    render(
      <TerminalLayout knowledgeBase="Test KB">
        <div>Test Content</div>
      </TerminalLayout>
    );
    
    expect(screen.getByText('KB:')).toBeTruthy();
    expect(screen.getByText('Test KB')).toBeTruthy();
  });

  it('shows help text in footer', () => {
    render(
      <TerminalLayout>
        <div>Test Content</div>
      </TerminalLayout>
    );
    
    expect(screen.getByText('Use ↑↓ for command history')).toBeTruthy();
    expect(screen.getByText('Type \'help\' for commands')).toBeTruthy();
    expect(screen.getByText('v1.0.0')).toBeTruthy();
  });
});