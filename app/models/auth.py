"""Authentication models"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., description="Username for authentication")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role")


class UserInfo(BaseModel):
    """User information model"""
    user_id: str
    username: str
    role: str
    carrier_access: Optional[str] = None
    is_active: bool

