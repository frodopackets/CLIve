"""
Authentication service for JWT token validation and user context management
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

import jwt
from jwt import PyJWTError
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request


logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """
    User context extracted from JWT token
    """
    user_id: str
    email: str
    name: str
    groups: list[str]
    issued_at: datetime
    expires_at: datetime
    token_id: str
    
    def is_expired(self) -> bool:
        """Check if the user context has expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def time_until_expiry(self) -> timedelta:
        """Get time remaining until token expires"""
        return self.expires_at - datetime.now(timezone.utc)
    
    def has_group(self, group_name: str) -> bool:
        """Check if user belongs to a specific group"""
        return group_name in self.groups
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user context to dictionary"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "groups": self.groups,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "token_id": self.token_id
        }


class AuthService:
    """
    Service for handling JWT token validation and user authentication
    """
    
    def __init__(self):
        # These would typically come from environment variables or AWS Parameter Store
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-key")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_issuer = os.getenv("JWT_ISSUER", "aws-identity-center")
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "ai-assistant-cli")
        
        # Token refresh settings
        self.refresh_threshold_minutes = int(os.getenv("JWT_REFRESH_THRESHOLD_MINUTES", "15"))
        
        self.security = HTTPBearer()
    
    def validate_token(self, token: str) -> UserContext:
        """
        Validate JWT token and extract user context
        
        Args:
            token: JWT token string
            
        Returns:
            UserContext: Extracted user information
            
        Raises:
            HTTPException: If token is invalid, expired, or malformed
        """
        try:
            # Decode and validate the JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                issuer=self.jwt_issuer,
                audience=self.jwt_audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True
                }
            )
            
            # Extract user information from payload
            user_context = self._extract_user_context(payload)
            
            logger.info(f"Successfully validated token for user: {user_context.user_id}")
            return user_context
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except PyJWTError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def _extract_user_context(self, payload: Dict[str, Any]) -> UserContext:
        """
        Extract user context from JWT payload
        
        Args:
            payload: Decoded JWT payload
            
        Returns:
            UserContext: User information
            
        Raises:
            ValueError: If required fields are missing from payload
        """
        try:
            # Extract standard JWT claims
            issued_at = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            token_id = payload.get("jti", "")
            
            # Extract user-specific claims (these would match AWS Identity Center format)
            user_id = payload.get("sub", "")
            email = payload.get("email", "")
            name = payload.get("name", payload.get("preferred_username", ""))
            groups = payload.get("groups", [])
            
            # Validate required fields
            if not user_id:
                raise ValueError("Missing user ID in token")
            if not email:
                raise ValueError("Missing email in token")
            
            return UserContext(
                user_id=user_id,
                email=email,
                name=name,
                groups=groups,
                issued_at=issued_at,
                expires_at=expires_at,
                token_id=token_id
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required field in token payload: {e}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid token payload format: {e}")
    
    def needs_refresh(self, user_context: UserContext) -> bool:
        """
        Check if token needs to be refreshed based on expiration time
        
        Args:
            user_context: Current user context
            
        Returns:
            bool: True if token should be refreshed
        """
        time_until_expiry = user_context.time_until_expiry()
        threshold = timedelta(minutes=self.refresh_threshold_minutes)
        
        return time_until_expiry <= threshold
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> UserContext:
        """
        FastAPI dependency to get current user from Authorization header
        
        Args:
            credentials: HTTP Bearer credentials from FastAPI security
            
        Returns:
            UserContext: Current user information
        """
        return self.validate_token(credentials.credentials)
    
    def create_test_token(self, user_id: str, email: str, name: str = "", groups: list[str] = None) -> str:
        """
        Create a test JWT token for development/testing purposes
        
        Args:
            user_id: User identifier
            email: User email
            name: User display name
            groups: User groups
            
        Returns:
            str: JWT token
        """
        if groups is None:
            groups = []
            
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "name": name,
            "groups": groups,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "iss": self.jwt_issuer,
            "aud": self.jwt_audience,
            "jti": f"test-{user_id}-{int(now.timestamp())}"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)


# Global auth service instance
auth_service = AuthService()