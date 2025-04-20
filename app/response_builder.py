"""
Response Builder Module for Voice Bot

This module provides enhanced response building functionality for the voice bot,
including ElevenLabs voice integration, background ambiance, and multilingual support.
"""

import os
import logging
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.elevenlabs_integration import get_audio_url, is_configured, validate_audio_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OFFICE_AMBIANCE_URL = "https://storage.googleapis.com/vanguard-voice-assets/office_ambiance_low.mp3"

def validate_url(url):
    """
    Validate and fix any URL to ensure it's properly formatted.
    This is a general URL validation function that can be used for any URL.
    """
    if not url:
        return url
    
    # Fix the specific malformed URL pattern with duplicate domains
    if "onrender.coms://" in url:
        fixed_url = url.replace("https://vanguard-voice-bot.onrender.coms://", "https://")
        logger.info(f"Response builder fixed malformed URL: {url} -> {fixed_url}")
        return fixed_url
    
    return url

def sanitize_twiml(twiml_str):
    """
    Final safety check that sanitizes the entire TwiML response string.
    This catches any malformed URLs that might have slipped through other validation layers.
    """
    if not twiml_str:
        return twiml_str
    
    # Fix the specific malformed URL pattern with duplicate domains
    if "onrender.coms://" in twiml_str:
        fixed_twiml = twiml_str.replace("https://vanguard-voice-bot.onrender.coms://", "https://")
        logger.info("Sanitized TwiML response with malformed URLs")
        return fixed_twiml
    
    return twiml_str

def enhanced_say(response, text, voice="Polly.Joanna", language="en-US", enhanced=True):
    """
    Enhanced version of TwiML Say that uses ElevenLabs when available.
    
    Args:
        response (VoiceResponse): The TwiML response object
        text (str): The text to speak
        voice (str): The voice to use (default: Polly.Joanna)
        language (str): The language to use (default: en-US)
        enhanced (bool): Whether to use ElevenLabs if available (default: True)
    """
    try:
        # Check if ElevenLabs is configured and enhancement is requested
        if enhanced and is_configured():
            logger.info(f"Using ElevenLabs for: {text[:30]}... (language: {language})")
            
            # Generate audio URL using ElevenLabs with language support
            audio_url = get_audio_url(text, language)
            
            if audio_url:
                # Validate the URL to ensure it's properly formatted
                audio_url = validate_url(audio_url)
                
                # Use Play verb with the validated audio URL
                response.play(audio_url)
                logger.info(f"Using validated ElevenLabs audio URL: {audio_url}")
                return
            else:
                logger.warning(f"Failed to get ElevenLabs audio URL for language {language}, falling back to Polly")
        
        # Fallback to standard Polly TTS
        # Use appropriate Polly voice based on language
        if language.startswith("es"):
            polly_voice = "Polly.Lupe" if voice == "Polly.Joanna" else voice
            logger.info(f"Using standard Polly TTS (Spanish) for: {text[:30]}...")
            response.say(text, voice=polly_voice, language="es-MX")
        else:
            logger.info(f"Using standard Polly TTS (English) for: {text[:30]}...")
            response.say(text, voice=voice, language=language)
    except Exception as e:
        logger.error(f"Error in enhanced_say: {str(e)}")
        # Ultimate fallback - use standard Polly TTS
        response.say(text, voice=voice, language=language)

