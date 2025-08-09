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
import pytz
from datetime import datetime, timedelta

# Optional imports for enhanced functionality
try:
    import dateparser
except ImportError:
    dateparser = None

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None

try:
    import openai
except ImportError:
    openai = None

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should be set by Railway
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# === Central Time timezone ===
TZ = pytz.timezone("America/Chicago")

# === Enhanced booking flow constants ===
AFFIRM = ["yes","yeah","yep","that works","sounds good","okay","ok","sure","perfect","great"]

def said_yes(s): 
    return any(a in (s or "").lower() for a in AFFIRM)

def said_morning(s): 
    return any(k in (s or "").lower() for k in ["morning","am","a m"])

def said_afternoon(s): 
    return any(k in (s or "").lower() for k in ["afternoon","evening","pm","p m"])

def normalize_time_tokens(text: str) -> str:
    """Normalize time tokens to fix AM/PM parsing issues."""
    t = (text or "").lower()
    # join spaced letters: "a p m" -> "pm", "a m" -> "am"
    t = re.sub(r"\b([ap])\s*p\s*m\b", lambda m: f"{m.group(1)}pm", t)
    t = re.sub(r"\b([ap])\s*m\b", lambda m: f"{m.group(1)}m", t)
    # fix artifacts like "2a pm" / "2apm" -> "2 pm"
    t = re.sub(r"(\d)\s*a\s*pm\b", r"\1 pm", t)
    t = re.sub(r"(\d)\s*p\s*am\b", r"\1 am", t)
    t = t.replace(" o'clock", "")
    return t

def normalize_email_tokens(text: str) -> str:
    """Normalize email speech to standard format."""
    t = (text or "").lower()
    # Convert spoken email parts
    t = t.replace(" at ", "@")
    t = t.replace(" dot ", ".")
    t = t.replace(" underscore ", "_")
    t = t.replace(" dash ", "-")
    t = t.replace(" hyphen ", "-")
    # Remove extra spaces
    t = re.sub(r"\s+", "", t)
    return t

# Enhanced email normalization for natural speech
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

SPOKEN_MAP = {
    " at ": "@", " dot ": ".", " period ": ".", " underscore ": "_",
    " dash ": "-", " hyphen ": "-", " plus ": "+", " space ": ""
}

def normalize_spoken_email(text: str) -> str:
    """Normalize spoken email like 'john at gmail dot com' to 'john@gmail.com'."""
    t = " " + (text or "").lower().strip() + " "
    # collapse spelled letters like "g m a i l" -> "gmail"
    t = re.sub(r"\b([a-z])\s+(?=[a-z]\b)", r"\1", t)
    # replace spoken tokens
    for k, v in SPOKEN_MAP.items():
        t = t.replace(k, v)
    t = re.sub(r"\s+", "", t)  # remove remaining spaces
    return t

