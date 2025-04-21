import os
import logging

# Debug mode
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ElevenLabs API key
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', 'your_elevenlabs_api_key_here')

# ElevenLabs voice ID - Rachel voice
ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')

# Background ambiance settings
ENABLE_BACKGROUND_AMBIANCE = True
BACKGROUND_AMBIANCE_URL = "https://storage.googleapis.com/voice-bot-assets/office_ambiance_low.mp3"
BACKGROUND_AMBIANCE_VOLUME = 0.15  # 15% volume

# Deployment base URL
BASE_URL = os.environ.get('BASE_URL', 'https://vanguard-voice-bot.onrender.com')

# Business information from environment variables
BUSINESS_NAME = os.environ.get('BUSINESS_NAME', 'Vanguard Chiropractic')
BUSINESS_LOCATION = os.environ.get('BUSINESS_LOCATION', '123 Main Street, Suite 456, in downtown Austin')
BUSINESS_PHONE = os.environ.get('BUSINESS_PHONE', '(830) 429-4111')

# S3 greeting audio URL
S3_GREETING_URL = "https://chirodesk-audio.s3.us-east-2.amazonaws.com/ElevenLabs_2025-04-20T04_45_30_Rachel_pre_sp100_s50_sb75_se0_b_m2.mp3"

# Configure logging
logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)
