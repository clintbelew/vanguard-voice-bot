"""
Updated routes.py with ElevenLabs integration and improved intent recognition

This module contains the main routes for the voice bot application with
enhanced ElevenLabs voice integration, improved intent recognition,
and optimized conversation flow.
"""

from flask import Blueprint, request, url_for, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.twilio_utils import (
    handle_greeting,
    handle_faq,
    handle_appointment_booking,
    handle_appointment_rescheduling,
    handle_missed_call,
    handle_fallback,
    log_speech_input,
    log_error
)
from app.response_builder import enhanced_say, enhanced_gather, add_background_ambiance
from app.elevenlabs_integration import is_configured
from config.config import GREETING_MESSAGE, ERROR_MESSAGES
import logging
import re
import os

# Configure logging
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "voice_bot.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page route."""
    return "Twilio Voice Bot for Vanguard Chiropractic is running!"

@main.route('/test')
def test():
    """Test route to verify ElevenLabs integration."""
    elevenlabs_configured = is_configured()
    return jsonify({
        "status": "ok",
        "elevenlabs_configured": elevenlabs_configured,
        "message": "Voice bot test endpoint"
    })

@main.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming voice calls."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Add subtle background ambiance
        add_background_ambiance(response, volume=0.1)
        
        # Get caller information
        caller_number = request.values.get('From', '')
        logger.info(f"Incoming call from: {caller_number}")
        
        # Check if this is the initial call or a continuation
        if 'SpeechResult' not in request.values:
            # Initial call - greet the caller
            logger.info("Initial call - greeting caller")
            enhanced_gather(
                response=response,
                text=GREETING_MESSAGE,
                action=url_for('main.handle_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                enhanced=True
            )
            
            # If no input is received, repeat the greeting
            response.redirect(url_for('main.voice'))
        else:
            # This shouldn't normally happen, but handle it gracefully
            speech_result = request.values.get('SpeechResult', '')
            log_speech_input(speech_result, caller_number)
            logger.info(f"Unexpected SpeechResult in /voice route: {speech_result}")
            
            # Redirect to handle_response
            response.redirect(url_for('main.handle_response'))
        
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in voice route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['general'])
        return str(response)