def norm(text: str) -> str:
    """Normalize text for consistent processing."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def parse_dt_central(user_text: str, prior_dt=None):
    """
    Enhanced datetime parser with normalization - no AM/PM questions when already specified.
    Returns (dt: aware datetime | None, clarify: str | None)
    """
    # Normalize time tokens first
    t = normalize_time_tokens(user_text or "")
    settings = {"TIMEZONE":"America/Chicago","RETURN_AS_TIMEZONE_AWARE":True,"PREFER_DATES_FROM":"future"}
    dt = dateparser.parse(t, settings=settings) if dateparser else None

    if not dt:
        # allow time-only with prior day context
        if prior_dt and re.search(r"\b(\d{1,2})(:\d{2})?\s*(am|pm)\b", t):
            merged = dateparser.parse(prior_dt.strftime("%A ") + re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", t).group(0), settings=settings) if dateparser else None
            if merged: return merged.astimezone(TZ), None
        return None, "What day and time works for you?"

    # If the user explicitly said am/pm (after normalization), accept it — no clarification
    if "am" in t or "pm" in t:
        return dt.astimezone(TZ), None

    # Otherwise, if hour is 1–11 and no am/pm, ask once
    if 1 <= dt.hour <= 11:
        return None, "Did you mean morning or afternoon?"

    return dt.astimezone(TZ), None

# === Environment variables ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")  # Jessica
ELEVEN_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

# GoHighLevel settings
GHL_API_KEY = os.environ.get("GHL_API_KEY")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID")
GHL_CALENDAR_ID = os.environ.get("GHL_CALENDAR_ID")

# === TTS Cache for common phrases + startup caching ===
TTS_CACHE = {}
CACHE_DURATION = 300  # 5 minutes

# Startup cache for common phrases to reduce latency
STARTUP_PHRASES = [
    "Thanks for calling Vanguard Chiropractic. How can I help you today?",
    "What day and time works for you?",
    "Did you mean morning or afternoon?",
    "What's your full name?",
    "What's the best mobile number for confirmation?",
    "What email should we use to send your confirmation?",
    "I didn't catch that. Could you say that again?",
    "Please spell your email address clearly."
]

def tts_cached(text: str) -> bytes:
    """Get cached TTS or generate new one - optimized for startup caching."""
    cache_key = text.lower().strip()
    if cache_key in TTS_CACHE:
        return TTS_CACHE[cache_key]
    
    # Generate and cache
    audio = tts_bytes_with_retry(text)
    TTS_CACHE[cache_key] = audio
    return audio

def get_cached_tts(text: str) -> bytes:
    """Get cached TTS or generate new one."""
    cache_key = text.lower().strip()
    now = time.time()
    
    # Check cache
    if cache_key in TTS_CACHE:
        cached_audio, timestamp = TTS_CACHE[cache_key]
        if now - timestamp < CACHE_DURATION:
            app.logger.info(f"TTS cache hit for: {text[:30]}...")
            return cached_audio
    
    # Generate new TTS
    audio = tts_bytes_with_retry(text)
    TTS_CACHE[cache_key] = (audio, now)
    
    # Clean old cache entries
    if len(TTS_CACHE) > 50:  # Keep cache size reasonable
        old_keys = [k for k, (_, ts) in TTS_CACHE.items() if now - ts > CACHE_DURATION]
        for k in old_keys:
            del TTS_CACHE[k]
    
    return audio

def tts_bytes_with_retry(text: str, max_retries: int = 2) -> bytes:
    """Generate TTS audio with retry logic for resilience."""
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
                timeout=60  # Keep 60s timeout for ElevenLabs
            )
            
            # Check for successful response
            if response.status_code == 200:
                return response.content
            elif response.status_code >= 500 and attempt < max_retries - 1:
                app.logger.warning(f"ElevenLabs 5xx error (attempt {attempt + 1}), retrying...")
                time.sleep(0.5)
                continue
            elif response.status_code == 429:
                # Rate limited, wait longer
                time.sleep(1.0)
                continue
            else:
                response.raise_for_status()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                app.logger.warning(f"ElevenLabs timeout (attempt {attempt + 1}), retrying...")
                time.sleep(0.5)
                continue
            else:
                raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"ElevenLabs request error (attempt {attempt + 1}): {e}, retrying...")
                time.sleep(0.5)
                continue
            else:
                raise
    
    # If we get here, all retries failed
    raise Exception("All TTS retry attempts failed")

# === Hardened TTS endpoint ===
@app.route("/tts", methods=["GET"])
def tts_get():
    """Hardened TTS endpoint with caching and proper headers."""
    text = request.args.get("text", "Thanks for calling Vanguard. How can I help you today?")
    
    try:
        # Use cached TTS for common phrases
        audio = get_cached_tts(text)
        app.logger.info(f"TTS successful for text: {text[:50]}...")
        
        # Return with hardened headers
        return Response(audio, headers={
            "Content-Type": "audio/mpeg",
            "Content-Length": str(len(audio)),
            "Cache-Control": "public, max-age=120",
            "Content-Disposition": "inline"
        })
    except Exception as e:
        app.logger.error(f"/tts error: {e}")
        
        # Fallback to simple text response that Twilio can handle
        fallback_text = "I'm having trouble with my voice system. Please hold on."
        try:
            fallback_audio = tts_bytes_with_retry(fallback_text)
            return Response(fallback_audio, headers={
                "Content-Type": "audio/mpeg",
                "Content-Length": str(len(fallback_audio)),
                "Cache-Control": "public, max-age=120",
                "Content-Disposition": "inline"
            })
        except Exception:
            # Last resort: return empty audio response
            return Response(b"", headers={
                "Content-Type": "audio/mpeg",
                "Content-Length": "0"
            }, status=200)

# === Session store ===
CALLS = {}  # {CallSid: {"booking": {...}}}

def get_session(call_sid):
    """Get or create session for a call."""
    if call_sid not in CALLS:
        CALLS[call_sid] = {"booking": {}}
    return CALLS[call_sid]

# === Helper function for TwiML responses ===
def respond_gather(base_url: str, message: str) -> Response:
    """Gold-standard TwiML: one Play + one Gather, no Redirect."""
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Gather input="speech"
        language="en-US"
        speechTimeout="auto"
        enhanced="true"
        speechModel="phone_call"
        actionOnEmptyResult="true"
        record="false"
        hints="monday,tuesday,wednesday,thursday,friday,saturday,sunday,9 am,10 am,11 am,1 pm,2 pm,3 pm,afternoon,morning,next week,appointment,book,schedule,at,dot,underscore,dash,gmail,yahoo,hotmail"
        action="/twilio-handoff" method="POST">
  <Play>{base_url}/tts?text={urllib.parse.quote_plus(message)}</Play>
  <Pause length="0.3"/>
</Gather>
</Response>"""
    return Response(twiml, mimetype="text/xml")

