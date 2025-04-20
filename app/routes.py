import os
from flask import Blueprint, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
from config.config import ELEVENLABS_API_KEY

# Create a blueprint for the routes
routes_bp = Blueprint('routes', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct S3 URL for greeting audio
S3_GREETING_URL = "https://chirodesk-audio.s3.us-east-2.amazonaws.com/ElevenLabs_2025-04-20T04_45_30_Rachel_pre_sp100_s50_sb75_se0_b_m2.mp3"

# Helper function to create a TwiML response without background ambiance
def create_response_without_ambiance():
    response = VoiceResponse()
    return response

# Enhanced say function that plays audio directly from S3
def enhanced_say(response, text, voice="Rachel"):
    # Always use S3 URL for the greeting, regardless of exact text matching
    if "thank you for calling vanguard chiropractic" in text.lower():
        logger.info(f"Using S3 URL for greeting: {S3_GREETING_URL}")
        response.play(S3_GREETING_URL)
    else:
        # For other text, we'll use Twilio's Say verb as a fallback
        response.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
    return response

# Enhanced gather function that plays audio directly from S3
def enhanced_gather(response, text, options, voice="Rachel"):
    gather = Gather(input='speech dtmf', action='/intent', method='POST', language='en-US', speechTimeout='auto', timeout=3)
    
    # Always use S3 URL for the greeting, regardless of exact text matching
    if "thank you for calling vanguard chiropractic" in text.lower():
        logger.info(f"Using S3 URL for greeting in gather: {S3_GREETING_URL}")
        gather.play(S3_GREETING_URL)
    else:
        # For other text, we'll use Twilio's Say verb as a fallback
        gather.say(text, voice="Polly.Joanna" if voice == "Rachel" else "Polly.Miguel")
    
    response.append(gather)
    # Add a redirect in case the user doesn't input anything
    response.redirect('/voice')
    return response

@routes_bp.route('/voice', methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and return TwiML."""
    try:
        logger.info("Voice endpoint called")
        
        # Create TwiML response without background ambiance
        response = create_response_without_ambiance()
        
        # Add the greeting using S3 URL
        enhanced_gather(
            response,
            "Hello, thank you for calling Vanguard Chiropractic. How may I help you today?",
            ["appointment", "hours", "location", "español", "spanish"],
            "Rachel"
        )
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in voice route: {str(e)}")
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/intent', methods=['POST'])
def intent():
    """Process speech input and determine intent."""
    try:
        logger.info("Intent endpoint called")
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response without background ambiance
        response = create_response_without_ambiance()
        
        # Check for Spanish language request
        if "español" in speech_result or "spanish" in speech_result:
            enhanced_gather(
                response,
                "Hola, gracias por llamar a Vanguard Chiropractic. ¿Cómo puedo ayudarte hoy?",
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
            
            gather = Gather(input='speech', action='/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
            gather.say("Please say yes to confirm, or no to find another time.", voice="Polly.Joanna")
            response.append(gather)
        
        # Handle hours intent
        elif any(word in speech_result for word in ["hours", "open", "close", "time"]):
            enhanced_say(
                response,
                "Our hours are Monday through Friday, 9 AM to 6 PM, and Saturday from 10 AM to 2 PM. We are closed on Sundays.",
                "Rachel"
            )
            
            gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
            gather.say("Is there anything else I can help you with?", voice="Polly.Joanna")
            response.append(gather)
        
        # Handle location intent
        elif any(word in speech_result for word in ["location", "address", "where", "directions"]):
            enhanced_say(
                response,
                "We're located at 123 Main Street, Suite 456, in downtown Austin. We're right across from the public library.",
                "Rachel"
            )
            
            gather = Gather(input='speech', action='/intent', method='POST', language='en-US', speechTimeout='auto')
            gather.say("Is there anything else I can help you with?", voice="Polly.Joanna")
            response.append(gather)
        
        # Default response for unrecognized intent
        else:
            enhanced_gather(
                response,
                "I'm sorry, I didn't quite catch that. Are you calling about an appointment, our hours, or our location?",
                ["appointment", "hours", "location", "español", "spanish"],
                "Rachel"
            )
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in intent route: {str(e)}")
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/appointment_confirm', methods=['POST'])
def appointment_confirm():
    """Process appointment confirmation."""
    try:
        logger.info("Appointment confirm endpoint called")
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response without background ambiance
        response = create_response_without_ambiance()
        
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
            
            gather = Gather(input='speech', action='/appointment_alternate', method='POST', language='en-US', speechTimeout='auto')
            gather.say("Please say Thursday or Friday to select a day, or say neither to find more options.", voice="Polly.Joanna")
            response.append(gather)
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in appointment confirm route: {str(e)}")
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/appointment_alternate', methods=['POST'])
def appointment_alternate():
    """Process alternate appointment selection."""
    try:
        logger.info("Appointment alternate endpoint called")
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Speech result: {speech_result}")
        
        # Create TwiML response without background ambiance
        response = create_response_without_ambiance()
        
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
                "I understand finding the right time can be difficult. Please call back during our office hours to speak with a staff member who can help find a time that works for you.",
                "Rachel"
            )
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in appointment alternate route: {str(e)}")
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        return Response(str(response), mimetype='text/xml')

@routes_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the service is running."""
    return "Voice bot is operational!"

# Remove the /audio route since we're using S3 directly
