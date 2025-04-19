"""
Middleware for logging and error handling.
"""
import logging
import json
import datetime
import os
import traceback
from functools import wraps
from flask import request, jsonify
from twilio.twiml.voice_response import VoiceResponse

# Ensure log directories exist
os.makedirs('logs', exist_ok=True)

def log_request(func):
    """Decorator to log all incoming requests."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log request details
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "route": request.path,
            "method": request.method,
            "params": dict(request.values),
            "remote_addr": request.remote_addr
        }
        
        # Log to file
        try:
            with open('logs/requests.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logging.error(f"Error logging request: {str(e)}")
        
        # Log to standard logger
        logging.info(f"Request to {request.path} from {request.remote_addr}")
        
        # Call the original function
        return func(*args, **kwargs)
    
    return wrapper

def error_handler(func):
    """Decorator to handle errors in routes."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Get full traceback
            error_traceback = traceback.format_exc()
            
            # Log the error
            error_msg = f"Error in {func.__name__}: {str(e)}\n{error_traceback}"
            log_error(error_msg)
            
            # Check if this is a Twilio voice route
            if request.path in ['/voice', '/handle-response', '/handle-transfer']:
                # Create a fallback response
                response = VoiceResponse()
                response.say("Sorry, I didn't catch that—let me connect you with someone who can help.", voice='Polly.Joanna')
                return str(response)
            else:
                # Return JSON error for API routes
                return jsonify({"status": "error", "message": str(e)}), 500
    
    return wrapper

def log_speech_input(speech_text, caller_number):
    """Log speech input for analysis and debugging."""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "caller": caller_number,
        "speech_text": speech_text
    }
    
    # Log to file
    try:
        with open('logs/speech_inputs.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logging.error(f"Error logging speech input: {str(e)}")
    
    # Also log to standard logger
    logging.info(f"Speech input from {caller_number}: {speech_text}")
    
    return True

def log_error(error_message):
    """Log errors for debugging."""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "error": error_message
    }
    
    # Log to file
    try:
        with open('logs/errors.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logging.error(f"Error logging to error log: {str(e)}")
    
    # Also log to standard logger
    logging.error(error_message)
    
    return True
