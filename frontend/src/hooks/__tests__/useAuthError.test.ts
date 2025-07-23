import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAuthError } from '../useAuthError';
import { useAuth } from '../../contexts/AuthContext';

// Mock the auth context
vi.mock('../../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

describe('useAuthError', () => {
  const mockSignOut = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue({
      signOut: mockSignOut,
    });
  });

  describe('handleAuthError', () => {
    it('should handle TOKEN_EXPIRED error by signing out', async () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = { code: 'TOKEN_EXPIRED', message: 'Token has expired' };
      await result.current.handleAuthError(error);

      expect(mockSignOut).toHaveBeenCalledOnce();
    });

    it('should handle INVALID_TOKEN error by signing out', async () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = { code: 'INVALID_TOKEN', message: 'Invalid token' };
      await result.current.handleAuthError(error);

      expect(mockSignOut).toHaveBeenCalledOnce();
    });

    it('should handle UNAUTHORIZED error by signing out', async () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = { code: 'UNAUTHORIZED', message: 'Unauthorized access' };
      await result.current.handleAuthError(error);

      expect(mockSignOut).toHaveBeenCalledOnce();
    });

    it('should handle NETWORK_ERROR without signing out', async () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = { code: 'NETWORK_ERROR', message: 'Network error' };
      await result.current.handleAuthError(error);

      expect(mockSignOut).not.toHaveBeenCalled();
    });

    it('should handle FORBIDDEN error without signing out', async () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = { code: 'FORBIDDEN', message: 'Access forbidden' };
      await result.current.handleAuthError(error);

      expect(mockSignOut).not.toHaveBeenCalled();
    });

    it('should handle Error objects', async () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Some error message');
      await result.current.handleAuthError(error);

      // Should not sign out for unknown errors
      expect(mockSignOut).not.toHaveBeenCalled();
    });

    it('should handle sign out errors gracefully', async () => {
      mockSignOut.mockRejectedValue(new Error('Sign out failed'));
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { result } = renderHook(() => useAuthError());
      
      const error = { code: 'TOKEN_EXPIRED', message: 'Token has expired' };
      await result.current.handleAuthError(error);

      expect(mockSignOut).toHaveBeenCalledOnce();
      expect(consoleSpy).toHaveBeenCalledWith('Error during sign out:', expect.any(Error));

      consoleSpy.mockRestore();
    });
  });

  describe('isAuthError', () => {
    it('should identify token expired errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Token has expired');
      expect(result.current.isAuthError(error)).toBe(true);
    });

    it('should identify invalid token errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Invalid token provided');
      expect(result.current.isAuthError(error)).toBe(true);
    });

    it('should identify unauthorized errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Unauthorized access');
      expect(result.current.isAuthError(error)).toBe(true);
    });

    it('should identify authentication failed errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Authentication failed');
      expect(result.current.isAuthError(error)).toBe(true);
    });

    it('should identify access denied errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Access denied');
      expect(result.current.isAuthError(error)).toBe(true);
    });

    it('should identify forbidden errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Forbidden resource');
      expect(result.current.isAuthError(error)).toBe(true);
    });

    it('should not identify non-auth errors', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = new Error('Network connection failed');
      expect(result.current.isAuthError(error)).toBe(false);
    });
  });

  describe('createAuthError', () => {
    it('should create auth error object', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = result.current.createAuthError('TEST_CODE', 'Test message', 401);
      
      expect(error).toEqual({
        code: 'TEST_CODE',
        message: 'Test message',
        statusCode: 401,
      });
    });

    it('should create auth error without status code', () => {
      const { result } = renderHook(() => useAuthError());
      
      const error = result.current.createAuthError('TEST_CODE', 'Test message');
      
      expect(error).toEqual({
        code: 'TEST_CODE',
        message: 'Test message',
      });
    });
  });
});