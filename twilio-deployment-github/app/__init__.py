from flask import Flask
from config.config import PORT, DEBUG

def create_app():
    """Initialize the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_pyfile('../config/config.py')
    
    # Register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app
