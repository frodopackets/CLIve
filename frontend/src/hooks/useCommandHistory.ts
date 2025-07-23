import { useState, useCallback } from 'react';

export interface CommandHistoryItem {
  id: string;
  command: string;
  timestamp: Date;
  response?: string;
  error?: string;
}

export const useCommandHistory = () => {
  const [history, setHistory] = useState<CommandHistoryItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);

  const addCommand = useCallback((command: string, response?: string, error?: string) => {
    const newItem: CommandHistoryItem = {
      id: Date.now().toString(),
      command,
      timestamp: new Date(),
      response,
      error,
    };

    setHistory(prev => [...prev, newItem]);
    setCurrentIndex(-1); // Reset to current position
  }, []);

  const getPreviousCommand = useCallback(() => {
    if (history.length === 0) return null;
    
    const newIndex = currentIndex === -1 ? history.length - 1 : Math.max(0, currentIndex - 1);
    setCurrentIndex(newIndex);
    return history[newIndex].command;
  }, [history, currentIndex]);

  const getNextCommand = useCallback(() => {
    if (currentIndex === -1) return null;
    
    const newIndex = currentIndex + 1;
    if (newIndex >= history.length) {
      setCurrentIndex(-1);
      return '';
    }
    
    setCurrentIndex(newIndex);
    return history[newIndex].command;
  }, [history, currentIndex]);

  const clearHistory = useCallback(() => {
    setHistory([]);
    setCurrentIndex(-1);
  }, []);

  const getRecentCommands = useCallback((limit: number = 10) => {
    return history.slice(-limit).reverse();
  }, [history]);

  return {
    history,
    addCommand,
    getPreviousCommand,
    getNextCommand,
    clearHistory,
    getRecentCommands,
  };
};

export default useCommandHistory;