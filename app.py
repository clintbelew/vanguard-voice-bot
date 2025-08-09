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
import re
from flask import Flask, request, jsonify, send_file, Response, session
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse, Gather
import pytz
from datetime import datetime, timedelta
import dateparser
from dateutil import parser as dateutil_parser
import openai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# === Reliable datetime parser for America/Chicago ===
TZ = pytz.timezone("America/Chicago")
DOW = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

def normalize_uttr(t: str) -> str:
    """Normalize user utterance for better datetime parsing."""
    t = t.lower().strip()
    t = t.replace("o'clock", " o clock ")
    t = re.sub(r"\bten in the morning\b", "10 am", t)
    t = re.sub(r"\b(\d+)\s*in the morning\b", r"\1 am", t)
    t = re.sub(r"\b(\d+)\s*in the evening\b", r"\1 pm", t)
    return re.sub(r"\s+", " ", t)

def parse_dt_central(text: str) -> tuple[datetime|None, str|None]:
    """
    Parse natural language datetime for America/Chicago timezone.
    Returns (datetime, None) if successful, (None, clarifier_question) if needs clarification.
    """
    t = normalize_uttr(text)
    settings = {
        "TIMEZONE": "America/Chicago",
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }
    
    # Common fast path: "tuesday at 10 am"
    if any(d in t for d in DOW) and re.search(r"\b(\d{1,2})(:\d{2})?\s*(am|pm)\b", t):
        dt = dateparser.parse(t, settings=settings)
        if dt: 
            return dt.astimezone(TZ), None

    # If only day-of-week + hour (no am/pm): ask to clarify
    if any(d in t for d in DOW) and re.search(r"\b(\d{1,2})(:\d{2})?\b", t) and not re.search(r"\bam|pm\b", t):
        return None, "Did you mean A M or P M for that time?"

    # Generic parse
    dt = dateparser.parse(t, settings=settings)
    if not dt:
        return None, "What day and time works for you? For example, Tuesday at 10 A M."
    
    # If still ambiguous morning/evening for 1-11 and no am/pm present
    if (1 <= dt.hour <= 11) and ("am" not in t and "pm" not in t):
        return None, f"Just to confirm, did you mean {dt.strftime('%A at %-I A M')} or {dt.strftime('%-I P M')}?"
    
    return dt.astimezone(TZ), None

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")  # Jessica
ELEVEN_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# GoHighLevel settings
GHL_API_KEY = os.environ.get("GHL_API_KEY")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID")
GHL_CALENDAR_ID = os.environ.get("GHL_CALENDAR_ID")

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

# Central Time timezone for appointment parsing
TZ = pytz.timezone("America/Chicago")

def parse_datetime_central(text: str) -> tuple[datetime|None, str|None]:
    """
    Try to parse a natural-language appointment time in Central Time.
    Returns (dt, clarifier) where:
      - dt is a timezone-aware datetime if confident,
      - clarifier is a question to disambiguate (e.g., AM/PM or day).
    """
    t = text.lower().strip()
    
    # If user only says "9 o'clock" or "9", ask AM/PM + day.
    if t in {"9", "9 oclock", "9 o'clock", "nine", "nine oclock", "nine o'clock"}:
        return None, "Did you mean 9 AM or 9 PM, and what day works for you?"

    # Try parsing with dateparser
    settings = {
        "TIMEZONE": "America/Chicago",
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",   # avoid past dates
    }
    dt = dateparser.parse(text, settings=settings)
    if not dt:
        return None, "What day and time works for you? For example, Monday at 9 AM."

    # If no AM/PM and it's ambiguous, nudge to morning by default but confirm
    # Detect: if hour in [1..11] and no 'am/pm' in text, ask confirm
    if any(k in t for k in ["am","a.m.","pm","p.m."]):
        # fine
        pass
    else:
        if 1 <= dt.hour <= 11:
            # Ask to confirm AM/PM
            return None, f"Just to confirm, did you mean {dt.strftime('%-I %p on %A')}?"

    return dt.astimezone(TZ), None

