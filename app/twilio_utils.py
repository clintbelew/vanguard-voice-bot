"""
Utility functions for Twilio voice interactions.
"""
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from flask import url_for
from config.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    FAQ,
    BUSINESS_NAME,
    BUSINESS_PHONE,
    VOICE_NAME,
    ERROR_MESSAGES
)
import logging
import datetime
import json
import os
from app.gohighlevel_integration import (
    create_contact,
    update_contact,
    create_appointment,
    update_appointment,
    get_appointment,
    tag_contact,
    get_available_slots,
    is_configured
)

# Ensure log directory exists
os.makedirs('logs', exist_ok=True)

# Initialize Twilio client
client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def log_speech_input(speech_text, caller_number):
    """Log speech input for analysis and debugging."""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "caller": caller_number,
        "speech_text": speech_text
    }
    
    # Log to file
    try:
        with open('logs/speech_inputs.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logging.error(f"Error logging speech input: {str(e)}")
    
    # Also log to standard logger
    logging.info(f"Speech input from {caller_number}: {speech_text}")
    
    return True

def log_error(error_message):
    """Log errors for debugging."""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "error": error_message
    }
    
    # Log to file
    try:
        with open('logs/errors.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logging.error(f"Error logging to error log: {str(e)}")
    
    # Also log to standard logger
    logging.error(error_message)
    
    return True

def handle_greeting(response):
    """Handle the initial greeting."""
    try:
        gather = Gather(
            input='speech dtmf',
            action='/handle-response',
            speech_timeout='auto',
            speech_model='phone_call',
            enhanced=True,
            # No language parameter - let Twilio auto-detect
        )
        gather.say(f"Thank you for calling {BUSINESS_NAME}. How can I help you today?", voice='Polly.Joanna')
        response.append(gather)
        
        # If no input is received, repeat the greeting
        response.redirect('/voice')
        
        return response
    except Exception as e:
        error_msg = f"Error in handle_greeting: {str(e)}"
        log_error(error_msg)
        
        # Fallback response
        response.say("Thank you for calling. Let me connect you with someone who can help.", voice='Polly.Joanna')
        return response

def handle_faq(response, question):
    """Handle frequently asked questions."""
    try:
        # Map of common questions and their answers
        faq_responses = {
            'hours': "Our hours are Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 2 PM.",
            'location': "We're located at 123 Main Street, Suite 200, in downtown.",
            'services': "We offer a full range of chiropractic services including adjustments, massage therapy, and rehabilitation.",
            'insurance': "We accept most major insurance plans. Our staff can verify your benefits before your appointment.",
            'payment': "We accept all major credit cards, cash, and checks.",
            'appointment': "We'd be happy to schedule an appointment for you. When would you like to come in?",
            'walk_in': "We do accept walk-ins based on availability, but we recommend scheduling an appointment to minimize wait time."
        }
        
        # Log the question for analysis
        log_speech_input(question, "FAQ")
        
        # Determine which FAQ to respond to
        for key, answer in faq_responses.items():
            if key in question.lower():
                response.say(answer, voice='Polly.Joanna')
                return response
        
        # If no match, use fallback
        return handle_fallback(response)
    except Exception as e:
        error_msg = f"Error in handle_faq: {str(e)}"
        log_error(error_msg)
        
        # Fallback response
        response.say("I'm not totally sure how to answer that, but I can connect you with someone if you'd like.", voice='Polly.Joanna')
        return response

def handle_appointment_booking(response, speech_input=None):
    """Handle appointment booking requests."""
    try:
        # Log the appointment request
        log_speech_input(speech_input or "Appointment booking request", "APPOINTMENT")
        
        # Check if GoHighLevel integration is configured
        if not is_configured():
            logging.warning("GoHighLevel integration not configured. Using fallback for appointment booking.")
            response.say(ERROR_MESSAGES['appointment_error'], voice='Polly.Joanna')
            response.say("Let me connect you with our scheduling team who can help you book an appointment.", voice='Polly.Joanna')
            # Add transfer logic here
            return response
        
        # Try to get available slots from GoHighLevel
        available_slots = get_available_slots()
        
        if not available_slots:
            logging.warning("No available slots returned from GoHighLevel. Using fallback.")
            response.say("I'm having trouble accessing our scheduling system right now.", voice='Polly.Joanna')
            response.say("Let me connect you with our scheduling team who can help you book an appointment.", voice='Polly.Joanna')
            # Add transfer logic here
            return response
        
        # Format available slots for speech
        slot_descriptions = []
        for i, slot in enumerate(available_slots[:2]):  # Limit to 2 slots for simplicity
            slot_descriptions.append(f"{slot['date']} at {slot['time']}")
        
        slots_text = " or ".join(slot_descriptions)
        response.say(f"I'd be happy to help you schedule an appointment. Our next available slots are {slots_text}.", voice='Polly.Joanna')
        
        gather = Gather(
            input='speech dtmf',
            timeout=3,
            speech_timeout='auto',
            action='/handle-appointment',
            speech_model='phone_call',
            enhanced=True
        )
        gather.say("Would either of those times work for you?", voice='Polly.Joanna')
        response.append(gather)
        
        # If no input is received, provide a fallback
        response.say("I'll connect you with our scheduling team to find a time that works for you.", voice='Polly.Joanna')
        
        return response
    except Exception as e:
        error_msg = f"Error in handle_appointment_booking: {str(e)}"
        log_error(error_msg)
        
        # Fallback response
        response.say(ERROR_MESSAGES['appointment_error'], voice='Polly.Joanna')
        response.say("Let me connect you with our staff who can help schedule your appointment.", voice='Polly.Joanna')
        return response

def handle_appointment_rescheduling(response, speech_input=None):
    """Handle appointment rescheduling requests."""
    try:
        # Log the rescheduling request
        log_speech_input(speech_input or "Appointment rescheduling request", "RESCHEDULE")
        
        # Check if GoHighLevel integration is configured
        if not is_configured():
            logging.warning("GoHighLevel integration not configured. Using fallback for appointment rescheduling.")
            response.say(ERROR_MESSAGES['appointment_error'], voice='Polly.Joanna')
            response.say("Let me connect you with our scheduling team who can help you reschedule your appointment.", voice='Polly.Joanna')
            # Add transfer logic here
            return response
        
        response.say("I understand you'd like to reschedule your appointment. To better assist you, I'll need to connect you with our scheduling team.", voice='Polly.Joanna')
        # Add transfer logic here
        
        return response
    except Exception as e:
        error_msg = f"Error in handle_appointment_rescheduling: {str(e)}"
        log_error(error_msg)
        
        # Fallback response
        response.say(ERROR_MESSAGES['appointment_error'], voice='Polly.Joanna')
        response.say("Let me connect you with our staff who can help reschedule your appointment.", voice='Polly.Joanna')
        return response

def handle_missed_call(caller_number):
    """Handle missed calls by sending SMS and creating record in GoHighLevel."""
    try:
        if not client:
            error_msg = "Twilio client not initialized. Cannot send SMS."
            log_error(error_msg)
            return False
            
        # Send SMS for missed call
        message = client.messages.create(
            body=f"Sorry we missed your call to {BUSINESS_NAME}. Please call us back at {BUSINESS_PHONE} or reply to this message to schedule an appointment.",
            from_=TWILIO_PHONE_NUMBER,
            to=caller_number
        )
        
        # Check if GoHighLevel integration is configured
        if not is_configured():
            logging.warning("GoHighLevel integration not configured. Skipping contact creation.")
            return True
        
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
        error_msg = f"Error handling missed call: {str(e)}"
        log_error(error_msg)
        return False

def handle_fallback(response):
    """Handle cases where the bot doesn't understand the request."""
    try:
        gather = Gather(
            input='speech dtmf',
            timeout=3,
            speech_timeout='auto',
            action='/handle-transfer',
            speech_model='phone_call',
            enhanced=True
        )
        gather.say("I'm not totally sure how to answer that, but I can connect you with someone if you'd like.", voice='Polly.Joanna')
        response.append(gather)
        
        # If no input is received, provide a default action
        response.say("I'll connect you with our staff for assistance.", voice='Polly.Joanna')
        
        return response
    except Exception as e:
        error_msg = f"Error in handle_fallback: {str(e)}"
        log_error(error_msg)
        
        # Ultimate fallback response if even the fallback handler fails
        response.say("Sorry, I didn't catch that—let me connect you with someone who can help.", voice='Polly.Joanna')
        return response

def send_appointment_confirmation_sms(phone_number, appointment_date, appointment_time):
    """Send appointment confirmation via SMS."""
    try:
        if not client:
            error_msg = "Twilio client not initialized. Cannot send SMS."
            log_error(error_msg)
            return False
            
        message = client.messages.create(
            body=f"Your appointment with {BUSINESS_NAME} is confirmed for {appointment_date} at {appointment_time}. Reply C to confirm or R to reschedule.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        return True
    except Exception as e:
        error_msg = f"Error sending appointment confirmation: {str(e)}"
        log_error(error_msg)
        return False

def make_outbound_call(to_number, call_type, appointment_data=None):
    """Make outbound calls for appointment reminders or follow-ups."""
    try:
        if not client:
            error_msg = "Twilio client not initialized. Cannot make outbound call."
            log_error(error_msg)
            return False
            
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
        error_msg = f"Error making outbound call: {str(e)}"
        log_error(error_msg)
        return False
