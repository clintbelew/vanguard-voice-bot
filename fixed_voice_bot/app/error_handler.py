import os
import logging
from twilio.twiml.voice_response import VoiceResponse
from config.config import ERROR_MESSAGES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("error_handler.log"),
        logging.StreamHandler()
    ]
)

class ErrorHandler:
    """Class to handle errors in the voice bot application."""
    
    @staticmethod
    def handle_error(error, error_type="general", caller_number=None):
        """Log error and return appropriate error message."""
        # Log the error
        error_msg = f"Error ({error_type}): {str(error)}"
        if caller_number:
            error_msg += f" - Caller: {caller_number}"
        
        logging.error(error_msg)
        
        # Return appropriate error message
        if error_type in ERROR_MESSAGES:
            return ERROR_MESSAGES[error_type]
        return ERROR_MESSAGES["general"]
    
    @staticmethod
    def create_error_response(error, error_type="general", speak_function=None):
        """Create a TwiML response for error handling."""
        response = VoiceResponse()
        error_message = ErrorHandler.handle_error(error, error_type)
        
        # Use speak function if provided, otherwise use say
        if speak_function:
            speak_function(response, error_message)
        else:
            response.say(error_message, voice='Polly.Joanna')
            
        return str(response)
    
    @staticmethod
    def log_to_file(error, context=None):
        """Log detailed error information to file."""
        try:
            os.makedirs('logs', exist_ok=True)
            
            with open('logs/error_log.txt', 'a') as f:
                f.write(f"ERROR: {str(error)}\n")
                if context:
                    f.write(f"CONTEXT: {context}\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            logging.error(f"Failed to log error to file: {str(e)}")

# Create singleton instance
error_handler = ErrorHandler()