# === Chiropractic-specific trigger-response library ===
CHIROPRACTIC_RESPONSES = {
    "version": "1.0",
    "domain": "chiropractic",
    "responses": [
        {
            "id": "back_pain",
            "triggers": ["back hurts", "back pain", "lower back", "hurt my back", "back injury", "sciatica"],
            "reply": "I'm sorry your back is hurting. Let's get you scheduled so the doctor can help. What day and time work best for you?"
        },
        {
            "id": "neck_pain",
            "triggers": ["neck pain", "stiff neck", "crick in my neck", "whiplash"],
            "reply": "Neck pain can be rough. We can help with that. Would you like to schedule a visit this week?"
        },
        {
            "id": "headache_migraine",
            "triggers": ["headache", "migraines", "migraine"],
            "reply": "I understand how disruptive headaches can be. We often help with that. Want me to find a time for you to come in?"
        },
        {
            "id": "new_patient",
            "triggers": ["new patient", "first time", "never been", "how do I start"],
            "reply": "Welcome! I'll get you set up. Can I have your full name and a good mobile number to book your first visit?"
        },
        {
            "id": "follow_up",
            "triggers": ["follow up", "another appointment", "next adjustment", "come back in"],
            "reply": "Absolutely. When would you like to come in—morning or afternoon?"
        },
        {
            "id": "walk_in",
            "triggers": ["walk in", "walk-in", "can I just come", "no appointment"],
            "reply": "We accept walk-ins when we can, but booking saves you waiting. What time works for you and I'll reserve it?"
        },
        {
            "id": "hours",
            "triggers": ["hours", "open", "what time are you open", "closing time"],
            "reply": "We're open Monday through Friday 9 to 6, and Saturday 9 to 1. What day would you like to come in?"
        },
        {
            "id": "location",
            "triggers": ["where are you", "address", "location", "how do I get there", "directions"],
            "reply": "We're located at your Vanguard office address. Would you like me to book you a time to come in?"
        },
        {
            "id": "pricing",
            "triggers": ["price", "cost", "how much", "visit cost"],
            "reply": "A standard visit is typically discussed with the doctor based on your needs, and we have self-pay options. Would you like to book a visit to get started?"
        },
        {
            "id": "insurance",
            "triggers": ["insurance", "do you take", "in network", "coverage"],
            "reply": "We work with many insurance plans and have self-pay options. I can connect you with our team to confirm coverage, or we can go ahead and schedule you."
        },
        {
            "id": "today_urgent",
            "triggers": ["today", "asap", "urgent", "right now", "soonest"],
            "reply": "Let me look for our earliest openings today. Do you prefer morning or afternoon?"
        },
        {
            "id": "auto_accident",
            "triggers": ["car accident", "auto accident", "hit", "rear-ended"],
            "reply": "I'm sorry you were in an accident. We help with whiplash and related injuries. Shall I book an evaluation for you?"
        },
        {
            "id": "sports_injury",
            "triggers": ["pulled", "sprained", "strain", "sports injury"],
            "reply": "We see sports injuries often. Let's set up a visit so the doctor can evaluate it. When works for you?"
        },
        {
            "id": "pediatric",
            "triggers": ["child", "kid", "pediatric"],
            "reply": "Yes, we treat children as well. Would you like to set up a time for your child this week?"
        },
        {
            "id": "prenatal",
            "triggers": ["pregnant", "prenatal", "pregnancy"],
            "reply": "We do offer prenatal chiropractic care. I can book you a comfortable time. What day works best?"
        },
        {
            "id": "xray",
            "triggers": ["x-ray", "xray", "imaging"],
            "reply": "We can take X-rays if the doctor recommends them during your visit. Want me to get you scheduled?"
        },
        {
            "id": "payment_plans",
            "triggers": ["payment plan", "financing", "payments"],
            "reply": "We do have payment options. We can discuss those at your visit. Would you like me to reserve a time?"
        },
        {
            "id": "book_appointment",
            "triggers": ["book", "appointment", "schedule", "make an appointment", "set up a visit"],
            "reply": "I can help with that. What day works best for you, and do you prefer morning or afternoon?"
        },
        {
            "id": "contact_info_request",
            "triggers": ["my name is", "number is", "email is", "here is my"],
            "reply": "Thanks! I'll confirm: please share your full name, your mobile number digit by digit, and your email spelled out. Then I'll secure your appointment."
        },
        {
            "id": "goodbye",
            "triggers": ["thank you", "thanks", "bye", "goodbye"],
            "reply": "You're very welcome. We look forward to seeing you soon!"
        }
    ],
    "fallbacks": {
        "no_speech": "I didn't catch that. Could you repeat that a little more clearly, like 'Monday at 9 AM'?",
        "clarify_time": "Did you mean 9 AM or 9 PM, and what day works for you?",
        "clarify_contact": "To finalize your booking, may I have your full name, mobile number, and email address?"
    }
}

