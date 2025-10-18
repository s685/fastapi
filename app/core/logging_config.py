"""Structured logging configuration"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging():
    """Configure structured JSON logging"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    log_handler = logging.StreamHandler(sys.stdout)
    
    # JSON formatter for structured logging
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        rename_fields={"levelname": "level", "asctime": "timestamp"}
    )
    
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    
    return logger


# Initialize logger
logger = setup_logging()

