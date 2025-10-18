"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from snowflake.snowpark import Session
from app.models.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.core.snowflake import session_manager
from app.core.logging_config import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_session() -> Session:
    """Get Snowpark session for authentication (no user context needed)"""
    return session_manager.get_sync_session()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    session: Session = Depends(get_auth_session)
):
    """
    Authenticate user and return JWT token
    
    Args:
        credentials: Username and password
    
    Returns:
        JWT token with user information
    
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        auth_service = AuthService(session)
        
        # Authenticate user
        user = auth_service.authenticate_user(
            credentials.username,
            credentials.password
        )
        
        if not user:
            logger.warning(f"Failed login attempt for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create JWT token
        token_response = auth_service.create_user_token(user)
        
        logger.info(f"User logged in successfully: {credentials.username}")
        
        return TokenResponse(**token_response)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )

