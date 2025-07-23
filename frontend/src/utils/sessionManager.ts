import { AuthUser } from '../types';

const SESSION_STORAGE_KEY = 'ai_assistant_session';
const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

export interface SessionData {
  user: AuthUser;
  timestamp: number;
  expiresAt: number;
}

export class SessionManager {
  static saveSession(user: AuthUser): void {
    const sessionData: SessionData = {
      user,
      timestamp: Date.now(),
      expiresAt: user.expiresAt * 1000, // Convert to milliseconds
    };

    try {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessionData));
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  }

  static getSession(): SessionData | null {
    try {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY);
      if (!stored) return null;

      const sessionData: SessionData = JSON.parse(stored);
      
      // Check if session has expired
      if (this.isSessionExpired(sessionData)) {
        this.clearSession();
        return null;
      }

      return sessionData;
    } catch (error) {
      console.error('Failed to get session:', error);
      this.clearSession();
      return null;
    }
  }

  static clearSession(): void {
    try {
      localStorage.removeItem(SESSION_STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
  }

  static isSessionExpired(sessionData: SessionData): boolean {
    const now = Date.now();
    
    // Check if the token has expired
    if (sessionData.expiresAt && now >= sessionData.expiresAt) {
      return true;
    }

    // Check if the session is older than our timeout
    if (now - sessionData.timestamp > SESSION_TIMEOUT) {
      return true;
    }

    return false;
  }

  static updateSessionActivity(): void {
    const session = this.getSession();
    if (session) {
      session.timestamp = Date.now();
      try {
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      } catch (error) {
        console.error('Failed to update session activity:', error);
      }
    }
  }

  static getRemainingTime(): number {
    const session = this.getSession();
    if (!session) return 0;

    const now = Date.now();
    const timeUntilExpiry = session.expiresAt - now;
    const timeUntilTimeout = SESSION_TIMEOUT - (now - session.timestamp);

    return Math.min(timeUntilExpiry, timeUntilTimeout);
  }

  static isSessionValid(): boolean {
    const session = this.getSession();
    return session !== null && !this.isSessionExpired(session);
  }
}