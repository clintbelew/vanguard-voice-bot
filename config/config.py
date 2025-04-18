import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# GoHighLevel Configuration
GOHIGHLEVEL_API_KEY = os.getenv('GOHIGHLEVEL_API_KEY')
GOHIGHLEVEL_LOCATION_ID = os.getenv('GOHIGHLEVEL_LOCATION_ID')
GOHIGHLEVEL_API_URL = 'https://api.gohighlevel.com/v1/'

# Application Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
PORT = int(os.getenv('PORT', 5000))

# Business Information
BUSINESS_NAME = os.getenv('BUSINESS_NAME', 'Vanguard Chiropractic')
BUSINESS_HOURS = {
    'Monday': '9:00 AM - 6:00 PM',
    'Tuesday': '9:00 AM - 6:00 PM',
    'Wednesday': '9:00 AM - 6:00 PM',
    'Thursday': '9:00 AM - 6:00 PM',
    'Friday': '9:00 AM - 5:00 PM',
    'Saturday': '10:00 AM - 2:00 PM',
    'Sunday': 'Closed'
}
BUSINESS_LOCATION = os.getenv('BUSINESS_LOCATION', '123 Main Street, Anytown, CA 12345')
BUSINESS_PHONE = os.getenv('BUSINESS_PHONE', TWILIO_PHONE_NUMBER)

# FAQ Information
FAQ = {
    'hours': 'Our hours of operation are: Monday through Thursday from 9:00 AM to 6:00 PM, Friday from 9:00 AM to 5:00 PM, Saturday from 10:00 AM to 2:00 PM, and we are closed on Sunday.',
    'services': 'We offer a variety of chiropractic services including spinal adjustments, massage therapy, physical rehabilitation, and nutritional counseling.',
    'insurance': 'We accept most major insurance plans including Blue Cross, Aetna, Cigna, and Medicare. Please call our office for specific details about your insurance coverage.',
    'location': f'We are located at {BUSINESS_LOCATION}. Free parking is available in our lot.',
    'appointment': 'To schedule an appointment, I can help you book one now, or I can send you a text message with a booking link.',
    'emergency': 'If you are experiencing a medical emergency, please hang up and dial 911 immediately.'
}

# Voice Bot Configuration
VOICE_NAME = 'Polly.Joanna'  # Twilio voice option
VOICE_LANGUAGE = 'en-US'
GREETING_MESSAGE = f"Thank you for calling {BUSINESS_NAME}. How can I help you today?"
