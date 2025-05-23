import os
import logging
import requests
import tempfile
import io
import base64
import json
import sys
from flask import Flask, request, jsonify, send_file, Response, session
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse, Gather
import pytz
from datetime import datetime
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout for Railway
    ]
)
logger = logging.getLogger('vanguard')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Initialize OpenAI client using simplified legacy method
openai.api_key = os.getenv('OPENAI_API_KEY')

# Environment variables
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')
GHL_API_KEY = os.getenv('GHL_API_KEY')
GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID')
GHL_CALENDAR_ID = os.getenv('GHL_CALENDAR_ID')
BUSINESS_NAME = os.getenv('BUSINESS_NAME', 'Vanguard Chiropractic')
BUSINESS_LOCATION = os.getenv('BUSINESS_LOCATION', '123 Main Street, Suite 456, in downtown Austin')
BUSINESS_PHONE = os.getenv('BUSINESS_PHONE', '(830) 429-4111')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'o4-mini')

# Store audio files temporarily
audio_files = {}

# Store conversation context
conversation_contexts = {}

# Simple test endpoint that always returns a valid TwiML response
@app.route('/twilio-test', methods=['GET', 'POST'])
def twilio_test():
    """Simple test endpoint that always returns a valid TwiML response."""
    print("Twilio test endpoint called")
    logger.info("Twilio test endpoint called")
    
    # Create a simple TwiML response
    response = VoiceResponse()
    response.say("This is a test response from the Vanguard Voice Bot.")
    
    # Return the response as XML
    return Response(str(response), mimetype='text/xml')

# Helper function to create a TwiML response
def create_response():
    response = VoiceResponse()
    return response

# OpenAI integration for generating responses
def generate_openai_response(prompt, conversation_history=None, call_sid=None):
    """Generate a response using OpenAI"""
    try:
        logger.info(f"Generating OpenAI response for prompt: {prompt[:50]}...")
        
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not configured")
            return "I'm sorry, but I'm having trouble accessing my knowledge base right now. Please try again later."
        
        # Initialize conversation history if not provided
        if conversation_history is None:
            conversation_history = []
        
        # Add system message if it's not already there
        if not any(msg.get("role") == "system" for msg in conversation_history):
            system_message = {
                "role": "system", 
                "content": f"""You are a helpful voice assistant for {BUSINESS_NAME}. 
                Your job is to help callers schedule appointments, provide information about business hours, 
                and answer questions about the location. Be conversational, friendly, and concise since this is a phone call.
                
                Business information:
                - Name: {BUSINESS_NAME}
                - Location: {BUSINESS_LOCATION}
                - Phone: {BUSINESS_PHONE}
                - Hours: Monday-Friday 9 AM to 6 PM, Saturday 10 AM to 2 PM, closed on Sundays
                
                When scheduling appointments, collect the caller's name, phone number, email, and preferred appointment time.
                Once you have all this information, you'll help book the appointment.
                """
            }
            conversation_history.insert(0, system_message)
        
        # Add the user's prompt to the conversation history
        conversation_history.append({"role": "user", "content": prompt})
        
        # Call OpenAI API using legacy method
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=conversation_history,
            temperature=0.7,
            max_tokens=150
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {response_text[:100]}...")
        
        # Add the assistant's response to the conversation history
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Store the updated conversation history if call_sid is provided
        if call_sid:
            conversation_contexts[call_sid] = conversation_history
        
        return response_text
        
    except Exception as e:
        logger.error(f"OpenAI error: {str(e)}")
        return "I'm sorry, but I'm having trouble accessing my knowledge base right now. Please try again later."

