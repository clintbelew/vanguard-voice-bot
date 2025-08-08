import os
import logging
import requests
import tempfile
import io
import base64
import json
import sys
import urllib.parse
import time
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
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# === ElevenLabs TTS ===
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")  # Jessica
ELEVEN_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

def tts_bytes(text: str) -> bytes:
    """Generate TTS audio bytes using ElevenLabs API."""
    if not ELEVEN_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")
    
    r = requests.post(
        ELEVEN_URL,
        headers={"xi-api-key": ELEVEN_KEY, "Accept": "audio/mpeg", "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": 0.55, "similarity_boost": 0.8}},
        timeout=60,
    )
    r.raise_for_status()
    return r.content

# TTS endpoint for Twilio
@app.route("/tts", methods=["GET"])
def tts_get():
    """Generate TTS audio using ElevenLabs for Twilio."""
    text = request.args.get("text", "Thanks for calling Vanguard Chiropractic. How can I help you today?")
    logger.info(f"TTS endpoint called with text: {text}")
    
    try:
        audio_bytes = tts_bytes(text)
        return Response(audio_bytes, mimetype="audio/mpeg")
    except Exception as e:
        logger.error(f"Error generating TTS: {str(e)}")
        # Return a simple error response
        return Response(b"", mimetype="audio/mpeg", status=500)

# === Simple session store (per call). For prod, use Redis. ===
CALLS = {}  # { CallSid: {"history": [ {role, content} ], "booking": {...}} }

def get_session(call_sid):
    """Get or create session for a call."""
    if call_sid not in CALLS:
        CALLS[call_sid] = {"history": []}
    return CALLS[call_sid]

# === OpenAI ===
SYSTEM_PROMPT = (
    "You are Jessica, a warm, friendly, highly competent front-desk receptionist for Vanguard Chiropractic. "
    "Speak like a real person in short, natural sentences (max 2 per turn). "
    "Answer questions about hours, location, services, pricing, and smoothly guide toward booking. "
    "When user indicates intent to book, politely collect: full name, phone (confirm digits), email (confirm spelling), and preferred date/time. "
    "Use the booking tool when details are sufficient, then confirm aloud. "
    "If requested time is unavailable, suggest closest available slots. "
    "If out-of-scope, offer to connect to a team member. "
    "Always close politely and helpfully. "
    "Tone: confident, approachable, caring. Avoid long lists; summarize when possible."
)

def openai_chat(messages):
    """
    messages: [{"role":"system"/"user"/"assistant","content":"..."}]
    returns assistant text
    """
    if not OPENAI_API_KEY:
        return "I'm sorry, but I'm having trouble accessing my system right now. Could you please call back in a few minutes?"
    
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": OPENAI_MODEL, "messages": messages, "temperature": 0.6, "max_tokens": 220}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return "I didn't catch that—could you rephrase or tell me what time you'd like to come in?"

# === Booking tool: calls existing /book ===
def try_booking(name, phone, email, datetime_iso):
    """
    Returns (ok: bool, message: str)
    """
    try:
        payload = {"name": name, "phone": phone, "email": email, "datetime": datetime_iso}
        r = requests.post(f"{request.url_root.rstrip('/')}/book", json=payload, timeout=60)
        if r.status_code == 200:
            return True, "You're all set. I've booked that appointment."
        return False, "I couldn't complete the booking just now. Would you like me to try a different time?"
    except Exception as e:
        logger.error(f"Booking error: {str(e)}")
        return False, "I had trouble booking just now. Would you like me to connect you to a team member?"

# === Twilio flow ===
@app.route("/twilio", methods=["GET", "POST"])
def twilio_entry():
    """Main Twilio entry point with Jessica greeting and speech gathering."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", f"NA-{int(time.time())}")
    session = get_session(call_sid)
    
    logger.info(f"Twilio entry called - CallSid: {call_sid}")

    # greet only on first turn of the call
    if not session["history"]:
        greet = request.values.get("text", "Thanks for calling Vanguard Chiropractic. How can I help you today?")
        greet_url = f"{base}/tts?text={urllib.parse.quote_plus(greet)}"
    else:
        greet_url = f"{base}/tts?text={urllib.parse.quote_plus('How else can I help you?')}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{greet_url}</Play>
  <Gather input="speech" language="en-US" speechTimeout="auto" action="/twilio-handoff" method="POST">
    <Pause length="1"/>
  </Gather>
  <Redirect>/twilio</Redirect>
</Response>"""
    
    logger.info(f"Generated TwiML: {twiml}")
    return Response(twiml, mimetype="text/xml")

