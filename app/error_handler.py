"""
Error Handler Module for Voice Bot

This module provides centralized error handling and logging functionality.
"""

import os
import logging
import json
import datetime
from pathlib import Path

# Configure logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

def log_error(error_message, context=None):
    """
    Log errors for debugging with additional context information.
    
    Args:
        error_message: The error message to log
        context: Optional dictionary with additional context information
    """
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "error": error_message
    }
    
    if context:
        log_entry["context"] = context
    
    # Log to file
    try:
        error_log_path = os.path.join(LOGS_DIR, 'errors.log')
        with open(error_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        logger.info(f"Error logged to {error_log_path}")
    except Exception as e:
        logger.error(f"Error logging to error log: {str(e)}")
    
    # Also log to standard logger
    logger.error(error_message)
    
    return True

def handle_exception(func):
    """
    Decorator for handling exceptions in routes.
    
    Args:
        func: The function to wrap with exception handling
    
    Returns:
        Wrapped function with exception handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"Exception in {func.__name__}: {str(e)}"
            log_error(error_msg, {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            # Return appropriate error response based on function context
            # This would be customized based on the application's needs
            return {"error": error_msg}, 500
    
    return wrapper
