from flask import Blueprint, request, Response, send_file
import os
import requests
import time
import logging
import base64
import tempfile
from twilio.twiml.voice_response import VoiceResponse, Gather
from config.config import (
    BUSINESS_NAME, BUSINESS_LOCATION, BUSINESS_PHONE, DEBUG,
    ENABLE_BACKGROUND_AMBIANCE, BACKGROUND_AMBIANCE_URL, BACKGROUND_AMBIANCE_VOLUME,
    S3_GREETING_URL
)
from app.elevenlabs_service import ElevenLabsService

# Configure logging
logging.basicConfig(level=logging.INFO if DEBUG else logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize ElevenLabs service
elevenlabs_service = ElevenLabsService()

# Timeout for S3 audio requests (in seconds)
S3_REQUEST_TIMEOUT = 5

# Helper function to create a TwiML response with background ambiance
def create_response():
    response = VoiceResponse()
    
    # Add background ambiance if enabled
    if ENABLE_BACKGROUND_AMBIANCE:
        # Play background ambiance at low volume (15%)
        response.play(BACKGROUND_AMBIANCE_URL, loop=0, volume=BACKGROUND_AMBIANCE_VOLUME)
    
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

# Enhanced say function that uses ElevenLabs for natural voice
def enhanced_say(response, text, voice="Rachel"):
    try:
        # For greeting, use the S3 audio file if available
        if "thank you for calling" in text.lower() and BUSINESS_NAME.lower() in text.lower():
            logger.info(f"Attempting to use S3 URL for greeting: {S3_GREETING_URL}")
            
            # Check if S3 audio is accessible before attempting to use it
            if is_s3_audio_accessible(S3_GREETING_URL):
                logger.info(f"S3 audio is accessible, using S3 URL for greeting")
                response.play(S3_GREETING_URL)
                return response
        
        # For all other responses, use ElevenLabs to generate natural voice
        logger.info(f"Generating audio with ElevenLabs for: {text[:50]}...")
        
        # Generate audio using ElevenLabs
        audio_content = elevenlabs_service.generate_audio(text)
        
        if audio_content:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_content)
                temp_path = temp_file.name
            
            # Create a unique URL for this audio file
            audio_url = f"/audio/{base64.urlsafe_b64encode(os.path.basename(temp_path).encode()).decode()}"
            
            # Store the file path for later retrieval
            from flask import current_app
            if not hasattr(current_app, 'audio_files'):
                current_app.audio_files = {}
            current_app.audio_files[audio_url] = temp_path
            
            # Play the audio in the response
            response.play(audio_url)
        else:
            # Fallback to Twilio's Say verb if ElevenLabs fails
            logger.warning(f"ElevenLabs audio generation failed, falling back to Twilio's Say verb")
            response.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Error in enhanced_say: {str(e)}")
        # Fallback to Twilio's Say verb
        response.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
    
    return response

# Enhanced gather function that uses ElevenLabs for natural voice
def enhanced_gather(response, text, options, voice="Rachel"):
    try:
        gather = Gather(input='speech dtmf', action='/intent', method='POST', language='en-US', speechTimeout='auto', timeout=3)
        
        # For greeting, use the S3 audio file if available
        if "thank you for calling" in text.lower() and BUSINESS_NAME.lower() in text.lower():
            logger.info(f"Attempting to use S3 URL for greeting in gather: {S3_GREETING_URL}")
            
            # Check if S3 audio is accessible before attempting to use it
            if is_s3_audio_accessible(S3_GREETING_URL):
                logger.info(f"S3 audio is accessible, using S3 URL for greeting in gather")
                gather.play(S3_GREETING_URL)
                response.append(gather)
                # Add a redirect in case the user doesn't input anything
                response.redirect('/voice')
                return response
        
        # For all other responses, use ElevenLabs to generate natural voice
        logger.info(f"Generating audio with ElevenLabs for gather: {text[:50]}...")
        
        # Generate audio using ElevenLabs
        audio_content = elevenlabs_service.generate_audio(text)
        
        if audio_content:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_content)
                temp_path = temp_file.name
            
            # Create a unique URL for this audio file
            audio_url = f"/audio/{base64.urlsafe_b64encode(os.path.basename(temp_path).encode()).decode()}"
            
            # Store the file path for later retrieval
            from flask import current_app
            if not hasattr(current_app, 'audio_files'):
                current_app.audio_files = {}
            current_app.audio_files[audio_url] = temp_path
            
            # Play the audio in the gather
            gather.play(audio_url)
        else:
            # Fallback to Twilio's Say verb if ElevenLabs fails
            logger.warning(f"ElevenLabs audio generation failed, falling back to Twilio's Say verb in gather")
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

# Import routes_bp from __init__.py to avoid circular imports
from app import routes_bp

@routes_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve generated audio files."""
    try:
        # Decode the filename
        decoded_filename = base64.urlsafe_b64decode(filename.encode()).decode()
        
        # Get the file path from the app
        from flask import current_app
        if hasattr(current_app, 'audio_files'):
            file_path = current_app.audio_files.get(f"/audio/{filename}")
            if file_path and os.path.exists(file_path):
                return send_file(file_path, mimetype='audio/mpeg')
        
        return "Audio file not found", 404
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        return "Error serving audio file", 500

@routes_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the application is running."""
    try:
        # Check if S3 audio is accessible
        s3_status = "accessible" if is_s3_audio_accessible(S3_GREETING_URL) else "inaccessible"
        
        # Check if ElevenLabs API is accessible
        elevenlabs_status = "accessible" if elevenlabs_service.test_connection() else "inaccessible"
        
        return f"Voice bot is operational! S3 audio is {s3_status}, ElevenLabs API is {elevenlabs_status}"
    except Exception as e:
        logger.error(f"Error in test route: {str(e)}")
        return f"Voice bot is operational, but encountered an error: {str(e)}"

