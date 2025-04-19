"""
Configuration settings for the Voice Bot application.

This module contains all the configuration settings and constants used
throughout the application.
"""

import os

# Environment variables with defaults
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# ElevenLabs configuration
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '')
ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Default to "Rachel" voice
ELEVENLABS_SPANISH_VOICE_ID = os.environ.get('ELEVENLABS_SPANISH_VOICE_ID', 'ErXwobaYiN019PkySvjV')  # Default to "Antonio" voice

# GoHighLevel configuration
GHL_API_KEY = os.environ.get('GHL_API_KEY', '')
GHL_LOCATION_ID = os.environ.get('GHL_LOCATION_ID', '')
GHL_CALENDAR_ID = os.environ.get('GHL_CALENDAR_ID', '')

# Application configuration
PUBLIC_URL_BASE = os.environ.get('PUBLIC_URL_BASE', 'https://vanguard-voice-bot.onrender.com')

# Voice bot messages
GREETING_MESSAGE = "Hello! Thank you for calling Vanguard Chiropractic. How can I help you today?"
GREETING_MESSAGE_SPANISH = "¡Hola! Gracias por llamar a Vanguard Chiropractic. ¿Cómo puedo ayudarle hoy?"

# Error messages
ERROR_MESSAGES = {
    'general': "I'm sorry, but I'm having trouble processing your request. Please try again or call back later.",
    'input_not_understood': "I'm sorry, but I didn't understand that. Could you please repeat?",
    'appointment_error': "I'm sorry, but I'm having trouble with the appointment system. Let me connect you with someone who can help.",
    'transfer_error': "I'm sorry, but I'm having trouble transferring your call. Please call back in a few minutes."
}

# Spanish error messages
ERROR_MESSAGES_SPANISH = {
    'general': "Lo siento, pero estoy teniendo problemas para procesar su solicitud. Por favor, inténtelo de nuevo o llame más tarde.",
    'input_not_understood': "Lo siento, pero no entendí eso. ¿Podría repetirlo, por favor?",
    'appointment_error': "Lo siento, pero estoy teniendo problemas con el sistema de citas. Permítame conectarlo con alguien que pueda ayudarle.",
    'transfer_error': "Lo siento, pero estoy teniendo problemas para transferir su llamada. Por favor, llame de nuevo en unos minutos."
}

# Appointment settings
APPOINTMENT_DURATION_MINUTES = 30
APPOINTMENT_BUFFER_MINUTES = 15