@main.route('/handle-response', methods=['POST'])
def handle_response():
    """Handle responses from the caller."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Add subtle background ambiance
        add_background_ambiance(response, volume=0.1)
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        logger.info(f"Speech input in handle_response: '{speech_result}'")
        
        # Debug log for appointment intent detection
        appointment_phrases = [
            'appointment', 'schedule', 'book', 'make appointment', 'make an appointment', 
            'set appointment', 'set up appointment', 'schedule appointment', 'book appointment',
            'need appointment', 'get appointment', 'want appointment', 'like appointment',
            'like to make', 'want to make', 'need to make', 'would like to make'
        ]
        
        for phrase in appointment_phrases:
            if phrase in speech_result:
                logger.info(f"APPOINTMENT INTENT DETECTED: Found '{phrase}' in '{speech_result}'")
        
        # Handle common questions with improved intent matching
        if any(phrase in speech_result for phrase in ['talk to someone', 'speak to someone', 'talk to a person', 'human', 'representative', 'operator']):
            logger.info("Intent detected: Talk to someone")
            enhanced_say(response, "I'll connect you with someone right away. Please hold.")
            # Add code to transfer to a human here
            
        elif any(phrase in speech_result for phrase in ['credit card', 'payment', 'pay with card', 'accept card', 'pay by card', 'credit cards']):
            logger.info("Intent detected: Payment question")
            enhanced_say(response, "Yes, we accept all major credit cards including Visa, Mastercard, American Express, and Discover.")
            
        elif any(phrase in speech_result for phrase in ['insurance', 'covered by insurance', 'my insurance', 'take insurance', 'accept insurance']):
            logger.info("Intent detected: Insurance question")
            enhanced_say(response, "We work with most major insurance providers. Our staff can verify your benefits before your appointment.")
            
        elif any(phrase in speech_result for phrase in ['walk in', 'walk-in', 'without appointment', 'without an appointment']):
            logger.info("Intent detected: Walk-in question")
            enhanced_say(response, "We do accept walk-ins based on availability, but we recommend scheduling an appointment to minimize wait time.")
            
        # Enhanced appointment intent recognition
        elif any(phrase in speech_result for phrase in appointment_phrases):
            logger.info("APPOINTMENT INTENT CONFIRMED - Calling handle_appointment_booking")
            # Handle appointment scheduling with robust error handling
            try:
                handle_appointment_booking(response, speech_result)
            except Exception as e:
                error_msg = f"Error in appointment booking: {str(e)}"
                log_error(error_msg)
                logger.error(error_msg)
                enhanced_say(response, ERROR_MESSAGES['appointment_error'])
                
        elif any(phrase in speech_result for phrase in ['reschedule', 'change appointment', 'move appointment', 'different time', 'another time']):
            logger.info("Intent detected: Reschedule appointment")
            # Handle appointment rescheduling with robust error handling
            try:
                handle_appointment_rescheduling(response, speech_result)
            except Exception as e:
                error_msg = f"Error in appointment rescheduling: {str(e)}"
                log_error(error_msg)
                logger.error(error_msg)
                enhanced_say(response, ERROR_MESSAGES['appointment_error'])
                
        else:
            logger.info(f"No specific intent detected for: '{speech_result}'")
            # Fallback for questions it can't answer
            enhanced_say(response, "I'm not totally sure how to answer that, but I can connect you with someone if you'd like.")
            
            enhanced_gather(
                response=response,
                text="Would you like me to connect you with someone?",
                action=url_for('main.handle_transfer'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call'
            )
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_response route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['input_not_understood'])
        return str(response)

@main.route('/handle-appointment', methods=['POST'])
def handle_appointment():
    """Handle appointment selection."""
    try:
        response = VoiceResponse()
        
        # Add subtle background ambiance
        add_background_ambiance(response, volume=0.1)
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        logger.info(f"Appointment selection: '{speech_result}'")
        
        # Enhanced time recognition patterns
        time_patterns = [
            r'\b9\s*(?:am|a\.m\.)\b',  # 9am, 9 am, 9a.m.
            r'\b9\s*(?::|00)\b',       # 9:00, 9 00
            r'\bnine\b',               # nine
            r'\bmorning\b',            # morning
            r'\b10\s*(?:am|a\.m\.)\b', # 10am, 10 am, 10a.m.
            r'\b10\s*(?::|00)\b',      # 10:00, 10 00
            r'\bten\b',                # ten
            r'\b11\s*(?:am|a\.m\.)\b', # 11am, 11 am, 11a.m.
            r'\b11\s*(?::|00)\b',      # 11:00, 11 00
            r'\beleven\b',             # eleven
            r'\b12\s*(?:pm|p\.m\.)\b', # 12pm, 12 pm, 12p.m.
            r'\b12\s*(?::|00)\b',      # 12:00, 12 00
            r'\btwelve\b',             # twelve
            r'\bnoon\b',               # noon
            r'\b1\s*(?:pm|p\.m\.)\b',  # 1pm, 1 pm, 1p.m.
            r'\b1\s*(?::|00)\b',       # 1:00, 1 00
            r'\bone\b',                # one
            r'\b2\s*(?:pm|p\.m\.)\b',  # 2pm, 2 pm, 2p.m.
            r'\b2\s*(?::|00)\b',       # 2:00, 2 00
            r'\btwo\b',                # two
            r'\b3\s*(?:pm|p\.m\.)\b',  # 3pm, 3 pm, 3p.m.
            r'\b3\s*(?::|00)\b',       # 3:00, 3 00
            r'\bthree\b',              # three
            r'\b4\s*(?:pm|p\.m\.)\b',  # 4pm, 4 pm, 4p.m.
            r'\b4\s*(?::|00)\b',       # 4:00, 4 00
            r'\bfour\b',               # four
            r'\b5\s*(?:pm|p\.m\.)\b',  # 5pm, 5 pm, 5p.m.
            r'\b5\s*(?::|00)\b',       # 5:00, 5 00
            r'\bfive\b',               # five
        ]
        
        # Affirmative response patterns
        affirmative_patterns = [
            r'\byes\b', r'\byeah\b', r'\bsure\b', r'\bfine\b', r'\bok\b', r'\bokay\b',
            r'\bsounds good\b', r'\bthat works\b', r'\bperfect\b', r'\bgreat\b',
            r'\btomorrow\b', r'\bmonday\b', r'\btuesday\b', r'\bwednesday\b', 
            r'\bthursday\b', r'\bfriday\b', r'\bsaturday\b', r'\bsunday\b'
        ]
        
        # Check if user wants to book one of the offered slots
        time_match = any(re.search(pattern, speech_result) for pattern in time_patterns)
        affirmative_match = any(re.search(pattern, speech_result) for pattern in affirmative_patterns)
        
        if time_match:
            logger.info(f"Time pattern matched in: '{speech_result}'")
        
        if affirmative_match:
            logger.info(f"Affirmative pattern matched in: '{speech_result}'")
        
        if time_match or affirmative_match or dtmf == '1':
            logger.info("Appointment confirmed")
            enhanced_say(response, "Great! I've scheduled your appointment. You'll receive a confirmation message shortly.")
            enhanced_say(response, "Is there anything else I can help you with today?")
            response.redirect(url_for('main.voice'))
        else:
            logger.info("Appointment times rejected")
            enhanced_say(response, "I understand those times don't work for you. Let me connect you with our scheduling team to find a better time.")
            # Add transfer logic here
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_appointment route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['appointment_error'])
        return str(response)

@main.route('/handle-transfer', methods=['POST'])
def handle_transfer():
    """Handle transfer to human request."""
    try:
        response = VoiceResponse()
        
        # Add subtle background ambiance
        add_background_ambiance(response, volume=0.1)
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        logger.info(f"Transfer response: '{speech_result}'")
        
        # Check if user wants to be transferred
        if any(word in speech_result for word in ['yes', 'yeah', 'sure', 'please', 'ok', 'okay']) or dtmf == '1':
            logger.info("User requested transfer to human")
            enhanced_say(response, "I'll connect you with someone right away. Please hold.")
            # Add code to transfer to a human here
        else:
            logger.info("User declined transfer to human")
            enhanced_say(response, "Alright. Is there anything else I can help you with today?")
            response.redirect(url_for('main.voice'))
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_transfer route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['input_not_understood'])
        return str(response)

# Route for logging speech inputs via API
@main.route('/log-speech', methods=['POST'])
def log_speech():
    """API endpoint to log speech inputs."""
    try:
        data = request.json
        speech_text = data.get('speech_text', '')
        caller = data.get('caller', '')
        log_speech_input(speech_text, caller)
        logger.info(f"API log speech: '{speech_text}' from {caller}")
        return jsonify({"status": "success", "message": "Speech input logged"}), 200
    except Exception as e:
        error_msg = f"Error in log_speech API: {str(e)}"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": str(e)}), 500
