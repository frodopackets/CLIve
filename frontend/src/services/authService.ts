import { UserManager, User, UserManagerSettings } from 'oidc-client-ts';

export interface AuthConfig {
  authority: string;
  clientId: string;
  redirectUri: string;
  postLogoutRedirectUri: string;
  scope: string;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
}

class AuthService {
  private userManager: UserManager;

  constructor(config: AuthConfig) {
    
    const settings: UserManagerSettings = {
      authority: config.authority,
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      post_logout_redirect_uri: config.postLogoutRedirectUri,
      response_type: 'code',
      scope: config.scope,
      automaticSilentRenew: true,
      silent_redirect_uri: `${window.location.origin}/silent-callback.html`,
      filterProtocolClaims: true,
      loadUserInfo: true,
    };

    this.userManager = new UserManager(settings);
    
    // Set up event handlers
    this.userManager.events.addUserLoaded((user) => {
      console.log('User loaded:', user);
    });

    this.userManager.events.addUserUnloaded(() => {
      console.log('User unloaded');
    });

    this.userManager.events.addAccessTokenExpiring(() => {
      console.log('Access token expiring');
    });

    this.userManager.events.addAccessTokenExpired(() => {
      console.log('Access token expired');
      this.signoutRedirect();
    });

    this.userManager.events.addSilentRenewError((error) => {
      console.error('Silent renew error:', error);
    });
  }

  async signIn(): Promise<void> {
    try {
      await this.userManager.signinRedirect();
    } catch (error) {
      console.error('Sign in error:', error);
      throw new Error('Failed to initiate sign in');
    }
  }

  async signInCallback(): Promise<User> {
    try {
      const user = await this.userManager.signinRedirectCallback();
      return user;
    } catch (error) {
      console.error('Sign in callback error:', error);
      throw new Error('Failed to complete sign in');
    }
  }

  async signOut(): Promise<void> {
    try {
      await this.userManager.signoutRedirect();
    } catch (error) {
      console.error('Sign out error:', error);
      throw new Error('Failed to sign out');
    }
  }

  async signoutRedirect(): Promise<void> {
    try {
      await this.userManager.signoutRedirect();
    } catch (error) {
      console.error('Sign out redirect error:', error);
    }
  }

  async getUser(): Promise<User | null> {
    try {
      return await this.userManager.getUser();
    } catch (error) {
      console.error('Get user error:', error);
      return null;
    }
  }

  async isAuthenticated(): Promise<boolean> {
    const user = await this.getUser();
    return user !== null && !user.expired;
  }

  async getAccessToken(): Promise<string | null> {
    const user = await this.getUser();
    return user?.access_token || null;
  }

  async refreshToken(): Promise<void> {
    try {
      await this.userManager.signinSilent();
    } catch (error) {
      console.error('Token refresh error:', error);
      throw new Error('Failed to refresh token');
    }
  }

  convertToAuthUser(user: User): AuthUser {
    return {
      id: user.profile.sub || '',
      email: user.profile.email || '',
      name: user.profile.name || user.profile.preferred_username || '',
      accessToken: user.access_token,
      refreshToken: user.refresh_token,
      expiresAt: user.expires_at || 0,
    };
  }

  // Remove user from storage (for logout)
  async removeUser(): Promise<void> {
    try {
      await this.userManager.removeUser();
    } catch (error) {
      console.error('Remove user error:', error);
    }
  }
}

// Default configuration - should be overridden with actual Identity Center values
const defaultConfig: AuthConfig = {
  authority: process.env.VITE_IDENTITY_CENTER_AUTHORITY || 'https://your-identity-center-domain.awsapps.com/start',
  clientId: process.env.VITE_IDENTITY_CENTER_CLIENT_ID || 'your-client-id',
  redirectUri: `${window.location.origin}/callback`,
  postLogoutRedirectUri: `${window.location.origin}/`,
  scope: 'openid profile email',
};

export const authService = new AuthService(defaultConfig);
export default authService;