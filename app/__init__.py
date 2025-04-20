"""
Updated app/__init__.py to integrate all new modules and add CORS support

This file initializes the Flask application and registers all blueprints
including the new audio serving blueprint for ElevenLabs integration.
It also configures CORS to allow Twilio to access audio files.
"""

from flask import Flask
import os
import logging
from app.audio_manager import audio_bp, CACHE_DIR, LOGS_DIR
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    # Create the Flask app
    app = Flask(__name__)
    
    # Configure CORS to allow Twilio to access audio files
    CORS(app, resources={
        r"/audio/*": {
            "origins": "*",
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    logger.info("CORS configured for audio routes")
    
    # Ensure the audio cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)
    logger.info(f"Audio cache directory confirmed at: {CACHE_DIR}")
    
    # Ensure the logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger.info(f"Logs directory confirmed at: {LOGS_DIR}")
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    logger.info("Main blueprint registered")
    
    # Register audio blueprint for serving cached audio files
    app.register_blueprint(audio_bp)
    logger.info("Audio blueprint registered")
    
    return app
