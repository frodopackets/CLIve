import '@testing-library/jest-dom';

// Mock xterm.js globally for all tests
import { vi } from 'vitest';

vi.mock('xterm', () => ({
  Terminal: vi.fn().mockImplementation(() => ({
    loadAddon: vi.fn(),
    open: vi.fn(),
    writeln: vi.fn(),
    write: vi.fn(),
    onData: vi.fn(),
    dispose: vi.fn(),
    clear: vi.fn(),
  })),
}));

vi.mock('xterm-addon-fit', () => ({
  FitAddon: vi.fn().mockImplementation(() => ({
    fit: vi.fn(),
  })),
}));

vi.mock('xterm-addon-web-links', () => ({
  WebLinksAddon: vi.fn().mockImplementation(() => ({})),
}));

// Mock CSS imports
vi.mock('xterm/css/xterm.css', () => ({}));