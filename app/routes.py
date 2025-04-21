import os
import requests
import time
import logging
import base64
import tempfile
from flask import Blueprint, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse, Gather
from config.config import (
    BUSINESS_NAME, BUSINESS_LOCATION, BUSINESS_PHONE, DEBUG,
    ENABLE_BACKGROUND_AMBIANCE, BACKGROUND_AMBIANCE_URL, BACKGROUND_AMBIANCE_VOLUME,
    S3_GREETING_URL
)
from app.elevenlabs_service import ElevenLabsService

# Create a blueprint for the routes
routes_bp = Blueprint('routes', __name__)

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
            app = response.app
            if not hasattr(app, 'audio_files'):
                app.audio_files = {}
            app.audio_files[audio_url] = temp_path
            
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
            app = response.app
            if not hasattr(app, 'audio_files'):
                app.audio_files = {}
            app.audio_files[audio_url] = temp_path
            
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

@routes_bp.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve generated audio files."""
    try:
        # Decode the filename
        decoded_filename = base64.urlsafe_b64decode(filename.encode()).decode()
        
        # Get the file path from the app
        app = routes_bp.app
        if hasattr(app, 'audio_files'):
            file_path = app.audio_files.get(f"/audio/{filename}")
            if file_path and os.path.exists(file_path):
                return send_file(file_path, mimetype='audio/mpeg')
        
        return "Audio file not found", 404
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        return "Error serving audio file", 500

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
        elif requested_time:
            # User requested a specific time
            enhanced_say(
                response,
                f"Let me check if we have availability at {requested_time}... Hmm, it looks like that time is already booked. But I do have openings at 10:15 AM or 3:45 PM tomorrow. Would either of those work better for your schedule?",
                "Rachel"
            )
            
            try:
                # Use natural language in the gather
                gather = Gather(input='speech', action='/appointment_alternate', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Just let me know which time you prefer, or if you'd like to look at options for another day.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment confirm with time request: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to discuss appointment options.", voice="Polly.Joanna")
        else:
            # User didn't confirm but didn't specify a time either
            enhanced_say(
                response,
                "No problem at all. Let me check what other times we have available... I see we have openings on Thursday at 10:15 AM or Friday at 3:45 PM. Would either of those days work better for you?",
                "Rachel"
            )
            
            try:
                # Use natural language in the gather
                gather = Gather(input='speech', action='/appointment_alternate', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Or if you have a specific day or time in mind, feel free to let me know and I'll check our availability.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment confirm: {str(e)}")
                # Add a simple fallback
                response.say("Please call back to discuss appointment options.", voice="Polly.Joanna")
        
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
    """Process alternate appointment selection with natural conversation."""
    start_time = time.time()
    logger.info("Appointment alternate endpoint called")
    
    try:
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response with background ambiance
        response = create_response()
        
        # Check for time preferences
        morning_keywords = ["morning", "am", "early", "before noon", "10:15", "10", "ten"]
        afternoon_keywords = ["afternoon", "pm", "later", "after lunch", "3:45", "3", "three"]
        
        # Check for day preferences
        thursday_keywords = ["thursday", "thurs", "tomorrow", "next day"]
        friday_keywords = ["friday", "fri", "end of week", "weekend"]
        
        # Determine if user mentioned morning/afternoon preference
        prefers_morning = any(keyword in speech_result for keyword in morning_keywords)
        prefers_afternoon = any(keyword in speech_result for keyword in afternoon_keywords)
        
        # Determine if user mentioned day preference
        prefers_thursday = any(keyword in speech_result for keyword in thursday_keywords)
        prefers_friday = any(keyword in speech_result for keyword in friday_keywords)
        
        # Handle various combinations of preferences
        if prefers_thursday and prefers_morning:
            enhanced_say(
                response,
                "Perfect! I've scheduled your appointment for Thursday at 10:15 AM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        elif prefers_thursday and prefers_afternoon:
            enhanced_say(
                response,
                "Let me check Thursday afternoon... It looks like we don't have any afternoon appointments on Thursday, but we do have Friday at 3:45 PM available. Would that work for you instead?",
                "Rachel"
            )
            
            try:
                gather = Gather(input='speech', action='/appointment_final', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Or if you prefer, I can check if we have any morning appointments available next week.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment alternate: {str(e)}")
                response.say("Please call back to finalize your appointment.", voice="Polly.Joanna")
        elif prefers_friday and prefers_afternoon:
            enhanced_say(
                response,
                "Perfect! I've scheduled your appointment for Friday at 3:45 PM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        elif prefers_friday and prefers_morning:
            enhanced_say(
                response,
                "Let me check Friday morning... It looks like we don't have any morning appointments on Friday, but we do have Thursday at 10:15 AM available. Would that work for you instead?",
                "Rachel"
            )
            
            try:
                gather = Gather(input='speech', action='/appointment_final', method='POST', language='en-US', speechTimeout='auto')
                gather.say("Or if you prefer, I can check if we have any afternoon appointments available next week.", voice="Polly.Joanna")
                response.append(gather)
            except Exception as e:
                logger.error(f"Error creating gather in appointment alternate: {str(e)}")
                response.say("Please call back to finalize your appointment.", voice="Polly.Joanna")
        elif prefers_thursday:
            enhanced_say(
                response,
                "Great! I've scheduled your appointment for Thursday at 10:15 AM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        elif prefers_friday:
            enhanced_say(
                response,
                "Great! I've scheduled your appointment for Friday at 3:45 PM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        elif prefers_morning:
            enhanced_say(
                response,
                "Perfect! I've scheduled your appointment for Thursday at 10:15 AM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        elif prefers_afternoon:
            enhanced_say(
                response,
                "Perfect! I've scheduled your appointment for Friday at 3:45 PM. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        else:
            enhanced_say(
                response,
                f"I understand finding the right time can be tricky. Let me check what else we have available... We also have next Monday at 11:30 AM or Tuesday at 2:00 PM. Would either of those work better for you? If not, you're welcome to call us directly at {BUSINESS_PHONE} and we can find a time that fits your schedule perfectly.",
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

@routes_bp.route('/appointment_final', methods=['POST'])
def appointment_final():
    """Process final appointment confirmation."""
    start_time = time.time()
    logger.info("Appointment final endpoint called")
    
    try:
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response with background ambiance
        response = create_response()
        
        if any(word in speech_result for word in ["yes", "sure", "okay", "confirm", "good", "works", "perfect", "fine"]):
            enhanced_say(
                response,
                "Wonderful! I've updated your appointment. We look forward to seeing you. If you could arrive about 15 minutes early to complete any paperwork, that would be great. Is there anything else you need to know before your visit?",
                "Rachel"
            )
        else:
            enhanced_say(
                response,
                f"I understand finding the right time can be difficult. Please feel free to call us directly at {BUSINESS_PHONE} during our office hours, and our staff will work with you to find a time that fits your schedule perfectly.",
                "Rachel"
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Appointment final endpoint completed in {elapsed_time:.2f} seconds")
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error in appointment final route after {elapsed_time:.2f} seconds: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the service is running."""
    try:
        # Check if S3 audio is accessible
        s3_status = "S3 audio is accessible" if is_s3_audio_accessible(S3_GREETING_URL) else "S3 audio is NOT accessible"
        
        # Check if ElevenLabs API is working
        elevenlabs_status = "ElevenLabs API is working" if elevenlabs_service.get_voices() else "ElevenLabs API is NOT working"
        
        return f"Enhanced voice bot is operational! {s3_status}. {elevenlabs_status}."
    except Exception as e:
        logger.error(f"Error in test route: {str(e)}")
        return "Enhanced voice bot is operational, but service checks failed."
