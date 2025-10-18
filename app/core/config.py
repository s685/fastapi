"""Configuration management using Pydantic Settings"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Snowflake Connection (Service Account)
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_USER: str
    SNOWFLAKE_PASSWORD: str
    SNOWFLAKE_ROLE: str = "API_SERVICE_ROLE"
    SNOWFLAKE_WAREHOUSE: str = "COMPUTE_WH"
    SNOWFLAKE_DATABASE: str = "LTC_INSURANCE"
    SNOWFLAKE_SCHEMA: str = "ANALYTICS"
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 1  # Token expiration in hours
    
    @property
    def JWT_EXPIRE_MINUTES(self) -> int:
        """Convert hours to minutes for compatibility"""
        return self.JWT_EXPIRATION_HOURS * 60
    
    # API Configuration
    API_VERSION: str = "v1"
    API_TITLE: str = "LTC Insurance Data API"
    API_DESCRIPTION: str = "FastAPI service for LTC insurance data with Snowpark integration"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MAX_PAGE_SIZE: int = 1000
    DEFAULT_PAGE_SIZE: int = 100
    
    # Azure AD (Future - Not Implemented Yet)
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_AUTHORITY: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()

