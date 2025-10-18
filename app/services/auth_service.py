"""Authentication service for user management"""
from typing import Optional, Dict
from datetime import timedelta
from snowflake.snowpark import Session
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.core.logging_config import logger


class AuthService:
    """Service for handling user authentication"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """
        Authenticate user credentials against API_USERS table
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User dictionary if authenticated, None otherwise
        """
        try:
            # Query API_USERS table
            query = f"""
                SELECT 
                    USER_ID,
                    USERNAME,
                    PASSWORD_HASH,
                    SNOWFLAKE_ROLE,
                    CARRIER_ACCESS,
                    IS_ACTIVE
                FROM API_USERS
                WHERE USERNAME = '{username}'
                AND IS_ACTIVE = TRUE
                LIMIT 1
            """
            
            logger.info(f"Authenticating user: {username}")
            result = self.session.sql(query).collect()
            
            if not result:
                logger.warning(f"User not found or inactive: {username}")
                return None
            
            user_row = result[0]
            
            # Verify password
            if not verify_password(password, user_row["PASSWORD_HASH"]):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            try:
                self.session.sql(f"""
                    UPDATE API_USERS
                    SET LAST_LOGIN = CURRENT_TIMESTAMP()
                    WHERE USER_ID = '{user_row["USER_ID"]}'
                """).collect()
            except Exception as e:
                logger.warning(f"Failed to update last login: {str(e)}")
            
            logger.info(f"User authenticated successfully: {username}")
            
            return {
                "user_id": user_row["USER_ID"],
                "username": user_row["USERNAME"],
                "role": user_row["SNOWFLAKE_ROLE"],
                "carrier_access": user_row["CARRIER_ACCESS"] or "ALL",
                "is_active": user_row["IS_ACTIVE"]
            }
        
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}")
            return None
    
    def create_user_token(self, user: Dict[str, str]) -> Dict[str, any]:
        """
        Create JWT token for authenticated user
        
        Args:
            user: User dictionary from authenticate_user
        
        Returns:
            Token response dictionary
        """
        token_data = {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "carrier_access": user["carrier_access"]
        }
        
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = create_access_token(token_data, expires_delta)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }

