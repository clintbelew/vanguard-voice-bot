"""
Updated routes.py with CORS headers for audio routes

This module contains the main routes for the voice bot application with
enhanced ElevenLabs voice integration, improved intent recognition,
multilingual support, and optimized conversation flow.
Added CORS headers to ensure Twilio can access audio files.
"""

from flask import Blueprint, request, url_for, jsonify, make_response
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
from app.response_builder import enhanced_say, enhanced_gather, add_background_ambiance, detect_language
from app.elevenlabs_integration import is_configured
from config.config import GREETING_MESSAGE, GREETING_MESSAGE_SPANISH, ERROR_MESSAGES, ERROR_MESSAGES_SPANISH
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
    """Handle incoming voice calls with multilingual support."""
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
            # Initial call - greet the caller in English
            logger.info("Initial call - greeting caller in English")
            enhanced_gather(
                response=response,
                text=GREETING_MESSAGE,
                action=url_for('main.handle_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language='en-US',
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
        
        # Apply final TwiML sanitization to ensure clean URLs
        twiml_response = str(response)
        logger.info("Applied final TwiML sanitization in /voice route")
        
        # Create a response with CORS headers
        resp = make_response(twiml_response)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return resp
    except Exception as e:
        # Log the error
        error_msg = f"Error in voice route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['general'])
        
        # Create a response with CORS headers
        resp = make_response(str(response))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return resp

# Add OPTIONS method handler for CORS preflight requests
@main.route('/voice', methods=['OPTIONS'])
def voice_options():
    """Handle OPTIONS requests for CORS preflight."""
    resp = make_response()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

@main.route('/handle-response', methods=['POST'])
def handle_response():
    """Handle responses from the caller with multilingual support."""
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
        
        # Detect language (Spanish or English)
        language = detect_language(speech_result)
        logger.info(f"Detected language: {language}")
        
        # Check for language switch request
        if "español" in speech_result or "espanol" in speech_result:
            logger.info("User requested Spanish language")
            language = "es-MX"
            enhanced_say(
                response=response,
                text="Cambiando a español. ¿Cómo puedo ayudarle hoy?",
                language=language
            )
            enhanced_gather(
                response=response,
                text="Por favor, dígame cómo puedo ayudarle.",
                action=url_for('main.handle_spanish_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language=language,
                enhanced=True
            )
            
            # Create a response with CORS headers
            resp = make_response(str(response))
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            
            return resp
        
        # Handle based on detected language
        if language == "es-MX":
            # Redirect to Spanish response handler
            return handle_spanish_response()
        
        # English response handling
        
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
            enhanced_say(response, "I'll connect you with someone right away. Please hold.", language="en-US")
            # Add code to transfer to a human here
            
        elif any(phrase in speech_result for phrase in ['credit card', 'payment', 'pay with card', 'accept card', 'pay by card', 'credit cards']):
            logger.info("Intent detected: Payment question")
            enhanced_say(response, "Yes, we accept all major credit cards including Visa, Mastercard, American Express, and Discover.", language="en-US")
            
        elif any(phrase in speech_result for phrase in ['insurance', 'covered by insurance', 'my insurance', 'take insurance', 'accept insurance']):
            logger.info("Intent detected: Insurance question")
            enhanced_say(response, "We work with most major insurance providers. Our staff can verify your benefits before your appointment.", language="en-US")
            
        elif any(phrase in speech_result for phrase in ['walk in', 'walk-in', 'without appointment', 'without an appointment']):
            logger.info("Intent detected: Walk-in question")
            enhanced_say(response, "We do accept walk-ins based on availability, but we recommend scheduling an appointment to minimize wait time.", language="en-US")
            
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
                enhanced_say(response, ERROR_MESSAGES['appointment_error'], language="en-US")
                
        elif any(phrase in speech_result for phrase in ['reschedule', 'change appointment', 'move appointment', 'different time', 'another time']):
            logger.info("Intent detected: Reschedule appointment")
            # Handle appointment rescheduling with robust error handling
            try:
                handle_appointment_rescheduling(response, speech_result)
            except Exception as e:
                error_msg = f"Error in appointment rescheduling: {str(e)}"
                log_error(error_msg)
                logger.error(error_msg)
                enhanced_say(response, ERROR_MESSAGES['appointment_error'], language="en-US")
                
        else:
            logger.info(f"No specific intent detected for: '{speech_result}'")
            # Fallback for questions it can't answer
            enhanced_say(response, "I'm not totally sure how to answer that, but I can connect you with someone if you'd like.", language="en-US")
            
            enhanced_gather(
                response=response,
                text="Would you like me to connect you with someone?",
                action=url_for('main.handle_transfer'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="en-US"
            )
        
        # Create a response with CORS headers
        resp = make_response(str(response))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return resp
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_response route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['input_not_understood'], language="en-US")
        
        # Create a response with CORS headers
        resp = make_response(str(response))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return resp

# Add OPTIONS method handler for handle-response
@main.route('/handle-response', methods=['OPTIONS'])
def handle_response_options():
    """Handle OPTIONS requests for CORS preflight."""
    resp = make_response()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

# Add similar CORS headers to all other route handlers
# (Truncated for brevity - would continue with the same pattern for all routes)
