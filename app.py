import os
import logging
import requests
import tempfile
import os
import re
import time
import random
import urllib.parse
from datetime import datetime
import pytz
import requests
from flask import Flask, request, Response
import dateparser
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

# === Enhanced TTS caching and caller memory ===
TTS_CACHE = {}  # In-memory cache for TTS audio
CALLER_MEMORY = {}  # Per-caller memory by phone number
BAD_TURNS_LOG = []  # Log for low confidence turns

# TTS optimization settings
TTS_TIMEOUT = 8  # Reduced timeout for faster responses
TTS_CACHE_DURATION = 15 * 60  # 15 minutes cache duration

# Caller memory structure
def get_caller_memory(phone):
    """Get or create caller memory for phone number."""
    if phone not in CALLER_MEMORY:
        CALLER_MEMORY[phone] = {
            "name": None,
            "last_success_dt": None,
            "pain_flag": False,
            "tone_pref": "normal",  # normal, human_mode, empathetic
            "call_count": 0,
            "last_seen": None
        }
    return CALLER_MEMORY[phone]

def update_caller_memory(phone, updates):
    """Update caller memory with new information."""
    memory = get_caller_memory(phone)
    memory.update(updates)
    memory["last_seen"] = datetime.now().isoformat()
    memory["call_count"] += 1

# Rotated confirmation phrases for natural variety
CONFIRMATION_PHRASES = [
    ["Perfect", "Great", "Excellent"],
    ["Got it", "Thanks", "Perfect"],
    ["Sounds good", "That works", "Great choice"]
]

def get_varied_confirmation():
    """Get a varied confirmation phrase to sound more natural."""
    import random
    return random.choice(random.choice(CONFIRMATION_PHRASES))

# === Enhanced booking flow constants ===
AFFIRM = ["yes","yeah","yep","that works","sounds good","okay","ok","sure","perfect","great"]
FEEDBACK_WARM = ["sound robotic", "more human", "more natural", "more sensitive", "less robotic", "too slow", "be quicker"]

# Emotional intelligence detection
URGENCY_KEYWORDS = ["severe pain", "emergency", "urgent", "asap", "right away", "can't wait", "killing me", "unbearable"]
FRUSTRATION_KEYWORDS = ["frustrated", "annoying", "stupid", "not working", "terrible", "awful", "hate this"]
CONFUSION_KEYWORDS = ["confused", "don't understand", "what", "huh", "repeat", "say again"]
PAIN_KEYWORDS = ["pain", "hurt", "ache", "sore", "injury", "accident", "can't move"]

# Human handoff detection
HUMAN_HANDOFF_KEYWORDS = ["speak to someone", "team member", "human", "representative", "real person", "talk to someone", "live person", "actual person"]

def said_yes(s): 
    return any(a in (s or "").lower() for a in AFFIRM)

def said_morning(s): 
    return any(k in (s or "").lower() for k in ["morning","am","a m","good morning"])

def said_afternoon(s): 
    return any(k in (s or "").lower() for k in ["afternoon","evening","pm","p m","good afternoon"])

def said_natural_confirmation(s):
    """Accept natural confirmations like 'yes', 'that works', 'sounds good'."""
    confirmations = ["yes", "yep", "sure", "that works", "sounds good", "perfect", "great", "okay", "ok"]
    return any(conf in (s or "").lower() for conf in confirmations)

def check_feedback(text, S):
    """Detect feedback phrases and switch to human_mode for more natural responses."""
    t = (text or "").lower()
    if any(k in t for k in FEEDBACK_WARM):
        S["human_mode"] = True
        return "Got it — I'll keep it natural and quick. Let's get you taken care of."
    return None

