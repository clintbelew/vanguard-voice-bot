from flask import Flask, Blueprint
from flask_cors import CORS

# Create a blueprint for the routes
routes_bp = Blueprint('routes', __name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    # Import routes after creating app to avoid circular imports
    from app import routes
    
    # Register blueprints
    app.register_blueprint(routes_bp)
    
    return app
