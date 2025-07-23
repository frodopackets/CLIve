import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import authService, { AuthUser } from '../services/authService';
import { SessionManager } from '../utils/sessionManager';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        
        // Check if we're returning from a sign-in callback
        if (window.location.pathname === '/callback') {
          try {
            const oidcUser = await authService.signInCallback();
            const authUser = authService.convertToAuthUser(oidcUser);
            setUser(authUser);
            
            // Redirect to main app after successful callback
            window.history.replaceState({}, document.title, '/');
            return;
          } catch (error) {
            console.error('Sign in callback failed:', error);
            // Redirect to home on callback error
            window.history.replaceState({}, document.title, '/');
          }
        }

        // Check for existing session first
        const savedSession = SessionManager.getSession();
        if (savedSession && SessionManager.isSessionValid()) {
          setUser(savedSession.user);
          return;
        }

        // Check for existing user session from OIDC
        const existingUser = await authService.getUser();
        if (existingUser && !existingUser.expired) {
          const authUser = authService.convertToAuthUser(existingUser);
          setUser(authUser);
          SessionManager.saveSession(authUser);
        } else if (existingUser && existingUser.expired) {
          // Try to refresh the token
          try {
            await authService.refreshToken();
            const refreshedUser = await authService.getUser();
            if (refreshedUser) {
              const authUser = authService.convertToAuthUser(refreshedUser);
              setUser(authUser);
              SessionManager.saveSession(authUser);
            }
          } catch (error) {
            console.error('Token refresh failed:', error);
            await authService.removeUser();
            SessionManager.clearSession();
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const signIn = async (): Promise<void> => {
    try {
      setIsLoading(true);
      await authService.signIn();
    } catch (error) {
      console.error('Sign in failed:', error);
      setIsLoading(false);
      throw error;
    }
  };

  const signOut = async (): Promise<void> => {
    try {
      setIsLoading(true);
      setUser(null);
      SessionManager.clearSession();
      await authService.signOut();
    } catch (error) {
      console.error('Sign out failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const getAccessToken = async (): Promise<string | null> => {
    try {
      return await authService.getAccessToken();
    } catch (error) {
      console.error('Get access token failed:', error);
      return null;
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      await authService.refreshToken();
      const refreshedUser = await authService.getUser();
      if (refreshedUser) {
        const authUser = authService.convertToAuthUser(refreshedUser);
        setUser(authUser);
        SessionManager.saveSession(authUser);
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      setUser(null);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    signIn,
    signOut,
    getAccessToken,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;