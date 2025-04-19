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
from config.config import GREETING_MESSAGE
import logging

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
            
            # Use voice parameter for a more natural sound
            gather.say(GREETING_MESSAGE, voice='Polly.Joanna')
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
        
        # Create a fallback response
        response = VoiceResponse()
        response.say("I'm sorry, we're experiencing technical difficulties. Let me connect you with someone who can help.", voice='Polly.Joanna')
        
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
            response.say("I'll connect you with someone right away. Please hold.", voice='Polly.Joanna')
            # Add code to transfer to a human here
            
        elif any(phrase in speech_result for phrase in ['credit card', 'payment', 'pay with card', 'accept card']):
            response.say("Yes, we accept all major credit cards including Visa, Mastercard, American Express, and Discover.", voice='Polly.Joanna')
            
        elif any(phrase in speech_result for phrase in ['insurance', 'covered by insurance', 'my insurance']):
            response.say("We work with most major insurance providers. Our staff can verify your benefits before your appointment.", voice='Polly.Joanna')
            
        elif any(phrase in speech_result for phrase in ['walk in', 'walk-in', 'appointment', 'schedule']):
            response.say("We do accept walk-ins based on availability, but we recommend scheduling an appointment to minimize wait time.", voice='Polly.Joanna')
            
        elif 'appointment' in speech_result:
            # Handle appointment scheduling
            handle_appointment_booking(response, speech_result)
            
        elif any(phrase in speech_result for phrase in ['reschedule', 'change appointment']):
            # Handle appointment rescheduling
            handle_appointment_rescheduling(response, speech_result)
            
        else:
            # Fallback for questions it can't answer
            response.say("I'm not totally sure how to answer that, but I can connect you with someone if you'd like.", voice='Polly.Joanna')
            gather = Gather(
                input='speech dtmf',
                timeout=3,
                speech_timeout='auto',
                action=url_for('main.handle_transfer'),
                speech_model='phone_call'
            )
            gather.say("Would you like me to connect you with someone?", voice='Polly.Joanna')
            response.append(gather)
        
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_response route: {str(e)}"
        log_error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        response.say("Sorry, I didn't catch that—let me connect you with someone who can help.", voice='Polly.Joanna')
        
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
            response.say("I'll connect you with someone right away. Please hold.", voice='Polly.Joanna')
            # Add code to transfer to a human here
            
        else:
            response.say("Alright. Is there anything else I can help you with today?", voice='Polly.Joanna')
            response.redirect(url_for('main.voice'))
        
        return str(response)
    except Exception as e:
        # Log the error
        error_msg = f"Error in handle_transfer route: {str(e)}"
        log_error(error_msg)
        
        # Create a fallback response
        response = VoiceResponse()
        response.say("Sorry, I didn't catch that—let me connect you with someone who can help.", voice='Polly.Joanna')
        
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
