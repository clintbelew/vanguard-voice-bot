"""
ElevenLabs Integration Module for Voice Bot

This module handles the integration with ElevenLabs API for generating
lifelike voice responses. It includes caching mechanisms to reduce API calls
and improve response times.
"""

import os
import requests
import json
import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Default to "Rachel" voice
PUBLIC_URL_BASE = os.environ.get('PUBLIC_URL_BASE', 'https://vanguard-voice-bot.onrender.com')

# Create cache directory with absolute path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, 'audio_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
logger.info(f"Audio cache directory created at: {CACHE_DIR}")

def is_configured():
    """Check if ElevenLabs API is configured properly."""
    if not ELEVENLABS_API_KEY:
        logger.warning("ElevenLabs API key is not set")
        return False
    
    if not PUBLIC_URL_BASE:
        logger.warning("PUBLIC_URL_BASE is not set")
        return False
    
    logger.info("ElevenLabs API is configured with key and PUBLIC_URL_BASE")
    return True

def generate_audio_hash(text, voice_id=ELEVENLABS_VOICE_ID):
    """Generate a unique hash for the text and voice combination."""
    hash_input = f"{text}_{voice_id}"
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()

def get_cached_audio_url(text, voice_id=ELEVENLABS_VOICE_ID):
    """
    Check if audio for this text and voice already exists in cache.
    Returns the public URL if found, None otherwise.
    """
    if not is_configured():
        logger.warning("ElevenLabs not configured, cannot get cached audio URL")
        return None
    
    audio_hash = generate_audio_hash(text, voice_id)
    cache_file = os.path.join(CACHE_DIR, f"{audio_hash}.mp3")
    
    if os.path.exists(cache_file):
        logger.info(f"Using cached audio for: {text[:30]}...")
        # Return the public URL for this cached file
        encoded_filename = quote(f"{audio_hash}.mp3")
        return f"{PUBLIC_URL_BASE}/audio/{encoded_filename}"
    
    logger.info(f"No cached audio found for: {text[:30]}...")
    return None

def generate_audio(text, voice_id=ELEVENLABS_VOICE_ID):
    """
    Generate audio using ElevenLabs API and cache it.
    Returns the public URL for the generated audio.
    """
    if not is_configured():
        logger.warning("ElevenLabs not configured, cannot generate audio")
        return None
    
    # First check if we already have this audio cached
    cached_url = get_cached_audio_url(text, voice_id)
    if cached_url:
        return cached_url
    
    # Generate a unique hash for this text and voice
    audio_hash = generate_audio_hash(text, voice_id)
    cache_file = os.path.join(CACHE_DIR, f"{audio_hash}.mp3")
    
    try:
        logger.info(f"Generating audio via ElevenLabs API for: {text[:30]}...")
        
        # API call to ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        end_time = time.time()
        
        logger.info(f"ElevenLabs API call took {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            # Save the audio file to cache
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Audio generated and cached successfully at {cache_file}")
            
            # Return the public URL for this cached file
            encoded_filename = quote(f"{audio_hash}.mp3")
            return f"{PUBLIC_URL_BASE}/audio/{encoded_filename}"
        else:
            logger.error(f"Error generating audio: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Exception in generate_audio: {str(e)}")
        return None

def get_audio_url(text, voice_id=ELEVENLABS_VOICE_ID):
    """
    Main function to get audio URL for a text.
    Checks cache first, then generates if needed.
    """
    # Try to get from cache first
    cached_url = get_cached_audio_url(text, voice_id)
    if cached_url:
        return cached_url
    
    # Generate new audio if not in cache
    return generate_audio(text, voice_id)
