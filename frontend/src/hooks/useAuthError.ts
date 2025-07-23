import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

export interface AuthError {
  code: string;
  message: string;
  statusCode?: number;
}

export const useAuthError = () => {
  const { signOut } = useAuth();

  const handleAuthError = useCallback(async (error: AuthError | Error) => {
    const authError = error instanceof Error 
      ? { code: 'UNKNOWN', message: error.message }
      : error;

    console.error('Authentication error:', authError);

    switch (authError.code) {
      case 'TOKEN_EXPIRED':
      case 'INVALID_TOKEN':
      case 'UNAUTHORIZED':
        // Token is invalid or expired, sign out user
        try {
          await signOut();
        } catch (signOutError) {
          console.error('Error during sign out:', signOutError);
        }
        break;

      case 'NETWORK_ERROR':
        // Network error, could be temporary
        console.warn('Network error during authentication, user may need to retry');
        break;

      case 'FORBIDDEN':
        // User doesn't have permission
        console.error('User does not have permission to access this resource');
        break;

      default:
        console.error('Unhandled authentication error:', authError);
    }
  }, [signOut]);

  const isAuthError = useCallback((error: Error): boolean => {
    const authErrorPatterns = [
      /token.*expired/i,
      /invalid.*token/i,
      /unauthorized/i,
      /authentication.*failed/i,
      /access.*denied/i,
      /forbidden/i,
    ];

    return authErrorPatterns.some(pattern => pattern.test(error.message));
  }, []);

  const createAuthError = useCallback((
    code: string, 
    message: string, 
    statusCode?: number
  ): AuthError => {
    return { code, message, statusCode };
  }, []);

  return {
    handleAuthError,
    isAuthError,
    createAuthError,
  };
};