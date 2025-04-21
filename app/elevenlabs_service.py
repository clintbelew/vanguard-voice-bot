import requests
import os
import logging
import time
from config.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, DEBUG

# Configure logging
logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Service for generating audio using ElevenLabs API."""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key=None):
        """Initialize the ElevenLabs service with API key."""
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.headers = {
            "Accept": "audio/mpeg",
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_voices(self):
        """Get available voices from ElevenLabs."""
        try:
            url = f"{self.BASE_URL}/voices"
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error getting voices from ElevenLabs: {str(e)}")
            return None
    
    def generate_audio(self, text, voice_id=None, stability=0.5, similarity_boost=0.75, style=0.0, use_speaker_boost=True):
        """Generate audio from text using ElevenLabs API."""
        try:
            start_time = time.time()
            logger.info(f"Generating audio for text: {text[:50]}...")
            
            # Use provided voice_id or default from config
            voice_id = voice_id or ELEVENLABS_VOICE_ID
            
            url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            
            if response.status_code == 200:
                elapsed_time = time.time() - start_time
                logger.info(f"Audio generated successfully in {elapsed_time:.2f} seconds")
                return response.content
            else:
                logger.error(f"Error generating audio: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error generating audio with ElevenLabs: {str(e)}")
            return None
    
    def save_audio_to_file(self, text, output_path, voice_id=None):
        """Generate audio and save to file."""
        try:
            audio_content = self.generate_audio(text, voice_id)
            if audio_content:
                with open(output_path, 'wb') as f:
                    f.write(audio_content)
                logger.info(f"Audio saved to {output_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving audio to file: {str(e)}")
            return False
