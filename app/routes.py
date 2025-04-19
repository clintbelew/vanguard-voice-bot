"""
Updated routes.py with ElevenLabs integration, improved intent recognition,
and multilingual support for English and Spanish.

This module contains the main routes for the voice bot application with
enhanced ElevenLabs voice integration, improved intent recognition,
multilingual support, and optimized conversation flow.
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
        add_background_ambiance(response, volume=0.1)
        
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
            # Add transfer logic here
                
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

@main.route('/handle-spanish-appointment', methods=['POST'])
def handle_spanish_appointment():
    """Handle Spanish appointment selection."""
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
        logger.info(f"Spanish appointment selection: '{speech_result}'")
        
        # Morning/afternoon patterns in Spanish
        morning_patterns = ['mañana', 'manana', 'temprano', 'antes del mediodía', 'antes de las 12']
        afternoon_patterns = ['tarde', 'después del mediodía', 'despues del mediodia', 'después de las 12', 'noche']
        
        # Check if user prefers morning or afternoon
        if any(pattern in speech_result for pattern in morning_patterns):
            logger.info("User prefers morning appointment (Spanish)")
            enhanced_say(response, "Tenemos disponibilidad a las 9:00 AM o a las 11:00 AM. ¿Cuál prefiere?", language="es-MX")
        elif any(pattern in speech_result for pattern in afternoon_patterns):
            logger.info("User prefers afternoon appointment (Spanish)")
            enhanced_say(response, "Tenemos disponibilidad a las 2:00 PM o a las 4:00 PM. ¿Cuál prefiere?", language="es-MX")
        else:
            logger.info("No clear preference detected (Spanish)")
            enhanced_say(response, "Tenemos citas disponibles a las 9:00 AM, 11:00 AM, 2:00 PM y 4:00 PM. ¿Qué horario prefiere?", language="es-MX")
        
        # Gather the specific time preference
        enhanced_gather(
            response=response,
            text="Por favor, dígame qué horario prefiere.",
            action=url_for('main.handle_spanish_appointment_confirmation'),
            input_types='speech dtmf',
            timeout=3,
            speech_timeout='auto',
            speech_model='phone_call',
            language="es-MX",
            enhanced=True
        )
            
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

@main.route('/handle-spanish-appointment-confirmation', methods=['POST'])
def handle_spanish_appointment_confirmation():
    """Handle Spanish appointment time confirmation."""
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
        logger.info(f"Spanish appointment time selection: '{speech_result}'")
        
        # Enhanced time recognition patterns in Spanish
        time_patterns = [
            r'\b9\b', r'\bnueve\b', r'\b9:00\b',
            r'\b11\b', r'\bonce\b', r'\b11:00\b',
            r'\b2\b', r'\bdos\b', r'\b2:00\b', r'\b14\b', r'\bcatorce\b', r'\b14:00\b',
            r'\b4\b', r'\bcuatro\b', r'\b4:00\b', r'\b16\b', r'\bdieciséis\b', r'\b16:00\b'
        ]
        
        # Check if a time was specified
        time_match = any(re.search(pattern, speech_result) for pattern in time_patterns)
        
        if time_match or dtmf == '1':
            logger.info("Spanish appointment time confirmed")
            enhanced_say(response, "¡Excelente! He programado su cita. Recibirá un mensaje de confirmación en breve.", language="es-MX")
            enhanced_say(response, "¿Hay algo más en lo que pueda ayudarle hoy?", language="es-MX")
            
            enhanced_gather(
                response=response,
                text="Por favor, dígame si necesita algo más.",
                action=url_for('main.handle_spanish_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="es-MX",
                enhanced=True
            )
        else:
            logger.info("Spanish appointment times rejected")
            enhanced_say(response, "Entiendo que esos horarios no funcionan para usted. Permítame conectarle con nuestro equipo de programación para encontrar un mejor horario.", language="es-MX")
            # Add transfer logic here
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_spanish_appointment_confirmation route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES_SPANISH['appointment_error'], language="es-MX")
        return str(response)

@main.route('/handle-spanish-transfer', methods=['POST'])
def handle_spanish_transfer():
    """Handle transfer to human request in Spanish."""
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
        logger.info(f"Spanish transfer response: '{speech_result}'")
        
        # Check if user wants to be transferred
        if any(word in speech_result for word in ['sí', 'si', 'por favor', 'claro', 'ok', 'okay']) or dtmf == '1':
            logger.info("Spanish user requested transfer to human")
            enhanced_say(response, "Le conectaré con alguien de inmediato. Por favor, espere.", language="es-MX")
            # Add code to transfer to a human here
        else:
            logger.info("Spanish user declined transfer to human")
            enhanced_say(response, "De acuerdo. ¿Hay algo más en lo que pueda ayudarle hoy?", language="es-MX")
            
            enhanced_gather(
                response=response,
                text="Por favor, dígame si necesita algo más.",
                action=url_for('main.handle_spanish_response'),
                input_types='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                speech_model='phone_call',
                language="es-MX",
                enhanced=True
            )
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_spanish_transfer route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES_SPANISH['input_not_understood'], language="es-MX")
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
            enhanced_say(response, "Great! I've scheduled your appointment. You'll receive a confirmation message shortly.", language="en-US")
            enhanced_say(response, "Is there anything else I can help you with today?", language="en-US")
            response.redirect(url_for('main.voice'))
        else:
            logger.info("Appointment times rejected")
            enhanced_say(response, "I understand those times don't work for you. Let me connect you with our scheduling team to find a better time.", language="en-US")
            # Add transfer logic here
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_appointment route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['appointment_error'], language="en-US")
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
            enhanced_say(response, "I'll connect you with someone right away. Please hold.", language="en-US")
            # Add code to transfer to a human here
        else:
            logger.info("User declined transfer to human")
            enhanced_say(response, "Alright. Is there anything else I can help you with today?", language="en-US")
            response.redirect(url_for('main.voice'))
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_transfer route: {str(e)}"
        log_error(error_msg)
        logger.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        enhanced_say(response, ERROR_MESSAGES['input_not_understood'], language="en-US")
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
