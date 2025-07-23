import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import Terminal from '../Terminal';

describe('Terminal Component', () => {
  it('renders without crashing', () => {
    render(<Terminal />);
    const terminalContainer = document.querySelector('.terminal-container');
    expect(terminalContainer).toBeTruthy();
  });

  it('applies custom className', () => {
    render(<Terminal className="custom-class" />);
    const terminalContainer = document.querySelector('.terminal-container.custom-class');
    expect(terminalContainer).toBeTruthy();
  });

  it('accepts onCommand prop', () => {
    const mockOnCommand = vi.fn();
    render(<Terminal onCommand={mockOnCommand} />);
    // Note: Full command testing would require more complex mocking of xterm.js
    expect(mockOnCommand).not.toHaveBeenCalled(); // Initially not called
  });
});