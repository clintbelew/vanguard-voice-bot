"""
Initialize the Flask application.
"""
from flask import Flask
import logging
import os
from config.config import LOG_LEVEL, LOG_FORMAT, LOG_FILE

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Ensure log directories exist
    os.makedirs('logs', exist_ok=True)
    
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
