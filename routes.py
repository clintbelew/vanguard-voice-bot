from flask import Blueprint, request, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.twilio_utils import (
    handle_greeting,
    handle_faq,
    handle_appointment_booking,
    handle_appointment_rescheduling,
    handle_missed_call,
    handle_fallback
)
from config.config import GREETING_MESSAGE

# Create blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page route."""
    return "Twilio Voice Bot for Vanguard Chiropractic is running!"

@main.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming voice calls."""
    # Create TwiML response
    response = VoiceResponse()
    
    # Set voice to Polly.Joanna for a more natural sound
    response.say('', voice='Polly.Joanna')
    
    # Get caller information
    caller_number = request.values.get('From', '')
    
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
            language='en-US'
        )
        
        # Use Polly.Joanna voice for a more natural sound
        gather.say(GREETING_MESSAGE, voice='Polly.Joanna')
        response.append(gather)
        
        # If no input is received, repeat the greeting
        response.redirect(url_for('main.voice'))
        
    return str(response)

@main.route('/handle-response', methods=['POST'])
def handle_response():
    """Handle responses from the caller."""
    # Create TwiML response
    response = VoiceResponse()
    
    # Get the user's speech or DTMF input
    speech_result = request.values.get('SpeechResult', '').lower()
    dtmf = request.values.get('Digits', '')
    
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

@main.route('/handle-transfer', methods=['POST'])
def handle_transfer():
    """Handle transfer to human request."""
    response = VoiceResponse()
    
    # Get the user's speech or DTMF input
    speech_result = request.values.get('SpeechResult', '').lower()
    dtmf = request.values.get('Digits', '')
    
    # Check if user wants to be transferred
    if any(word in speech_result for word in ['yes', 'yeah', 'sure', 'please']) or dtmf == '1':
        response.say("I'll connect you with someone right away. Please hold.", voice='Polly.Joanna')
        # Add code to transfer to a human here
        
    else:
        response.say("Alright. Is there anything else I can help you with today?", voice='Polly.Joanna')
        response.redirect(url_for('main.voice'))
    
    return str(response)