def match_chiropractic_response(user_input: str) -> str|None:
    """
    Match user input against chiropractic trigger-response library.
    Returns the appropriate response if a trigger matches, None otherwise.
    """
    if not user_input:
        return None
    
    user_lower = user_input.lower()
    
    # Check each response for trigger matches
    for response in CHIROPRACTIC_RESPONSES["responses"]:
        for trigger in response["triggers"]:
            if trigger.lower() in user_lower:
                logger.info(f"Matched trigger '{trigger}' for response ID '{response['id']}'")
                return response["reply"]
    
    return None

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
    """Resilient TTS endpoint - ALWAYS returns valid audio."""
    text = request.args.get("text", "Thanks for calling Vanguard. How can I help you today?")
    
    try:
        # Try ElevenLabs TTS with retry logic
        audio = tts_bytes_with_retry(text)
        logger.info(f"ElevenLabs TTS successful for text: {text[:50]}...")
        return Response(audio, mimetype="audio/mpeg")
        
    except Exception as e:
        app.logger.error(f"/tts error: {e}", exc_info=True)
        logger.error(f"TTS failed for text: {text[:50]}..., using fallback audio")
        
        # Return fallback audio file so Twilio doesn't get 5xx
        try:
            return send_file("static/fallback.mp3", mimetype="audio/mpeg")
        except Exception as fallback_error:
            app.logger.error(f"Fallback audio error: {fallback_error}", exc_info=True)
            # Last resort: return empty audio response
            return Response(b"", mimetype="audio/mpeg", status=200)

def tts_bytes_with_retry(text: str, max_retries: int = 2) -> bytes:
    """
    Generate TTS audio with retry logic for resilience.
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                ELEVEN_URL,
                headers={
                    "xi-api-key": ELEVEN_KEY,
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8
                    }
                },
                timeout=10  # Shorter timeout for faster fallback
            )
            
            # Check for successful response
            if response.status_code == 200:
                return response.content
            elif response.status_code >= 500 and attempt < max_retries - 1:
                # Retry on 5xx errors
                logger.warning(f"ElevenLabs 5xx error (attempt {attempt + 1}), retrying...")
                time.sleep(0.5)  # Brief delay before retry
                continue
            else:
                # Don't retry on 4xx errors or final attempt
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                logger.warning(f"ElevenLabs timeout (attempt {attempt + 1}), retrying...")
                continue
            else:
                raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"ElevenLabs request error (attempt {attempt + 1}): {e}, retrying...")
                continue
            else:
                raise
    
    # If we get here, all retries failed
    raise Exception("All TTS retry attempts failed")

# === Enhanced session store with booking state (per call). For prod, use Redis. ===
CALLS = {}  # {CallSid: {"history": [{role, content}], "greeted": bool, "booking": {"name":..., "phone":..., "email":..., "datetime":...}}}

def get_session(call_sid):
    """Get or create enhanced session for a call with booking state."""
    if call_sid not in CALLS:
        CALLS[call_sid] = {
            "history": [],
            "greeted": False,
            "booking": {}
        }
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
    """Main Twilio entry point with one-time greeting and enhanced speech gathering."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", "NA")
    session = get_session(call_sid)
    
    # Check if this is the first time we're greeting this caller
    first_time = not session.get("greeted")
    session["greeted"] = True
    
    logger.info(f"Twilio entry called - CallSid: {call_sid}, First time: {first_time}")

    # Use full greeting only on first call, shorter prompt on subsequent loops
    greeting = request.values.get("text", "Thanks for calling Vanguard Chiropractic. How can I help you today?")
    greet_text = greeting if first_time else "How can I help you?"
    greet_url = f"{base}/tts?text={urllib.parse.quote_plus(greet_text)}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{greet_url}</Play>
  <Gather input="speech"
          language="en-US"
          speechTimeout="auto"
          enhanced="true"
          speechModel="phone_call"
          hints="monday,tuesday,wednesday,thursday,friday,saturday,sunday,9 am,10 am,11 am,1 pm,2 pm,3 pm,tomorrow,next week,appointment,book,schedule"
          action="/twilio-handoff" method="POST">
    <Pause length="1"/>
  </Gather>
  <Redirect>/twilio</Redirect>