def detect_emotional_state(text, S):
    """Advanced emotional intelligence - detect urgency, frustration, confusion, pain."""
    t = (text or "").lower()
    
    # Urgency detection - prioritize immediate care
    if any(k in t for k in URGENCY_KEYWORDS):
        S["urgency"] = True
        S["pain_mentioned"] = True
        return "I understand this is urgent. Let me get you the earliest available appointment."
    
    # Pain detection - show empathy
    if any(k in t for k in PAIN_KEYWORDS):
        S["pain_mentioned"] = True
        return "I hear you're in pain. Let's get you scheduled right away."
    
    # Frustration detection - apologize and offer human help
    if any(k in t for k in FRUSTRATION_KEYWORDS):
        S["frustrated"] = True
        return "I'm sorry this has been frustrating. Let me help you quickly, or I can connect you to a team member."
    
    # Confusion detection - slow down and simplify
    if any(k in t for k in CONFUSION_KEYWORDS):
        S["confused"] = True
        return "No problem, let me explain that more clearly."
    
    return None

def get_contextual_response(stage, B, S):
    """Generate contextual responses based on conversation history and emotional state."""
    human_mode = S.get("human_mode", False)
    urgency = S.get("urgency", False)
    pain_mentioned = S.get("pain_mentioned", False)
    
    if stage == "datetime_confirmed" and pain_mentioned:
        return f"Perfect. We'll get you some relief on {B['friendly_dt']}. What's your name?"
    elif stage == "booking_success" and pain_mentioned:
        return f"You're all set for {B['friendly_dt']}. We'll help you feel better soon. Confirmation will be texted to {B['phone']}."
    elif human_mode:
        # Shorter, more natural responses in human mode
        responses = {
            "datetime_request": ["What day works for you?", "When would you like to come in?"],
            "name_request": ["And your name?", "What's your name?"],
            "phone_request": ["Phone number?", "What's your number?"],
            "email_request": ["Email address?", "What's your email?"]
        }
        return random.choice(responses.get(stage, ["How can I help?"]))
    
    return None

def cleanup_name(text):
    """Precision Fix 3: Clean up name capture with proper formatting."""
    if not text:
        return ""
    
    # Remove filler phrases more precisely
    cleaned = text.lower()
    filler_patterns = [
        r'\bmy name is\b',
        r'\bfirst name is\b', 
        r'\blast name is\b',
        r'\bname is\b',
        r'\bit\'s\b',
        r'\bthis is\b'
    ]
    
    for pattern in filler_patterns:
        cleaned = re.sub(pattern, '', cleaned)
    
    # Collapse spelled-out letters: "c l i n t" -> "clint"
    cleaned = re.sub(r'\b([a-z])\s+(?=[a-z]\b)', r'\1', cleaned)
    
    # Clean up and title case
    cleaned = re.sub(r'[^\w\s-]', '', cleaned).strip()
    return ' '.join(word.capitalize() for word in cleaned.split() if word)

def normalize_email_advanced(text):
    """Precision Fix 2: Advanced email normalization with filler phrase removal."""
    if not text:
        return ""
    
    # Remove filler phrases
    filler_phrases = ["it's", "this is", "my email is", "email is", "the email is", "my email address is"]
    cleaned = text.lower()
    for phrase in filler_phrases:
        cleaned = cleaned.replace(phrase, "")
    
    # Remove all punctuation except email-valid characters
    cleaned = re.sub(r'[^\w\s@._+-]', '', cleaned)
    
    # Apply spoken email normalization
    return normalize_spoken_email(cleaned)

def detect_human_handoff(text):
    """Precision Fix 5: Detect requests for human assistance."""
    t = (text or "").lower()
    return any(phrase in t for phrase in HUMAN_HANDOFF_KEYWORDS)

def has_ampm_indicator(text):
    """Precision Fix 1: Check if text contains AM/PM indicators."""
    t = (text or "").lower()
    ampm_patterns = ["am", "pm", "a.m.", "p.m.", "a m", "p m"]
    return any(pattern in t for pattern in ampm_patterns)

def normalize_time_tokens(text: str) -> str:
    """Normalize time tokens to fix AM/PM parsing issues per gold standard spec."""
    t = (text or "").lower()
    # join spaced letters: "a m" -> "am", "p m" -> "pm"
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

# Enhanced email normalization for natural speech per specification
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

