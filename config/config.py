import os

# ElevenLabs API key
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', 'your_elevenlabs_api_key_here')

# Deployment base URL
BASE_URL = os.environ.get('BASE_URL', 'https://vanguard-voice-bot.onrender.com')

# Business information from environment variables
BUSINESS_LOCATION = os.environ.get('BUSINESS_LOCATION', '123 Main Street, Suite 456, in downtown Austin')
BUSINESS_NAME = os.environ.get('BUSINESS_NAME', 'Vanguard Chiropractic')
BUSINESS_PHONE = os.environ.get('BUSINESS_PHONE', '(830) 429-4111')

# Debug mode
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
