import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import Login from './Login';
import AuthLoading from './AuthLoading';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loadingFallback?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  fallback,
  loadingFallback,
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <>{loadingFallback || <AuthLoading />}</>;
  }

  if (!isAuthenticated) {
    return <>{fallback || <Login />}</>;
  }

  return <>{children}</>;
};

export default ProtectedRoute;