@routes_bp.route('/', methods=['GET'])
def index():
    """Root endpoint to verify the application is running."""
    return f"Twilio Voice Bot for {BUSINESS_NAME} is running!"

@routes_bp.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and return TwiML."""
    start_time = time.time()
    logger.info("Voice endpoint called")
    
    try:
        # Create TwiML response with background ambiance
        response = create_response()
        
        # Add the greeting using natural voice
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
        
        # Create TwiML response with background ambiance
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
            # Use more natural, conversational language
            enhanced_say(
                response,
                f"I'd be happy to help you schedule an appointment. Let me check what we have available... It looks like we have an opening tomorrow at 2:30 PM. Would that work for your schedule?",
                "Rachel"
            )
            
            try:
                # Use more natural language in the gather
                gather = Gather(input='speech', action='/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
                gather.say("If that time doesn't work, just let me know and I can check some other options for you.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment intent: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to confirm your appointment.", voice="Polly.Joanna")
        
        # Handle hours intent
        elif any(word in speech_result for word in ["hours", "open", "close", "time"]):
            enhanced_say(
                response,
                f"We're open Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 2 PM. We're closed on Sundays to give our staff a well-deserved break.",
                "Rachel"
            )
            
            try:
                # Use more natural language in the gather
                gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Is there anything else I can help you with today?", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in hours intent: {str(e)}")
                # Add a simple fallback
                response.say("Thank you for calling.", voice="Polly.Joanna")
        
        # Handle location intent
        elif any(word in speech_result for word in ["location", "address", "where", "directions"]):
            enhanced_say(
                response,
                f"We're located at {BUSINESS_LOCATION}. We're right across from the public library, in the building with the blue awning. There's plenty of parking available in the front and back of the building.",
                "Rachel"
            )
            
            try:
                # Use more natural language in the gather
                gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Is there anything else you'd like to know?", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in location intent: {str(e)}")
                # Add a simple fallback
                response.say("Thank you for calling.", voice="Polly.Joanna")
        
        # Default response for unrecognized intent
        else:
            enhanced_gather(
                response,
                "I'm sorry, I didn't quite catch that. Are you calling about scheduling an appointment, our hours, or our location?",
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
    """Process appointment confirmation with natural conversation."""
    start_time = time.time()
    logger.info("Appointment confirm endpoint called")
    
    try:
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response with background ambiance
        response = create_response()
        
        # Check for specific time requests
        time_keywords = {
            "9": "9 AM", "nine": "9 AM", "morning": "morning",
            "10": "10 AM", "ten": "10 AM", 
            "11": "11 AM", "eleven": "11 AM",
            "12": "12 PM", "noon": "12 PM", "twelve": "12 PM",
            "1": "1 PM", "one": "1 PM",
            "2": "2 PM", "two": "2 PM",
            "3": "3 PM", "three": "3 PM",
            "4": "4 PM", "four": "4 PM",
            "5": "5 PM", "five": "5 PM", "evening": "evening",
            "afternoon": "afternoon"
        }
        
        # Check if user mentioned a specific time
        requested_time = None
        for keyword, time_value in time_keywords.items():
            if keyword in speech_result:
                requested_time = time_value
                break
        
        # Handle confirmation or specific time request
        if any(word in speech_result for word in ["yes", "sure", "okay", "confirm", "good", "works", "perfect", "fine"]):
            # User confirmed the suggested time
            enhanced_say(
                response,
                "Great! I've scheduled your appointment for tomorrow at 2:30 PM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be perfect. Is there anything else you need to know before your visit?",
                "Rachel"
            )
            
            try:
                # Use more natural language in the gather
                gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
                gather.say("If you need to reschedule, please call us back at least 24 hours in advance.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment confirmation: {str(e)}")
                # Add a simple fallback
                response.say("Thank you for scheduling with us.", voice="Polly.Joanna")
        
        # Handle specific time request
        elif requested_time:
            # User requested a specific time
            enhanced_say(
                response,
                f"Hmm, it looks like {requested_time} is already booked — but I do have 10:15 AM or 1:45 PM available. Would either of those work for you?",
                "Rachel"
            )
            
            try:
                # Use more natural language in the gather
                gather = Gather(input='speech', action='/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Or if you prefer a different day, just let me know.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in specific time request: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to schedule your appointment.", voice="Polly.Joanna")
        
        # Handle negative response
        elif any(word in speech_result for word in ["no", "not", "don't", "cant", "cannot", "different", "another"]):
            # User declined the suggested time
            enhanced_say(
                response,
                "No problem at all. Let me check what other times we have available... I can offer you 10:15 AM or 4:45 PM tomorrow. Would either of those times work better for you?",
                "Rachel"
            )
            
            try:
                # Use more natural language in the gather
                gather = Gather(input='speech', action='/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Or if you'd prefer a different day entirely, I'd be happy to check our availability.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in negative response: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to schedule your appointment.", voice="Polly.Joanna")
        
        # Default response for unrecognized input
        else:
            enhanced_gather(
                response,
                "I'm sorry, I didn't quite understand. Would you like to schedule an appointment for tomorrow at 2:30 PM? Or would you prefer a different time?",
                ["yes", "no", "different time", "another day"],
                "Rachel"
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Appointment confirm endpoint completed in {elapsed_time:.2f} seconds")
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error in appointment_confirm route after {elapsed_time:.2f} seconds: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')
