import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface UserInfoProps {
  className?: string;
}

const UserInfo: React.FC<UserInfoProps> = ({ className = '' }) => {
  const { user, signOut, isLoading } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out failed:', error);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center space-x-2 text-green-400 hover:text-green-300 transition-colors"
        disabled={isLoading}
      >
        <span className="text-sm font-mono">{user.name || user.email}</span>
        <svg 
          className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {showDropdown && (
        <div className="absolute right-0 top-full mt-1 w-48 bg-black border border-green-400 rounded shadow-lg z-50">
          <div className="p-3 border-b border-green-400">
            <p className="text-xs text-green-300">Signed in as:</p>
            <p className="text-sm font-mono text-green-400 truncate">{user.email}</p>
          </div>
          <div className="p-1">
            <button
              onClick={handleSignOut}
              disabled={isLoading}
              className={`
                w-full text-left px-3 py-2 text-sm font-mono rounded
                transition-colors
                ${isLoading 
                  ? 'text-gray-400 cursor-not-allowed' 
                  : 'text-green-400 hover:bg-green-400 hover:text-black'
                }
              `}
            >
              {isLoading ? 'Signing out...' : 'Sign out'}
            </button>
          </div>
        </div>
      )}

      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};

export default UserInfo;