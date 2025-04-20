"""
Error Handler Module for Voice Bot

This module provides centralized error handling functionality for the voice bot application.
It includes functions for logging errors and generating appropriate error responses.
"""

import os
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants with absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
logger.info(f"Logs directory created at: {LOGS_DIR}")

ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'error.log')

def log_error(error_message, error_type=None, stack_trace=None):
    """
    Log an error to the error log file.
    
    Args:
        error_message (str): The error message to log
        error_type (str, optional): The type of error
        stack_trace (str, optional): The stack trace of the error
    """
    try:
        # Ensure the logs directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the error message
        formatted_error = f"[{timestamp}] "
        if error_type:
            formatted_error += f"[{error_type}] "
        formatted_error += f"{error_message}\n"
        
        if stack_trace:
            formatted_error += f"Stack trace:\n{stack_trace}\n"
        
        # Append the error to the log file
        with open(ERROR_LOG_FILE, 'a') as f:
            f.write(formatted_error)
            f.write('-' * 80 + '\n')
        
        # Also log to the console
        logger.error(error_message)
        if stack_trace:
            logger.error(f"Stack trace: {stack_trace}")
        
        return True
    except Exception as e:
        # If we can't log to the file, at least try to log to the console
        logger.error(f"Error logging error: {str(e)}")
        logger.error(f"Original error: {error_message}")
        return False

def handle_exception(e, context=None):
    """
    Handle an exception by logging it and returning appropriate error information.
    
    Args:
        e (Exception): The exception to handle
        context (str, optional): The context in which the exception occurred
    
    Returns:
        dict: A dictionary containing error information
    """
    try:
        # Get the stack trace
        stack_trace = traceback.format_exc()
        
        # Log the error
        error_message = str(e)
        if context:
            error_message = f"[{context}] {error_message}"
        
        log_error(error_message, type(e).__name__, stack_trace)
        
        # Return error information
        return {
            'error': True,
            'message': str(e),
            'type': type(e).__name__,
            'context': context
        }
    except Exception as logging_error:
        # If we can't handle the exception properly, at least try to log something
        logger.error(f"Error handling exception: {str(logging_error)}")
        logger.error(f"Original exception: {str(e)}")
        
        return {
            'error': True,
            'message': str(e),
            'type': 'UnknownError',
            'context': context
        }
