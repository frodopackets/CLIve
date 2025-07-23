import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import KnowledgeBaseSelector from '../KnowledgeBaseSelector';

describe('KnowledgeBaseSelector Component', () => {
  const mockOnKnowledgeBaseChange = vi.fn();

  const defaultProps = {
    onKnowledgeBaseChange: mockOnKnowledgeBaseChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    render(<KnowledgeBaseSelector {...defaultProps} />);
    
    expect(screen.getByText('Loading knowledge bases...')).toBeInTheDocument();
  });

  it('renders knowledge base selector after loading', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Select Knowledge Base')).toBeInTheDocument();
    });
  });

  it('displays selected knowledge base', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} selectedKnowledgeBase="tech" />);
    
    await waitFor(() => {
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });
  });

  it('opens dropdown when clicked', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} />);
    
    await waitFor(() => {
      const button = screen.getByText('Select Knowledge Base');
      fireEvent.click(button);
    });

    expect(screen.getByText('General Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
    expect(screen.getByText('Science')).toBeInTheDocument();
    expect(screen.getByText('Business')).toBeInTheDocument();
  });

  it('calls onKnowledgeBaseChange when option is selected', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} />);
    
    await waitFor(() => {
      const button = screen.getByText('Select Knowledge Base');
      fireEvent.click(button);
    });

    const techOption = screen.getByText('Technology');
    fireEvent.click(techOption);

    expect(mockOnKnowledgeBaseChange).toHaveBeenCalledWith('tech');
  });

  it('shows knowledge base info when selected', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} selectedKnowledgeBase="general" />);
    
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('ID: general')).toBeInTheDocument();
      expect(screen.getByText('General purpose AI assistant knowledge base')).toBeInTheDocument();
    });
  });

  it('only shows active knowledge bases in dropdown', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} />);
    
    await waitFor(() => {
      const button = screen.getByText('Select Knowledge Base');
      fireEvent.click(button);
    });

    // Should show active knowledge bases
    expect(screen.getByText('General Knowledge')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
    expect(screen.getByText('Science')).toBeInTheDocument();
    expect(screen.getByText('Business')).toBeInTheDocument();
    
    // Should not show inactive knowledge base
    expect(screen.queryByText('Medical')).not.toBeInTheDocument();
  });

  it('closes dropdown after selection', async () => {
    render(<KnowledgeBaseSelector {...defaultProps} />);
    
    await waitFor(() => {
      const button = screen.getByText('Select Knowledge Base');
      fireEvent.click(button);
    });

    const techOption = screen.getByText('Technology');
    fireEvent.click(techOption);

    // Dropdown should be closed, so options should not be visible
    await waitFor(() => {
      expect(screen.queryByText('General Knowledge')).not.toBeInTheDocument();
    });
  });
});