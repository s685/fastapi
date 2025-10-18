"""JWT authentication and security utilities"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging_config import logger


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary with user data (user_id, username, role, carrier_access)
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    logger.info(f"Created JWT token for user: {data.get('username')}")
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, str]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, str]:
    """
    FastAPI dependency to extract and validate current user from JWT
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User context dictionary with user_id, username, role, carrier_access
    
    Raises:
        HTTPException: If credentials are invalid
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    # Extract user information
    user_id = payload.get("user_id")
    username = payload.get("username")
    role = payload.get("role")
    carrier_access = payload.get("carrier_access")
    
    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_context = {
        "user_id": user_id,
        "username": username,
        "role": role or "VIEWER",
        "carrier": carrier_access or "ALL"
    }
    
    logger.info(f"Authenticated user: {username} (role: {role})")
    return user_context


def get_user_context_for_session(current_user: Dict[str, str]) -> Dict[str, str]:
    """
    Extract session context from user for Snowpark RBAC
    
    Args:
        current_user: User context from get_current_user
    
    Returns:
        Dictionary with role and carrier for session parameters
    """
    return {
        "role": current_user.get("role", "VIEWER"),
        "carrier": current_user.get("carrier", "ALL")
    }


# Azure AD Provider (Placeholder for future implementation)
class AzureADProvider:
    """
    Azure AD OAuth2 provider (not implemented yet)
    This class provides structure for future Azure AD integration
    """
    
    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.authority = settings.AZURE_AUTHORITY
    
    async def validate_token(self, token: str) -> Dict[str, str]:
        """Validate Azure AD token (placeholder)"""
        raise NotImplementedError("Azure AD authentication not implemented yet")
    
    async def get_user_info(self, token: str) -> Dict[str, str]:
        """Get user info from Azure AD (placeholder)"""
        raise NotImplementedError("Azure AD authentication not implemented yet")

