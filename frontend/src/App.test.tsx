import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('renders the AI Assistant CLI interface', () => {
    render(<App />);
    
    // Check that the main title is rendered
    expect(screen.getByText('AI Assistant CLI')).toBeTruthy();
    
    // Check that the status is shown
    expect(screen.getByText('● Disconnected')).toBeTruthy();
    
    // Check that help text is shown in footer
    expect(screen.getByText('Use ↑↓ for command history')).toBeTruthy();
  });

  it('renders terminal container', () => {
    render(<App />);
    
    // Check that terminal container exists
    const terminalContainer = document.querySelector('.terminal-container');
    expect(terminalContainer).toBeTruthy();
  });
});