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
import re
from pathlib import Path
from urllib.parse import quote, urlparse, urljoin

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

def normalize_url(url):
    """
    Enhanced URL normalization to ensure it doesn't have duplicate schemes or domains.
    Handles various malformed URL patterns including the specific production issue.
    """
    if not url:
        logger.warning("Empty URL passed to normalize_url")
        return url
    
    logger.info(f"Normalizing URL: {url}")
    
    # Pattern 1: Handle the specific production issue pattern
    # Example: https://vanguard-voice-bot.onrender.coms://vanguard-voice-bot.onrender.com/audio/...
    pattern1 = r'(https?://[^/]+)s://(.*)'
    match1 = re.match(pattern1, url)
    if match1:
        domain = match1.group(1)
        path = match1.group(2)
        # If path contains another domain, extract just the path portion
        if '/' in path:
            path = '/' + path.split('/', 1)[1]
        else:
            path = '/'
        
        fixed_url = f"{domain}{path}"
        logger.info(f"Fixed malformed URL (pattern 1): {url} -> {fixed_url}")
        return fixed_url
    
    # Pattern 2: Handle URLs with domain in the path
    # Example: https://domain.com/https://domain.com/path
    pattern2 = r'(https?://[^/]+)/(https?://[^/]+)(.*)'
    match2 = re.match(pattern2, url)
    if match2:
        domain = match2.group(1)
        path = match2.group(3)
        fixed_url = f"{domain}{path}"
        logger.info(f"Fixed malformed URL (pattern 2): {url} -> {fixed_url}")
        return fixed_url
    
    # Pattern 3: Use urlparse for other cases
    try:
        parsed = urlparse(url)
        
        # Check for malformed netloc or path
        if 's://' in parsed.netloc or '://' in parsed.path:
            # Extract the base domain
            if 's://' in parsed.netloc:
                netloc = parsed.netloc.split('s://')[0]
            else:
                netloc = parsed.netloc
                
            # Clean up the path
            path = parsed.path
            if '://' in path:
                path = '/' + path.split('://')[-1].split('/', 1)[-1]
                
            # Reconstruct the URL
            fixed_url = f"{parsed.scheme}://{netloc}{path}"
            logger.info(f"Fixed malformed URL (pattern 3): {url} -> {fixed_url}")
            return fixed_url
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {str(e)}")
    
    # If we get here, no patterns matched or there was an error
    # As a last resort, try to construct a clean URL from PUBLIC_URL_BASE and the filename
    try:
        # Extract the filename from the URL
        filename = url.split('/')[-1]
        if filename and '.' in filename:  # Ensure it looks like a filename
            clean_url = f"{PUBLIC_URL_BASE}/audio/{filename}"
            logger.info(f"Reconstructed URL as fallback: {url} -> {clean_url}")
            return clean_url
    except Exception as e:
        logger.error(f"Error reconstructing URL {url}: {str(e)}")
    
    # If all else fails, return the original URL
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
        # Construct a clean URL directly
        encoded_filename = quote(f"{audio_hash}.mp3")
        clean_url = f"{PUBLIC_URL_BASE}/audio/{encoded_filename}"
        logger.info(f"Generated clean cached audio URL: {clean_url}")
        return clean_url
    
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
            
            # Construct a clean URL directly
            encoded_filename = quote(f"{audio_hash}.mp3")
            clean_url = f"{PUBLIC_URL_BASE}/audio/{encoded_filename}"
            logger.info(f"Generated clean new audio URL: {clean_url}")
            return clean_url
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
    """
    # Try to get from cache first
    cached_url = get_cached_audio_url(text, language)
    if cached_url:
        return cached_url
    
    # Generate new audio if not in cache
    return generate_audio(text, language)