# Function to extract appointment information from conversation
def extract_appointment_info(conversation_history):
    """Extract appointment information from conversation history"""
    try:
        # Prepare a prompt to extract the information
        extraction_prompt = """
        Based on the conversation, extract the following information for booking an appointment:
        - name: The caller's full name
        - phone: The caller's phone number
        - email: The caller's email address
        - selectedSlot: The preferred appointment time in ISO format (YYYY-MM-DDTHH:MM:SS)
        
        Format your response as a valid JSON object with these fields. If any information is missing, set the value to null.
        """
        
        # Add the extraction prompt to a copy of the conversation history
        extraction_history = conversation_history.copy()
        extraction_history.append({"role": "user", "content": extraction_prompt})
        
        # Call OpenAI API for extraction using legacy method
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=extraction_history,
            temperature=0,
            max_tokens=200
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            appointment_info = json.loads(response_text)
            logger.info(f"Extracted appointment info: {appointment_info}")
            return appointment_info
        except json.JSONDecodeError:
            logger.error(f"Failed to parse appointment info JSON: {response_text}")
            return None
        
    except Exception as e:
        logger.error(f"Error extracting appointment info: {str(e)}")
        return None

# ElevenLabs voice generation function
def generate_elevenlabs_audio(text):
    """Generate audio using ElevenLabs API"""
    try:
        logger.info(f"Generating audio with ElevenLabs for: {text[:50]}...")
        
        if not ELEVENLABS_API_KEY:
            logger.error("ELEVENLABS_API_KEY not configured")
            return None
            
        if not ELEVENLABS_VOICE_ID:
            logger.error("ELEVENLABS_VOICE_ID not configured")
            return None
        
        # Call ElevenLabs API
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("Voice successfully generated")
            return response.content
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Voice generation error: {str(e)}")
        return None

# Enhanced say function that uses ElevenLabs for natural voice
def enhanced_say(response, text):
    try:
        # Generate audio using ElevenLabs
        audio_content = generate_elevenlabs_audio(text)
        
        if audio_content:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_content)
                temp_path = temp_file.name
            
            # Create a unique URL for this audio file
            audio_url = f"/audio/{base64.urlsafe_b64encode(os.path.basename(temp_path).encode()).decode()}"
            
            # Store the file path for later retrieval
            audio_files[audio_url] = temp_path
            
            # Play the audio in the response
            response.play(f"{request.url_root.rstrip('/')}{audio_url}")
        else:
            # Log error if ElevenLabs fails
            logger.error("Failed to generate audio with ElevenLabs")
            response.say(text, voice="Polly.Joanna")
    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Error in enhanced_say: {str(e)}")
        # Fallback to Twilio's Say verb
        response.say(text, voice="Polly.Joanna")
    
    return response

# Enhanced gather function that uses ElevenLabs for natural voice
def enhanced_gather(response, text, action='/twilio/intent'):
    try:
        gather = Gather(input='speech dtmf', action=action, method='POST', language='en-US', speechTimeout='auto', timeout=3)
        
        # Generate audio using ElevenLabs
        audio_content = generate_elevenlabs_audio(text)
        
        if audio_content:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(audio_content)
                temp_path = temp_file.name
            
            # Create a unique URL for this audio file
            audio_url = f"/audio/{base64.urlsafe_b64encode(os.path.basename(temp_path).encode()).decode()}"
            
            # Store the file path for later retrieval
            audio_files[audio_url] = temp_path
            
            # Play the audio in the gather
            gather.play(f"{request.url_root.rstrip('/')}{audio_url}")
        else:
            # Log error if ElevenLabs fails
            logger.error("Failed to generate audio with ElevenLabs for gather")
            gather.say(text, voice="Polly.Joanna")
        
        response.append(gather)
        # Add a redirect in case the user doesn't input anything
        response.redirect('/twilio/voice')
    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"Error in enhanced_gather: {str(e)}")
        # Create a simple gather as fallback
        gather = Gather(input='speech dtmf', action=action, method='POST', language='en-US', speechTimeout='auto', timeout=3)
        gather.say(text, voice="Polly.Joanna")
        response.append(gather)
        response.redirect('/twilio/voice')
    
    return response

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    print("Health check endpoint called")
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy", "service": "Vanguard Voice Bot Backend"})