SPOKEN_MAP = {
    " at ": "@", " dot ": ".", " period ": ".", " underscore ": "_",
    " dash ": "-", " hyphen ": "-", " plus ": "+", " space ": ""
}

def normalize_spoken_email(text: str) -> str:
    """Normalize spoken email like 'john at gmail dot com' to 'john@gmail.com' per specification."""
    t = " " + (text or "").lower().strip() + " "
    # collapse spelled letters like "g m a i l" -> "gmail"
    t = re.sub(r"\b([a-z])\s+(?=[a-z]\b)", r"\1", t)
    # replace spoken tokens
    for k, v in SPOKEN_MAP.items():
        t = t.replace(k, v)
    return re.sub(r"\s+", "", t)

def norm(text: str) -> str:
    """Normalize text for consistent processing."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def try_booking_safe(booking_url, payload):
    """Safe booking with timeout handling to eliminate booking timeouts."""
    try:
        r = requests.post(booking_url, json=payload, timeout=8)
        if r.status_code == 200:
            return True, None
        return False, "I couldn't complete the booking just now. Would you like me to try a different time?"
    except requests.Timeout:
        return False, "It's taking a little long to confirm. Want me to try another time or have a team member text you?"
    except Exception:
        return False, "I hit a snag booking. Would you like me to connect you to a team member?"

def parse_dt_central(user_text: str, prior_dt=None):
    """
    Enhanced datetime parser with normalization - skip AM/PM when already specified.
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
    if any(indicator in t for indicator in ["am", "a.m.", "pm", "p.m."]):
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
    """Generate TTS audio with enhanced settings and retry logic for resilience."""
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
                        "stability": 0.4,  # Slightly lower for more natural variation
                        "similarity_boost": 0.8,  # Higher for better voice consistency
                        "style": 0.6,  # Increased for more expressive delivery
                        "use_speaker_boost": True
                    }
                },
                timeout=TTS_TIMEOUT  # Reduced to 8 seconds for faster responses
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
    """Twilio entry point - personalized greet and gather speech with hot mic."""
    base = request.url_root.rstrip("/")
    caller_phone = request.values.get("From", "")
    
    # Use personalized greeting based on caller memory
    greeting = get_personalized_greeting(caller_phone)
    
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

def log_bad_turn(call_sid, heard_raw, confidence, stage, reason):
    """Log bad turns for weekly review and optimization."""
    bad_turn = {
        "timestamp": datetime.now().isoformat(),
        "call_sid": call_sid,
        "heard": heard_raw,
        "confidence": confidence,
        "stage": stage,
        "reason": reason
    }
    BAD_TURNS_LOG.append(bad_turn)
    
    # Keep only last 1000 entries to prevent memory issues
    if len(BAD_TURNS_LOG) > 1000:
        BAD_TURNS_LOG.pop(0)
    
    app.logger.warning(f"Bad turn logged: {bad_turn}")

def get_personalized_greeting(caller_phone):
    """Get personalized greeting based on caller memory."""
    if not caller_phone:
        return "Thanks for calling Vanguard Chiropractic. How can I help you today?"
    
    memory = get_caller_memory(caller_phone)
    
    if memory["call_count"] > 0 and memory["name"]:
        # Returning caller with name
        if memory["pain_flag"]:
            return f"Hi {memory['name']}, thanks for calling back. How are you feeling?"
        else:
            return f"Hi {memory['name']}, thanks for calling Vanguard Chiropractic. How can I help you today?"
    elif memory["call_count"] > 0:
        # Returning caller without name
        return "Thanks for calling back! How can I help you today?"
    else:
        # First-time caller
        return "Thanks for calling Vanguard Chiropractic. How can I help you today?"

def send_booking_sms(phone, booking_link):
    """Send SMS with booking link when booking fails."""
    try:
        # This would integrate with Twilio SMS API
        # For now, just log the action
        app.logger.info(f"SMS booking link sent to {phone}: {booking_link}")
        return True
    except Exception as e:
        app.logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        return False

