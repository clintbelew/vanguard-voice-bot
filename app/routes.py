"""
Simplified routes.py with direct S3 URL integration for voice bot.

This module contains the main routes for the voice bot application with
direct S3 URL integration for the greeting message, removing dependency
on the problematic audio_manager.py file.
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
from app.response_builder import enhanced_say, enhanced_gather, add_background_ambiance, detect_language
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

# S3 URL for the greeting audio
S3_GREETING_URL = "https://chirodesk-audio.s3.us-east-2.amazonaws.com/ElevenLabs_2025-04-20T04_45_30_Rachel_pre_sp100_s50_sb75_se0_b_m2.mp3"

# Constants
OFFICE_AMBIANCE_URL = "https://storage.googleapis.com/vanguard-voice-assets/office_ambiance_low.mp3"

@main.route('/')
def index():
    """Home page route."""
    return "Twilio Voice Bot for Vanguard Chiropractic is running!"

@main.route('/test')
def test():
    """Test route to verify S3 integration."""
    return jsonify({
        "status": "ok",
        "s3_greeting_url": S3_GREETING_URL,
        "message": "Voice bot test endpoint with S3 integration"
    })

@main.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming voice calls with multilingual support and direct S3 URL for greeting."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Add subtle background ambiance
        response.play(OFFICE_AMBIANCE_URL, loop=0, volume=0.1)
        
        # Get caller information
        caller_number = request.values.get('From', '')
        logger.info(f"Incoming call from: {caller_number}")
        
        # Check if this is the initial call or a continuation
        if 'SpeechResult' not in request.values:
            # Initial call - greet the caller in English using S3 URL directly
            logger.info("Initial call - greeting caller in English using S3 URL")
            
            # Create the Gather verb
            gather = Gather(
                input='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                action=url_for('main.handle_response'),
                language='en-US'
            )
            gather.speech_model = 'phone_call'
            
            # Play the S3 greeting audio directly
            gather.play(S3_GREETING_URL)
            response.append(gather)
            
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
    """Handle responses from the caller with multilingual support."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Add subtle background ambiance
        response.play(OFFICE_AMBIANCE_URL, loop=0, volume=0.1)
        
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
            return str(response)
        
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
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_response route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['input_not_understood'], language="en-US")
        return str(response)