# Voice generation endpoint with OpenAI integration
@app.route('/voice', methods=['POST'])
def generate_voice():
    """
    Generate voice audio from text using OpenAI for content and ElevenLabs for speech
    
    Expects JSON with:
    {
        "text": "Text input from user",
        "conversation_id": "Optional ID to maintain conversation context"
    }
    
    Returns audio file (MP3)
    """
    try:
        print("Voice generation endpoint called")
        logger.info("Voice generation endpoint called")
        
        data = request.get_json()
        
        if not data:
            logger.error("Invalid request: missing request body")
            return jsonify({"error": "Missing request body"}), 400
            
        # Get text input and conversation ID
        text_input = data.get('text', '')
        conversation_id = data.get('conversation_id', None)
        
        logger.info(f"Voice generation request received: {text_input[:50]}...")
        
        # Get conversation history if conversation_id is provided
        conversation_history = conversation_contexts.get(conversation_id, [])
        
        # Generate response using OpenAI
        response_text = generate_openai_response(text_input, conversation_history, conversation_id)
        
        # Check if we have all the appointment information
        if "appointment" in text_input.lower() or "schedule" in text_input.lower() or "book" in text_input.lower():
            # Try to extract appointment information
            appointment_info = extract_appointment_info(conversation_contexts.get(conversation_id, []))
            
            # If we have all the required information, book the appointment
            if appointment_info and all(appointment_info.get(field) for field in ['name', 'phone', 'email', 'selectedSlot']):
                logger.info("All appointment information collected, booking appointment")
                
                # Call the book endpoint
                try:
                    book_response = book_appointment_internal(appointment_info)
                    
                    # If booking was successful, add confirmation to the response
                    if book_response.get('success'):
                        scheduled_time = book_response.get('scheduled_time', appointment_info['selectedSlot'])
                        response_text += f" Great news! I've booked your appointment for {scheduled_time}. You'll receive a confirmation shortly."
                    else:
                        error_details = book_response.get('details', 'Unknown error')
                        response_text += f" I'm sorry, but there was an issue booking your appointment. {error_details}"
                except Exception as e:
                    logger.error(f"Error booking appointment: {str(e)}")
                    response_text += " I'm sorry, but there was an issue booking your appointment. Please try again later."
        
        # Generate audio using ElevenLabs
        audio_content = generate_elevenlabs_audio(response_text)
        
        if audio_content:
            # Create a BytesIO object to store the audio
            audio_data = io.BytesIO(audio_content)
            audio_data.seek(0)
            
            # Store the conversation context for future reference
            if conversation_id:
                conversation_contexts[conversation_id] = conversation_contexts.get(conversation_id, [])
                conversation_contexts[conversation_id].append({"role": "assistant", "content": response_text})
            
            return send_file(
                audio_data,
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name="voice.mp3"
            )
        else:
            return jsonify({"error": "Failed to generate voice"}), 500
            
    except Exception as e:
        logger.error(f"Voice generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Internal function to book appointments
def book_appointment_internal(data):
    """Internal function to book appointments using the same logic as the /book endpoint"""
    try:
        logger.info(f"Internal booking request received: {data}")
        
        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'selectedSlot']
        for field in required_fields:
            if field not in data:
                logger.error(f"Invalid request: missing '{field}' field")
                return {"error": f"Missing '{field}' field"}
        
        logger.info(f"Booking request received for {data['name']}")
        
        if not all([GHL_API_KEY, GHL_LOCATION_ID, GHL_CALENDAR_ID]):
            logger.error("GoHighLevel API configuration incomplete")
            return {"error": "GoHighLevel API configuration incomplete"}
        
        # Parse and localize the appointment time
        central = pytz.timezone("America/Chicago")
        try:
            appointment_time = central.localize(datetime.fromisoformat(data['selectedSlot']))
            appointment_time_str = appointment_time.isoformat()
        except Exception as e:
            logger.error(f"Invalid datetime format: {str(e)}")
            return {"error": f"Invalid datetime format: {str(e)}"}
        
        # Add selectedTimezone if not provided (required by GoHighLevel)
        if 'selectedTimezone' not in data:
            data['selectedTimezone'] = "America/Chicago"
        
        # First, create or update contact in GoHighLevel
        contact_url = "https://rest.gohighlevel.com/v1/contacts/"
        contact_headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json"
        }
        contact_payload = {
            "email": data['email'],
            "phone": data['phone'],
            "firstName": data['name'].split(' ')[0],
            "lastName": " ".join(data['name'].split(' ')[1:]) if len(data['name'].split(' ')) > 1 else "",
            "locationId": GHL_LOCATION_ID
        }
        
        logger.info(f"Creating/updating contact with payload: {contact_payload}")
        contact_response = requests.post(contact_url, json=contact_payload, headers=contact_headers)
        
        if contact_response.status_code not in [200, 201]:
            logger.error(f"GoHighLevel contact creation error: {contact_response.status_code} - {contact_response.text}")
            return {
                "error": "Failed to create contact",
                "details": contact_response.text
            }
        
        contact_data = contact_response.json()
        contact_id = contact_data.get('id') or contact_data.get('contact', {}).get('id')
        
        if not contact_id:
            logger.error("Failed to get contact ID from GoHighLevel response")
            return {"error": "Failed to get contact ID"}
        
        # Now book the appointment
        calendar_url = f"https://rest.gohighlevel.com/v1/appointments/"
        calendar_payload = {
            "calendarId": GHL_CALENDAR_ID,
            "contactId": contact_id,
            "startTime": appointment_time_str,
            "title": f"Appointment with {data['name']}",
            "description": "Appointment booked via Vanguard Voice Bot",
            "locationId": GHL_LOCATION_ID,
            "timezone": "America/Chicago",
            "selectedTimezone": "America/Chicago",
            "selectedSlot": data['selectedSlot']
        }
        
        logger.info(f"Booking appointment with payload: {calendar_payload}")
        calendar_response = requests.post(calendar_url, json=calendar_payload, headers=contact_headers)
        
        if calendar_response.status_code in [200, 201]:
            logger.info(f"Appointment successfully booked for {data['name']}")
            return {
                "success": True,
                "message": "Appointment booked successfully",
                "scheduled_time": appointment_time_str,
                "appointment": calendar_response.json()
            }
        else:
            logger.error(f"GoHighLevel appointment booking error: {calendar_response.status_code} - {calendar_response.text}")
            return {
                "error": "Failed to book appointment",
                "details": calendar_response.text
            }
            
    except Exception as e:
        logger.error(f"Appointment booking error: {str(e)}")
        return {"error": str(e)}

