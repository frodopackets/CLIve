import { AuthError } from '../hooks/useAuthError';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  statusCode?: number;
}

export class ApiAuthError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'ApiAuthError';
  }
}

export const createAuthenticatedFetch = (getAccessToken: () => Promise<string | null>) => {
  return async (url: string, options: RequestInit = {}): Promise<Response> => {
    const token = await getAccessToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle authentication errors
    if (response.status === 401) {
      throw new ApiAuthError(
        'UNAUTHORIZED',
        'Authentication required',
        401
      );
    }

    if (response.status === 403) {
      throw new ApiAuthError(
        'FORBIDDEN',
        'Access denied',
        403
      );
    }

    return response;
  };
};

export const handleApiError = (error: unknown): AuthError => {
  if (error instanceof ApiAuthError) {
    return {
      code: error.code,
      message: error.message,
      statusCode: error.statusCode,
    };
  }

  if (error instanceof Error) {
    // Check for network errors
    if (error.message.includes('fetch')) {
      return {
        code: 'NETWORK_ERROR',
        message: 'Network error occurred',
      };
    }

    return {
      code: 'UNKNOWN',
      message: error.message,
    };
  }

  return {
    code: 'UNKNOWN',
    message: 'An unknown error occurred',
  };
};

export const isTokenExpiredError = (error: unknown): boolean => {
  if (error instanceof ApiAuthError) {
    return error.code === 'UNAUTHORIZED' || error.code === 'TOKEN_EXPIRED';
  }

  if (error instanceof Error) {
    return /token.*expired|unauthorized/i.test(error.message);
  }

  return false;
};