# === Health endpoint ===
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

# === Twilio entry point ===
@app.route("/twilio", methods=["GET","POST"])
def twilio_entry():
    """Twilio entry point - greet once and gather speech with hot mic."""
    base = request.url_root.rstrip("/")
    greeting = request.values.get("text", "Thanks for calling Vanguard Chiropractic. How can I help you today?")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Gather input="speech"
        language="en-US"
        speechTimeout="auto"
        enhanced="true"
        speechModel="phone_call"
        actionOnEmptyResult="true"
        record="false"
        hints="monday,tuesday,wednesday,thursday,friday,saturday,sunday,9 am,10 am,11 am,1 pm,2 pm,3 pm,tomorrow,next week,appointment,book,schedule"
        action="/twilio-handoff" method="POST">
  <Play>{base}/tts?text={urllib.parse.quote_plus(greeting)}</Play>
  <Pause length="0.3"/>
</Gather>
</Response>"""
    return Response(twiml, mimetype="text/xml")

# === Gold-standard conversation handler ===
@app.route("/twilio-handoff", methods=["POST"])
def twilio_handoff():
    """Gold-standard conversation handler with no loops or redundant questions."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", f"NA-{int(time.time())}")
    heard_raw = request.values.get("SpeechResult", "") or ""
    confidence = request.values.get("Confidence", "0.0")
    
    # Enhanced logging per specification
    session = get_session(call_sid)
    B = session.setdefault("booking", {})
    
    # Log per turn: heard, confidence, stage keys, and any slot values
    app.logger.info({
        "sid": call_sid, 
        "stage": list(B.keys()), 
        "heard": heard_raw, 
        "confidence": confidence,
        "values": {k: v for k, v in B.items() if k in ["datetime", "name", "phone", "email"]}
    })
    
    try:
        # Detect booking intent from phrases
        booking_keywords = ["book", "schedule", "appointment", "come in", "new patient", "back hurts", "pain", "visit"]
        if any(k in heard_raw.lower() for k in booking_keywords) or B.get("intent") == "booking":
            B["intent"] = "booking"

            # === GOLD-STANDARD BOOKING FLOW ===
            
            # 1) Date & time capture - NO AM/PM questions if already specified
            if "datetime" not in B:
                
                # A) "Yes" confirmation to proposed time
                if said_yes(heard_raw) and B.get("candidate_dt"):
                    dt = B["candidate_dt"]
                    B["datetime"] = dt.isoformat()
                    B["friendly_dt"] = dt.strftime("%A at %-I:%M %p")
                    app.logger.info({"stage": "datetime_confirmed", "heard": heard_raw, "datetime": B["datetime"]})
                    return respond_gather(base, f"Great. What's your full name?")

                # B) Parse new time utterance with normalization
                dt, clar = parse_dt_central(heard_raw, B.get("last_context_dt"))
                
                # If clarification needed (only for truly ambiguous times)
                if clar and not ("am" in heard_raw.lower() or "pm" in heard_raw.lower()):
                    B["candidate_dt"] = B.get("last_context_dt")
                    B["awaiting_ampm"] = True
                    app.logger.info({"stage": "datetime_clarification", "heard": heard_raw, "clarification": clar})
                    return respond_gather(base, clar)

                # If we got a valid datetime, confirm it
                if dt:
                    B["candidate_dt"] = dt
                    B["last_context_dt"] = dt
                    B["candidate_friendly"] = dt.strftime("%A at %-I:%M %p")
                    app.logger.info({"stage": "datetime_candidate", "heard": heard_raw, "candidate": B["candidate_friendly"]})
                    return respond_gather(base, f"Just to confirm, {B['candidate_friendly']} — is that right?")

                # Couldn't parse - simple ask
                app.logger.info({"stage": "datetime_request", "heard": heard_raw})
                return respond_gather(base, "What day and time works for you?")

            # 2) Name capture - accept any non-empty utterance
            elif "name" not in B:
                cleaned = heard_raw.strip()
                if cleaned:
                    B["name"] = cleaned
                    app.logger.info({"stage": "name_captured", "heard": heard_raw, "name": B["name"]})
                    return respond_gather(base, f"Thanks, {B['name']}. What's the best mobile number for confirmation? Please say it digit by digit.")
                else:
                    app.logger.info({"stage": "name_empty", "heard": heard_raw})
                    return respond_gather(base, "I didn't catch your name. Could you say it again?")

            # 3) Phone capture - extract 10+ digits
            elif "phone" not in B:
                digits = re.sub(r"\D", "", heard_raw)
                if len(digits) >= 10:
                    B["phone"] = f"+1{digits[-10:]}"
                    app.logger.info({"stage": "phone_captured", "heard": heard_raw, "phone": B["phone"]})
                    return respond_gather(base, "Got it. And what email should we send your confirmation to?")
                else:
                    app.logger.info({"stage": "phone_insufficient", "heard": heard_raw, "digits_found": len(digits)})
                    return respond_gather(base, "Please say the 10-digit mobile number including area code.")

            # 4) Email capture with normalization
            elif "email" not in B:
                # Normalize spoken email first
                norm1 = normalize_spoken_email(heard_raw)
                m = EMAIL_RE.search(heard_raw) or EMAIL_RE.search(norm1)
                if m:
                    B["email"] = m.group(0)
                    app.logger.info({"stage": "email_captured", "heard": heard_raw, "normalized": norm1, "email": B["email"]})
                    
                    # Proceed directly to booking
                    payload = {"name": B["name"], "phone": B["phone"], "email": B["email"], "datetime": B["datetime"]}
                    try:
                        r = requests.post(f"{base}/book", json=payload, timeout=60)
                        if r.status_code == 200:
                            app.logger.info({"stage": "booking_success", "payload": payload})
                            # Clear booking state after successful booking
                            CALLS[call_sid] = {"booking": {}}
                            return respond_gather(base, f"Perfect. You're all set for {B['friendly_dt']}. We'll text your confirmation to {B['phone']}. Anything else I can help with?")
                        else:
                            app.logger.info({"stage": "booking_failed", "status_code": r.status_code, "payload": payload})
                            return respond_gather(base, "I'm having trouble booking at the moment. Would you like a team member to call you back, or try a different time?")
                    except Exception as booking_error:
                        app.logger.error({"stage": "booking_error", "error": str(booking_error), "payload": payload})
                        return respond_gather(base, "I'm having trouble booking at the moment. Would you like a team member to call you back, or try a different time?")
                else:
                    app.logger.info({"stage": "email_invalid", "heard": heard_raw, "normalized": norm1})
                    return respond_gather(base, "Please say it like john at gmail dot com.")

            # All booking info collected - this shouldn't happen but handle gracefully
            else:
                app.logger.info({"stage": "booking_complete_fallback", "heard": heard_raw, "booking_state": B})
                return respond_gather(base, "Your appointment is confirmed. Is there anything else I can help you with?")

        # === NON-BOOKING CONVERSATION ===
        else:
            if not heard_raw:
                app.logger.info({"stage": "empty_speech", "heard": heard_raw})
                return respond_gather(base, "Sorry, I didn't catch that — could you say it again?")
            
            # Natural follow-ups / FAQs (short, friendly)
            heard_lower = heard_raw.lower()
            
            if any(word in heard_lower for word in ["hours", "open", "time"]):
                app.logger.info({"stage": "hours_inquiry", "heard": heard_raw})
                return respond_gather(base, "We're open Monday through Friday 9 to 6, and Saturday 9 to 1. Would you like me to get you scheduled?")
            
            elif any(word in heard_lower for word in ["location", "address", "where"]):
                app.logger.info({"stage": "location_inquiry", "heard": heard_raw})
                return respond_gather(base, "We're located in downtown Austin. Would you like me to get you scheduled?")
            
            elif any(word in heard_lower for word in ["price", "cost", "how much", "insurance"]):
                app.logger.info({"stage": "pricing_inquiry", "heard": heard_raw})
                return respond_gather(base, "We have various options and work with insurance. Would you like to schedule a consultation?")
            
            elif any(word in heard_lower for word in ["pain", "hurt", "back", "neck", "sore"]):
                app.logger.info({"stage": "pain_inquiry", "heard": heard_raw})
                return respond_gather(base, "I'm sorry you're experiencing pain. Let's get you scheduled so the doctor can help. What day and time works for you?")
            
            else:
                app.logger.info({"stage": "general_inquiry", "heard": heard_raw})
                return respond_gather(base, "I can help with hours, location, services, or I can book an appointment. What would you like?")

    except Exception as e:
        app.logger.error(f"/twilio-handoff error: {e}")
        # SAFE fallback TwiML (keeps call alive, no crash)
        return respond_gather(base, "I had a little trouble just then. Could you say that one more time?")