</Response>"""
    
    logger.info(f"Generated TwiML: {twiml}")
    return Response(twiml, mimetype="text/xml")

@app.route("/twilio-handoff", methods=["POST"])
def twilio_handoff():
    """Handle conversation with comprehensive error handling - ALWAYS returns valid TwiML."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", "NA")
    heard = (request.values.get("SpeechResult") or "").strip()
    
    # Enhanced logging to see exactly what Twilio heard
    app.logger.info({"call": call_sid, "heard": heard})
    
    try:
        # Get session and ensure system prompt
        session = get_session(call_sid)
        if not any(m["role"] == "system" for m in session["history"]):
            session["history"].insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        
        # Add user input to conversation history
        if heard:
            session["history"].append({"role": "user", "content": heard})
        
        # Generate reply with booking state confirmation flow
        B = session.setdefault("booking", {})
        
        if heard:
            # Check for booking intent
            if ("book" in heard.lower() or "appointment" in heard.lower() or B.get("intent") == "booking"):
                B["intent"] = "booking"
                
                if "datetime" not in B:
                    # Try to parse datetime from user input
                    dt, clar = parse_dt_central(heard)
                    if clar:
                        # Need clarification
                        reply = clar
                    elif dt:
                        # Successfully parsed datetime
                        B["datetime"] = dt.isoformat()
                        reply = dt.strftime("Great — %A at %-I:%M %p. What is your full name?")
                    else:
                        # Couldn't parse datetime
                        reply = "What day and time works for you? For example, Tuesday at 10 A M."
                else:
                    # Already have datetime, collect other info
                    reply = "Thanks. Please tell me your full name, mobile number, and email so I can confirm the booking."
            else:
                # Not booking intent - try chiropractic responses first
                chiro_response = match_chiropractic_response(heard)
                if chiro_response:
                    reply = chiro_response
                    logger.info(f"Using chiropractic response: {reply}")
                else:
                    # Use OpenAI for natural conversation
                    reply = openai_chat(session["history"])
        else:
            # No speech detected
            reply = CHIROPRACTIC_RESPONSES["fallbacks"]["no_speech"]
        
        # Add assistant reply to conversation history (for non-booking conversations)
        if B.get("intent") != "booking":
            session["history"].append({"role": "assistant", "content": reply})
        
        logger.info(f"Generated reply: {reply}")
        logger.info(f"Booking state: {B}")
        
        # Generate TTS URL
        tts_url = f"{base}/tts?text={urllib.parse.quote_plus(reply)}"
        
        # Return TwiML with enhanced Gather (mic stays hot)
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{tts_url}</Play>
  <Gather input="speech"
          language="en-US"
          speechTimeout="auto"
          enhanced="true"
          speechModel="phone_call"
          hints="monday,tuesday,wednesday,thursday,friday,saturday,sunday,9 am,10 am,11 am,1 pm,2 pm,3 pm,tomorrow,next week,appointment,book,schedule"
          action="/twilio-handoff" method="POST">
    <Pause length="1"/>
  </Gather>
  <Redirect>/twilio</Redirect>
</Response>"""
        
        logger.info(f"Generated TwiML successfully for call {call_sid}")
        return Response(twiml, mimetype="text/xml")
        
    except Exception as e:
        app.logger.error(f"/twilio-handoff error: {e}", exc_info=True)
        
        # SAFE fallback TwiML (keeps call alive, no crash)
        fallback = "I had a little trouble just then. Could you say that one more time, like Monday at 9 A M?"
        tts_url = f"{base}/tts?text={urllib.parse.quote_plus(fallback)}"
        
        fallback_twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>{tts_url}</Play>
  <Gather input="speech"
          language="en-US"
          speechTimeout="auto"
          enhanced="true"
          speechModel="phone_call"
          hints="monday,tuesday,wednesday,thursday,friday,saturday,sunday,9 am,10 am,11 am,1 pm,2 pm,3 pm,tomorrow,next week,appointment,book,schedule"
          action="/twilio-handoff" method="POST">
    <Pause length="1"/>
  </Gather>
  <Redirect>/twilio</Redirect>
</Response>"""
        
        logger.info(f"Using fallback TwiML for call {call_sid}")
        return Response(fallback_twiml, mimetype="text/xml")

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

