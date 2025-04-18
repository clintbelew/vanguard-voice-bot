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

@main.route('/voice', methods=['POST'])
def voice():
    """Handle incoming voice calls."""
    # Create TwiML response
    response = VoiceResponse()
    
    # Get caller information
    caller_number = request.values.get('From', '')
    
    # Check if this is the initial call or a continuation
    if 'SpeechResult' not in request.values:
        # Initial call - greet the caller
        gather = Gather(
            input='speech dtmf',
            action=url_for('main.handle_response'),
            speech_timeout='auto',
            speech_model='phone_call',
            enhanced=True,
            language='en-US'
        )
        gather.say(GREETING_MESSAGE)
        response.append(gather)
        
        # If no input is received, repeat the greeting
        response.redirect(url_for('main.voice'))
    
    return str(response)

@main.route('/handle-response', methods=['POST'])
def handle_response():
    """Process the caller's speech or keypad input."""
    # Create TwiML response
    response = VoiceResponse()
    
    # Get caller's input
    speech_result = request.values.get('SpeechResult', '').lower()
    digits = request.values.get('Digits', '')
    caller_number = request.values.get('From', '')
    
    # Determine intent from speech or digits
    if 'hour' in speech_result or 'open' in speech_result or digits == '1':
        # FAQ about hours
        handle_faq(response, 'hours')
    elif 'service' in speech_result or 'offer' in speech_result or digits == '2':
        # FAQ about services
        handle_faq(response, 'services')
    elif 'insurance' in speech_result or digits == '3':
        # FAQ about insurance
        handle_faq(response, 'insurance')
    elif 'location' in speech_result or 'address' in speech_result or 'where' in speech_result or digits == '4':
        # FAQ about location
        handle_faq(response, 'location')
    elif ('appointment' in speech_result or 'schedule' in speech_result or 'book' in speech_result or digits == '5') and 'reschedule' not in speech_result:
        # Appointment booking
        handle_appointment_booking(response, caller_number)
    elif 'reschedule' in speech_result or 'change' in speech_result or 'move' in speech_result or digits == '6':
        # Appointment rescheduling
        handle_appointment_rescheduling(response, caller_number)
    elif 'emergency' in speech_result or digits == '0':
        # Emergency situation
        handle_faq(response, 'emergency')
    else:
        # Fallback for unrecognized intent
        handle_fallback(response)
    
    return str(response)

@main.route('/missed-call', methods=['POST'])
def missed_call():
    """Handle missed calls."""
    caller_number = request.values.get('From', '')
    
    # Process missed call
    handle_missed_call(caller_number)
    
    return "Missed call processed"

@main.route('/appointment-reminder', methods=['POST'])
def appointment_reminder():
    """Handle appointment reminder responses."""
    # Create TwiML response
    response = VoiceResponse()
    
    # Get caller's input
    digits = request.values.get('Digits', '')
    caller_number = request.values.get('From', '')
    
    if digits == '1':
        # Confirm appointment
        response.say("Thank you for confirming your appointment. We look forward to seeing you!")
    elif digits == '2':
        # Reschedule appointment
        handle_appointment_rescheduling(response, caller_number)
    else:
        # Transfer to staff
        response.say("Please hold while I transfer you to our staff.")
        # In a real implementation, you would add code to transfer the call
    
    return str(response)

@main.route('/outbound-call', methods=['POST'])
def outbound_call():
    """Handle outbound call responses."""
    # Create TwiML response
    response = VoiceResponse()
    
    # This would be expanded based on the type of outbound call
    response.say("This is an automated call from Vanguard Chiropractic.")
    
    return str(response)
