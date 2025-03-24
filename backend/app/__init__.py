import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import get_config
from controllers import instagram_monitor
from app.routes import api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    config = get_config()
    
    # Load configuration
    app.config.from_object(config)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configure rate limiting
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[config.RATELIMIT_DEFAULT],
        storage_uri=config.RATELIMIT_STORAGE_URL
    )
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    # Start the Instagram monitor in the background
    @app.before_first_request
    def start_monitor():
        instagram_monitor.start()
    
    # Shutdown the Instagram monitor when the app is stopping
    @app.teardown_appcontext
    def stop_monitor(exception=None):
        instagram_monitor.stop()
    
    # Health check route
    @app.route('/health', methods=['GET'])
    @limiter.exempt
    def health_check():
        return {'status': 'ok'}, 200
    
    return app

app = create_app() 