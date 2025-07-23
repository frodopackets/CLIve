import React from 'react';

interface AuthLoadingProps {
  className?: string;
}

const AuthLoading: React.FC<AuthLoadingProps> = ({ className = '' }) => {
  return (
    <div className={`flex flex-col items-center justify-center min-h-screen bg-black text-green-400 ${className}`}>
      <div className="text-center">
        <div className="mb-4">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-400"></div>
        </div>
        <h2 className="text-xl font-mono mb-2">AI Assistant CLI</h2>
        <p className="text-sm text-green-300">Authenticating...</p>
      </div>
    </div>
  );
};

export default AuthLoading;