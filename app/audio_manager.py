import os
import hashlib
import logging
from flask import send_from_directory, Response, request

# Define CACHE_DIR as a module-level variable that can be imported by other modules
CACHE_DIR = os.environ.get('AUDIO_CACHE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'audio_cache'))
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'audio_manager.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"Audio cache directory: {CACHE_DIR}")

def get_audio_bp():
    """
    Returns a function that serves audio files from the cache directory.
    """
    from flask import Blueprint
    audio_bp = Blueprint('audio', __name__)

    @audio_bp.route('/<filename>')
    def serve_audio(filename):
        try:
            # Log the request
            logger.info(f"Serving audio file: {filename}")
            
            # Check if the file exists
            file_path = os.path.join(CACHE_DIR, filename)
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {filename}")
                return Response(f"Audio file not found: {filename}", status=404)
            
            # Create response with the file
            response = send_from_directory(CACHE_DIR, filename)
            
            # Add CORS headers to allow Twilio to access the audio files
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Content-Type'] = 'audio/mpeg'
            response.headers['Cache-Control'] = 'public, max-age=86400'
            
            return response
        except Exception as e:
            logger.error(f"Error serving audio file {filename}: {str(e)}")
            return Response(f"Error serving audio file: {str(e)}", status=500)

    @audio_bp.route('/<filename>', methods=['OPTIONS'])
    def options(filename):
        # Handle OPTIONS method for CORS preflight requests
        response = Response('')
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    return audio_bp

def get_cache_path(text_hash):
    """
    Returns the path to the cached audio file for the given text hash.
    """
    try:
        # Ensure the cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Return the path to the cached file
        return os.path.join(CACHE_DIR, f"{text_hash}.mp3")
    except Exception as e:
        logger.error(f"Error getting cache path for {text_hash}: {str(e)}")
        # Return a fallback path in the current directory
        return f"{text_hash}.mp3"

def get_text_hash(text):
    """
    Returns a hash of the given text.
    """
    try:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    except Exception as e:
        logger.error(f"Error hashing text: {str(e)}")
        # Return a fallback hash
        return hashlib.md5(b"error_fallback").hexdigest()

