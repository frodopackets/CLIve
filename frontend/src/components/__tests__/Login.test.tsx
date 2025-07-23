import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../Login';
import { useAuth } from '../../contexts/AuthContext';

// Mock the auth context
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('Login', () => {
  const mockSignIn = vi.fn();
  const mockUseAuth = {
    signIn: mockSignIn,
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue(mockUseAuth);
  });

  it('should render login form', () => {
    render(<Login />);

    expect(screen.getByText('AI Assistant CLI')).toBeInTheDocument();
    expect(screen.getByText('Please sign in to continue')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in with Identity Center' })).toBeInTheDocument();
    expect(screen.getByText('This application uses AWS Identity Center for authentication')).toBeInTheDocument();
  });

  it('should call signIn when button is clicked', async () => {
    mockSignIn.mockResolvedValue(undefined);

    render(<Login />);

    const signInButton = screen.getByRole('button', { name: 'Sign in with Identity Center' });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledOnce();
    });
  });

  it('should show loading state', () => {
    (useAuth as any).mockReturnValue({
      ...mockUseAuth,
      isLoading: true,
    });

    render(<Login />);

    const button = screen.getByRole('button');
    expect(button).toHaveTextContent('Signing in...');
    expect(button).toBeDisabled();
  });

  it('should display error message when sign in fails', async () => {
    const errorMessage = 'Sign in failed';
    mockSignIn.mockRejectedValue(new Error(errorMessage));

    render(<Login />);

    const signInButton = screen.getByRole('button', { name: 'Sign in with Identity Center' });
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Error should be displayed in red styling
    const errorDiv = screen.getByText(errorMessage).closest('div');
    expect(errorDiv).toHaveClass('border-red-400', 'bg-red-900/20', 'text-red-400');
  });

  it('should clear error when signing in again', async () => {
    const errorMessage = 'Sign in failed';
    mockSignIn
      .mockRejectedValueOnce(new Error(errorMessage))
      .mockResolvedValueOnce(undefined);

    render(<Login />);

    const signInButton = screen.getByRole('button', { name: 'Sign in with Identity Center' });
    
    // First click - should show error
    fireEvent.click(signInButton);
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Second click - should clear error
    fireEvent.click(signInButton);
    await waitFor(() => {
      expect(screen.queryByText(errorMessage)).not.toBeInTheDocument();
    });
  });

  it('should apply custom className', () => {
    const customClass = 'custom-login-class';
    render(<Login className={customClass} />);

    const container = screen.getByText('AI Assistant CLI').closest('div');
    expect(container).toHaveClass(customClass);
  });

  it('should have proper styling for terminal theme', () => {
    render(<Login />);

    const container = screen.getByText('AI Assistant CLI').closest('div');
    expect(container).toHaveClass('bg-black', 'text-green-400');

    const formContainer = screen.getByText('Please sign in to continue').closest('div');
    expect(formContainer).toHaveClass('border-green-400', 'bg-black');

    const button = screen.getByRole('button', { name: 'Sign in with Identity Center' });
    expect(button).toHaveClass('border-green-400', 'text-green-400', 'font-mono');
  });
});