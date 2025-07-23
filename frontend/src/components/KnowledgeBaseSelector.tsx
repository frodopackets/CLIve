import React, { useState, useEffect } from 'react';
import { KnowledgeBase } from '../types';
import { knowledgeBaseService } from '../services/knowledgeBaseService';

interface KnowledgeBaseSelectorProps {
  selectedKnowledgeBase?: string;
  onKnowledgeBaseChange: (knowledgeBaseId: string) => void;
  className?: string;
}

export const KnowledgeBaseSelector: React.FC<KnowledgeBaseSelectorProps> = ({
  selectedKnowledgeBase,
  onKnowledgeBaseChange,
  className = '',
}) => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  // Load knowledge bases from the service
  useEffect(() => {
    const loadKnowledgeBases = async () => {
      try {
        setIsLoading(true);
        const kbs = await knowledgeBaseService.listKnowledgeBases();
        setKnowledgeBases(kbs);
      } catch (error) {
        console.error('Failed to load knowledge bases:', error);
        // Set empty array on error - service will provide defaults
        setKnowledgeBases([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadKnowledgeBases();
  }, []);

  const activeKnowledgeBases = knowledgeBases.filter(kb => kb.status === 'ACTIVE');
  const selectedKb = knowledgeBases.find(kb => kb.id === selectedKnowledgeBase);

  const handleSelect = (knowledgeBaseId: string) => {
    onKnowledgeBaseChange(knowledgeBaseId);
    setIsOpen(false);
  };

  if (isLoading) {
    return (
      <div className={`knowledge-base-selector ${className}`}>
        <div className="flex items-center space-x-2 text-gray-400">
          <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading knowledge bases...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`knowledge-base-selector relative ${className}`}>
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center justify-between w-full px-3 py-2 text-sm bg-gray-800 border border-gray-600 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              selectedKb ? 'bg-green-400' : 'bg-gray-400'
            }`} />
            <span className="text-gray-200">
              {selectedKb ? selectedKb.name : 'Select Knowledge Base'}
            </span>
          </div>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${
              isOpen ? 'transform rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
            <ul className="py-1" role="listbox">
              {activeKnowledgeBases.map((kb) => (
                <li key={kb.id} role="option" aria-selected={selectedKnowledgeBase === kb.id}>
                  <button
                    onClick={() => handleSelect(kb.id)}
                    className={`w-full px-3 py-2 text-left hover:bg-gray-700 focus:outline-none focus:bg-gray-700 ${
                      selectedKnowledgeBase === kb.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{kb.name}</div>
                        <div className="text-xs text-gray-400 mt-1">{kb.description}</div>
                      </div>
                      {selectedKnowledgeBase === kb.id && (
                        <svg
                          className="w-4 h-4 text-white"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Knowledge Base Info */}
      {selectedKb && (
        <div className="mt-2 p-2 bg-gray-900 rounded-md border border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <span className="text-xs font-medium text-green-400">Active</span>
            </div>
            <span className="text-xs text-gray-400">ID: {selectedKb.id}</span>
          </div>
          <p className="text-xs text-gray-300 mt-1">{selectedKb.description}</p>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseSelector;