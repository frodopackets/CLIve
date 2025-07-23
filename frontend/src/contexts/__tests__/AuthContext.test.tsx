import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { User } from 'oidc-client-ts';
import { AuthProvider, useAuth } from '../AuthContext';
import authService from '../../services/authService';

// Mock the auth service
vi.mock('../../services/authService', () => ({
  default: {
    signIn: vi.fn(),
    signInCallback: vi.fn(),
    signOut: vi.fn(),
    getUser: vi.fn(),
    getAccessToken: vi.fn(),
    refreshToken: vi.fn(),
    removeUser: vi.fn(),
    convertToAuthUser: vi.fn(),
  },
}));

// Mock window.location
const mockLocation = {
  pathname: '/',
  origin: 'http://localhost:3000',
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock window.history
const mockHistory = {
  replaceState: vi.fn(),
};

Object.defineProperty(window, 'history', {
  value: mockHistory,
  writable: true,
});

// Test component that uses the auth context
const TestComponent = () => {
  const { user, isAuthenticated, isLoading, signIn, signOut } = useAuth();
  
  return (
    <div>
      <div data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="user">{user ? user.name : 'no-user'}</div>
      <button onClick={signIn} data-testid="signin">Sign In</button>
      <button onClick={signOut} data-testid="signout">Sign Out</button>
    </div>
  );
};

describe('AuthContext', () => {
  const mockUser: User = {
    access_token: 'test-token',
    refresh_token: 'refresh-token',
    expires_at: Date.now() / 1000 + 3600,
    expired: false,
    profile: {
      sub: 'user-id',
      email: 'test@example.com',
      name: 'Test User',
    },
  } as User;

  const mockAuthUser = {
    id: 'user-id',
    email: 'test@example.com',
    name: 'Test User',
    accessToken: 'test-token',
    refreshToken: 'refresh-token',
    expiresAt: Date.now() / 1000 + 3600,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.pathname = '/';
    (authService.convertToAuthUser as any).mockReturnValue(mockAuthUser);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should provide authentication context', async () => {
    (authService.getUser as any).mockResolvedValue(null);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('no-user');
  });

  it('should handle existing authenticated user', async () => {
    (authService.getUser as any).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('Test User');
  });

  it('should handle sign in callback', async () => {
    mockLocation.pathname = '/callback';
    (authService.signInCallback as any).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(authService.signInCallback).toHaveBeenCalled();
    expect(mockHistory.replaceState).toHaveBeenCalledWith({}, document.title, '/');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
  });

  it('should handle expired token with refresh', async () => {
    const expiredUser = { ...mockUser, expired: true };
    (authService.getUser as any)
      .mockResolvedValueOnce(expiredUser)
      .mockResolvedValueOnce(mockUser);
    (authService.refreshToken as any).mockResolvedValue(undefined);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(authService.refreshToken).toHaveBeenCalled();
    expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
  });

  it('should handle failed token refresh', async () => {
    const expiredUser = { ...mockUser, expired: true };
    (authService.getUser as any).mockResolvedValue(expiredUser);
    (authService.refreshToken as any).mockRejectedValue(new Error('Refresh failed'));
    (authService.removeUser as any).mockResolvedValue(undefined);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    expect(authService.refreshToken).toHaveBeenCalled();
    expect(authService.removeUser).toHaveBeenCalled();
    expect(screen.getByTestId('authenticated')).toHaveTextContent('not-authenticated');
  });

  it('should handle sign in', async () => {
    (authService.getUser as any).mockResolvedValue(null);
    (authService.signIn as any).mockResolvedValue(undefined);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('not-loading');
    });

    const signInButton = screen.getByTestId('signin');
    
    await act(async () => {
      signInButton.click();
    });

    expect(authService.signIn).toHaveBeenCalled();
  });

  it('should handle sign out', async () => {
    (authService.getUser as any).mockResolvedValue(mockUser);
    (authService.signOut as any).mockResolvedValue(undefined);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('authenticated');
    });

    const signOutButton = screen.getByTestId('signout');
    
    await act(async () => {
      signOutButton.click();
    });

    expect(authService.signOut).toHaveBeenCalled();
  });

  it('should throw error when useAuth is used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });
});