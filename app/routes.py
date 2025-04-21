import os
import requests
import time
import logging
from flask import Blueprint, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from config.config import BUSINESS_NAME, BUSINESS_LOCATION, BUSINESS_PHONE, DEBUG

# Create a blueprint for the routes
routes_bp = Blueprint('routes', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)

# Direct S3 URL for greeting audio
S3_GREETING_URL = "https://chirodesk-audio.s3.us-east-2.amazonaws.com/ElevenLabs_2025-04-20T04_45_30_Rachel_pre_sp100_s50_sb75_se0_b_m2.mp3"

# Timeout for S3 audio requests (in seconds)
S3_REQUEST_TIMEOUT = 5

# Helper function to create a TwiML response
def create_response():
    response = VoiceResponse()
    return response

# Function to check if S3 audio URL is accessible
def is_s3_audio_accessible(url, timeout=S3_REQUEST_TIMEOUT):
    """Check if the S3 audio URL is accessible."""
    try:
        logger.info(f"Checking S3 audio accessibility: {url}")
        start_time = time.time()
        response = requests.head(url, timeout=timeout)
        elapsed_time = time.time() - start_time
        logger.info(f"S3 audio check completed in {elapsed_time:.2f} seconds with status code: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking S3 audio accessibility: {str(e)}")
        return False

# Enhanced say function that plays audio directly from S3 with fallback
def enhanced_say(response, text, voice="Rachel"):
    try:
        # Always use S3 URL for the greeting, regardless of exact text matching
        if "thank you for calling" in text.lower() and BUSINESS_NAME.lower() in text.lower():
            logger.info(f"Attempting to use S3 URL for greeting: {S3_GREETING_URL}")
            
            # Check if S3 audio is accessible before attempting to use it
            if is_s3_audio_accessible(S3_GREETING_URL):
                logger.info(f"S3 audio is accessible, using S3 URL for greeting")
                response.play(S3_GREETING_URL)
            else:
                # Fallback to Twilio's Say verb if S3 audio is not accessible
                logger.warning(f"S3 audio is not accessible, falling back to Twilio's Say verb")
                response.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
        else:
            # For other text, we'll use Twilio's Say verb
            response.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Error in enhanced_say: {str(e)}")
        # Fallback to Twilio's Say verb
        response.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
    
    return response

# Enhanced gather function that plays audio directly from S3 with fallback
def enhanced_gather(response, text, options, voice="Rachel"):
    try:
        gather = Gather(input='speech dtmf', action='/intent', method='POST', language='en-US', speechTimeout='auto', timeout=3)
        
        # Always use S3 URL for the greeting, regardless of exact text matching
        if "thank you for calling" in text.lower() and BUSINESS_NAME.lower() in text.lower():
            logger.info(f"Attempting to use S3 URL for greeting in gather: {S3_GREETING_URL}")
            
            # Check if S3 audio is accessible before attempting to use it
            if is_s3_audio_accessible(S3_GREETING_URL):
                logger.info(f"S3 audio is accessible, using S3 URL for greeting in gather")
                gather.play(S3_GREETING_URL)
            else:
                # Fallback to Twilio's Say verb if S3 audio is not accessible
                logger.warning(f"S3 audio is not accessible, falling back to Twilio's Say verb in gather")
                gather.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
        else:
            # For other text, we'll use Twilio's Say verb
            gather.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
        
        response.append(gather)
        # Add a redirect in case the user doesn't input anything
        response.redirect('/voice')
    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Error in enhanced_gather: {str(e)}")
        # Create a simple gather as fallback
        gather = Gather(input='speech dtmf', action='/intent', method='POST', language='en-US', speechTimeout='auto', timeout=3)
        gather.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
        response.append(gather)
        response.redirect('/voice')
    
    return response