@app.route("/twilio-handoff", methods=["POST"])
def twilio_handoff():
    """Handle conversation with Jessica using OpenAI and booking functionality."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", f"NA-{int(time.time())}")
    user_text = request.values.get("SpeechResult", "") or ""
    session = get_session(call_sid)
    
    logger.info(f"Twilio handoff - CallSid: {call_sid}, Speech: {user_text}")

    # store user turn
    if not any(m["role"] == "system" for m in session["history"]):
        session["history"].insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    session["history"].append({"role": "user", "content": user_text})

    # Use OpenAI to generate response
    assistant = openai_chat(session["history"])
    reply_text = None

    # Example lightweight tool convention:
    # If the assistant replies with a line starting BOOK: JSON {...}, parse and call booking.
    if assistant.strip().startswith("BOOK:"):
        try:
            data_json = assistant.split("BOOK:", 1)[1].strip()
            data = json.loads(data_json)
            ok, msg = try_booking(
                name=data.get("name",""),
                phone=data.get("phone",""),
                email=data.get("email",""),
                datetime_iso=data.get("datetime",""),
            )
            reply_text = msg
        except Exception as e:
            logger.error(f"Booking parsing error: {str(e)}")
            reply_text = "I had trouble booking that. Could I confirm your full name, mobile number, email, and a good time?"
    else:
        reply_text = assistant

    # store assistant turn
    session["history"].append({"role": "assistant", "content": reply_text})
    
    logger.info(f"Generated reply: {reply_text}")

    tts_url = f"{base}/tts?text={urllib.parse.quote_plus(reply_text)}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{tts_url}</Play>
  <Redirect>/twilio</Redirect>
</Response>"""
    
    logger.info(f"Generated TwiML: {twiml}")
    return Response(twiml, mimetype="text/xml")

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    print("Health check endpoint called")
    logger.info("Health check endpoint called")
    return jsonify({"status": "ok"}), 200

# Voice endpoint for API testing
@app.route('/voice', methods=['POST'])
def voice_endpoint():
    """Voice endpoint for API testing with ElevenLabs integration."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field in request"}), 400
        
        text = data['text']
        logger.info(f"Voice endpoint called with text: {text}")
        
        # Generate audio using ElevenLabs
        audio_bytes = tts_bytes(text)
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        # Return the audio file
        return send_file(temp_path, mimetype='audio/mpeg', as_attachment=True, download_name='voice.mp3')
        
    except Exception as e:
        logger.error(f"Error in voice endpoint: {str(e)}")
        return jsonify({"error": "Failed to generate voice"}), 500

# Book appointment endpoint
@app.route('/book', methods=['POST'])
def book_appointment():
    """Book an appointment using GoHighLevel API."""
    try:
        data = request.get_json()
        logger.info(f"Booking request received: {data}")
        
        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'datetime']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Extract data
        name = data['name']
        phone = data['phone']
        email = data['email']
        datetime_str = data['datetime']
        
        # Parse datetime
        try:
            if datetime_str.endswith('Z'):
                appointment_datetime = datetime.fromisoformat(datetime_str[:-1])
            else:
                appointment_datetime = datetime.fromisoformat(datetime_str)
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
        
        # Convert to Central Time for GoHighLevel
        central_tz = pytz.timezone('America/Chicago')
        if appointment_datetime.tzinfo is None:
            appointment_datetime = central_tz.localize(appointment_datetime)
        else:
            appointment_datetime = appointment_datetime.astimezone(central_tz)
        
        # Format for GoHighLevel API
        formatted_datetime = appointment_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare GoHighLevel API request
        ghl_url = f"https://rest.gohighlevel.com/v1/appointments/"
        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "calendarId": GHL_CALENDAR_ID,
            "locationId": GHL_LOCATION_ID,
            "contactId": "",  # Will be created if doesn't exist
            "startTime": formatted_datetime,
            "endTime": formatted_datetime,  # GoHighLevel will set duration
            "title": f"Appointment for {name}",
            "appointmentStatus": "confirmed",
            "assignedUserId": "",
            "address": "",
            "ignoreDateRange": False,
            "toNotify": True,
            "notes": f"Booked via voice bot. Phone: {phone}, Email: {email}"
        }
        
        # First, create or find the contact
        contact_payload = {
            "firstName": name.split()[0] if name.split() else name,
            "lastName": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            "email": email,
            "phone": phone,
            "locationId": GHL_LOCATION_ID
        }
        
        # Create contact
        contact_url = "https://rest.gohighlevel.com/v1/contacts/"
        contact_response = requests.post(contact_url, json=contact_payload, headers=headers)
        
        if contact_response.status_code in [200, 201]:
            contact_data = contact_response.json()
            contact_id = contact_data.get('contact', {}).get('id') or contact_data.get('id')
            payload["contactId"] = contact_id
        else:
            logger.warning(f"Failed to create contact: {contact_response.text}")
        
        # Create appointment
        response = requests.post(ghl_url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"Appointment booked successfully: {result}")
            return jsonify({
                "success": True,
                "message": "Appointment booked successfully",
                "appointment_id": result.get('id'),
                "datetime": formatted_datetime
            }), 200
        else:
            logger.error(f"GoHighLevel API error: {response.status_code} - {response.text}")
            return jsonify({
                "success": False,
                "error": "Failed to book appointment with GoHighLevel"
            }), 500
            
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

# Make sure the app runs when executed directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