def enhanced_gather(response, text, action, input_types='speech dtmf', 
                   timeout=3, speech_timeout='auto', speech_model='phone_call',
                   hints=None, language="en-US", voice="Polly.Joanna", enhanced=True):
    """
    Enhanced version of TwiML Gather that uses ElevenLabs for the prompt when available.
    
    Args:
        response (VoiceResponse): The TwiML response object
        text (str): The text to speak as the prompt
        action (str): The URL to request when the gather is complete
        input_types (str): The input types to accept (default: 'speech dtmf')
        timeout (int): The timeout in seconds (default: 3)
        speech_timeout (str): The speech timeout (default: 'auto')
        speech_model (str): The speech recognition model to use (default: 'phone_call')
        hints (str): Speech recognition hints (default: None)
        language (str): The language to use (default: en-US)
        voice (str): The voice to use (default: Polly.Joanna)
        enhanced (bool): Whether to use ElevenLabs if available (default: True)
    """
    try:
        # Create the Gather verb with language support
        gather = Gather(
            input=input_types,
            timeout=timeout,
            speech_timeout=speech_timeout,
            action=action,
            language=language  # Set the speech recognition language
        )
        
        # Add speech recognition model if specified
        if speech_model:
            gather.speech_model = speech_model
        
        # Add hints if specified
        if hints:
            gather.hints = hints
        
        # Check if ElevenLabs is configured and enhancement is requested
        if enhanced and is_configured():
            logger.info(f"Using ElevenLabs for gather prompt: {text[:30]}... (language: {language})")
            
            # Generate audio URL using ElevenLabs with language support
            audio_url = get_audio_url(text, language)
            
            if audio_url:
                # Validate the URL to ensure it's properly formatted
                audio_url = validate_url(audio_url)
                
                # Use Play verb with the validated audio URL
                gather.play(audio_url)
                logger.info(f"Using validated ElevenLabs audio URL for gather: {audio_url}")
                response.append(gather)
                return
            else:
                logger.warning(f"Failed to get ElevenLabs audio URL for gather in language {language}, falling back to Polly")
        
        # Fallback to standard Polly TTS with language support
        if language.startswith("es"):
            polly_voice = "Polly.Lupe" if voice == "Polly.Joanna" else voice
            logger.info(f"Using standard Polly TTS (Spanish) for gather prompt: {text[:30]}...")
            gather.say(text, voice=polly_voice, language="es-MX")
        else:
            logger.info(f"Using standard Polly TTS (English) for gather prompt: {text[:30]}...")
            gather.say(text, voice=voice, language=language)
        
        response.append(gather)
    except Exception as e:
        logger.error(f"Error in enhanced_gather: {str(e)}")
        # Ultimate fallback - use standard gather with Polly TTS
        gather = Gather(
            input=input_types,
            timeout=timeout,
            speech_timeout=speech_timeout,
            action=action
        )
        gather.say(text, voice=voice, language=language)
        response.append(gather)

def add_background_ambiance(response, volume=0.1):
    """
    Add subtle background office ambiance to the call.
    
    Args:
        response (VoiceResponse): The TwiML response object
        volume (float): The volume level from 0.0 to 1.0 (default: 0.1)
    """
    try:
        logger.info(f"Adding background ambiance at volume {volume}")
        
        # Ensure volume is between 0 and 1
        volume = max(0.0, min(1.0, volume))
        
        # Validate the ambiance URL
        validated_url = validate_url(OFFICE_AMBIANCE_URL)
        
        # Add the Play verb with the validated ambiance audio
        response.play(validated_url, loop=0, volume=volume)
    except Exception as e:
        logger.error(f"Error adding background ambiance: {str(e)}")
        # If there's an error, just continue without ambiance

def detect_language(speech_result):
    """
    Detect if the speech is in Spanish or English.
    
    Args:
        speech_result (str): The speech text to analyze
        
    Returns:
        str: Language code ("es-MX" for Spanish, "en-US" for English)
    """
    # Common Spanish words and phrases that might indicate Spanish speech
    spanish_indicators = [
        'hola', 'gracias', 'por favor', 'buenos días', 'buenas tardes', 'buenas noches',
        'cita', 'necesito', 'quiero', 'ayuda', 'hablar', 'español', 'habla', 'puedo',
        'doctor', 'médico', 'dolor', 'espalda', 'cuello', 'cabeza', 'pierna', 'brazo',
        'mañana', 'tarde', 'noche', 'día', 'hora', 'semana', 'mes', 'año',
        'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'
    ]
    
    # Convert to lowercase for case-insensitive matching
    speech_lower = speech_result.lower()
    
    # Check if any Spanish indicators are in the speech
    for indicator in spanish_indicators:
        if indicator in speech_lower:
            logger.info(f"Detected Spanish language: found '{indicator}' in '{speech_lower}'")
            return "es-MX"
    
    # If no Spanish indicators are found, default to English
    logger.info(f"Defaulting to English language for: '{speech_lower}'")
    return "en-US"