@routes_bp.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and return TwiML."""
    start_time = time.time()
    logger.info("Voice endpoint called")
    
    try:
        # Create TwiML response
        response = create_response()
        
        # Add the greeting using S3 URL with fallback
        greeting_text = f"Hello, thank you for calling {BUSINESS_NAME}. How may I help you today?"
        enhanced_gather(
            response,
            greeting_text,
            ["appointment", "hours", "location", "español", "spanish"],
            "Rachel"
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Voice endpoint completed in {elapsed_time:.2f} seconds")
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error in voice route after {elapsed_time:.2f} seconds: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/intent', methods=['POST'])
def intent():
    """Process speech input and determine intent."""
    start_time = time.time()
    logger.info("Intent endpoint called")
    
    try:
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response
        response = create_response()
        
        # Check for Spanish language request
        if "español" in speech_result or "spanish" in speech_result:
            enhanced_gather(
                response,
                f"Hola, gracias por llamar a {BUSINESS_NAME}. ¿Cómo puedo ayudarte hoy?",
                ["cita", "horas", "ubicación", "english"],
                "Antonio"
            )
        
        # Handle appointment intent
        elif any(word in speech_result for word in ["appointment", "schedule", "book", "visit"]):
            enhanced_say(
                response,
                "I'd be happy to help you schedule an appointment. Our next available slot is tomorrow at 2:30 PM. Would that work for you?",
                "Rachel"
            )
            
            try:
                gather = Gather(input='speech', action='/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Please say yes to confirm, or no to find another time.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment intent: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to confirm your appointment.", voice="Polly.Joanna")
        
        # Handle hours intent
        elif any(word in speech_result for word in ["hours", "open", "close", "time"]):
            enhanced_say(
                response,
                "Our hours are Monday through Friday, 9 AM to 6 PM, and Saturday from 10 AM to 2 PM. We are closed on Sundays.",
                "Rachel"
            )
            
            try:
                gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Is there anything else I can help you with?", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in hours intent: {str(e)}")
                # Add a simple fallback
                response.say("Thank you for calling.", voice="Polly.Joanna")
        
        # Handle location intent
        elif any(word in speech_result for word in ["location", "address", "where", "directions"]):
            enhanced_say(
                response,
                f"We're located at {BUSINESS_LOCATION}. We're right across from the public library.",
                "Rachel"
            )
            
            try:
                gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Is there anything else I can help you with?", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in location intent: {str(e)}")
                # Add a simple fallback
                response.say("Thank you for calling.", voice="Polly.Joanna")
        
        # Default response for unrecognized intent
        else:
            enhanced_gather(
                response,
                "I'm sorry, I didn't quite catch that. Are you calling about an appointment, our hours, or our location?",
                ["appointment", "hours", "location", "español", "spanish"],
                "Rachel"
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Intent endpoint completed in {elapsed_time:.2f} seconds")
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error in intent route after {elapsed_time:.2f} seconds: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/appointment_confirm', methods=['POST'])
def appointment_confirm():
    """Process appointment confirmation."""
    start_time = time.time()
    logger.info("Appointment confirm endpoint called")
    
    try:
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response
        response = create_response()
        
        if any(word in speech_result for word in ["yes", "sure", "okay", "confirm", "good"]):
            enhanced_say(
                response,
                "Great! I've scheduled your appointment for tomorrow at 2:30 PM. We look forward to seeing you. Please arrive 15 minutes early to complete any paperwork.",
                "Rachel"
            )
        else:
            enhanced_say(
                response,
                "No problem. We also have availability on Thursday at 10:15 AM or Friday at 3:45 PM. Would either of those times work better for you?",
                "Rachel"
            )
            
            try:
                gather = Gather(input='speech', action='/appointment_alternate', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Please say Thursday or Friday to select a day, or say neither to find more options.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment confirm: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to confirm your preferred time.", voice="Polly.Joanna")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Appointment confirm endpoint completed in {elapsed_time:.2f} seconds")
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error in appointment confirm route after {elapsed_time:.2f} seconds: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/appointment_alternate', methods=['POST'])
def appointment_alternate():
    """Process alternate appointment selection."""
    start_time = time.time()
    logger.info("Appointment alternate endpoint called")
    
    try:
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response
        response = create_response()
        
        if "thursday" in speech_result:
            enhanced_say(
                response,
                "Perfect! I've scheduled your appointment for Thursday at 10:15 AM. We look forward to seeing you. Please arrive 15 minutes early to complete any paperwork.",
                "Rachel"
            )
        elif "friday" in speech_result:
            enhanced_say(
                response,
                "Perfect! I've scheduled your appointment for Friday at 3:45 PM. We look forward to seeing you. Please arrive 15 minutes early to complete any paperwork.",
                "Rachel"
            )
        else:
            enhanced_say(
                response,
                f"I understand finding the right time can be difficult. Please call back during our office hours to speak with a staff member who can help find a time that works for you. You can reach us at {BUSINESS_PHONE}.",
                "Rachel"
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Appointment alternate endpoint completed in {elapsed_time:.2f} seconds")
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error in appointment alternate route after {elapsed_time:.2f} seconds: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the service is running."""
    try:
        # Also check if S3 audio is accessible
        s3_status = "S3 audio is accessible" if is_s3_audio_accessible(S3_GREETING_URL) else "S3 audio is NOT accessible"
        return f"Voice bot is operational! {s3_status}"
    except Exception as e:
        logger.error(f"Error in test route: {str(e)}")
        return "Voice bot is operational, but S3 audio check failed."
