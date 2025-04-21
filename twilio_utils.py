"""
Utility functions for Twilio voice interactions.
"""
from twilio.twiml.voice_response import VoiceResponse, Gather
from flask import url_for

def handle_greeting(response, caller_number=None):
    """Handle initial greeting for callers."""
    # Use Polly.Joanna voice for more natural sound
    response.say("Thank you for calling Vanguard Chiropractic. How can I help you today?", voice='Polly.Joanna')
    return response

def handle_faq(response, question):
    """Handle frequently asked questions."""
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
    
    # Determine which FAQ to respond to
    for key, answer in faq_responses.items():
        if key in question.lower():
            response.say(answer, voice='Polly.Joanna')
            return response
    
    # If no match, use fallback
    return handle_fallback(response)

def handle_appointment_booking(response, speech_input=None):
    """Handle appointment booking requests."""
    response.say("I'd be happy to help you schedule an appointment. Our next available slots are tomorrow at 10 AM or Friday at 2 PM.", voice='Polly.Joanna')
    
    gather = Gather(
        input='speech dtmf',
        timeout=3,
        speech_timeout='auto',
        action=url_for('main.handle_response'),
        speech_model='phone_call'
    )
    gather.say("Would either of those times work for you?", voice='Polly.Joanna')
    response.append(gather)
    
    return response

def handle_appointment_rescheduling(response, speech_input=None):
    """Handle appointment rescheduling requests."""
    response.say("I understand you'd like to reschedule your appointment. To better assist you, I'll need to connect you with our scheduling team.", voice='Polly.Joanna')
    # Add transfer logic here
    
    return response

def handle_missed_call(response, caller_number=None):
    """Handle missed call scenarios."""
    response.say("I'm sorry we missed your call. Our team will call you back as soon as possible.", voice='Polly.Joanna')
    
    return response

def handle_fallback(response):
    """Handle cases where the bot doesn't understand the request."""
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
    
    return response
