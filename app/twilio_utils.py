from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from config.config import (
    TWILIO_ACCOUNT_SID, 
    TWILIO_AUTH_TOKEN, 
    TWILIO_PHONE_NUMBER,
    FAQ,
    BUSINESS_NAME,
    BUSINESS_PHONE,
    VOICE_NAME
)
import logging
from app.gohighlevel_integration import (
    create_contact,
    update_contact,
    create_appointment,
    update_appointment,
    get_appointment,
    tag_contact
)

# Initialize Twilio client
client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def handle_greeting(response):
    """Handle the initial greeting."""
    gather = Gather(
        input='speech dtmf',
        action='/handle-response',
        speech_timeout='auto',
        speech_model='phone_call',
        enhanced=True,
        language='en-US'
    )
    gather.say(f"Thank you for calling {BUSINESS_NAME}. How can I help you today?", voice=VOICE_NAME)
    response.append(gather)
    return response

def handle_faq(response, faq_type):
    """Handle FAQ responses."""
    if faq_type in FAQ:
        response.say(FAQ[faq_type], voice=VOICE_NAME)
    else:
        response.say("I'm sorry, I don't have information about that topic. Let me connect you with our staff.", voice=VOICE_NAME)
    
    # Ask if they need anything else
    gather = Gather(
        input='speech dtmf',
        action='/handle-response',
        speech_timeout='auto',
        speech_model='phone_call',
        enhanced=True,
        language='en-US'
    )
    gather.say("Is there anything else I can help you with today?", voice=VOICE_NAME)
    response.append(gather)
    return response

def handle_appointment_booking(response, caller_number):
    """Handle appointment booking requests."""
    # First, ask if they are a new or existing patient
    gather = Gather(
        input='speech dtmf',
        action='/appointment-type',
        speech_timeout='auto',
        speech_model='phone_call',
        enhanced=True,
        language='en-US',
        num_digits=1
    )
    gather.say("I'd be happy to help you book an appointment. Are you a new patient or have you visited us before? Press 1 for new patient, or press 2 if you've been here before.", voice=VOICE_NAME)
    response.append(gather)
    
    # If no input is received, repeat the question
    response.redirect('/voice')
    return response

def handle_appointment_rescheduling(response, caller_number):
    """Handle appointment rescheduling requests."""
    gather = Gather(
        input='speech dtmf',
        action='/reschedule-appointment',
        speech_timeout='auto',
        speech_model='phone_call',
        enhanced=True,
        language='en-US'
    )
    gather.say("I can help you reschedule your appointment. To locate your current appointment, could you please provide your phone number or say your full name?", voice=VOICE_NAME)
    response.append(gather)
    
    # If no input is received, repeat the question
    response.redirect('/voice')
    return response

def handle_missed_call(caller_number):
    """Handle missed calls by sending SMS and creating record in GoHighLevel."""
    if not client:
        logging.error("Twilio client not initialized. Cannot send SMS.")
        return False
    
    try:
        # Send SMS for missed call
        message = client.messages.create(
            body=f"Sorry we missed your call to {BUSINESS_NAME}. Please call us back at {BUSINESS_PHONE} or reply to this message to schedule an appointment.",
            from_=TWILIO_PHONE_NUMBER,
            to=caller_number
        )
        
        # Create or update contact in GoHighLevel
        contact_data = {
            'phone': caller_number,
            'source': 'Missed Call'
        }
        contact_id = create_contact(contact_data)
        
        # Tag contact for follow-up
        if contact_id:
            tag_contact(contact_id, 'Missed Call')
        
        return True
    except Exception as e:
        logging.error(f"Error handling missed call: {str(e)}")
        return False

def handle_fallback(response):
    """Handle unrecognized intents."""
    gather = Gather(
        input='speech dtmf',
        action='/handle-response',
        speech_timeout='auto',
        speech_model='phone_call',
        enhanced=True,
        language='en-US'
    )
    gather.say("I'm sorry, but I didn't quite understand that. Could you please rephrase your question? You can ask about our hours, services, insurance, location, or scheduling an appointment.", voice=VOICE_NAME)
    response.append(gather)
    
    # If no input is received, transfer to staff
    response.say("I'll connect you with our staff for assistance.", voice=VOICE_NAME)
    return response

def send_appointment_confirmation_sms(phone_number, appointment_date, appointment_time):
    """Send appointment confirmation via SMS."""
    if not client:
        logging.error("Twilio client not initialized. Cannot send SMS.")
        return False
    
    try:
        message = client.messages.create(
            body=f"Your appointment with {BUSINESS_NAME} is confirmed for {appointment_date} at {appointment_time}. Reply C to confirm or R to reschedule.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        logging.error(f"Error sending appointment confirmation: {str(e)}")
        return False

def make_outbound_call(to_number, call_type, appointment_data=None):
    """Make outbound calls for appointment reminders or follow-ups."""
    if not client:
        logging.error("Twilio client not initialized. Cannot make outbound call.")
        return False
    
    try:
        # Determine the URL based on call type
        if call_type == 'reminder':
            url = '/outbound-reminder'
        elif call_type == 'missed_appointment':
            url = '/outbound-missed'
        else:
            url = '/outbound-call'
        
        # Make the call
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=url,
            method='POST'
        )
        
        return True
    except Exception as e:
        logging.error(f"Error making outbound call: {str(e)}")
        return False
