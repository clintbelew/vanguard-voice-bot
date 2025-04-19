"""
Twilio Utilities Module for Voice Bot

This module provides utility functions for working with Twilio,
including handling different types of voice interactions and logging.
"""

import os
import logging
from datetime import datetime
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.response_builder import enhanced_say, enhanced_gather
from app.gohighlevel_integration import check_availability, book_appointment
from config.config import ERROR_MESSAGES

# Configure logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Speech log file
SPEECH_LOG_FILE = os.path.join(LOGS_DIR, 'speech_inputs.log')
ERROR_LOG_FILE = os.path.join(LOGS_DIR, 'error.log')

def log_speech_input(speech_text, caller=None):
    """Log speech input to a file."""
    try:
        # Ensure the logs directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the log entry
        log_entry = f"[{timestamp}] "
        if caller:
            log_entry += f"[{caller}] "
        log_entry += f"{speech_text}\n"
        
        # Append the log entry to the file
        with open(SPEECH_LOG_FILE, 'a') as f:
            f.write(log_entry)
        
        return True
    except Exception as e:
        logger.error(f"Error logging speech input: {str(e)}")
        return False

def log_error(error_message):
    """Log an error to the error log file."""
    try:
        # Ensure the logs directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the log entry
        log_entry = f"[{timestamp}] ERROR: {error_message}\n"
        
        # Append the log entry to the file
        with open(ERROR_LOG_FILE, 'a') as f:
            f.write(log_entry)
        
        return True
    except Exception as e:
        logger.error(f"Error logging error: {str(e)}")
        return False

def handle_greeting(response):
    """Handle the initial greeting."""
    try:
        enhanced_say(response, "Hello! Thank you for calling Vanguard Chiropractic. How can I help you today?")
        return True
    except Exception as e:
        logger.error(f"Error in handle_greeting: {str(e)}")
        log_error(f"Error in handle_greeting: {str(e)}")
        return False

def handle_faq(response, question):
    """Handle frequently asked questions."""
    try:
        # Simple FAQ handling logic
        if "hours" in question or "open" in question:
            enhanced_say(response, "We're open Monday through Friday from 9 AM to 6 PM, and Saturdays from 9 AM to noon.")
        elif "location" in question or "address" in question or "where" in question:
            enhanced_say(response, "We're located at 123 Main Street, Suite 100, in downtown Austin.")
        elif "insurance" in question:
            enhanced_say(response, "We accept most major insurance plans. Our staff can verify your benefits before your appointment.")
        elif "cost" in question or "price" in question or "fee" in question:
            enhanced_say(response, "The cost varies depending on your treatment plan and insurance coverage. We offer a free initial consultation to discuss your specific needs.")
        else:
            # Default response for unrecognized questions
            enhanced_say(response, "I'm not sure I have the answer to that. Would you like me to connect you with someone who can help?")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error in handle_faq: {str(e)}")
        log_error(f"Error in handle_faq: {str(e)}")
        return False

def handle_appointment_booking(response, speech_result):
    """Handle appointment booking requests."""
    try:
        logger.info(f"Handling appointment booking for: {speech_result}")
        
        # Check availability using GoHighLevel integration
        available_slots = check_availability()
        
        if not available_slots or len(available_slots) == 0:
            enhanced_say(response, "I'm sorry, but I don't see any available appointments in the next few days. Let me connect you with our scheduling team.")
            # Add transfer logic here
            return False
        
        # Format available slots for speech
        slots_text = "We have the following appointments available: "
        for i, slot in enumerate(available_slots[:3]):  # Limit to 3 options
            slots_text += f"{slot['formatted_time']}. "
        
        slots_text += "Would any of these times work for you?"
        
        # Present available slots to the caller
        enhanced_gather(
            response=response,
            text=slots_text,
            action="/handle-appointment",
            input_types='speech dtmf',
            timeout=5,
            speech_timeout='auto',
            speech_model='phone_call'
        )
        
        return True
    except Exception as e:
        logger.error(f"Error in handle_appointment_booking: {str(e)}")
        log_error(f"Error in handle_appointment_booking: {str(e)}")
        enhanced_say(response, ERROR_MESSAGES['appointment_error'])
        return False

def handle_appointment_rescheduling(response, speech_result):
    """Handle appointment rescheduling requests."""
    try:
        logger.info(f"Handling appointment rescheduling for: {speech_result}")
        
        # For now, just redirect to the regular booking flow
        # In a real implementation, this would check existing appointments first
        enhanced_say(response, "I'd be happy to help you reschedule. Let me check what times we have available.")
        
        return handle_appointment_booking(response, speech_result)
    except Exception as e:
        logger.error(f"Error in handle_appointment_rescheduling: {str(e)}")
        log_error(f"Error in handle_appointment_rescheduling: {str(e)}")
        enhanced_say(response, ERROR_MESSAGES['appointment_error'])
        return False

def handle_missed_call(response, caller_number):
    """Handle missed calls by sending a text message."""
    try:
        logger.info(f"Handling missed call from: {caller_number}")
        
        enhanced_say(response, "I'm sorry we missed your call. We'll send you a text message with information on how to reach us.")
        
        # In a real implementation, this would send an SMS via Twilio
        # client.messages.create(
        #     body="Sorry we missed your call to Vanguard Chiropractic. Please call us back at (555) 123-4567 or reply to this message to schedule an appointment.",
        #     from_=TWILIO_PHONE_NUMBER,
        #     to=caller_number
        # )
        
        return True
    except Exception as e:
        logger.error(f"Error in handle_missed_call: {str(e)}")
        log_error(f"Error in handle_missed_call: {str(e)}")
        return False

def handle_fallback(response):
    """Handle fallback for unrecognized inputs."""
    try:
        enhanced_say(response, "I'm sorry, but I didn't understand that. Would you like to schedule an appointment, ask about our services, or speak with someone?")
        return True
    except Exception as e:
        logger.error(f"Error in handle_fallback: {str(e)}")
        log_error(f"Error in handle_fallback: {str(e)}")
        return False
