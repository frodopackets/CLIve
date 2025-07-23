import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface LoginProps {
  className?: string;
}

const Login: React.FC<LoginProps> = ({ className = '' }) => {
  const { signIn, isLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async () => {
    try {
      setError(null);
      await signIn();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Sign in failed';
      setError(errorMessage);
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center min-h-screen bg-black text-green-400 ${className}`}>
      <div className="max-w-md w-full mx-auto p-8 border border-green-400 rounded-lg bg-black">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-mono mb-2">AI Assistant CLI</h1>
          <p className="text-sm text-green-300">Please sign in to continue</p>
        </div>

        {error && (
          <div className="mb-4 p-3 border border-red-400 rounded bg-red-900/20 text-red-400">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <div className="space-y-4">
          <button
            onClick={handleSignIn}
            disabled={isLoading}
            className={`
              w-full py-3 px-4 border border-green-400 rounded
              font-mono text-sm
              transition-colors duration-200
              ${isLoading 
                ? 'bg-gray-800 text-gray-400 cursor-not-allowed' 
                : 'bg-black text-green-400 hover:bg-green-400 hover:text-black'
              }
            `}
          >
            {isLoading ? 'Signing in...' : 'Sign in with Identity Center'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-green-300">
            This application uses AWS Identity Center for authentication
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;