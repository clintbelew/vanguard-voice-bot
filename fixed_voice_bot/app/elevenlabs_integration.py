import os
import requests
import hashlib
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("elevenlabs.log"),
        logging.StreamHandler()
    ]
)

class ElevenLabsAPI:
    """Class to handle interactions with the ElevenLabs API."""
    
    def __init__(self):
        self.api_key = os.environ.get('ELEVENLABS_API_KEY', '')
        self.voice_id = os.environ.get('ELEVENLABS_VOICE_ID', 'Rachel') # Default to Rachel voice if not specified
        self.base_url = "https://api.elevenlabs.io/v1"
        self.cache_dir = Path("audio_cache")
        self.public_url_base = os.environ.get('PUBLIC_URL_BASE', '')
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Log initialization
        if self.is_configured():
            logging.info("ElevenLabs API initialized with voice: %s", self.voice_id)
        else:
            logging.warning("ElevenLabs API not fully configured. Missing API key or voice ID.")
    
    def is_configured(self):
        """Check if the API is properly configured."""
        return bool(self.api_key) and bool(self.public_url_base)
    
    def get_cache_filename(self, text):
        """Generate a unique filename for caching based on the text content."""
        # Create a hash of the text to use as the filename
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"{text_hash}.mp3"
    
    def get_cache_path(self, text):
        """Get the full path to the cached audio file."""
        filename = self.get_cache_filename(text)
        return self.cache_dir / filename
    
    def get_public_url(self, text):
        """Get the public URL for the cached audio file."""
        if not self.public_url_base:
            logging.error("PUBLIC_URL_BASE environment variable not set")
            return None
            
        filename = self.get_cache_filename(text)
        return f"{self.public_url_base}/audio/{filename}"
    
    def text_to_speech(self, text):
        """Convert text to speech using ElevenLabs API."""
        if not self.is_configured():
            logging.error("ElevenLabs API not configured. Cannot generate speech.")
            return None
        
        # Check if we already have this audio cached
        cache_path = self.get_cache_path(text)
        if cache_path.exists():
            logging.info("Using cached audio for: %s", text[:30])
            return self.get_public_url(text)
        
        # If not cached, call the API
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            logging.info("Generating speech for: %s", text[:30])
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save the audio file
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                
                logging.info("Successfully generated and cached audio")
                return self.get_public_url(text)
            else:
                logging.error("Failed to generate speech. Status code: %d, Response: %s", 
                             response.status_code, response.text)
                return None
                
        except Exception as e:
            logging.error("Error generating speech: %s", str(e))
            return None
    
    def get_available_voices(self):
        """Get a list of available voices from ElevenLabs."""
        if not self.api_key:
            logging.error("ElevenLabs API key not configured")
            return []
            
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                return voices
            else:
                logging.error("Failed to get voices. Status code: %d", response.status_code)
                return []
                
        except Exception as e:
            logging.error("Error getting voices: %s", str(e))
            return []

# Create a singleton instance
elevenlabs_api = ElevenLabsAPI()