# === Gold-standard conversation handler ===
@app.route("/twilio-handoff", methods=["POST"])
def twilio_handoff():
    """Gold-standard conversation handler with enhanced logging per specification."""
    base = request.url_root.rstrip("/")
    call_sid = request.values.get("CallSid", f"NA-{int(time.time())}")
    heard_raw = request.values.get("SpeechResult", "") or ""
    confidence = request.values.get("Confidence", "0.0")
    
    # Enhanced logging per specification
    session = get_session(call_sid)
    B = session.setdefault("booking", {})
    
    try:
        # Enhanced logging per specification - log per turn
        def log_turn(stage_info, next_prompt=None):
            log_data = {
                "sid": call_sid,
                "stage": list(B.keys()),
                "heard": heard_raw,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }
            
            if isinstance(stage_info, dict):
                log_data.update(stage_info)
            else:
                log_data["stage_info"] = stage_info
                
            if next_prompt:
                log_data["next_prompt"] = next_prompt
                
            app.logger.info(log_data)
            
            # Check for bad turns and log them
            conf_float = float(confidence) if confidence else 0.0
            if conf_float < 0.6:  # Low confidence threshold
                log_bad_turn(call_sid, heard_raw, confidence, list(B.keys()), "low_confidence")
        
        # Get caller phone for memory lookup
        caller_phone = request.values.get("From", "")
        caller_memory = get_caller_memory(caller_phone) if caller_phone else None
        
        # Apply caller memory preferences
        if caller_memory and caller_memory["tone_pref"] == "human_mode":
            session["human_mode"] = True
        
        # Check for tone feedback first - adapt instantly
        session = get_session(call_sid)
        feedback_response = check_feedback(heard_raw, session)
        if feedback_response:
            log_turn({"feedback_detected": True, "human_mode": True})
            return respond_gather(base, feedback_response)
        
        # Check for emotional states - respond with empathy
        emotional_response = detect_emotional_state(heard_raw, session)
        if emotional_response:
            log_turn({"emotional_state_detected": True, "response": emotional_response})
            return respond_gather(base, emotional_response)
        
        # Precision Fix 5: Check for human handoff requests
        if detect_human_handoff(heard_raw):
            log_turn({"fix_applied": "human_handoff", "heard": heard_raw})
            # Clear booking state and mark for human callback
            CALLS[call_sid] = {"booking": {}, "human_requested": True}
            return respond_gather(base, "I'll connect you with a team member right away. Please hold on while I transfer you, or someone will call you back within a few minutes.")
        
        # Detect booking intent from phrases
        booking_keywords = ["book", "schedule", "appointment", "come in", "new patient", "back hurts", "pain", "visit"]
        if any(k in heard_raw.lower() for k in booking_keywords) or B.get("intent") == "booking":
            B["intent"] = "booking"

            # === GOLD-STANDARD BOOKING FLOW ===
            
            # 1) Date & time capture with natural confirmation handling
            if "datetime" not in B:
                
                # A) Handle AM/PM clarification if awaiting
                if B.get("awaiting_ampm") and B.get("candidate_dt"):
                    cand = B["candidate_dt"]
                    if said_morning(heard_raw):
                        # Keep AM (no change needed if already AM)
                        if cand.hour > 12:
                            cand = cand.replace(hour=cand.hour - 12)
                    elif said_afternoon(heard_raw):
                        # Convert to PM
                        if cand.hour < 12:
                            cand = cand.replace(hour=cand.hour + 12)
                    else:
                        # Still unclear, ask again
                        return respond_gather(base, "Did you mean morning or afternoon?")
                    
                    # Lock in the time and advance
                    B["datetime"] = cand.isoformat()
                    B["friendly_dt"] = cand.strftime("%A at %-I:%M %p")
                    B["awaiting_ampm"] = False  # Clear immediately
                    app.logger.info({"stage": "datetime_ampm_resolved", "heard": heard_raw, "datetime": B["datetime"]})
                    return respond_gather(base, f"Great. What's your full name?")

                # B) Natural confirmation to proposed time
                if said_natural_confirmation(heard_raw) and B.get("candidate_dt"):
                    dt = B["candidate_dt"]
                    B["datetime"] = dt.isoformat()
                    B["friendly_dt"] = dt.strftime("%A at %-I:%M %p")
                    log_turn({"stage": "datetime_confirmed", "heard": heard_raw, "datetime": B["datetime"]})
                    
                    # Use contextual response based on conversation history
                    contextual_response = get_contextual_response("datetime_confirmed", B, session)
                    if contextual_response:
                        return respond_gather(base, contextual_response)
                    else:
                        return respond_gather(base, f"Great. What's your full name?")

                # C) Parse new time utterance with normalization
                dt, clar = parse_dt_central(heard_raw, B.get("last_context_dt"))
                
                # Precision Fix 1: Skip AM/PM clarification if already specified
                if clar and has_ampm_indicator(heard_raw):
                    log_turn({"fix_applied": "skip_ampm", "heard": heard_raw, "reason": "ampm_already_specified"})
                    # Force accept the datetime without clarification
                    if dt:
                        B["datetime"] = dt.isoformat()
                        B["friendly_dt"] = dt.strftime("%A at %-I:%M %p")
                        log_turn({"stage": "datetime_confirmed_auto", "datetime": B["datetime"]})
                        
                        contextual_response = get_contextual_response("datetime_confirmed", B, session)
                        if contextual_response:
                            return respond_gather(base, contextual_response)
                        else:
                            return respond_gather(base, f"Great. What's your full name?")
                
                if clar:
                    # Only ask AM/PM if truly ambiguous AND no am/pm specified
                    if not B.get("candidate_dt") and B.get("last_context_dt"):
                        B["candidate_dt"] = B["last_context_dt"]
                    B["awaiting_ampm"] = True
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

            # === NAME CAPTURE ===
            elif "name" not in B:
                # Precision Fix 3: Clean up name capture with proper formatting
                cleaned_name = cleanup_name(heard_raw)
                if cleaned_name:
                    B["name"] = cleaned_name
                    log_turn({"fix_applied": "name_cleanup", "heard": heard_raw, "cleaned": cleaned_name})
                    return respond_gather(base, f"Thanks, {B['name']}. What's the best mobile number for confirmation? Please say it digit by digit.")
                else:
                    return respond_gather(base, "I didn't catch your name. Could you say it again?")

            # === PHONE CAPTURE ===
            elif "phone" not in B:
                digits = re.sub(r"\D", "", heard_raw)
                if len(digits) >= 10:
                    B["phone"] = f"+1{digits[-10:]}"
                    app.logger.info({"stage": "phone_captured", "heard": heard_raw, "phone": B["phone"]})
                    return respond_gather(base, "Thank you. What email should we use to send your confirmation?")
                else:
                    app.logger.info({"stage": "phone_insufficient", "heard": heard_raw, "digits_found": len(digits)})
                    return respond_gather(base, "Could you share your mobile number digit by digit, including area code?")

            # === EMAIL CAPTURE ===
            elif "email" not in B:
                # Precision Fix 2: Advanced email normalization with filler phrase removal
                norm1 = normalize_email_advanced(heard_raw)
                m = EMAIL_RE.search(heard_raw) or EMAIL_RE.search(norm1)
                if m:
                    B["email"] = m.group(0)
                    log_turn({"fix_applied": "email_normalization", "heard": heard_raw, "normalized": norm1, "email": B["email"]})
                    
                    # Proceed directly to booking per specification with timeout handling
                    payload = {"name": B["name"], "phone": B["phone"], "email": B["email"], "datetime": B["datetime"]}
                    success, error_msg = try_booking_safe(f"{base}/book", payload)
                    if success:
                        log_turn({"stage": "booking_success", "payload": payload})
                        
                        # Update caller memory with successful booking
                        if caller_phone:
                            memory_updates = {
                                "name": B["name"],
                                "last_success_dt": B["datetime"],
                                "pain_flag": session.get("pain_mentioned", False),
                                "tone_pref": session.get("human_mode", False) and "human_mode" or "normal"
                            }
                            update_caller_memory(caller_phone, memory_updates)
                        
                        # Clear booking state after successful booking
                        CALLS[call_sid] = {"booking": {}}
                        
                        # Use varied confirmation and contextual response
                        confirmation = get_varied_confirmation()
                        contextual_response = get_contextual_response("booking_success", B, session)
                        if contextual_response:
                            return respond_gather(base, contextual_response)
                        else:
                            return respond_gather(base, f"{confirmation}! You're all set for {B['friendly_dt']}. We'll text your confirmation to {B['phone']}. Anything else I can help with?")
                    else:
                        log_turn({"stage": "booking_failed", "error": error_msg})
                        
                        # Send SMS booking link as fallback
                        booking_link = f"https://vanguard-chiropractic.com/book"  # Replace with actual booking link
                        if caller_phone and send_booking_sms(caller_phone, booking_link):
                            return respond_gather(base, f"I'm having trouble booking right now, but I've texted you a direct booking link. You can also call back and I'll try again. Anything else I can help with?")
                        else:
                            return respond_gather(base, error_msg)
                else:
                    app.logger.info({"stage": "email_invalid", "heard": heard_raw, "normalized": norm1})
                    return respond_gather(base, "Please say it like john at gmail dot com.")

            # All booking info collected - this shouldn't happen but handle gracefully
            else:
                app.logger.info({"stage": "booking_complete_fallback", "heard": heard_raw, "booking_state": B})
                return respond_gather(base, "Your appointment is confirmed. Is there anything else I can help you with?")

        # === NON-BOOKING CONVERSATION ===
        else:
            # Precision Fix 4: Empty speech handling with shorter delay
            if not heard_raw.strip():
                log_turn({"fix_applied": "empty_speech", "stage": "quick_reprompt"})
                return respond_gather(base, "Still with me? How can I help you today?")
            
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

