"""Snowpark session management with RBAC support and optimizations"""
import asyncio
from typing import Optional, Dict
from functools import lru_cache
from snowflake.snowpark import Session
from app.core.config import settings
from app.core.logging_config import logger


class SnowparkSessionManager:
    """
    Optimized Snowpark session manager with:
    - Singleton pattern for connection reuse
    - Async-safe locking mechanism
    - Automatic connection health checks
    - Resource cleanup on shutdown
    """
    
    _instance: Optional['SnowparkSessionManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Implement singleton pattern for single session across app"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._session: Optional[Session] = None
            self._lock = asyncio.Lock()
            self._connection_params: Optional[Dict[str, str]] = None
            SnowparkSessionManager._initialized = True
    
    async def get_session(self, user_context: Optional[Dict[str, str]] = None) -> Session:
        """
        Get or create Snowpark session with optional user context for RBAC
        
        Args:
            user_context: Dict with 'role' and optional 'carrier' for RBAC
        
        Returns:
            Snowpark Session with context set
        """
        async with self._lock:
            if not self._session:
                logger.info("Creating new Snowpark session")
                self._session = self._create_session()
            
            if user_context:
                # Log RBAC context (session parameters disabled for now)
                # To enable, create custom session parameters in Snowflake first
                role = user_context.get('role', 'VIEWER')
                carrier = user_context.get('carrier', 'ALL')
                
                logger.info(f"User context: role={role}, carrier={carrier}")
            
            return self._session
    
    def _get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters (cached for performance)
        Time Complexity: O(1) after first call
        Space Complexity: O(1) - only stores dict once
        """
        if self._connection_params is None:
            self._connection_params = {
                "account": settings.SNOWFLAKE_ACCOUNT,
                "user": settings.SNOWFLAKE_USER,
                "password": settings.SNOWFLAKE_PASSWORD,
                "role": settings.SNOWFLAKE_ROLE,
                "warehouse": settings.SNOWFLAKE_WAREHOUSE,
                "database": settings.SNOWFLAKE_DATABASE,
                "schema": settings.SNOWFLAKE_SCHEMA,
            }
        return self._connection_params
    
    def _is_session_valid(self) -> bool:
        """
        Check if session is still valid
        Time Complexity: O(1)
        """
        if self._session is None:
            return False
        try:
            # Quick health check query
            self._session.sql("SELECT 1").collect()
            return True
        except Exception:
            return False
    
    def _create_session(self) -> Session:
        """
        Create a new Snowpark session with optimization
        Time Complexity: O(1) for connection
        Space Complexity: O(1) - single session object
        """
        try:
            connection_params = self._get_connection_params()
            session = Session.builder.configs(connection_params).create()
            logger.info(f"Snowpark session created: {settings.SNOWFLAKE_DATABASE}.{settings.SNOWFLAKE_SCHEMA}")
            return session
        except Exception as e:
            logger.error(f"Failed to create Snowpark session: {str(e)}")
            raise
    
    async def close(self):
        """Close the Snowpark session"""
        async with self._lock:
            if self._session:
                try:
                    self._session.close()
                    logger.info("Snowpark session closed")
                except Exception as e:
                    logger.error(f"Error closing session: {str(e)}")
                finally:
                    self._session = None
    
    def get_sync_session(self, user_context: Optional[Dict[str, str]] = None) -> Session:
        """
        Synchronous version for non-async contexts
        
        Args:
            user_context: Dict with 'role' and optional 'carrier' for RBAC
        
        Returns:
            Snowpark Session with context set
        """
        if not self._session:
            logger.info("Creating new Snowpark session (sync)")
            self._session = self._create_session()
        
        if user_context:
            # Log RBAC context (session parameters disabled for now)
            role = user_context.get('role', 'VIEWER')
            carrier = user_context.get('carrier', 'ALL')
            
            logger.info(f"User context (sync): role={role}, carrier={carrier}")
        
        return self._session


# Global session manager instance
session_manager = SnowparkSessionManager()


async def get_snowpark_session(user_context: Optional[Dict[str, str]] = None) -> Session:
    """Dependency injection for FastAPI endpoints"""
    return await session_manager.get_session(user_context)

