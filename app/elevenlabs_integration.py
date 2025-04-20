"""
ElevenLabs Integration Module for Voice Bot

This module handles the integration with ElevenLabs API for generating
lifelike voice responses. It includes caching mechanisms to reduce API calls
and improve response times. Now with multilingual support for English and Spanish.
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
ELEVENLABS_SPANISH_VOICE_ID = os.environ.get('ELEVENLABS_SPANISH_VOICE_ID', 'ErXwobaYiN019PkySvjV')  # Default to "Antonio" voice
# Hardcoded base URL to ensure consistency
HARDCODED_BASE_URL = 'https://vanguard-voice-bot.onrender.com'
PUBLIC_URL_BASE = os.environ.get('PUBLIC_URL_BASE', HARDCODED_BASE_URL)

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
    
    logger.info("ElevenLabs API is configured with key")
    return True

def get_voice_id_for_language(language="en-US"):
    """Get the appropriate voice ID based on language."""
    if language.startswith("es"):
        logger.info(f"Using Spanish voice ID: {ELEVENLABS_SPANISH_VOICE_ID}")
        return ELEVENLABS_SPANISH_VOICE_ID
    else:
        logger.info(f"Using English voice ID: {ELEVENLABS_VOICE_ID}")
        return ELEVENLABS_VOICE_ID

def generate_audio_hash(text, voice_id, language="en-US"):
    """Generate a unique hash for the text, voice, and language combination."""
    hash_input = f"{text}_{voice_id}_{language}"
    return hashlib.md5(hash_input.encode('utf-8')).hexdigest()

def get_audio_url_from_filename(filename):
    """
    Generate a clean, direct URL for an audio file using a hardcoded base URL.
    This ensures consistent URL formatting regardless of environment variables.
    """
    # Use hardcoded base URL instead of environment variable
    base_url = HARDCODED_BASE_URL
    
    # Create a clean URL by directly concatenating the base URL and path
    clean_url = f"{base_url}/audio/{filename}"
    
    logger.info(f"Created hardcoded audio URL: {clean_url}")
    return clean_url

def validate_audio_url(url):
    """
    Validate and fix audio URLs to ensure they don't have the malformed pattern.
    """
    if not url:
        return url
    
    # Check for the specific malformed pattern
    if "onrender.coms://" in url:
        # Fix the malformed URL by replacing the problematic pattern
        fixed_url = url.replace("https://vanguard-voice-bot.onrender.coms://", "https://")
        logger.info(f"Fixed malformed URL: {url} -> {fixed_url}")
        return fixed_url
    
    return url

def get_cached_audio_url(text, language="en-US"):
    """
    Check if audio for this text and language already exists in cache.
    Returns the public URL if found, None otherwise.
    """
    if not is_configured():
        logger.warning("ElevenLabs not configured, cannot get cached audio URL")
        return None
    
    voice_id = get_voice_id_for_language(language)
    audio_hash = generate_audio_hash(text, voice_id, language)
    cache_file = os.path.join(CACHE_DIR, f"{audio_hash}.mp3")
    
    if os.path.exists(cache_file):
        logger.info(f"Using cached audio for: {text[:30]}... (language: {language})")
        # Return the public URL for this cached file using the direct URL construction
        encoded_filename = quote(f"{audio_hash}.mp3")
        url = get_audio_url_from_filename(encoded_filename)
        # Validate the URL before returning
        return validate_audio_url(url)
    
    logger.info(f"No cached audio found for: {text[:30]}... (language: {language})")
    return None

def generate_audio(text, language="en-US"):
    """
    Generate audio using ElevenLabs API and cache it.
    Returns the public URL for the generated audio.
    """
    if not is_configured():
        logger.warning("ElevenLabs not configured, cannot generate audio")
        return None
    
    # Get the appropriate voice ID for the language
    voice_id = get_voice_id_for_language(language)
    
    # First check if we already have this audio cached
    cached_url = get_cached_audio_url(text, language)
    if cached_url:
        return cached_url
    
    # Generate a unique hash for this text, voice, and language
    audio_hash = generate_audio_hash(text, voice_id, language)
    cache_file = os.path.join(CACHE_DIR, f"{audio_hash}.mp3")
    
    try:
        logger.info(f"Generating audio via ElevenLabs API for: {text[:30]}... (language: {language})")
        
        # API call to ElevenLabs
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        # Use multilingual model for Spanish
        model_id = "eleven_multilingual_v2" if language.startswith("es") else "eleven_monolingual_v1"
        
        data = {
            "text": text,
            "model_id": model_id,
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
            
            # Return the public URL for this cached file using the direct URL construction
            encoded_filename = quote(f"{audio_hash}.mp3")
            url = get_audio_url_from_filename(encoded_filename)
            # Validate the URL before returning
            return validate_audio_url(url)
        else:
            logger.error(f"Error generating audio: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Exception in generate_audio: {str(e)}")
        return None

def get_audio_url(text, language="en-US"):
    """
    Main function to get audio URL for a text.
    Checks cache first, then generates if needed.
    Always validates the URL before returning.
    """
    # Try to get from cache first
    cached_url = get_cached_audio_url(text, language)
    if cached_url:
        return cached_url
    
    # Generate new audio if not in cache
    url = generate_audio(text, language)
    # Validate the URL before returning
    return validate_audio_url(url)
