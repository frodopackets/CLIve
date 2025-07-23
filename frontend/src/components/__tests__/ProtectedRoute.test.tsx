import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProtectedRoute from '../ProtectedRoute';
import { useAuth } from '../../contexts/AuthContext';

// Mock the auth context
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock child components
vi.mock('../Login', () => ({
  default: () => <div data-testid="login">Login Component</div>,
}));

vi.mock('../AuthLoading', () => ({
  default: () => <div data-testid="auth-loading">Loading Component</div>,
}));

describe('ProtectedRoute', () => {
  const mockUseAuth = {
    isAuthenticated: false,
    isLoading: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue(mockUseAuth);
  });

  it('should render children when authenticated', () => {
    (useAuth as any).mockReturnValue({
      ...mockUseAuth,
      isAuthenticated: true,
    });

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.queryByTestId('login')).not.toBeInTheDocument();
    expect(screen.queryByTestId('auth-loading')).not.toBeInTheDocument();
  });

  it('should render loading component when loading', () => {
    (useAuth as any).mockReturnValue({
      ...mockUseAuth,
      isLoading: true,
    });

    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByTestId('auth-loading')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.queryByTestId('login')).not.toBeInTheDocument();
  });

  it('should render login component when not authenticated', () => {
    render(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByTestId('login')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.queryByTestId('auth-loading')).not.toBeInTheDocument();
  });

  it('should render custom fallback when provided', () => {
    const CustomFallback = () => <div data-testid="custom-fallback">Custom Fallback</div>;

    render(
      <ProtectedRoute fallback={<CustomFallback />}>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.queryByTestId('login')).not.toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  it('should render custom loading fallback when provided', () => {
    (useAuth as any).mockReturnValue({
      ...mockUseAuth,
      isLoading: true,
    });

    const CustomLoading = () => <div data-testid="custom-loading">Custom Loading</div>;

    render(
      <ProtectedRoute loadingFallback={<CustomLoading />}>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByTestId('custom-loading')).toBeInTheDocument();
    expect(screen.queryByTestId('auth-loading')).not.toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });
});