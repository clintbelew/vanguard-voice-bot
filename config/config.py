import os

# ElevenLabs API key
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', 'your_elevenlabs_api_key_here')

# Background ambiance URL
BACKGROUND_AMBIANCE_URL = "https://vanguard-voice-bot.onrender.com/static/background_ambiance.mp3"

# Deployment base URL
BASE_URL = os.environ.get('BASE_URL', 'https://vanguard-voice-bot.onrender.com')
