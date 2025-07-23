import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class AuthErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Authentication error caught by boundary:', error, errorInfo);
    
    // Check if this is an authentication-related error
    if (this.isAuthError(error)) {
      // Handle authentication errors specifically
      this.handleAuthError(error);
    }
  }

  private isAuthError(error: Error): boolean {
    const authErrorMessages = [
      'useAuth must be used within an AuthProvider',
      'Authentication failed',
      'Token expired',
      'Invalid token',
      'Access denied',
      'Unauthorized',
    ];

    return authErrorMessages.some(message => 
      error.message.includes(message)
    );
  }

  private handleAuthError(error: Error) {
    // Log the authentication error
    console.error('Authentication error:', error.message);
    
    // You could also trigger additional actions here like:
    // - Clearing stored tokens
    // - Redirecting to login
    // - Showing specific error messages
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black text-green-400">
          <div className="max-w-md w-full mx-auto p-8 border border-red-400 rounded-lg bg-black">
            <div className="text-center mb-6">
              <h1 className="text-xl font-mono mb-2 text-red-400">Authentication Error</h1>
              <p className="text-sm text-red-300">
                {this.state.error?.message || 'An authentication error occurred'}
              </p>
            </div>

            <div className="space-y-4">
              <button
                onClick={this.handleRetry}
                className="w-full py-3 px-4 border border-green-400 rounded font-mono text-sm bg-black text-green-400 hover:bg-green-400 hover:text-black transition-colors duration-200"
              >
                Try Again
              </button>
              
              <button
                onClick={() => window.location.reload()}
                className="w-full py-3 px-4 border border-gray-400 rounded font-mono text-sm bg-black text-gray-400 hover:bg-gray-400 hover:text-black transition-colors duration-200"
              >
                Reload Page
              </button>
            </div>

            <div className="mt-6 text-center">
              <p className="text-xs text-gray-400">
                If this problem persists, please contact support
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default AuthErrorBoundary;