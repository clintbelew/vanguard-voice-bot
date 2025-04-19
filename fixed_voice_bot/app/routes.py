from flask import Blueprint, request, url_for, jsonify, send_from_directory
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
from app.elevenlabs_integration import elevenlabs_api
from config.config import GREETING_MESSAGE, ERROR_MESSAGES
import logging
import re
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voice_bot.log"),
        logging.StreamHandler()
    ]
)

# Create blueprint
main = Blueprint('main', __name__)

# Create audio cache directory
os.makedirs('audio_cache', exist_ok=True)

# Helper function to use ElevenLabs or fallback to Polly
def speak(response, text, voice='Polly.Joanna'):
    """Generate speech using ElevenLabs if available, otherwise fallback to Polly."""
    try:
        # Try to use ElevenLabs
        if elevenlabs_api.is_configured():
            audio_url = elevenlabs_api.text_to_speech(text)
            if audio_url:
                # Add subtle background ambiance at 10% volume
                response.play('https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3?filename=office-ambience-6321.mp3', volume=0.1)
                # Play the ElevenLabs generated audio
                response.play(audio_url)
                return
    except Exception as e:
        logging.error(f"Error using ElevenLabs: {str(e)}")
    
    # Fallback to Polly if ElevenLabs fails or is not configured
    response.say(text, voice=voice)

@main.route('/audio/<filename>')
def serve_audio(filename):
    """Serve cached audio files."""
    return send_from_directory('audio_cache', filename)

@main.route('/')
def index():
    """Home page route."""
    return "Twilio Voice Bot for Vanguard Chiropractic is running!"

@main.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming voice calls."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Get caller information
        caller_number = request.values.get('From', '')
        logging.info(f"Incoming call from: {caller_number}")
        
        # Check if this is the initial call or a continuation
        if 'SpeechResult' not in request.values:
            # Initial call - greet the caller
            gather = Gather(
                input='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                action=url_for('main.handle_response'),
                speech_model='phone_call',
                enhanced=True,
                # No language parameter here - let Twilio auto-detect
            )
            
            # Use ElevenLabs or fallback to Polly
            speak(gather, GREETING_MESSAGE)
            response.append(gather)
            
            # If no input is received, repeat the greeting
            response.redirect(url_for('main.voice'))
        else:
            # This shouldn't normally happen, but handle it gracefully
            speech_result = request.values.get('SpeechResult', '')
            log_speech_input(speech_result, caller_number)
            
            # Redirect to handle_response
            response.redirect(url_for('main.handle_response'))
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in voice route: {str(e)}"
        log_error(error_msg)
        logging.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        speak(response, ERROR_MESSAGES['general'])
        return str(response)

@main.route('/handle-response', methods=['POST'])
def handle_response():
    """Handle responses from the caller."""
    try:
        # Create TwiML response
        response = VoiceResponse()
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        
        # Handle common questions with intent matching
        if any(phrase in speech_result for phrase in ['talk to someone', 'speak to someone', 'talk to a person', 'human']):
            speak(response, "I'll connect you with someone right away. Please hold.")
            # Add code to transfer to a human here
            
        elif any(phrase in speech_result for phrase in ['credit card', 'payment', 'pay with card', 'accept card']):
            speak(response, "Yes, we accept all major credit cards including Visa, Mastercard, American Express, and Discover.")
            
        elif any(phrase in speech_result for phrase in ['insurance', 'covered by insurance', 'my insurance']):
            speak(response, "We work with most major insurance providers. Our staff can verify your benefits before your appointment.")
            
        elif any(phrase in speech_result for phrase in ['walk in', 'walk-in']):
            speak(response, "We do accept walk-ins based on availability, but we recommend scheduling an appointment to minimize wait time.")
            
        elif any(phrase in speech_result for phrase in ['appointment', 'schedule', 'book', 'make an appointment']):
            # Handle appointment scheduling with robust error handling
            try:
                handle_appointment_booking(response, speech_result)
            except Exception as e:
                error_msg = f"Error in appointment booking: {str(e)}"
                log_error(error_msg)
                logging.error(error_msg)
                speak(response, ERROR_MESSAGES['appointment_error'])
                
        elif any(phrase in speech_result for phrase in ['reschedule', 'change appointment']):
            # Handle appointment rescheduling with robust error handling
            try:
                handle_appointment_rescheduling(response, speech_result)
            except Exception as e:
                error_msg = f"Error in appointment rescheduling: {str(e)}"
                log_error(error_msg)
                logging.error(error_msg)
                speak(response, ERROR_MESSAGES['appointment_error'])
                
        else:
            # Fallback for questions it can't answer
            speak(response, "I'm not totally sure how to answer that, but I can connect you with someone if you'd like.")
            
            gather = Gather(
                input='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                action=url_for('main.handle_transfer'),
                speech_model='phone_call'
            )
            speak(gather, "Would you like me to connect you with someone?")
            response.append(gather)
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_response route: {str(e)}"
        log_error(error_msg)
        logging.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        speak(response, ERROR_MESSAGES['input_not_understood'])
        return str(response)