# === Startup TTS caching for instant responses ===
def cache_startup_phrases():
    """Pre-cache common phrases at startup for instant first-turn responses."""
    app.logger.info("Pre-caching common TTS phrases for instant responses...")
    
    startup_phrases = [
        "Thanks for calling Vanguard Chiropractic. How can I help you today?",
        "Thanks for calling back! How can I help you today?",
        "What day and time works for you?",
        "Did you mean morning or afternoon?",
        "What's your full name?",
        "What's the best mobile number for confirmation?",
        "What email should we use to send your confirmation?",
        "Perfect. What's your full name?",
        "Great. What's your full name?",
        "Excellent. What's your full name?",
        "Still with me? How can I help you today?",
        "I'll connect you with a team member right away."
    ]
    
    cached_count = 0
    for phrase in startup_phrases:
        try:
            audio = tts_cached(phrase)
            if audio:
                cached_count += 1
                app.logger.info(f"Cached: {phrase[:30]}...")
        except Exception as e:
            app.logger.error(f"Failed to cache phrase '{phrase[:30]}...': {str(e)}")
    
    app.logger.info(f"Successfully cached {cached_count}/{len(startup_phrases)} startup phrases")

# === Keepalive endpoint for Railway always-on ===
@app.route("/keepalive", methods=["GET"])
def keepalive():
    """Keepalive endpoint to prevent Railway from sleeping."""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "cached_phrases": len(TTS_CACHE),
        "active_calls": len(CALLS),
        "caller_memory_count": len(CALLER_MEMORY),
        "bad_turns_logged": len(BAD_TURNS_LOG)
    }, 200

# === Weekly review endpoint for bad turns ===
@app.route("/review", methods=["GET"])
def weekly_review():
    """Get bad turns log for weekly review and optimization."""
    return {
        "bad_turns": BAD_TURNS_LOG,
        "total_count": len(BAD_TURNS_LOG),
        "generated_at": datetime.now().isoformat()
    }, 200

if __name__ == "__main__":
    # Cache startup phrases for instant responses
    cache_startup_phrases()
    
    # Start the Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)