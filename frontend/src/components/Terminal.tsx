import { useEffect, useRef, useState, forwardRef, useImperativeHandle } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { TerminalRef } from '../types';
import 'xterm/css/xterm.css';

interface TerminalProps {
  onCommand?: (command: string) => void;
  className?: string;
  isStreaming?: boolean;
}

export const Terminal = forwardRef<TerminalRef, TerminalProps>(({ onCommand, className = '', isStreaming = false }, ref) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [currentLine, setCurrentLine] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [cursorPosition, setCursorPosition] = useState(0);

  const PROMPT = '$ ';

  useEffect(() => {
    if (!terminalRef.current) return;

    // Initialize xterm.js
    const terminal = new XTerm({
      theme: {
        background: '#000000',
        foreground: '#00ff00',
        cursor: '#00ff00',
      },
      fontFamily: 'Courier New, monospace',
      fontSize: 14,
      cursorBlink: true,
      cursorStyle: 'block',
      scrollback: 1000,
      tabStopWidth: 4,
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    terminal.loadAddon(fitAddon);
    terminal.loadAddon(webLinksAddon);

    terminal.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Welcome message
    terminal.writeln('AI Assistant CLI v1.0.0');
    terminal.writeln('Type commands to interact with the AI assistant.');
    terminal.writeln('');
    terminal.write(PROMPT);

    // Handle input
    terminal.onData((data) => {
      const code = data.charCodeAt(0);

      // Handle special keys
      if (code === 13) { // Enter
        handleEnter(terminal);
      } else if (code === 127) { // Backspace
        handleBackspace(terminal);
      } else if (code === 27) { // Escape sequences (arrow keys)
        const sequence = data.slice(1);
        if (sequence === '[A') { // Up arrow
          handleArrowUp(terminal);
        } else if (sequence === '[B') { // Down arrow
          handleArrowDown(terminal);
        } else if (sequence === '[C') { // Right arrow
          handleArrowRight(terminal);
        } else if (sequence === '[D') { // Left arrow
          handleArrowLeft(terminal);
        }
      } else if (code >= 32 && code <= 126) { // Printable characters
        handlePrintableChar(terminal, data);
      }
    });

    // Handle window resize
    const handleResize = () => {
      fitAddon.fit();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      terminal.dispose();
    };
  }, []);

  const handleEnter = (terminal: XTerm) => {
    terminal.writeln('');
    
    if (currentLine.trim()) {
      // Add to history
      setCommandHistory(prev => [...prev, currentLine]);
      setHistoryIndex(-1);
      
      // Execute command
      if (onCommand) {
        onCommand(currentLine);
      }
    }
    
    // Reset for new command
    setCurrentLine('');
    setCursorPosition(0);
    terminal.write(PROMPT);
  };

  const handleBackspace = (terminal: XTerm) => {
    if (cursorPosition > 0) {
      const newLine = currentLine.slice(0, cursorPosition - 1) + currentLine.slice(cursorPosition);
      setCurrentLine(newLine);
      setCursorPosition(cursorPosition - 1);
      
      // Clear current line and rewrite
      terminal.write('\r' + PROMPT + newLine + ' ');
      // Move cursor to correct position
      const moveBack = newLine.length - cursorPosition + 1;
      if (moveBack > 0) {
        terminal.write('\x1b[' + moveBack + 'D');
      }
    }
  };

  const handleArrowUp = (terminal: XTerm) => {
    if (commandHistory.length > 0) {
      const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
      setHistoryIndex(newIndex);
      const historyCommand = commandHistory[newIndex];
      
      // Clear current line and write history command
      terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
      terminal.write('\r' + PROMPT + historyCommand);
      
      setCurrentLine(historyCommand);
      setCursorPosition(historyCommand.length);
    }
  };

  const handleArrowDown = (terminal: XTerm) => {
    if (historyIndex >= 0) {
      const newIndex = historyIndex + 1;
      
      if (newIndex >= commandHistory.length) {
        // Back to current line
        setHistoryIndex(-1);
        terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
        terminal.write('\r' + PROMPT);
        setCurrentLine('');
        setCursorPosition(0);
      } else {
        setHistoryIndex(newIndex);
        const historyCommand = commandHistory[newIndex];
        
        // Clear current line and write history command
        terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
        terminal.write('\r' + PROMPT + historyCommand);
        
        setCurrentLine(historyCommand);
        setCursorPosition(historyCommand.length);
      }
    }
  };

  const handleArrowLeft = (terminal: XTerm) => {
    if (cursorPosition > 0) {
      setCursorPosition(cursorPosition - 1);
      terminal.write('\x1b[D');
    }
  };

  const handleArrowRight = (terminal: XTerm) => {
    if (cursorPosition < currentLine.length) {
      setCursorPosition(cursorPosition + 1);
      terminal.write('\x1b[C');
    }
  };

  const handlePrintableChar = (terminal: XTerm, char: string) => {
    const newLine = currentLine.slice(0, cursorPosition) + char + currentLine.slice(cursorPosition);
    setCurrentLine(newLine);
    setCursorPosition(cursorPosition + 1);
    
    // Write character and update display
    if (cursorPosition === currentLine.length) {
      // At end of line, just write the character
      terminal.write(char);
    } else {
      // In middle of line, rewrite from cursor position
      const remaining = currentLine.slice(cursorPosition);
      terminal.write(char + remaining);
      // Move cursor back to correct position
      if (remaining.length > 0) {
        terminal.write('\x1b[' + remaining.length + 'D');
      }
    }
  };

  // Public methods for external control
  const writeOutput = (text: string) => {
    if (xtermRef.current) {
      xtermRef.current.writeln(text);
      if (!isStreaming) {
        xtermRef.current.write(PROMPT);
      }
    }
  };

  const writeError = (text: string) => {
    if (xtermRef.current) {
      xtermRef.current.write('\x1b[31m'); // Red color
      xtermRef.current.writeln(text);
      xtermRef.current.write('\x1b[0m'); // Reset color
      if (!isStreaming) {
        xtermRef.current.write(PROMPT);
      }
    }
  };

  const writeStream = (text: string) => {
    if (xtermRef.current) {
      xtermRef.current.write(text);
    }
  };

  const writePrompt = () => {
    if (xtermRef.current) {
      xtermRef.current.write(PROMPT);
    }
  };

  const clear = () => {
    if (xtermRef.current) {
      xtermRef.current.clear();
      xtermRef.current.write(PROMPT);
    }
  };

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    writeOutput,
    writeError,
    writeStream,
    writePrompt,
    clear,
  }));

  return (
    <div className={`terminal-container ${className}`}>
      <div 
        ref={terminalRef} 
        className="w-full h-full"
        style={{ minHeight: '400px' }}
      />
    </div>
  );
});

export default Terminal;