@main.route('/handle-appointment', methods=['POST'])
def handle_appointment():
    """Handle appointment selection."""
    try:
        response = VoiceResponse()
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        
        # Enhanced time recognition patterns
        time_patterns = [
            r'\b9\s*(?:am|a\.m\.)\b',  # 9am, 9 am, 9a.m.
            r'\b9\s*(?:o\'clock)\b',   # 9 o'clock
            r'\b9\s*(?:in the morning)\b',  # 9 in the morning
            r'\b9:00\b',               # 9:00
            r'\bnine\b',               # nine
            r'\bmorning\b',            # morning
            r'\b10\s*(?:am|a\.m\.)\b', # 10am, 10 am, 10a.m.
            r'\b10\s*(?:o\'clock)\b',  # 10 o'clock
            r'\b10:00\b',              # 10:00
            r'\bten\b',                # ten
            r'\b11\s*(?:am|a\.m\.)\b', # 11am, 11 am, 11a.m.
            r'\b11\s*(?:o\'clock)\b',  # 11 o'clock
            r'\b11:00\b',              # 11:00
            r'\beleven\b',             # eleven
            r'\b12\s*(?:pm|p\.m\.)\b', # 12pm, 12 pm, 12p.m.
            r'\b12\s*(?:o\'clock)\b',  # 12 o'clock
            r'\b12:00\b',              # 12:00
            r'\btwelve\b',             # twelve
            r'\bnoon\b',               # noon
            r'\b1\s*(?:pm|p\.m\.)\b',  # 1pm, 1 pm, 1p.m.
            r'\b1\s*(?:o\'clock)\b',   # 1 o'clock
            r'\b1:00\b',               # 1:00
            r'\bone\b',                # one
            r'\b2\s*(?:pm|p\.m\.)\b',  # 2pm, 2 pm, 2p.m.
            r'\b2\s*(?:o\'clock)\b',   # 2 o'clock
            r'\b2:00\b',               # 2:00
            r'\btwo\b',                # two
            r'\b3\s*(?:pm|p\.m\.)\b',  # 3pm, 3 pm, 3p.m.
            r'\b3\s*(?:o\'clock)\b',   # 3 o'clock
            r'\b3:00\b',               # 3:00
            r'\bthree\b',              # three
            r'\b4\s*(?:pm|p\.m\.)\b',  # 4pm, 4 pm, 4p.m.
            r'\b4\s*(?:o\'clock)\b',   # 4 o'clock
            r'\b4:00\b',               # 4:00
            r'\bfour\b',               # four
            r'\b5\s*(?:pm|p\.m\.)\b',  # 5pm, 5 pm, 5p.m.
            r'\b5\s*(?:o\'clock)\b',   # 5 o'clock
            r'\b5:00\b',               # 5:00
            r'\bfive\b',               # five
        ]
        
        # Affirmative response patterns
        affirmative_patterns = [
            r'\byes\b',
            r'\byeah\b',
            r'\bsure\b',
            r'\bplease\b',
            r'\bthat works\b',
            r'\bsounds good\b',
            r'\bperfect\b',
            r'\bgreat\b',
            r'\bok\b',
            r'\bokay\b',
        ]
        
        # Day patterns
        day_patterns = [
            r'\btoday\b',
            r'\btomorrow\b',
            r'\bmonday\b',
            r'\btuesday\b',
            r'\bwednesday\b',
            r'\bthursday\b',
            r'\bfriday\b',
            r'\bsaturday\b',
            r'\bsunday\b',
        ]
        
        # Check if user wants to book one of the offered slots
        time_match = any(re.search(pattern, speech_result) for pattern in time_patterns)
        affirmative_match = any(re.search(pattern, speech_result) for pattern in affirmative_patterns)
        day_match = any(re.search(pattern, speech_result) for pattern in day_patterns)
        
        if time_match or affirmative_match or day_match:
            speak(response, "Great! I've scheduled your appointment. You'll receive a confirmation message shortly.")
            speak(response, "Is there anything else I can help you with today?")
            response.redirect(url_for('main.voice'))
        else:
            speak(response, "I understand those times don't work for you. Let me connect you with our scheduling team to find a better time.")
            # Add transfer logic here
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_appointment route: {str(e)}"
        log_error(error_msg)
        logging.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        speak(response, ERROR_MESSAGES['appointment_error'])
        return str(response)

@main.route('/handle-transfer', methods=['POST'])
def handle_transfer():
    """Handle transfer to human request."""
    try:
        response = VoiceResponse()
        
        # Get the user's speech or DTMF input
        speech_result = request.values.get('SpeechResult', '').lower()
        dtmf = request.values.get('Digits', '')
        
        # Log the speech input
        caller_number = request.values.get('From', '')
        log_speech_input(speech_result, caller_number)
        
        # Check if user wants to be transferred
        if any(word in speech_result for word in ['yes', 'yeah', 'sure', 'please']) or dtmf == '1':
            speak(response, "I'll connect you with someone right away. Please hold.")
            # Add code to transfer to a human here
        else:
            speak(response, "Alright. Is there anything else I can help you with today?")
            response.redirect(url_for('main.voice'))
            
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_transfer route: {str(e)}"
        log_error(error_msg)
        logging.error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        speak(response, ERROR_MESSAGES['input_not_understood'])
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
        return jsonify({"status": "success", "message": "Speech input logged"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
