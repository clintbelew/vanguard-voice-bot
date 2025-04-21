"""
Initialize the Flask application.
"""
from flask import Flask

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app

# Create the application instance
app = create_app()
