from flask import Flask
from flask_cors import CORS
from app.routes import routes_bp

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(routes_bp)
    
    return app