@main.route('/handle-spanish-response', methods=['POST'])
def handle_spanish_response():
    """Handle responses from Spanish-speaking callers."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Add subtle background ambiance
        response.play(OFFICE_AMBIANCE_URL, loop=0, volume=0.1)
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        logger.info(f"Spanish speech input: '{speech_result}'")
        
        # Check for language switch request
        if "english" in speech_result or "inglés" in speech_result or "ingles" in speech_result:
            logger.info("User requested English language")
            enhanced_say(
                response=response,
                text="Switching to English. How can I help you today?",
                language="en-US"
            )
            enhanced_gather(
                response=response,
                text="Please tell me how I can assist you.",
                action=url_for('main.handle_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="en-US",
                enhanced=True
            )
            return str(response)
        
        # Spanish appointment intent phrases
        appointment_phrases_spanish = [
            'cita', 'agendar', 'programar', 'reservar', 'hacer cita', 'hacer una cita',
            'necesito cita', 'quiero cita', 'quisiera cita', 'me gustaría', 'agendar cita',
            'programar cita', 'reservar cita', 'consulta', 'ver al doctor', 'ver al médico'
        ]
        
        # Debug log for Spanish appointment intent detection
        for phrase in appointment_phrases_spanish:
            if phrase in speech_result:
                logger.info(f"SPANISH APPOINTMENT INTENT DETECTED: Found '{phrase}' in '{speech_result}'")
        
        # Handle common questions in Spanish
        if any(phrase in speech_result for phrase in ['hablar con alguien', 'hablar con una persona', 'persona', 'representante', 'operador']):
            logger.info("Spanish intent detected: Talk to someone")
            enhanced_say(response, "Le conectaré con alguien de inmediato. Por favor, espere.", language="es-MX")
            # Add code to transfer to a human here
            
        elif any(phrase in speech_result for phrase in ['tarjeta de crédito', 'pago', 'pagar con tarjeta', 'aceptan tarjeta', 'tarjetas']):
            logger.info("Spanish intent detected: Payment question")
            enhanced_say(response, "Sí, aceptamos todas las tarjetas de crédito principales, incluyendo Visa, Mastercard, American Express y Discover.", language="es-MX")
            
        elif any(phrase in speech_result for phrase in ['seguro', 'seguro médico', 'mi seguro', 'aceptan seguro']):
            logger.info("Spanish intent detected: Insurance question")
            enhanced_say(response, "Trabajamos con la mayoría de los proveedores de seguros principales. Nuestro personal puede verificar sus beneficios antes de su cita.", language="es-MX")
            
        elif any(phrase in speech_result for phrase in ['sin cita', 'sin cita previa', 'sin agendar', 'llegar sin cita']):
            logger.info("Spanish intent detected: Walk-in question")
            enhanced_say(response, "Aceptamos pacientes sin cita previa según disponibilidad, pero recomendamos programar una cita para minimizar el tiempo de espera.", language="es-MX")
            
        # Spanish appointment intent recognition
        elif any(phrase in speech_result for phrase in appointment_phrases_spanish):
            logger.info("SPANISH APPOINTMENT INTENT CONFIRMED")
            # Handle Spanish appointment scheduling
            try:
                enhanced_say(response, "Me gustaría ayudarle a programar una cita. ¿Prefiere una cita por la mañana o por la tarde?", language="es-MX")
                enhanced_gather(
                    response=response,
                    text="Por favor, dígame si prefiere por la mañana o por la tarde.",
                    action=url_for('main.handle_spanish_appointment'),
                    input_types='speech dtmf',
                    timeout=3,
                    speech_timeout='auto',
                    speech_model='phone_call',
                    language="es-MX",
                    enhanced=True
                )
            except Exception as e:
                error_msg = f"Error in Spanish appointment booking: {str(e)}"
                log_error(error_msg)
                logger.error(error_msg)
                enhanced_say(response, ERROR_MESSAGES_SPANISH['appointment_error'], language="es-MX")
                
        elif any(phrase in speech_result for phrase in ['cambiar cita', 'mover cita', 'reprogramar', 'otra hora', 'otro día']):
            logger.info("Spanish intent detected: Reschedule appointment")
            # Handle Spanish appointment rescheduling
            enhanced_say(response, "Para cambiar su cita, necesito conectarle con nuestro equipo de programación. Por favor, espere un momento.", language="es-MX")
            
        else:
            logger.info(f"No specific Spanish intent detected for: '{speech_result}'")
            # Fallback for questions it can't answer in Spanish
            enhanced_say(response, "No estoy seguro de cómo responder a eso, pero puedo conectarle con alguien si lo desea.", language="es-MX")
            
            enhanced_gather(
                response=response,
                text="¿Le gustaría que le conecte con alguien?",
                action=url_for('main.handle_spanish_transfer'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="es-MX"
            )
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_spanish_response route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES_SPANISH['input_not_understood'], language="es-MX")
        return str(response)

@main.route('/handle-transfer', methods=['POST'])
def handle_transfer():
    """Handle transfer requests."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        
        # Check if user wants to be transferred
        if any(word in speech_result for word in ['yes', 'yeah', 'sure', 'please', 'ok', 'okay']):
            enhanced_say(response, "I'll connect you with someone right away. Please hold.", language="en-US")
            # Add code to transfer to a human here
        else:
            enhanced_say(response, "Alright, is there anything else I can help you with?", language="en-US")
            enhanced_gather(
                response=response,
                text="Please let me know how else I can assist you.",
                action=url_for('main.handle_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="en-US"
            )
        
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_transfer route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['transfer_error'], language="en-US")
        return str(response)

@main.route('/handle-spanish-transfer', methods=['POST'])
def handle_spanish_transfer():
    """Handle transfer requests in Spanish."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        
        # Check if user wants to be transferred
        if any(word in speech_result for word in ['sí', 'si', 'claro', 'por favor', 'ok', 'okay']):
            enhanced_say(response, "Le conectaré con alguien de inmediato. Por favor, espere.", language="es-MX")
            # Add code to transfer to a human here
        else:
            enhanced_say(response, "Muy bien, ¿hay algo más en lo que pueda ayudarle?", language="es-MX")
            enhanced_gather(
                response=response,
                text="Por favor, dígame en qué más puedo ayudarle.",
                action=url_for('main.handle_spanish_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="es-MX"
            )
        
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_spanish_transfer route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES_SPANISH['transfer_error'], language="es-MX")
        return str(response)

@main.route('/handle-spanish-appointment', methods=['POST'])
def handle_spanish_appointment():
    """Handle Spanish appointment scheduling."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        
        # Simple logic to handle morning/afternoon preference
        if any(word in speech_result for word in ['mañana', 'manana', 'temprano']):
            enhanced_say(response, "Tenemos disponibilidad los lunes, miércoles y viernes por la mañana. Para programar una cita específica, necesito conectarle con nuestro equipo de programación.", language="es-MX")
        elif any(word in speech_result for word in ['tarde', 'noche']):
            enhanced_say(response, "Tenemos disponibilidad los martes y jueves por la tarde. Para programar una cita específica, necesito conectarle con nuestro equipo de programación.", language="es-MX")
        else:
            enhanced_say(response, "No pude entender su preferencia. Para programar una cita, necesito conectarle con nuestro equipo de programación.", language="es-MX")
        
        enhanced_say(response, "Le conectaré con nuestro equipo de programación ahora. Por favor, espere un momento.", language="es-MX")
        # Add code to transfer to scheduling team here
        
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_spanish_appointment route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES_SPANISH['appointment_error'], language="es-MX")
        return str(response)
