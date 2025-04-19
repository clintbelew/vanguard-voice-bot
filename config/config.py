"""
Configuration settings for the voice bot application.
"""
import os

# Twilio account settings
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', "")  # Add your Twilio Account SID here
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', "")    # Add your Twilio Auth Token here
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', "") # Add your Twilio Phone Number here

# GoHighLevel settings
GOHIGHLEVEL_API_KEY = os.environ.get('GOHIGHLEVEL_API_KEY', "")
GOHIGHLEVEL_LOCATION_ID = os.environ.get('GOHIGHLEVEL_LOCATION_ID', "")
GOHIGHLEVEL_CALENDAR_ID = os.environ.get('GOHIGHLEVEL_CALENDAR_ID', "")

# Business information
BUSINESS_NAME = "Vanguard Chiropractic"
BUSINESS_PHONE = "(830) 429-4111"
BUSINESS_ADDRESS = "123 Main Street, Suite 200"
BUSINESS_CITY = "San Antonio"
BUSINESS_STATE = "TX"
BUSINESS_ZIP = "78209"

# Voice settings
VOICE_NAME = "Polly.Joanna"  # Using Polly.Joanna for more natural voice

# Greeting message used when a caller first connects
GREETING_MESSAGE = "Thank you for calling Vanguard Chiropractic. How can I help you today?"

# FAQ responses
FAQ = {
    "hours": "Our hours are Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 2 PM.",
    "location": f"We're located at {BUSINESS_ADDRESS} in {BUSINESS_CITY}, {BUSINESS_STATE} {BUSINESS_ZIP}.",
    "services": "We offer a full range of chiropractic services including adjustments, massage therapy, and rehabilitation.",
    "insurance": "We accept most major insurance plans. Our staff can verify your benefits before your appointment.",
    "payment": "We accept all major credit cards, cash, and checks.",
    "appointment": "We'd be happy to schedule an appointment for you. When would you like to come in?",
    "walk_in": "We do accept walk-ins based on availability, but we recommend scheduling an appointment to minimize wait time."
}

# Error messages
ERROR_MESSAGES = {
    "general": "I'm sorry, we're experiencing technical difficulties. Let me connect you with someone who can help.",
    "input_not_understood": "Sorry, I didn't catch that—let me connect you with someone who can help.",
    "appointment_error": "I'm having trouble with our scheduling system. Let me connect you with our staff who can help schedule your appointment."
}

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "voice_bot.log"

# Speech recognition settings
SPEECH_TIMEOUT = "auto"
SPEECH_MODEL = "phone_call"
ENHANCED_RECOGNITION = True

# Transfer settings
TRANSFER_NUMBER = BUSINESS_PHONE  # Default to business phone
