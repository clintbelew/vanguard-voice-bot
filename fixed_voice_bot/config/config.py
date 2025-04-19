import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# GoHighLevel configuration
GOHIGHLEVEL_API_KEY = os.environ.get('GHL_API_KEY', "")
GOHIGHLEVEL_LOCATION_ID = os.environ.get('GHL_LOCATION_ID', "")
GOHIGHLEVEL_CALENDAR_ID = os.environ.get('GHL_CALENDAR_ID', "")

# ElevenLabs configuration
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', 'Rachel')  # Default to Rachel voice
PUBLIC_URL_BASE = os.environ.get('PUBLIC_URL_BASE', '')  # Base URL for serving audio files

# Voice bot messages
GREETING_MESSAGE = "Thank you for calling Vanguard Chiropractic. This is Joanna, how can I help you today?"

# Voice configuration
VOICE_NAME = "Polly.Joanna"  # Fallback voice if ElevenLabs is not available

# Error messages
ERROR_MESSAGES = {
    "general": "We're sorry, an application error has occurred. Please try again later or call back during business hours to speak with our staff.",
    "input_not_understood": "I'm sorry, I didn't understand that. Could you please repeat?",
    "appointment_error": "I'm having trouble with our scheduling system. Let me connect you with our staff who can help schedule your appointment.",
    "transfer_error": "I'm having trouble transferring your call. Please call back during business hours to speak with our staff."
}

# Business hours
BUSINESS_HOURS = {
    "monday": {"open": "9:00", "close": "18:00"},
    "tuesday": {"open": "9:00", "close": "18:00"},
    "wednesday": {"open": "9:00", "close": "18:00"},
    "thursday": {"open": "9:00", "close": "18:00"},
    "friday": {"open": "9:00", "close": "17:00"},
    "saturday": {"open": "10:00", "close": "14:00"},
    "sunday": {"open": None, "close": None}  # Closed on Sunday
}

# Available appointment slots (for demo purposes)
AVAILABLE_SLOTS = [
    {"day": "tomorrow", "time": "9:00 AM"},
    {"day": "tomorrow", "time": "10:30 AM"},
    {"day": "tomorrow", "time": "2:00 PM"},
    {"day": "friday", "time": "11:00 AM"},
    {"day": "friday", "time": "3:30 PM"}
]
