import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { UserManager, User } from 'oidc-client-ts';
import authService from '../authService';

// Mock oidc-client-ts
vi.mock('oidc-client-ts', () => ({
  UserManager: vi.fn(),
  User: vi.fn(),
}));

describe('AuthService', () => {
  let mockUserManager: any;
  let mockUser: User;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Mock UserManager
    mockUserManager = {
      signinRedirect: vi.fn(),
      signinRedirectCallback: vi.fn(),
      signoutRedirect: vi.fn(),
      getUser: vi.fn(),
      signinSilent: vi.fn(),
      removeUser: vi.fn(),
      events: {
        addUserLoaded: vi.fn(),
        addUserUnloaded: vi.fn(),
        addAccessTokenExpiring: vi.fn(),
        addAccessTokenExpired: vi.fn(),
        addSilentRenewError: vi.fn(),
      },
    };

    (UserManager as any).mockImplementation(() => mockUserManager);

    // Mock User
    mockUser = {
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      expires_at: Date.now() / 1000 + 3600, // 1 hour from now
      expired: false,
      profile: {
        sub: 'test-user-id',
        email: 'test@example.com',
        name: 'Test User',
        preferred_username: 'testuser',
      },
    } as User;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('signIn', () => {
    it('should call UserManager.signinRedirect', async () => {
      mockUserManager.signinRedirect.mockResolvedValue(undefined);

      await authService.signIn();

      expect(mockUserManager.signinRedirect).toHaveBeenCalledOnce();
    });

    it('should throw error when signIn fails', async () => {
      const error = new Error('Sign in failed');
      mockUserManager.signinRedirect.mockRejectedValue(error);

      await expect(authService.signIn()).rejects.toThrow('Failed to initiate sign in');
    });
  });

  describe('signInCallback', () => {
    it('should return user from callback', async () => {
      mockUserManager.signinRedirectCallback.mockResolvedValue(mockUser);

      const result = await authService.signInCallback();

      expect(result).toBe(mockUser);
      expect(mockUserManager.signinRedirectCallback).toHaveBeenCalledOnce();
    });

    it('should throw error when callback fails', async () => {
      const error = new Error('Callback failed');
      mockUserManager.signinRedirectCallback.mockRejectedValue(error);

      await expect(authService.signInCallback()).rejects.toThrow('Failed to complete sign in');
    });
  });

  describe('signOut', () => {
    it('should call UserManager.signoutRedirect', async () => {
      mockUserManager.signoutRedirect.mockResolvedValue(undefined);

      await authService.signOut();

      expect(mockUserManager.signoutRedirect).toHaveBeenCalledOnce();
    });

    it('should throw error when signOut fails', async () => {
      const error = new Error('Sign out failed');
      mockUserManager.signoutRedirect.mockRejectedValue(error);

      await expect(authService.signOut()).rejects.toThrow('Failed to sign out');
    });
  });

  describe('getUser', () => {
    it('should return user when available', async () => {
      mockUserManager.getUser.mockResolvedValue(mockUser);

      const result = await authService.getUser();

      expect(result).toBe(mockUser);
      expect(mockUserManager.getUser).toHaveBeenCalledOnce();
    });

    it('should return null when getUser fails', async () => {
      const error = new Error('Get user failed');
      mockUserManager.getUser.mockRejectedValue(error);

      const result = await authService.getUser();

      expect(result).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when user exists and is not expired', async () => {
      mockUserManager.getUser.mockResolvedValue(mockUser);

      const result = await authService.isAuthenticated();

      expect(result).toBe(true);
    });

    it('should return false when user is expired', async () => {
      const expiredUser = { ...mockUser, expired: true };
      mockUserManager.getUser.mockResolvedValue(expiredUser);

      const result = await authService.isAuthenticated();

      expect(result).toBe(false);
    });

    it('should return false when no user', async () => {
      mockUserManager.getUser.mockResolvedValue(null);

      const result = await authService.isAuthenticated();

      expect(result).toBe(false);
    });
  });

  describe('getAccessToken', () => {
    it('should return access token when user exists', async () => {
      mockUserManager.getUser.mockResolvedValue(mockUser);

      const result = await authService.getAccessToken();

      expect(result).toBe('test-access-token');
    });

    it('should return null when no user', async () => {
      mockUserManager.getUser.mockResolvedValue(null);

      const result = await authService.getAccessToken();

      expect(result).toBeNull();
    });
  });

  describe('refreshToken', () => {
    it('should call UserManager.signinSilent', async () => {
      mockUserManager.signinSilent.mockResolvedValue(mockUser);

      await authService.refreshToken();

      expect(mockUserManager.signinSilent).toHaveBeenCalledOnce();
    });

    it('should throw error when refresh fails', async () => {
      const error = new Error('Refresh failed');
      mockUserManager.signinSilent.mockRejectedValue(error);

      await expect(authService.refreshToken()).rejects.toThrow('Failed to refresh token');
    });
  });

  describe('convertToAuthUser', () => {
    it('should convert OIDC user to AuthUser', () => {
      const result = authService.convertToAuthUser(mockUser);

      expect(result).toEqual({
        id: 'test-user-id',
        email: 'test@example.com',
        name: 'Test User',
        accessToken: 'test-access-token',
        refreshToken: 'test-refresh-token',
        expiresAt: mockUser.expires_at,
      });
    });

    it('should handle missing profile fields', () => {
      const userWithMissingFields = {
        ...mockUser,
        profile: {
          sub: 'test-user-id',
          preferred_username: 'testuser',
        },
      } as User;

      const result = authService.convertToAuthUser(userWithMissingFields);

      expect(result).toEqual({
        id: 'test-user-id',
        email: '',
        name: 'testuser',
        accessToken: 'test-access-token',
        refreshToken: 'test-refresh-token',
        expiresAt: mockUser.expires_at,
      });
    });
  });

  describe('removeUser', () => {
    it('should call UserManager.removeUser', async () => {
      mockUserManager.removeUser.mockResolvedValue(undefined);

      await authService.removeUser();

      expect(mockUserManager.removeUser).toHaveBeenCalledOnce();
    });

    it('should not throw when removeUser fails', async () => {
      const error = new Error('Remove user failed');
      mockUserManager.removeUser.mockRejectedValue(error);

      await expect(authService.removeUser()).resolves.toBeUndefined();
    });
  });
});