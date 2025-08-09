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

def norm(text: str) -> str:
    """Normalize text for consistent processing."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def parse_dt_central(user_text: str, prior_dt=None):
    """
    Enhanced datetime parser - no AM/PM questions when already specified.
    Returns (dt: aware datetime | None, clarify: str | None)
    """
    t = (user_text or "").lower()
    settings = {"TIMEZONE":"America/Chicago","RETURN_AS_TIMEZONE_AWARE":True,"PREFER_DATES_FROM":"future"}
    dt = dateparser.parse(t, settings=settings) if dateparser else None

    if not dt:
        # allow time-only with prior day context
        if prior_dt and re.search(r"\b(\d{1,2})(:\d{2})?\s*(am|pm)\b", t):
            merged = dateparser.parse(prior_dt.strftime("%A ") + re.search(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b", t).group(0), settings=settings) if dateparser else None
            if merged: return merged.astimezone(TZ), None
        return None, "What day and time works for you?"

    # If the user explicitly said am/pm, accept it — no clarification
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

# === TTS Cache for common phrases ===
TTS_CACHE = {}
CACHE_DURATION = 300  # 5 minutes

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
    """Helper to return TwiML response with hot mic gather block."""
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
<Gather input="speech"
        language="en-US"
        speechTimeout="auto"
        enhanced="true"
        speechModel="phone_call"
        actionOnEmptyResult="true"
        record="false"
        hints="monday,tuesday,wednesday,thursday,friday,9 am,10 am,11 am,1 pm,2 pm,3 pm,afternoon,morning,next week,appointment,book,schedule,name,phone,email"
        action="/twilio-handoff" method="POST">
  <Play>{base_url}/tts?text={urllib.parse.quote_plus(message)}</Play>
  <Pause length="0.3"/>
</Gather>
<Redirect>/twilio</Redirect>
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
<Redirect>/twilio</Redirect>
</Response>"""
    return Response(twiml, mimetype="text/xml")

# === Enhanced conversation handler ===
@app.route("/twilio-handoff", methods=["POST"])
def twilio_handoff():
    """Enhanced conversation handler with optimized booking flow."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", f"NA-{int(time.time())}")
    heard_raw = request.values.get("SpeechResult", "") or ""
    
    # Lean logging
    session = get_session(call_sid)
    B = session.setdefault("booking", {})
    app.logger.info({"call": call_sid, "stage": list(B.keys()), "heard": heard_raw})
    
    try:
        # Detect booking intent
        if any(k in heard_raw.lower() for k in ["book","schedule","appointment"]) or B.get("intent") == "booking":
            B["intent"] = "booking"

            # === BOOKING STATE MACHINE ===
            
            # 1) datetime - candidate → confirm → set → advance flow
            if "datetime" not in B:
                
                # A) AM/PM clarification response to a prior candidate
                if B.get("awaiting_ampm") and B.get("candidate_dt"):
                    cand = B["candidate_dt"]
                    if 1 <= cand.hour <= 11:
                        if said_morning(heard_raw):
                            pass  # keep AM
                        elif said_afternoon(heard_raw):
                            cand = cand.replace(hour=(cand.hour % 12) + 12)
                        else:
                            return respond_gather(base, "Did you mean morning or afternoon?")

                    B["awaiting_ampm"] = False
                    B["datetime"] = cand.isoformat()
                    B["friendly_dt"] = cand.strftime("%A at %-I:%M %p")
                    return respond_gather(base, f"Great — {B['friendly_dt']}. What's your full name?")

                # B) "Yes" to previously proposed candidate
                if said_yes(heard_raw) and B.get("candidate_dt"):
                    dt = B["candidate_dt"]
                    B["datetime"] = dt.isoformat()
                    B["friendly_dt"] = dt.strftime("%A at %-I:%M %p")
                    return respond_gather(base, f"Great — {B['friendly_dt']}. What's your full name?")

                # C) Parse new utterance
                dt, clar = parse_dt_central(heard_raw, B.get("last_context_dt"))
                if clar:
                    # We're asking AM/PM only when truly ambiguous; keep it short.
                    if not B.get("candidate_dt") and B.get("last_context_dt"):
                        B["candidate_dt"] = B["last_context_dt"]
                    B["awaiting_ampm"] = True
                    return respond_gather(base, clar)

                if dt:
                    B["candidate_dt"] = dt
                    B["last_context_dt"] = dt
                    B["candidate_friendly"] = dt.strftime("%A at %-I:%M %p")
                    return respond_gather(base, f"Just to confirm, {B['candidate_friendly']} — is that right?")

                # D) Couldn't parse yet — simple ask (no repeated examples)
                return respond_gather(base, "What day and time works for you?")

            # 2) name collection
            elif "name" not in B:
                m = re.search(r"(my name is|this is)\s+([a-zA-Z][a-zA-Z ,.'-]+)$", heard_raw, re.I)
                if m:
                    B["name"] = m.group(2).strip()
                    return respond_gather(base, "Thanks. What's the best mobile number for confirmation? Please say it digit by digit.")
                else:
                    return respond_gather(base, "Got it. May I have your full name?")

            # 3) phone collection
            elif "phone" not in B:
                digits = re.sub(r"\D", "", heard_raw)
                if len(digits) >= 10:
                    B["phone"] = f"+1{digits[-10:]}"
                    return respond_gather(base, "Thank you. What email should we use to send your confirmation?")
                else:
                    return respond_gather(base, "Could you share your mobile number digit by digit, including area code?")

            # 4) email → book
            elif "email" not in B:
                m = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", heard_raw, re.I)
                if m:
                    B["email"] = m.group(0)
                    payload = {"name": B["name"], "phone": B["phone"], "email": B["email"], "datetime": B["datetime"]}
                    try:
                        r = requests.post(f"{base}/book", json=payload, timeout=60)
                        if r.status_code == 200:
                            # Clear booking state after successful booking
                            CALLS[call_sid] = {"booking": {}}
                            return respond_gather(base, f"You're all set for {B['friendly_dt']}. We'll text your confirmation to {B['phone']}.")
                        else:
                            return respond_gather(base, "I couldn't complete the booking just now. Would you like me to try a different time?")
                    except Exception:
                        return respond_gather(base, "I had trouble booking just now. Would you like me to connect you to a team member?")
                else:
                    return respond_gather(base, "Please spell your email address clearly.")

        # === NON-BOOKING CONVERSATION ===
        else:
            if not heard_raw:
                return respond_gather(base, "I didn't hear that clearly. How can I help you today?")
            
            # Simple responses for common queries
            heard_lower = heard_raw.lower()
            
            if any(word in heard_lower for word in ["hours", "open", "time"]):
                return respond_gather(base, "We're open Monday through Friday 9 to 6, and Saturday 9 to 1. Would you like to schedule a visit?")
            
            elif any(word in heard_lower for word in ["location", "address", "where"]):
                return respond_gather(base, "We're located in downtown Austin. Would you like me to book you an appointment?")
            
            elif any(word in heard_lower for word in ["price", "cost", "how much"]):
                return respond_gather(base, "We have various options and work with insurance. Would you like to schedule a consultation?")
            
            elif any(word in heard_lower for word in ["pain", "hurt", "back", "neck"]):
                return respond_gather(base, "I'm sorry you're experiencing pain. Let's get you scheduled so the doctor can help. What day works for you?")
            
            else:
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

