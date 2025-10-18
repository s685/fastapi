"""FastAPI application entry point"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import time
from app.core.config import settings
from app.core.logging_config import logger
from app.core.snowflake import session_manager
from app.api.v1 import auth, policies, claims
from app.models.responses import HealthResponse, ReadinessResponse, ErrorResponse


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url=f"/api/{settings.API_VERSION}/docs",
    redoc_url=f"/api/{settings.API_VERSION}/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json"
)


# CORS middleware - configure origins based on environment
allowed_origins = ["*"] if settings.ENVIRONMENT == "development" else [
    "https://*.snowflakecomputing.com",  # Snowflake UI
    # Add your frontend domains here for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information"""
    start_time = time.time()
    
    # Generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", f"req-{int(time.time()*1000)}")
    
    logger.info(
        f"Request started",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    logger.info(
        f"Request completed",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint for SPCS probes
    
    Returns:
        Service health status
    """
    return HealthResponse(status="healthy")


@app.get("/ready", response_model=ReadinessResponse, tags=["System"])
async def readiness_check():
    """
    Readiness check endpoint - validates Snowflake connection
    
    Returns:
        Service readiness status with Snowflake connection check
    """
    try:
        # Test Snowflake connection
        session = session_manager.get_sync_session()
        session.sql("SELECT 1").collect()
        
        return ReadinessResponse(
            status="ready",
            snowflake="connected"
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ReadinessResponse(
                status="not_ready",
                snowflake=f"disconnected: {str(e)}"
            ).dict()
        )


# Include API routers
app.include_router(auth.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(policies.router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(claims.router, prefix=f"/api/{settings.API_VERSION}")


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("=" * 80)
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Snowflake Database: {settings.SNOWFLAKE_DATABASE}.{settings.SNOWFLAKE_SCHEMA}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down application...")
    
    # Close Snowpark session
    try:
        await session_manager.close()
        logger.info("Snowpark session closed successfully")
    except Exception as e:
        logger.error(f"Error closing Snowpark session: {str(e)}")
    
    logger.info("Application shutdown complete")


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    API root endpoint with basic information
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "environment": settings.ENVIRONMENT,
        "docs": f"/api/{settings.API_VERSION}/docs",
        "health": "/health",
        "ready": "/ready"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )

