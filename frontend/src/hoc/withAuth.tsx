import React, { ComponentType } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Login from '../components/Login';
import AuthLoading from '../components/AuthLoading';

interface WithAuthOptions {
  fallback?: React.ComponentType;
  loadingFallback?: React.ComponentType;
  requireAuth?: boolean;
}

export function withAuth<P extends object>(
  WrappedComponent: ComponentType<P>,
  options: WithAuthOptions = {}
) {
  const {
    fallback: FallbackComponent = Login,
    loadingFallback: LoadingComponent = AuthLoading,
    requireAuth = true,
  } = options;

  const WithAuthComponent: React.FC<P> = (props) => {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return <LoadingComponent />;
    }

    if (requireAuth && !isAuthenticated) {
      return <FallbackComponent />;
    }

    return <WrappedComponent {...props} />;
  };

  WithAuthComponent.displayName = `withAuth(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithAuthComponent;
}

export default withAuth;