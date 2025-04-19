"""
Updated app/__init__.py to integrate all new modules

This file initializes the Flask application and registers all blueprints
including the new audio serving blueprint for ElevenLabs integration.
"""

from flask import Flask
import os
import logging
from app.audio_manager import audio_bp, CACHE_DIR, LOGS_DIR

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
