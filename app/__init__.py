from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)
    
    return app