# === GoHighLevel booking endpoint ===
@app.route("/book", methods=["POST"])
def book_appointment():
    """Book appointment in GoHighLevel."""
    try:
        data = request.get_json()
        name = data.get("name")
        phone = data.get("phone")
        email = data.get("email")
        datetime_str = data.get("datetime")
        
        if not all([name, phone, email, datetime_str]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Parse datetime
        try:
            appointment_dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            if appointment_dt.tzinfo is None:
                appointment_dt = TZ.localize(appointment_dt)
        except Exception as e:
            return jsonify({"error": f"Invalid datetime format: {e}"}), 400
        
        # Create contact in GoHighLevel
        contact_data = {
            "firstName": name.split()[0] if name.split() else name,
            "lastName": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            "phone": phone,
            "email": email,
            "locationId": GHL_LOCATION_ID
        }
        
        contact_response = requests.post(
            "https://rest.gohighlevel.com/v1/contacts/",
            headers={
                "Authorization": f"Bearer {GHL_API_KEY}",
                "Content-Type": "application/json"
            },
            json=contact_data,
            timeout=30
        )
        
        if contact_response.status_code not in [200, 201]:
            app.logger.error(f"Contact creation failed: {contact_response.text}")
            return jsonify({"error": "Failed to create contact"}), 500
        
        contact_id = contact_response.json().get("contact", {}).get("id")
        if not contact_id:
            return jsonify({"error": "No contact ID returned"}), 500
        
        # Create appointment
        appointment_data = {
            "calendarId": GHL_CALENDAR_ID,
            "contactId": contact_id,
            "startTime": appointment_dt.isoformat(),
            "endTime": (appointment_dt + timedelta(minutes=30)).isoformat(),
            "title": f"Appointment with {name}",
            "appointmentStatus": "confirmed"
        }
        
        appointment_response = requests.post(
            "https://rest.gohighlevel.com/v1/appointments/",
            headers={
                "Authorization": f"Bearer {GHL_API_KEY}",
                "Content-Type": "application/json"
            },
            json=appointment_data,
            timeout=30
        )
        
        if appointment_response.status_code not in [200, 201]:
            app.logger.error(f"Appointment creation failed: {appointment_response.text}")
            return jsonify({"error": "Failed to create appointment"}), 500
        
        return jsonify({
            "success": True,
            "contact_id": contact_id,
            "appointment": appointment_response.json()
        })
        
    except Exception as e:
        app.logger.error(f"Booking error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Startup TTS caching to reduce first-call latency
    if ELEVEN_KEY:
        app.logger.info("Pre-caching common TTS phrases for faster response...")
        try:
            for phrase in STARTUP_PHRASES:
                tts_cached(phrase)
                app.logger.info(f"Cached: {phrase[:30]}...")
        except Exception as e:
            app.logger.warning(f"TTS pre-caching failed: {e}")
    
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

