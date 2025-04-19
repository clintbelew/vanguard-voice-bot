import os
import logging
from flask import Flask
from pathlib import Path

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("voice_bot.log"),
            logging.StreamHandler()
        ]
    )
    
    # Ensure log directories exist
    os.makedirs('logs', exist_ok=True)
    
    # Ensure audio cache directory exists
    os.makedirs('audio_cache', exist_ok=True)
    
    # Initialize ElevenLabs API
    from app.elevenlabs_integration import elevenlabs_api
    if elevenlabs_api.is_configured():
        logging.info("ElevenLabs API initialized successfully")
    else:
        logging.warning("ElevenLabs API not fully configured. Voice responses will use Polly fallback.")
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        logging.error(f"404 error: {str(e)}")
        return "Not Found", 404
    
    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"500 error: {str(e)}")
        return "Internal Server Error", 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {str(e)}")
        return "Internal Server Error", 500
    
    return app