# Appointment booking endpoint (from VAPPI)
@app.route('/book', methods=['POST'])
def book_appointment():
    """
    Book an appointment in GoHighLevel
    
    Expects JSON with:
    {
        "name": "Client Name",
        "phone": "1234567890",
        "email": "client@example.com",
        "selectedSlot": "2025-04-25T14:00:00"
    }
    
    Returns success or error JSON
    """
    try:
        print("Book appointment endpoint called")
        logger.info("Book appointment endpoint called")
        
        data = request.get_json()
        result = book_appointment_internal(data)
        
        # Check if there's an error
        if 'error' in result:
            return jsonify(result), 400 if 'Invalid' in result.get('error', '') else 500
        
        # Return success response
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Appointment booking error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Serve audio files
@app.route('/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    """Serve generated audio files."""
    try:
        print(f"Serving audio file: {filename}")
        logger.info(f"Serving audio file: {filename}")
        
        # Get the file path from the audio_files dictionary
        file_path = audio_files.get(f"/audio/{filename}")
        if file_path and os.path.exists(file_path):
            return send_file(file_path, mimetype='audio/mpeg')
        
        return "Audio file not found", 404
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        return "Error serving audio file", 500

# Root endpoint
@app.route('/', methods=['GET'])
def index():
    """Root endpoint to verify the application is running."""
    print("Root endpoint called")
    logger.info("Root endpoint called")
    return f"Vanguard Voice Bot for {BUSINESS_NAME} is running!"

# Twilio voice webhook with hyphen (to match user's configuration)
@app.route('/twilio-voice', methods=['GET', 'POST'])
def twilio_voice():
    """Handle incoming phone calls and return TwiML."""
    print("Twilio call received at /twilio-voice endpoint")
    logger.info("Twilio-voice endpoint called")
    
    try:
        # Log all request data for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request form data: {request.form}")
        logger.info(f"Request values: {request.values}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get the call SID for tracking conversation
        call_sid = request.values.get('CallSid')
        logger.info(f"Call SID: {call_sid}")
        
        # Create TwiML response
        response = create_response()
        
        # Add a simple Say element first for immediate response
        response.say("Welcome to Vanguard Chiropractic. One moment while I connect you.")
        
        # Generate greeting using OpenAI if API key is configured
        if OPENAI_API_KEY:
            greeting_prompt = f"Generate a brief, friendly greeting for someone calling {BUSINESS_NAME}. Ask how you can help them today."
            greeting_text = generate_openai_response(greeting_prompt, None, call_sid)
        else:
            greeting_text = f"Hello, thank you for calling {BUSINESS_NAME}. How may I help you today?"
        
        # Then add the enhanced gather with ElevenLabs voice
        enhanced_gather(response, greeting_text)
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in twilio-voice route: {str(e)}")
        
        # Create a simple error response that will always work
        response = VoiceResponse()
        response.say("Thank you for calling. Our system is currently experiencing technical difficulties. Please try again in a few minutes.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Original Twilio voice webhook with slash (for backward compatibility)
@app.route('/twilio/voice', methods=['GET', 'POST'])
def twilio_voice_slash():
    """Handle incoming phone calls and return TwiML (slash version)."""
    print("Twilio call received at /twilio/voice endpoint")
    logger.info("Twilio/voice endpoint called (slash version)")
    
    try:
        # Log all request data for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request form data: {request.form}")
        logger.info(f"Request values: {request.values}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get the call SID for tracking conversation
        call_sid = request.values.get('CallSid')
        logger.info(f"Call SID: {call_sid}")
        
        # Create TwiML response
        response = create_response()
        
        # Add a simple Say element first for immediate response
        response.say("Welcome to Vanguard Chiropractic. One moment while I connect you.")
        
        # Generate greeting using OpenAI if API key is configured
        if OPENAI_API_KEY:
            greeting_prompt = f"Generate a brief, friendly greeting for someone calling {BUSINESS_NAME}. Ask how you can help them today."
            greeting_text = generate_openai_response(greeting_prompt, None, call_sid)
        else:
            greeting_text = f"Hello, thank you for calling {BUSINESS_NAME}. How may I help you today?"
        
        # Then add the enhanced gather with ElevenLabs voice
        enhanced_gather(response, greeting_text)
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in voice route: {str(e)}")
        
        # Create a simple error response that will always work
        response = VoiceResponse()
        response.say("Thank you for calling. Our system is currently experiencing technical difficulties. Please try again in a few minutes.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Twilio intent webhook
@app.route('/twilio/intent', methods=['POST'])
def twilio_intent():
    """Process speech input and determine intent using OpenAI."""
    print("Twilio intent endpoint called")
    logger.info("Twilio intent endpoint called")
    
    try:
        # Log all request data for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request form data: {request.form}")
        logger.info(f"Request values: {request.values}")
        
        # Get the call SID and speech result
        call_sid = request.values.get('CallSid')
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Call SID: {call_sid}, Speech result: {speech_result}")
        
        # Create TwiML response
        response = create_response()
        
        # Generate response using OpenAI if API key is configured
        if OPENAI_API_KEY:
            # Get conversation history for this call
            conversation_history = conversation_contexts.get(call_sid, [])
            
            # Generate response
            ai_response = generate_openai_response(speech_result, conversation_history, call_sid)
            
            # Check if we have all the appointment information
            if "appointment" in speech_result.lower() or "schedule" in speech_result.lower() or "book" in speech_result.lower():
                # Try to extract appointment information
                appointment_info = extract_appointment_info(conversation_contexts.get(call_sid, []))
                
                # If we have all the required information, book the appointment
                if appointment_info and all(appointment_info.get(field) for field in ['name', 'phone', 'email', 'selectedSlot']):
                    logger.info("All appointment information collected, booking appointment")
                    
                    # Call the book endpoint
                    try:
                        book_response = book_appointment_internal(appointment_info)
                        
                        # If booking was successful, add confirmation to the response
                        if book_response.get('success'):
                            scheduled_time = book_response.get('scheduled_time', appointment_info['selectedSlot'])
                            ai_response += f" Great news! I've booked your appointment for {scheduled_time}. You'll receive a confirmation shortly."
                        else:
                            error_details = book_response.get('details', 'Unknown error')
                            ai_response += f" I'm sorry, but there was an issue booking your appointment. {error_details}"
                    except Exception as e:
                        logger.error(f"Error booking appointment: {str(e)}")
                        ai_response += " I'm sorry, but there was an issue booking your appointment. Please try again later."
            
            # Use the AI response in the TwiML
            enhanced_gather(response, ai_response)
        else:
            # Fallback to hardcoded responses if OpenAI is not configured
            # Handle appointment intent
            if any(word in speech_result for word in ["appointment", "schedule", "book", "visit"]):
                enhanced_say(
                    response,
                    f"I'd be happy to help you schedule an appointment. Let me check what we have available... It looks like we have an opening tomorrow at 2:30 PM. Would that work for your schedule?"
                )
                
                try:
                    # Use gather for confirmation
                    gather = Gather(input='speech', action='/twilio/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
                    gather.say("If that time doesn't work, just let me know and I can check some other options for you.", voice="Polly.Joanna")
                    response.append(gather)
                except Exception as e:
                    logger.error(f"Error creating gather in appointment intent: {str(e)}")
                    response.say("Please call back to confirm your appointment.", voice="Polly.Joanna")
            
            # Handle hours intent
            elif any(word in speech_result for word in ["hours", "open", "close", "time"]):
                enhanced_say(
                    response,
                    f"We're open Monday through Friday from 9 AM to 6 PM, and Saturday from 10 AM to 2 PM. We're closed on Sundays to give our staff a well-deserved break."
                )
                
                try:
                    # Use gather for follow-up
                    gather = Gather(input='speech', action='/twilio/intent', method='POST', language='en-US', speechTimeout='auto')
                    gather.say("Is there anything else I can help you with today?", voice="Polly.Joanna")
                    response.append(gather)
                except Exception as e:
                    logger.error(f"Error creating gather in hours intent: {str(e)}")
                    response.say("Thank you for calling.", voice="Polly.Joanna")
            
            # Handle location intent
            elif any(word in speech_result for word in ["location", "address", "where", "directions"]):
                enhanced_say(
                    response,
                    f"We're located at {BUSINESS_LOCATION}. We're right across from the public library, in the building with the blue awning. There's plenty of parking available in the front and back of the building."
                )
                
                try:
                    # Use gather for follow-up
                    gather = Gather(input='speech', action='/twilio/intent', method='POST', language='en-US', speechTimeout='auto')
                    gather.say("Is there anything else you'd like to know?", voice="Polly.Joanna")
                    response.append(gather)
                except Exception as e:
                    logger.error(f"Error creating gather in location intent: {str(e)}")
                    response.say("Thank you for calling.", voice="Polly.Joanna")
            
            # Default response for unrecognized intent
            else:
                enhanced_gather(
                    response,
                    "I'm sorry, I didn't quite catch that. Are you calling about scheduling an appointment, our hours, or our location?"
                )
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in intent route: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Twilio appointment confirmation webhook
@app.route('/twilio/appointment_confirm', methods=['POST'])
def twilio_appointment_confirm():
    """Process appointment confirmation."""
    logger.info("Twilio appointment confirm endpoint called")
    
    try:
        # Get the call SID and speech result
        call_sid = request.values.get('CallSid')
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Call SID: {call_sid}, Speech result: {speech_result}")
        
        # Create TwiML response
        response = create_response()
        
        # Generate response using OpenAI if API key is configured
        if OPENAI_API_KEY:
            # Get conversation history for this call
            conversation_history = conversation_contexts.get(call_sid, [])
            
            # Add context about appointment confirmation
            prompt = f"The caller said: '{speech_result}' in response to confirming an appointment time. Ask for their name, phone number, and email address if they confirmed. If they didn't confirm, suggest alternative times."
            
            # Generate response
            ai_response = generate_openai_response(prompt, conversation_history, call_sid)
            
            # Use the AI response in the TwiML
            enhanced_gather(response, ai_response, '/twilio/collect_info')
        else:
            # Fallback to hardcoded responses if OpenAI is not configured
            # Check for confirmation
            if any(word in speech_result for word in ["yes", "sure", "okay", "fine", "good", "works", "perfect"]):
                enhanced_say(
                    response,
                    "Great! I've booked your appointment for tomorrow at 2:30 PM. Can I get your name and phone number for our records?"
                )
                
                try:
                    # Use gather for collecting contact info
                    gather = Gather(input='speech', action='/twilio/collect_name', method='POST', language='en-US', speechTimeout='auto')
                    gather.say("Please say your full name.", voice="Polly.Joanna")
                    response.append(gather)
                except Exception as e:
                    logger.error(f"Error creating gather for name collection: {str(e)}")
                    response.say("Please call back to complete your appointment booking.", voice="Polly.Joanna")
            
            # Handle rejection
            elif any(word in speech_result for word in ["no", "not", "can't", "cannot", "don't", "different"]):
                enhanced_say(
                    response,
                    "I understand that time doesn't work for you. Let me check what other times we have available... We also have an opening on Friday at 10:00 AM. Would that work better for you?"
                )
                
                try:
                    # Use gather for confirmation
                    gather = Gather(input='speech', action='/twilio/appointment_confirm', method='POST', language='en-US', speechTimeout='auto')
                    gather.say("If that still doesn't work, we can check more options.", voice="Polly.Joanna")
                    response.append(gather)
                except Exception as e:
                    logger.error(f"Error creating gather for alternate time: {str(e)}")
                    response.say("Please call back to schedule your appointment.", voice="Polly.Joanna")
            
            # Handle unclear response
            else:
                enhanced_gather(
                    response,
                    "I'm sorry, I didn't understand if that time works for you. Would you like to book the appointment for tomorrow at 2:30 PM?",
                    '/twilio/appointment_confirm'
                )
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in appointment confirm route: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Twilio collect information webhook
@app.route('/twilio/collect_info', methods=['POST'])
def twilio_collect_info():
    """Collect information for appointment booking using OpenAI."""
    logger.info("Twilio collect info endpoint called")
    
    try:
        # Get the call SID and speech result
        call_sid = request.values.get('CallSid')
        speech_result = request.values.get('SpeechResult', '').lower()
        logger.info(f"Call SID: {call_sid}, Speech result: {speech_result}")
        
        # Create TwiML response
        response = create_response()
        
        # Generate response using OpenAI if API key is configured
        if OPENAI_API_KEY:
            # Get conversation history for this call
            conversation_history = conversation_contexts.get(call_sid, [])
            
            # Add the user's input to the conversation history
            conversation_history.append({"role": "user", "content": speech_result})
            conversation_contexts[call_sid] = conversation_history
            
            # Try to extract appointment information
            appointment_info = extract_appointment_info(conversation_history)
            
            # If we have all the required information, book the appointment
            if appointment_info and all(appointment_info.get(field) for field in ['name', 'phone', 'email', 'selectedSlot']):
                logger.info("All appointment information collected, booking appointment")
                
                # Call the book endpoint
                try:
                    book_response = book_appointment_internal(appointment_info)
                    
                    # If booking was successful, add confirmation to the response
                    if book_response.get('success'):
                        scheduled_time = book_response.get('scheduled_time', appointment_info['selectedSlot'])
                        ai_response = f"Great! I've booked your appointment for {scheduled_time}. You'll receive a confirmation shortly. Is there anything else I can help you with today?"
                    else:
                        error_details = book_response.get('details', 'Unknown error')
                        ai_response = f"I'm sorry, but there was an issue booking your appointment. {error_details} Is there anything else I can help you with?"
                except Exception as e:
                    logger.error(f"Error booking appointment: {str(e)}")
                    ai_response = "I'm sorry, but there was an issue booking your appointment. Please try again later. Is there anything else I can help you with?"
            else:
                # We still need more information
                missing_fields = []
                if not appointment_info or not appointment_info.get('name'):
                    missing_fields.append("name")
                if not appointment_info or not appointment_info.get('phone'):
                    missing_fields.append("phone number")
                if not appointment_info or not appointment_info.get('email'):
                    missing_fields.append("email address")
                if not appointment_info or not appointment_info.get('selectedSlot'):
                    missing_fields.append("preferred appointment time")
                
                prompt = f"The caller said: '{speech_result}'. I still need to collect their {', '.join(missing_fields)}. Ask for this information in a conversational way."
                ai_response = generate_openai_response(prompt, conversation_history, call_sid)
            
            # Use the AI response in the TwiML
            enhanced_gather(response, ai_response, '/twilio/collect_info')
        else:
            # Fallback to hardcoded responses if OpenAI is not configured
            enhanced_gather(
                response,
                "Thank you for providing that information. Could you please also provide your email address so we can send you a confirmation?",
                '/twilio/collect_info'
            )
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in collect info route: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Twilio collect name webhook (legacy)
@app.route('/twilio/collect_name', methods=['POST'])
def twilio_collect_name():
    """Collect name for appointment booking."""
    logger.info("Twilio collect name endpoint called")
    
    try:
        name = request.values.get('SpeechResult', '')
        logger.info(f"Name collected: {name}")
        
        # Store name in session (would need to implement session management)
        # For now, just proceed to phone collection
        
        # Create TwiML response
        response = create_response()
        
        enhanced_say(
            response,
            f"Thank you, {name}. Now, what's the best phone number to reach you?"
        )
        
        try:
            # Use gather for collecting phone
            gather = Gather(input='speech dtmf', action='/twilio/collect_phone', method='POST', language='en-US', speechTimeout='auto')
            gather.say("Please say or enter your 10-digit phone number.", voice="Polly.Joanna")
            response.append(gather)
        except Exception as e:
            logger.error(f"Error creating gather for phone collection: {str(e)}")
            response.say("Please call back to complete your appointment booking.", voice="Polly.Joanna")
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in collect name route: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Twilio collect phone webhook (legacy)
@app.route('/twilio/collect_phone', methods=['POST'])
def twilio_collect_phone():
    """Collect phone for appointment booking."""
    logger.info("Twilio collect phone endpoint called")
    
    try:
        phone = request.values.get('SpeechResult', '')
        # Clean up phone number - remove spaces, dashes, etc.
        phone = ''.join(filter(str.isdigit, phone))
        logger.info(f"Phone collected: {phone}")
        
        # Create TwiML response
        response = create_response()
        
        enhanced_say(
            response,
            f"Thank you for providing your contact information. Your appointment has been confirmed for tomorrow at 2:30 PM. We'll send a confirmation to your phone. Is there anything else I can help you with today?"
        )
        
        try:
            # Use gather for follow-up
            gather = Gather(input='speech', action='/twilio/intent', method='POST', language='en-US', speechTimeout='auto')
            gather.say("You can say 'hours' for our business hours, 'location' for our address, or 'goodbye' to end the call.", voice="Polly.Joanna")
            response.append(gather)
        except Exception as e:
            logger.error(f"Error creating gather for follow-up: {str(e)}")
            response.say("Thank you for calling. We look forward to seeing you soon.", voice="Polly.Joanna")
        
        logger.info(f"Generated TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    except Exception as e:
        logger.error(f"Error in collect phone route: {str(e)}")
        
        # Create a simple error response
        response = VoiceResponse()
        response.say("We're sorry, but we're experiencing technical difficulties. Please try again later.")
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')

# Fallback route for any Twilio-related requests
@app.route('/<path:path>', methods=['GET', 'POST'])
def fallback_route(path):
    """Fallback route to catch any mistyped Twilio webhook URLs."""
    if path.startswith('twilio') or path.startswith('twilio-'):
        print(f"Fallback route called for path: {path}")
        logger.info(f"Fallback route called for path: {path}")
        
        # Log all request data for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request form data: {request.form}")
        logger.info(f"Request values: {request.values}")
        
        # Create a simple TwiML response
        response = VoiceResponse()
        response.say("Thank you for calling. I'll connect you with our voice assistant.")
        
        # Redirect to the correct voice endpoint
        response.redirect('/twilio-voice')
        
        logger.info(f"Fallback TwiML: {response}")
        return Response(str(response), mimetype='text/xml')
    
    # For non-Twilio paths, return a 404
    return "Not Found", 404

# Make sure the app runs when executed directly
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT') or os.getenv('RAILWAY_PORT') or 5000)
    print(f"Starting Vanguard Voice Bot Backend on port {port}")
    logger.info(f"Starting Vanguard Voice Bot Backend on port {port}")
    app.run(host='0.0.0.0', port=port)
