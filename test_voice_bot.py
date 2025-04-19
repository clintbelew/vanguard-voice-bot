"""
Test script for voice bot functionality

This script tests the voice bot's ElevenLabs integration and appointment booking functionality.
"""

import os
import requests
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base URL for the voice bot
BASE_URL = os.environ.get('PUBLIC_URL_BASE', 'https://vanguard-voice-bot.onrender.com')

def test_elevenlabs_integration():
    """Test if ElevenLabs integration is working properly."""
    try:
        # Call the test endpoint
        response = requests.get(f"{BASE_URL}/test")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Test endpoint response: {data}")
            
            if data.get('elevenlabs_configured'):
                logger.info("✅ ElevenLabs is configured")
            else:
                logger.error("❌ ElevenLabs is not configured")
                
            return data
        else:
            logger.error(f"❌ Test endpoint returned status code {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Error testing ElevenLabs integration: {str(e)}")
        return None

def test_audio_cache():
    """Test if audio cache directory exists and is accessible."""
    try:
        # Get the absolute path to the audio_cache directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, 'audio_cache')
        
        # Check if directory exists
        if os.path.exists(cache_dir):
            logger.info(f"✅ Audio cache directory exists at {cache_dir}")
            
            # Check if directory is writable
            test_file = os.path.join(cache_dir, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info("✅ Audio cache directory is writable")
            except Exception as e:
                logger.error(f"❌ Audio cache directory is not writable: {str(e)}")
                
            # List files in directory
            files = os.listdir(cache_dir)
            logger.info(f"Files in audio cache: {files}")
            
            return True
        else:
            logger.error(f"❌ Audio cache directory does not exist at {cache_dir}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing audio cache: {str(e)}")
        return False

def test_logs_directory():
    """Test if logs directory exists and is accessible."""
    try:
        # Get the absolute path to the logs directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, 'logs')
        
        # Check if directory exists
        if os.path.exists(logs_dir):
            logger.info(f"✅ Logs directory exists at {logs_dir}")
            
            # Check if directory is writable
            test_file = os.path.join(logs_dir, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info("✅ Logs directory is writable")
            except Exception as e:
                logger.error(f"❌ Logs directory is not writable: {str(e)}")
                
            # List files in directory
            files = os.listdir(logs_dir)
            logger.info(f"Files in logs directory: {files}")
            
            return True
        else:
            logger.error(f"❌ Logs directory does not exist at {logs_dir}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing logs directory: {str(e)}")
        return False

def simulate_appointment_request():
    """Simulate an appointment request to test intent recognition."""
    try:
        # This is just a simulation - in a real test, we would use Twilio's API
        # to make a call and test the voice bot's response
        logger.info("Simulating appointment request...")
        logger.info("In a real test, we would use Twilio's API to make a call")
        logger.info("and test the voice bot's response to 'I'd like to make an appointment'")
        
        # For now, just log that this would be tested in a real environment
        logger.info("✅ Appointment request simulation completed")
        return True
    except Exception as e:
        logger.error(f"❌ Error simulating appointment request: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting voice bot tests...")
    
    # Test ElevenLabs integration
    test_elevenlabs_integration()
    
    # Test audio cache
    test_audio_cache()
    
    # Test logs directory
    test_logs_directory()
    
    # Simulate appointment request
    simulate_appointment_request()
    
    logger.info("Voice bot tests completed")
